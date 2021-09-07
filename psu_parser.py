# Import modules for work with web and html
import requests
from selenium import webdriver
from selenium.common.exceptions import *
from bs4 import BeautifulSoup

# Import Google API modules
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Import helpers
from time import time, sleep, strftime
import os.path
import pickle
from zipfile import ZipFile
from datetime import datetime
from configparser import ConfigParser
from typing import *
import re
import ini_creator


class PSUParser:
    def __init__(self, login: str, password: str, conf_filename: str = ''):
        self.TIMETABLE_URL = 'pls/stu_cus_et/stu.timetable/'
        if not conf_filename or not os.path.exists(conf_filename):
            print("No config found")
            conf_filename = ini_creator.write_config_to_file()
            print("Default config created")
        self.conf_filename = conf_filename
        self.config = ConfigParser()
        self.config.read(conf_filename)

        self.requester = PSURequester(
            login, password,
            int(self.config['ProgData']['timeout_start'])
        )

    def set_timetable_to_calendar(self):
        # Get html source of timetable webpage
        url = self.TIMETABLE_URL + '?p_cons=y&p_week='

        page_source = self.requester.get_page(url)
        
        self.config['ProgData']['LastCode'] = page_source[0:10]
        self.config.write(open(self.conf_filename, 'w'))

        # '!' means 'error'
        if page_source[0] == '!':
            if page_source == '!Login failed':
                self.config['ProgData']['timeout_start'] = str(int(time()))
                self.config.write(open(self.conf_filename, 'w'))
            return page_source

        # Create Google Calendar service (Google API)
        service = build('calendar', 'v3', credentials=self.login_into_google())

        # Find calendar called "PSU Timetable" or,
        # if it doesn't exist, create it
        calendar_id = None
        page_token = None
        while True:
            calendar_list = service.calendarList().list(
                pageToken=page_token
            ).execute()
            for calendar_list_entry in calendar_list['items']:
                if calendar_list_entry['summary'] == 'PSU Timetable':
                    calendar_id = calendar_list_entry['id']
                    break
            page_token = calendar_list.get('nextPageToken')
            if not page_token or calendar_id:
                break

        if not calendar_id:
            calendar_id = service.calendars().insert(body={
                'summary': 'PSU Timetable',
                'timeZone': 'Etc/GMT-5'
            }).execute()['id']

        # Parse html code
        page = BeautifulSoup(page_source, 'html5lib')

        # Find current week number
        cur_week = page.find('li', attrs={'class': re.compile('week .* current')})
        if not cur_week:
            cur_week = page.find('li', attrs={'class': re.compile('week .*')})
        if not cur_week:
            return "!Parse error"
        cur_week_i = int(cur_week.text)

        while cur_week_i:
            for day in page.find_all('div', attrs={'class': 'day'}):
                # Format of 'date' - day_of_week day month
                date = day.find('h3').text.split(' ')
                # Construct date to RFC3339 format (yyyy-mm-dd)
                day_n = '{:0>2}'.format(date[1])
                month_n = '{:0>2}'.format(self.config['Months'][date[2]])
                year_n = strftime('%Y')
                if int(month_n) < int(strftime('%m')):
                    year_n = str(int(year_n) + 1)
                rfc_date = year_n + '-' + month_n + '-' + day_n

                old_lessons = service.events().list(
                    calendarId=calendar_id,
                    timeMin=rfc_date + 'T' + '00:00:00+05:00',
                    timeMax=rfc_date + 'T' + '23:59:00+05:00'
                ).execute()['items']

                for lesson in day.find_all('tr'):
                    # If this lesson isn't empty
                    if lesson.find('span', attrs={'class': 'dis'}):
                        pair_num = lesson.find('td', attrs={'pair_num'}).text
                        lesson_num = pair_num[:pair_num.index(' ')]

                        dis = lesson.find(
                            'span',
                            attrs={'class': 'dis'}).find('a').text
                        subject = dis[0:dis.rfind('(') - 1]
                        type_of_lesson = self.config['LessonTypes'][
                            dis[dis.rfind('(') + 1:-1]
                        ]

                        aud = lesson.find('span', attrs={'class': 'aud'})
                        if aud.find('a'):
                            event_description = aud.find('a').get('href')
                            classroom = 'Дист'
                        else:
                            event_description = self.config.get(
                                type_of_lesson, subject, fallback=''
                            )
                            classroom = lesson.find(
                                'span',
                                attrs={'class': 'aud'}
                            ).text.split(' ')[1]
                            if classroom == 'Дистанционно':
                                classroom = 'Дист'

                        event_summary = self.config.get(
                            'Abbreviations',
                            subject,
                            fallback=subject) + ' (' + classroom + ')'
                        event_start_time = (rfc_date + 'T'
                                            + self.config['ClassesStartEnd'][
                                               'start' + lesson_num]
                                            + '+05:00')
                        event_end_time = (rfc_date + 'T'
                                          + self.config['ClassesStartEnd'][
                                              'end' + lesson_num]
                                          + '+05:00')

                        create_new_event = True
                        for event in old_lessons:   
                            old_event_start = datetime.strptime(
                                event['start']['dateTime'],
                                '%Y-%m-%dT%H:%M:%S+05:00'
                            )
                            if (event['summary'] == event_summary
                                and old_event_start.isoformat('T') + '+05:00'== event_start_time
                                and (event_description == event.get('description')
                                     or event_description == ''
                                     and not event.get('description'))):
                                old_lessons.remove(event)
                                create_new_event = False
                                break

                        if create_new_event:
                            print('New lesson: ', event_summary, ' - ',
                                  event_start_time, ', ', event_description)
                            event = service.events().insert(
                                calendarId=calendar_id,
                                body={
                                    'summary': event_summary,
                                    'description': event_description,
                                    'start': {
                                        'dateTime': event_start_time,
                                        'timeZone': 'Etc/GMT-5'
                                    },
                                    'end': {
                                        'dateTime': event_end_time,
                                        'timeZone': 'Etc/GMT-5'
                                    },
                                    'reminders': {
                                        'useDefault': True
                                    },
                                    'colorId': self.config[type_of_lesson][
                                        'color'
                                    ]
                                }).execute()
                for event in old_lessons:
                    print('Lesson deleted: ', event['summary'], '-',
                          event['start']['dateTime'],
                          event['description'] if event.get('description') else '')
                    service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()

            # Go to the next week, if it isn't the last one
            cur_week_i += 1
            page_source = self.requester.get_page(url + str(cur_week_i))
            page = BeautifulSoup(page_source, 'html5lib')
            if not page.find('div', attrs={'class': 'timetable'}):
                cur_week_i = 0
                
        self.config['ProgData']['LastUseTime'] = datetime.now().strftime('pres-%Y-%m-%dT%H:%M:%S')
        self.config.write(open(self.conf_filename, 'w'))

        return 'Completed'

    def login_into_google(self):
        scopes = ['https://www.googleapis.com/auth/calendar']

        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json',
                    scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds


