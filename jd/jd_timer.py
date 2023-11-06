# -*- coding: utf-8 -*-
# !/usr/bin/python
import requests
from loguru import logger
from jd.jd_constants import JdConstants as JDC
from timer import Timer


class JdTimer(Timer):

    def server_time(self):
        resp = requests.get(JDC.API_DOMAIN)
        jdTimestamp = None
        if resp.ok:
            jdTimestamp = int(resp.headers.get('X-API-Request-Id')[-13:])
        else:
            logger.error("获取京东服务器时间失败！")
        return jdTimestamp



