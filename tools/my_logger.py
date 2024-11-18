# -*- coding: utf-8 -*-
# !/usr/bin/python
import os
import sys
from datetime import datetime

from loguru import logger

log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILENAME = os.path.join(log_path, "log_all_{}.log".format(datetime.now().strftime('%Y%m%d')))
LOG_ERROR_FILENAME = os.path.join(log_path, "log_error_{}.log".format(datetime.now().strftime('%Y%m%d')))


def setup_logger():
    log_format = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                  "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                  "<cyan>{process.name}</cyan>:<cyan>{thread.name}</cyan> - <level>{message}</level>")
    logger.remove()
    logger.add(LOG_FILENAME, format=log_format, rotation='100 MB', retention='15 days', level="DEBUG", encoding='utf8',
               enqueue=True)
    logger.add(LOG_ERROR_FILENAME, format=log_format, rotation='100 MB', retention='15 days', level="ERROR",
               encoding='utf8',
               enqueue=True)
    logger.add(sink=sys.stdout, format=log_format, level="DEBUG")
