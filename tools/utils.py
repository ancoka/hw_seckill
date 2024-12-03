# -*- coding: utf-8 -*-
# !/usr/bin/python
import json
import locale
import os
import sys

import constants


def get_profile_path(base_profile_path, browser_type, serial_no=1):
    base_browser_profile_path = os.path.join(base_profile_path, browser_type)
    profile_path = os.path.join(base_browser_profile_path, "profile_{0}".format(serial_no))
    return profile_path


def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def set_locale_chinese():
    if sys.platform.startswith('win'):
        locale.setlocale(locale.LC_ALL, 'en')
        locale.setlocale(locale.LC_CTYPE, 'chinese')


def write_cookies(cookies):
    with open(constants.COOKIES_FILE, 'w') as f:
        f.write(json.dumps(cookies))
        f.close()


def read_cookies():
    cookies = None
    with open(constants.COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
        f.close()
    return cookies
