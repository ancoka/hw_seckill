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
    def build(browserType):
        supportBrowsers = ['chrome', 'firefox', 'edge', 'safari']
        if browserType not in supportBrowsers:
            logger.info("不支持的浏览器类型，浏览器类型为：{}", browserType)
            exit()

        return eval(browserType.title() + "Browser")()
