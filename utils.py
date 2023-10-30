# -*- coding: utf-8 -*-
# !/usr/bin/python
import math
import os
import time
from datetime import datetime, timedelta

import requests


def format_countdown_time(countdown_times):
    countdown_all_times = []
    countdown_time_units = ["天", "时", "分", "秒", "毫秒"]
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


def timestamp2time(timestamp):
    fromDatetime = datetime.fromtimestamp(timestamp / 1000)
    return fromDatetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def calc_countdown_ms_diff(targetDatetime, msDiff):
    localTimestamp = get_local_timestamp() - msDiff
    targetTimestamp = math.floor(targetDatetime.timestamp() * 1000)
    return targetTimestamp - localTimestamp


def calc_countdown_times(targetDatetime, msDiff):
    localTimestamp = get_local_timestamp() - msDiff
    targetTimestamp = math.floor(targetDatetime.timestamp() * 1000)
    originTimestampDiff = (targetTimestamp - localTimestamp) / 1000
    timestampDiff = math.floor(originTimestampDiff)

    days = max(math.floor(timestampDiff / 86400), 0)
    timestampDiff = timestampDiff - days * 86400
    hours = max(math.floor(timestampDiff / 3600), 0)
    timestampDiff = timestampDiff - hours * 3600
    minutes = max(math.floor(timestampDiff / 60), 0)
    seconds = max(timestampDiff - minutes * 60, 0)
    microseconds = max(math.floor((originTimestampDiff - days * 86400 - hours * 3600 - minutes * 60 - seconds) * 1000),
                       0)
    countdown_times = [str(days).zfill(2), str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2),
                       str(microseconds).zfill(3)]
    return countdown_times


def get_profile_path(baseProfilePath, browserType, profileIndex):
    baseBrowserProfilePath = os.path.join(baseProfilePath, browserType)
    return os.path.join(baseBrowserProfilePath, "profile_{0}".format(profileIndex))
