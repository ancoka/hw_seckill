# -*- coding: utf-8 -*-
# !/usr/bin/python
from selenium import webdriver

from browser.browser import Browser
from config import Config


class FirefoxBrowser(Browser):

    def setting(self, config: Config = None, log_path: str = "", userDataDir: str = ""):
        options = webdriver.FirefoxOptions()

        if config.getboolean("browser", "headless", False):
            options.add_argument('--headless')
            defaultUserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0"
            userAgent = config.get("browser", "userAgent", defaultUserAgent)
            options.set_preference("general.useragent.override", userAgent)

        # options.add_argument(r"--profile-root={}".format(os.path.dirname(os.path.abspath(__file__))))
        # options.add_argument(r"-profile={}".format("profiles"))

        driverPath = config.get("browser", "driverPath", '')
        executable_path = None if len(driverPath) < 1 else driverPath
        browser = webdriver.Firefox(
            service=webdriver.FirefoxService(executable_path=executable_path, log_path=log_path),
            options=options)
        browser.set_window_size(1920, 1080)
        return browser
