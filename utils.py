# -*- coding: utf-8 -*-
# !/usr/bin/python

def format_countdown_time(countdown_times):
    countdown_all_times = []
    countdown_time_units = ["天", "时", "分", "秒"]
    for index, countdown_time in enumerate(countdown_times):
        countdown_all_times.append(countdown_time)
        countdown_all_times.append(countdown_time_units[index])
    return " ".join(countdown_all_times)
