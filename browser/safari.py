# -*- coding: utf-8 -*-
# !/usr/bin/python
from selenium import webdriver

from browser.browser import Browser
from config import Config


class SafariBrowser(Browser):

    def setting(self, config: Config = None, log_path: str = "", userDataDir: str = ""):
        options = webdriver.SafariOptions()

        if config.getboolean("browser", "headless", False):
            options.add_argument('--headless')
            defaultUserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            userAgent = config.get("browser", "userAgent", defaultUserAgent)
            options.add_argument(r"--user-agent={}".format(userAgent))
            options.add_argument("--window-size=1920,1080")

        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-ssl-error')
        options.add_argument('--logs-level=3')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')

        driverPath = config.get("browser", "driverPath", '')
        executable_path = None if len(driverPath) < 1 else driverPath
        browser = webdriver.Safari(service=webdriver.SafariService(executable_path=executable_path, log_path=log_path,
                                                                   service_args=["--diagnose"]),
                                   options=options)
        browser.set_window_size(1920, 1080)
        return browser
