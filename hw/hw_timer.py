# -*- coding: utf-8 -*-
# !/usr/bin/python
import requests
from loguru import logger
from timer import Timer


class HwTimer(Timer):

    def server_time(self):
        resp = requests.get(
            "https://buy.vmall.com/queryRushbuyInfo.json?sbomCodes=2601010453707&portal=1&t=1697127872971")
        hwTimestamp = None
        if resp.ok:
            data = resp.json()
            hwTimestamp = data['currentTime']
        else:
            logger.error("获取华为服务器时间失败！")
        return hwTimestamp
