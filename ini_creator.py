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
    },
    'LabLessons': {
        'color': 5,
    },
    'PracticalLessons': {
        'color': 6,
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
