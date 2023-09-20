# -*- coding: utf-8 -*-
# !/usr/bin/python

from huawei import HuaWei


def main():
    huawei = HuaWei("config.ini")
    huawei.start_process()
    huawei.stop_process()


if __name__ == '__main__':
    main()
