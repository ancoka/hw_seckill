# -*- coding: utf-8 -*-
# !/usr/bin/python
import os
import sys
from datetime import datetime
from selenium.common import WebDriverException
from huawei import HuaWei
from loguru import logger

LOGURU_FORMAT = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                 "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                 "<cyan>{thread.name}</cyan>:<cyan>{thread.id}</cyan> - <level>{message}</level>")


def main():
    huawei = HuaWei()
    try:
        huawei.start_process()
        huawei.stop_process()
    except WebDriverException as we:
        logger.error("程序执行异常：except: {}", we)
    finally:
        if os.path.exists(huawei.cookiesFile):
            os.remove(huawei.cookiesFile)


def log():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_name = os.path.join(log_path, "log_all_{}.log".format(datetime.now().strftime('%Y%m%d')))
    log_error_name = os.path.join(log_path, "log_error_{}.log".format(datetime.now().strftime('%Y%m%d')))
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
    banner = """
        ooooo   ooooo                           .oooooo..o                     oooo    oooo  o8o  oooo  oooo  
        `888'   `888'                          d8P'    `Y8                     `888   .8P'   `"'  `888  `888  
         888     888  oooo oooo    ooo         Y88bo.       .ooooo.   .ooooo.   888  d8'    oooo   888   888  
         888ooooo888   `88. `88.  .8'           `"Y8888o.  d88' `88b d88' `"Y8  88888[      `888   888   888  
         888     888    `88..]88..8'   8888888      `"Y88b 888ooo888 888        888`88b.     888   888   888  
         888     888     `888'`888'            oo     .d8P 888    .o 888   .o8  888  `88b.   888   888   888  
        o888o   o888o     `8'  `8'             8""88888P'  `Y8bod8P' `Y8bod8P' o888o  o888o o888o o888o o888o                                                                                                                                                                             
    """
    log()
    logger.info(banner)
    try:
        main()
    except KeyboardInterrupt:
        logger.info("正常退出")
        exit(0)
