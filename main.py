#!/usr/bin/env python3.7

from psu_parser import PSUParser
from configparser import ConfigParser


login_data = ConfigParser()
login_data.read('login_data.ini')

parser = PSUParser(login_data['LoginData']['login'], login_data['LoginData']['password'])
print(parser.set_timetable_to_calendar())
