# -*- coding: utf-8 -*-
# !/usr/bin/python
from datetime import datetime

from browser.browser import Browser
from browser.chrome import ChromeBrowser
from browser.edge import EdgeBrowser
from browser.firefox import FirefoxBrowser
from browser.safari import SafariBrowser
from loguru import logger


class BrowserFactory:

    @staticmethod
    def build(browser_type):
        support_browsers = ['chrome', 'firefox', 'edge', 'safari']
        if browser_type not in support_browsers:
            logger.info("不支持的浏览器类型，浏览器类型为：{}", browser_type)
            exit()

        return eval(browser_type.title() + "Browser")()
