# -*- coding: utf-8 -*-
# !/usr/bin/python
import math
import time
from datetime import datetime, timedelta

import requests


def format_countdown_time(countdown_times):
    countdown_all_times = []
    countdown_time_units = ["天", "时", "分", "秒"]
    for index, countdown_time in enumerate(countdown_times):
        countdown_all_times.append(countdown_time)
        countdown_all_times.append(countdown_time_units[index])
    return " ".join(countdown_all_times)


def get_start_buying_time(countdown_times):
    current_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    days_delta = timedelta(days=int(countdown_times[0]))
    hours_delta = timedelta(hours=int(countdown_times[1]))
    minutes_delta = timedelta(minutes=int(countdown_times[2]))
    seconds_delta = timedelta(seconds=int(countdown_times[3]))
    start_buying_date = current_date + days_delta + hours_delta + minutes_delta + seconds_delta
    return start_buying_date


def date_second_add(date, seconds):
    seconds_delta = timedelta(seconds=seconds)
    return date + seconds_delta


def seconds_diff(d1, d2):
    return (d2 - d1).total_seconds()


def get_hw_server_timestamp():
    res = requests.get("https://buy.vmall.com/queryRushbuyInfo.json?sbomCodes=2601010453707&portal=1&t=1697127872971")
    if res.ok:
        data = res.json()
        return data['currentTime']


def get_local_timestamp():
    return math.floor(time.time() * 1000)
