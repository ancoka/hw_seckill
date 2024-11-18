# -*- coding: utf-8 -*-
# !/usr/bin/python
import math
import time

import requests
from loguru import logger
from datetime import datetime, timedelta


def server_time():
    logger.info("开始获取华为服务器时间")
    url = "https://buy.vmall.com/queryRushbuyInfo.json?sbomCodes=2601010453707&portal=1&t=1697127872971"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        return data['currentTime']
    else:
        logger.error("华为服务器获取时间失败！")


def local_time():
    logger.info("开始获取本地机器时间")
    local_timestamp = math.floor(time.time() * 1000)
    return local_timestamp


def local_hw_time_diff():
    start_timestamp = local_time()
    server_timestamp = server_time()
    end_timestamp = local_time()

    # 使用平均时间来获取更准确的本地时间戳
    local_timestamp = round((start_timestamp + end_timestamp) / 2)
    ms_diff = milliseconds_diff(local_timestamp, server_timestamp)
    logger.info("当前华为服务器时间为：[{}]", timestamp2time(server_timestamp))
    logger.info("当前本地时间为：【{}】", timestamp2time(local_timestamp))

    compareRes = "晚于" if ms_diff >= 0 else "早于"
    logger.info("结束获取华为服务器时间及本地时间，结果：本地时间【{}】华为服务器时间【{}】毫秒", compareRes,
                abs(ms_diff))
    return server_timestamp, local_timestamp, ms_diff


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


def milliseconds_diff(local_timestamp, hw_server_timestamp):
    ms_diff = local_timestamp - hw_server_timestamp
    return ms_diff


def seconds_diff(d1, d2):
    return (d2 - d1).total_seconds()


def timestamp2time(timestamp):
    fromDatetime = datetime.fromtimestamp(timestamp / 1000)
    return fromDatetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def calc_countdown_ms_diff(target_date_time, ms_diff):
    local_timestamp = local_time() - ms_diff
    target_timestamp = math.floor(target_date_time.timestamp() * 1000)
    return target_timestamp - local_timestamp


def calc_countdown_times(target_date_time, ms_diff):
    local_timestamp = local_time() - ms_diff
    target_timestamp = math.floor(target_date_time.timestamp() * 1000)
    origin_timestamp_sec_diff = (target_timestamp - local_timestamp) / 1000
    timestamp_sec_diff = math.floor(origin_timestamp_sec_diff)

    days = max(math.floor(timestamp_sec_diff / 86400), 0)
    timestamp_sec_diff = timestamp_sec_diff - days * 86400
    hours = max(math.floor(timestamp_sec_diff / 3600), 0)
    timestamp_sec_diff = timestamp_sec_diff - hours * 3600
    minutes = max(math.floor(timestamp_sec_diff / 60), 0)
    seconds = max(timestamp_sec_diff - minutes * 60, 0)
    microseconds = max(
        math.floor((origin_timestamp_sec_diff - days * 86400 - hours * 3600 - minutes * 60 - seconds) * 1000),
        0)
    countdown_times = [str(days).zfill(2), str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2),
                       str(microseconds).zfill(3)]
    return countdown_times
