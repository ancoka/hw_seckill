# -*- coding: utf-8 -*-
# !/usr/bin/python
import threading
from threading import Thread
from loguru import logger


class HuaWeiThread(Thread):
    def __init__(self, serial_no, huawei):
        self.serial_no = serial_no
        self.huawei = huawei
        Thread.__init__(self, name="thread_{0}".format(self.serial_no))

    def run(self):
        logger.info("线程：{} 开始运行，当前活跃线程数为：{}", threading.current_thread().name, threading.active_count())
        self.huawei.thread_process()
        self.huawei.stop_process()
