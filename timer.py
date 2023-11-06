# -*- coding: utf-8 -*-
# !/usr/bin/python
from abc import ABC
import time
from abc import abstractmethod
from datetime import datetime


class Timer(ABC):
    @abstractmethod
    def server_time(self):
        pass

    def local_time_diff(self):
        return self.local_time() - self.server_time()

    @staticmethod
    def local_time():
        localTimestamp = round(time.time() * 1000)
        return localTimestamp

    @staticmethod
    def timestamp2time(timestamp):
        fromDatetime = datetime.fromtimestamp(timestamp / 1000)
        return fromDatetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