class PSURequester:

    def __init__(self, login: str, password: str, timeout_start: int):
        self.LOGIN = login
        self.PASSWORD = password
        self.MAIN_URL = 'https://student.psu.ru/'
        self.ses = requests.Session()
        self.ses.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/84.0.4147.125 YaBrowser/20.8.2.92 '
                          'Yowser/2.5 Safari/537.36}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}

        self.timeout_start = timeout_start

    def login(self):
        driver = self.setup_chromedriver()
        if not driver:
            driver = self.setup_geckodriver()
        if not driver:
            return 1

        driver.implicitly_wait(10)
        driver.get(self.MAIN_URL)

        driver.find_element_by_id('login').send_keys(self.LOGIN)
        driver.find_element_by_id('password').send_keys(self.PASSWORD)
        driver.find_element_by_id('sbmt').click()

        result_code = 0
        try:
            # If authorization happened with an error,
            # start counting the 10-minutes timeout
            driver.find_element_by_class_name('error_message')
            open(' last_error_page.html', 'w').write(driver.page_source)
            result_code = 1
        except NoSuchElementException:
            # Else copy cookies from webdriver to main requests session
            self.ses.cookies.clear()
            self.set_cookies_to_session(driver.get_cookies())
            # self.ses.headers = driver.requests[0].headers
        driver.close()
        driver.quit()
        return result_code

    def get_page(self, url: str = ''):
        if self.timeout_start:
            if time() - self.timeout_start < 600:
                # If request happens during 10-minutes login timeout
                # (after 5 unsuccessful login attempts), abort the method
                return ('!Login timeout, '
                        + str(600 - int(time() - self.timeout_start))
                        + ' seconds remain')
            else:
                # If timeout has been started more that 10 minutes ago, nullify it
                self.timeout_start = 0

        res = self.ses.get(self.MAIN_URL + url)
        soup = BeautifulSoup(res.text, 'html5lib')
        # TODO: проверить будет ли таймаут без автологина
        if soup.find('div', attrs={'class': 'login'}):
            print('Login...')
            login_error = self.login()
            if login_error:
                self.timeout_start = time()
                return '!Login failed'
            res = self.ses.get(self.MAIN_URL + url)
        return res.text

    def set_cookies_to_session(self, cookies: List[Dict]):
        for c in cookies:
            c['rest'] = {'HttpOnly': c['httpOnly']}
            c.pop('httpOnly')
            self.ses.cookies.set_cookie(requests.cookies.create_cookie(**c))

    def setup_chromedriver(self):
        try:
            options = webdriver.ChromeOptions()
            options.headless = True
            driver = webdriver.Chrome(options=options)
        except Exception as ex:
            if 'This version of' in str(ex):
                browser_version = re.search(
                    r'Current browser version is (\d+)',
                    str(ex)
                ).group(1)
                print(f'Your version of ChromeDrive doesn`t match with '
                      f'browser version ({browser_version}...)\n'
                      f'Downloading of necessary version...')

                page_source = requests.get('https://chromedriver.chromium.org/downloads').text

                driver_version = re.search(
                    rf'ChromeDriver ({browser_version}(\.|\d)*)', page_source
                ).group(1)
                open('chromedriver.zip', 'wb').write(
                    requests.get(
                        'https://chromedriver.storage.googleapis.com/'
                        + driver_version + '/chromedriver_win32.zip'
                    ).content
                )
                ZipFile('chromedriver.zip', 'r').extractall()
                os.remove('chromedriver.zip')

                try:
                    options = webdriver.ChromeOptions()
                    options.headless = True
                    return webdriver.Chrome(options=options)
                except:
                    return None
            else:
                return None
        else:
            return driver

    def setup_geckodriver(self):
        try:
            options = webdriver.FirefoxOptions()
            options.headless = True
            return webdriver.Firefox(options=options)
        except:
            return None

    def __del__(self):
        self.ses.close()
