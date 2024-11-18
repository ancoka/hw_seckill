# -*- coding: utf-8 -*-
# !/usr/bin/python
from selenium import webdriver

from browser.browser import Browser
from config import Config


class FirefoxBrowser(Browser):

    def setting(self, config: Config = None, log_path: str = "", user_data_dir: str = ""):
        options = webdriver.FirefoxOptions()

        if config.getboolean("browser", "headless", False):
            options.add_argument('--headless')
            default_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0"
            user_agent = config.get("browser", "userAgent", default_user_agent)
            options.set_preference("general.useragent.override", user_agent)

        # options.add_argument(r"--profile-root={}".format(os.path.dirname(os.path.abspath(__file__))))
        # options.add_argument(r"-profile={}".format("profiles"))

        driver_path = config.get("browser", "driverPath", '')
        executable_path = None if len(driver_path) < 1 else driver_path
        browser = webdriver.Firefox(
            service=webdriver.FirefoxService(executable_path=executable_path, log_path=log_path),
            options=options)
        browser.set_window_size(1920, 1080)
        return browser
