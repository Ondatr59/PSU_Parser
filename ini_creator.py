from configparser import ConfigParser


conf_dict = {
    'Abbreviations': {
        'template': 'Subject (Classroom)',
        'Математический анализ': 'Матан',
        'Системное и прикладное программное обеспечение': 'СППО',
        'Языки программирования': 'ЯП',
        'Физическая культура': 'Физра',
        'Дискретная математика [ИТ]': 'Дискретка',
        'Теория вероятностей и математическая статистика': 'Тервер',
        'Иностранный язык (английский) [Базовый уровень]': 'ИнЯз',
        'Операционные системы II': 'ОС 2',
    },
    'ClassesStartEnd': {
        'start1': '08:00:00',
        'end1': '09:35:00',
        'start2': '09:45:00',
        'end2': '11:20:00',
        'start3': '11:30:00',
        'end3': '13:05:00',
        'start4': '13:30:00',
        'end4': '15:05:00',
        'start5': '15:15:00',
        'end5': '16:50:00',
        'start6': '17:00:00',
        'end6': '18:35:00',
        'start7': '18:40:00',
        'end7': '20:15:00',
        'start8': '20:25:00',
        'end8': '22:00:00',
    },
    'SubjectsDescriptions': {
         '----------------': ''
    },
    'Lectures': {
        'color': 7,
        'системное и прикладное программное обеспечение': 'https://bbb7.psu.ru/b/dat-ghx-74y',
        'математический анализ': 'https://bbb11.psu.ru/b/lev-jya-pje',
        'операционные системы ii': 'https://us04web.zoom.us/j/74129488551?pwd=RWdTWHhsYTFSL21qR3JZRDJRLzl1QT09'
	                                'Meeting ID: 741 2948 8551'
	                                'Passcode: 2AxKsz',
        'теория вероятностей и математическая статистика': 'https://bbb5.psu.ru/b/chi-tgm-xvm',
        'дискретная математика [ит]': 'https://us02web.zoom.us/j/89084840750?pwd=bnhEWExoM3RNTmp1N2RZT245Q2trdz09'
	                                   'Идентификатор конференции: 890 8484 0750'
	                                   'Код доступа: 830608',
        'языки программирования': 'https://bbb7.psu.ru/b/zal-4j6-utm'
    },
    'LabLessons': {
        'color': 5,
    },
    'PracticalLessons': {
        'color': 6,
        'дискретная математика [ит]': 'https://us02web.zoom.us/j/82036883528',
        'физическая культура': 'https://us04web.zoom.us/j/73066239279?pwd=aG43THdNKzNXck5Ib2diL0VSQTlTUT09',
        'языки программирования': 'https://us04web.zoom.us/j/7499908231?pwd=YzJGQlRzVGwxTUQ1akh0RlExK2NYUT09',
        'операционные системы ii': 'https://bbb13.psu.ru/b/lab-hy3-v9a',
        'теория вероятностей и математическая статистика' : 'https://bbb8.psu.ru/b/bal-zjq-e2e',
        'математический анализ': 'Discord'
    },
    'Consultations': {
        'color': 3,
    },
    'Months': {
            'января': '1',
            'февраля': '2',
            'марта': '3',
            'апреля': '4',
            'мая': '5',
            'июня': '6',
            'июля': '7',
            'августа': '8',
            'сентября': '9',
            'октября': '10',
            'ноября': '11',
            'декабря': '12'
    },
    'LessonTypes': {
        'лек': 'Lectures',
        'лаб': 'LabLessons',
        'практ': 'PracticalLessons'
    },
    'ProgData': {
        'timeout_start': 0
    }
}

config = ConfigParser()
config.read_dict(conf_dict)

def write_config_to_file():
    config.write(open('config.ini', 'w'))
    return 'config.ini'

def get_default_config():
    return config


'''login_data = ConfigParser()
login_data.read_dict({
    'LoginData': {
        'login': '',
        'password': ''
    }
})'''
#login_data.write(open('login_data.ini', 'w'))


if __name__ == '__main__':
    write_config_to_file()
