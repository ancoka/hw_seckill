# -*- coding: utf-8 -*-
# !/usr/bin/python
import threading
from threading import Thread
from loguru import logger
from selenium.common import WebDriverException, NoSuchWindowException


class HuaWeiThread(Thread):
    def __init__(self, serial_no, huawei):
        self.serial_no = serial_no
        self.huawei = huawei
        Thread.__init__(self, name="thread_{0}".format(self.serial_no))

    def run(self):
        try:
            logger.info("线程：{} 开始运行，当前活跃线程数为：{}", threading.current_thread().name, threading.active_count())
            self.huawei.thread_process()
            self.huawei.stop_process()
        except NoSuchWindowException:
            logger.info("已关闭浏览器窗口，程序自动退出")
        except WebDriverException as we:
            logger.error("程序执行异常：except: {}", we)
        except Exception as e:
            logger.error("线程：{} 运行异常：{}", threading.current_thread().name, e)
