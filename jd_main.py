# -*- coding: utf-8 -*-
# !/usr/bin/python
import os
import sys
from datetime import datetime
from loguru import logger
from jd.jd_timer import JdTimer

from jd.jd_constants import JdConstants as JDC

basePath = os.path.dirname(os.path.abspath(__file__))
rootPath = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]


def mian():
    logger.info("当前京东时间：{}", JdTimer.timestamp2time(JdTimer().server_time()))


def log():
    log_path = os.path.join(basePath, "logs")
    log_name = os.path.join(log_path, "jd_log_all_{}.log".format(datetime.now().strftime('%Y%m%d')))
    log_error_name = os.path.join(log_path, "jd_log_error_{}.log".format(datetime.now().strftime('%Y%m%d')))
    logFormat = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                 "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                 "<cyan>{process.name}</cyan>:<cyan>{thread.name}</cyan> - <level>{message}</level>")
    logger.remove()
    logger.add(log_name, format=logFormat, rotation='100 MB', retention='15 days', level="DEBUG", encoding='utf8',
               enqueue=True)
    logger.add(log_error_name, format=logFormat, rotation='100 MB', retention='15 days', level="ERROR", encoding='utf8',
               enqueue=True)
    logger.add(sink=sys.stdout, format=logFormat, level="DEBUG")


if __name__ == '__main__':
    log()
    mian()
