# -*- coding: utf-8 -*-
# !/usr/bin/python
import os

# 项目目录及文件定义
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(PROJECT_PATH, "logs")
BASE_PROFILE_PATH = os.path.join(PROJECT_PATH, "profiles")
SELENIUM_LOG_FILE = os.path.join(LOG_PATH, "selenium.log")
COOKIES_FILE = os.path.join(PROJECT_PATH, "hw_cookies.txt")
CONFIG_FILE = os.path.join(PROJECT_PATH, "config.ini")

# 华为官网页面定义
INDEX_PAGE_URL = "www.vmall.com/index.html"
LOGIN_PAGE_URL = "id1.cloud.huawei.com/CAS/portal/loginAuth.html"
PRODUCT_PAGE_URL = "www.vmall.com/product/comdetail/index.html"
ORDER_PAGE_URL = "www.vmall.com/order/nowConfirmcart"
RUSH_ORDER_PAGE_URL = "www.vmall.com/order/rush/confirm"
PAYMENT_PAGE_URL = "payment.vmall.com/cashier/web/pcIndex.htm"

PAGES = [
    {'page': 'index', 'pageDesc': '首页', 'url': INDEX_PAGE_URL},
    {'page': 'login', 'pageDesc': '登录页', 'url': LOGIN_PAGE_URL},
    {'page': 'product', 'pageDesc': '产品页', 'url': PRODUCT_PAGE_URL},
    {'page': 'order', 'pageDesc': '下单页', 'url': ORDER_PAGE_URL},
    {'page': 'rushorder', 'pageDesc': '抢购下单页', 'url': RUSH_ORDER_PAGE_URL},
    {'page': 'payment', 'pageDesc': '付款页', 'url': PAYMENT_PAGE_URL}
]

# 提醒文案定义
TIP_MSGS = [
    '抱歉，已售完，下次再来',
    '抱歉，没有抢到',
    '抱歉，您没有抢到',
    '抱歉，仅限预约用户购买',
    '抢购活动未开始，看看其他商品吧',
    '本次发售商品数量有限，您已超过购买上限，将机会留给其他人吧',
    '本次发售商品数量有限，您已超过购买上限，请勿重复购买，将机会留给其他人吧',
    '活动已结束',
    '抱歉，不符合购买条件',
    '抱歉，您不符合购买条件',
    '登记排队，有货时通知您',
    '抱歉，库存不足',
    '您已超过购买上限，本场活动最多还能买',
    '当前排队人数过多，是否继续排队等待？',
    '排队中',
    '活动已结束',
    '秒杀火爆<br/>该秒杀商品已售罄',
]

DEFAULT_THREAD_NUM = '1'
DEFAULT_BROWSER_TYPE = 'chrome'

# 失败重试次数
RETRY_TIMES = 3
