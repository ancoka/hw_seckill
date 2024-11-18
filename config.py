# -*- coding: utf-8 -*-
# !/usr/bin/python

from configparser import ConfigParser
from loguru import logger


class Config:
    def __init__(self, filename, encoding="utf-8"):
        logger.info("开始解析配置文件")
        self.filename = filename
        self.encoding = encoding
        self.config = ConfigParser()
        self.config.read(filename, encoding)
        logger.info("结束解析配置文件")

    def get(self, section, option, default_value=None):
        if default_value is None:
            return self.config.get(section, option)
        else:
            return self.config.get(section, option, fallback=default_value)

    def getboolean(self, section, option, default_value=None):
        if default_value is None:
            return self.config.getboolean(section, option)
        else:
            return self.config.getboolean(section, option, fallback=default_value)
