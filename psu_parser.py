# Import modules for work with web and html
import requests
# from seleniumwire import webdriver
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
from datetime import datetime
from typing import *
from configparser import ConfigParser
import ini_creator


class PSUParser:
    def __init__(self, login: str, password: str, conf_file_name: str = ''):
        self.TIMETABLE_URL = 'pls/stu_cus_et/stu.timetable/'

        self.requester = PSURequester(login, password)
        if not conf_file_name or not os.path.exists(conf_file_name):
            print("No config found")
            conf_file_name = ini_creator.write_config_to_file()
        self.config = ConfigParser()
        self.config.read(conf_file_name)

    def set_timetable_to_calendar(self):
        # Get html source of timetable webpage
        url = self.TIMETABLE_URL + '?p_cons=y&p_week='

        page_source = self.requester.get_page(url)

        # '!' means 'error'
        if page_source[0] == '!':
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

        cur_week = int(page.find(
            'li', attrs={'class': 'week theory current'}
        ).text)
        while cur_week:
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
                    if (lesson.find('span', attrs={'class': 'dis'}) and
                            lesson.find('span',
                                        attrs={'class': 'dis'}).find('a')):
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
                                                    type_of_lesson,
                                                    subject,
                                                    fallback='')
                            print(type_of_lesson, ' ', subject, ' ', event_description)
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
                            # print(1, ' ', event['start']['dateTime'])
                            old_event_start = datetime.strptime(
                                event['start']['dateTime'],
                                '%Y-%m-%dT%H:%M:%S+05:00'
                            )
                            #old_event_start = old_event_start.replace(
                             #   hour=(old_event_start.hour + 5)
                            #)
                            if (event['summary'] == event_summary and
                                    old_event_start.isoformat('T') + '+05:00'
                                    == event_start_time and
                                        (event_description
                                        == event.get('description') or
                                        event_description == '' and
                                        event.get('description') == None)):
                                old_lessons.remove(event)
                                create_new_event = False
                                break

                        if create_new_event:
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
                    service.events().delete(calendarId=calendar_id,
                                            eventId=event['id']).execute()

            # Go to the next week, if it isn't the last one
            cur_week += 1
            page_source = self.requester.get_page(url + str(cur_week))
            page = BeautifulSoup(page_source, 'html5lib')
            if not page.find('div', attrs={'class': 'timetable'}):
                cur_week = 0

        return '\n'

    def login_into_google(self):
        SCOPES = ['https://www.googleapis.com/auth/calendar']

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
                    SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def timetable_to_dicts(self):
        page_source = self.requester.get_page(self.TIMETABLE_URL)

        if page_source[0] == '!':
            return page_source

        page = BeautifulSoup(page_source, 'html5lib')
        res = []


class PSURequester:

    def __init__(self, login: str, password: str):
        self.LOGIN = login
        self.PASSWORD = password
        self.MAIN_URL = 'https://student.psu.ru/'
        self.ses = requests.Session()
        self.ses.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/84.0.4147.125 YaBrowser/20.8.2.92 Yowser/2.5 Safari/537.36}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}

        self.config = ConfigParser()

        self.timeout_start = 0

        # self.login()

    def login(self):
        if time() - self.timeout_start < 600:
            # If loginnig happens during 10-minutes login timeout
            # (after 5 unsuccessful login attempts), abort the method
            return 1
        if self.timeout_start:
            # If timeout has been started more that 10 minutes ago,
            # nullify it
            self.timeout_start = 0

        try:
            options = webdriver.ChromeOptions()
            options.headless = False
            driver = webdriver.Chrome(options=options)
        except:
            options = webdriver.FirefoxOptions()
            options.headless = False
            driver = webdriver.Firefox(options=options)

            # executable_path=r'/home/ondatr/pythonProjects/psu_parser/PSU_Parser/geckodriver') as driver:
        driver.implicitly_wait(3)
        driver.get(self.MAIN_URL)

        sleep(1)

        driver.find_element_by_id('login').send_keys(self.LOGIN)
        driver.find_element_by_id('password').send_keys(self.PASSWORD)
        driver.find_element_by_id('sbmt').click()

        '''self.selenium_funcs_without_stale_exc(driver.find_element_by_id('login').send_keys, self.LOGIN)
        self.selenium_funcs_without_stale_exc(driver.find_element_by_id('password').send_keys, self.PASSWORD)
        self.selenium_funcs_without_stale_exc(driver.find_element_by_id('sbmt').click)'''

        try:
            # If authorization happened with an error,
            # start counting the 10-minutes timeout
            driver.find_element_by_class_name('error_message')
            self.timeout_start = time()
            return 1
        except NoSuchElementException:
            # Else copy cookies from webdriver to main requests session
            self.ses.cookies.clear()
            self.set_cookies_to_session(driver.get_cookies())
            # self.ses.headers = driver.requests[0].headers
            return 0

    def get_page(self, url: str = ''):
        res = self.ses.get(self.MAIN_URL + url)
        open('test.html', 'w').write(res.text)
        soup = BeautifulSoup(res.text, 'html5lib')
        if soup.find('div', attrs={'class': 'login'}):
            print('login')
            login_error = self.login()
            if login_error:
                return '!Login failed.'
            res = self.ses.get(self.MAIN_URL + url)
        return res.text

    def set_cookies_to_session(self, cookies: List[Dict]):
        for c in cookies:
            c['rest'] = {'HttpOnly': c['httpOnly']}
            c.pop('httpOnly')
            self.ses.cookies.set_cookie(requests.cookies.create_cookie(**c))

    def selenium_funcs_without_stale_exc(self, func, *args):
        for attempt in range(50):
            print(attempt)
            try:
                return func(*args)
            except StaleElementReferenceException:
                sleep(0.1)

    def __del__(self):
        self.ses.close()
