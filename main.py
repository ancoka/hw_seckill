# -*- coding: utf-8 -*-
# !/usr/bin/python
import os
from datetime import datetime

from huawei import HuaWei
from loguru import logger


def main():
    try:
        huawei = HuaWei(os.path.abspath("./config.ini"))
        huawei.start_process()
        huawei.stop_process()
    except Exception as e:
        logger.error("程序执行异常：except: {}", e)


def log():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_name = os.path.join(log_path, "log_all_{}.log".format(datetime.now().strftime('%Y%m%d')))
    log_error_name = os.path.join(log_path, "log_error_{}.log".format(datetime.now().strftime('%Y%m%d')))
    logger.add(log_name, format="{time} {level} {message}", filter="", rotation='100 MB', retention='15 days',
               level="DEBUG", encoding='utf8', enqueue=True)
    logger.add(log_error_name, format="{time} {level} {message}", rotation='100 MB', retention='15 days',
               level="ERROR", encoding='utf8', enqueue=True)


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
    main()
