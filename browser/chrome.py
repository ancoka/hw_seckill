# -*- coding: utf-8 -*-
# !/usr/bin/python
import os

from selenium import webdriver

from browser.browser import Browser
from config import Config


class ChromeBrowser(Browser):
    def setting(self, config: Config = None, log_path: str = "", user_data_dir: str = ""):
        options = webdriver.ChromeOptions()

        options.add_argument(r"--user-data-dir={}".format(user_data_dir))
        options.add_argument(r"--profile-directory={}".format("Default"))
        if config.getboolean("browser", "headless", False):
            options.add_argument('--headless')
            # headless 模式下需要设置user_agent及窗口大小，否则会被识别成移动端访问
            default_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
            user_agent = config.get("browser", "userAgent", default_user_agent)
            options.add_argument(r"user-agent={}".format(user_agent))
            options.add_argument("--window-size=1920,1080")

        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-ssl-error')
        options.add_argument('--logs-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')


        driver_path = config.get("browser", "driverPath", '')
        executable_path = None if len(driver_path) < 1 else driver_path
        browser = webdriver.Chrome(service=webdriver.ChromeService(executable_path=executable_path, log_path=log_path),
                                   options=options)
        return browser
