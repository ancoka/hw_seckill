# -*- coding: utf-8 -*-
# !/usr/bin/python
import time

from selenium import webdriver
from datetime import datetime

from selenium.common import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from configparser import ConfigParser


class HuaWei:
    browser = None
    configparser = None
    isLogin = False
    isCountdown = True
    isStartBuying = False

    def __init__(self, config_file):
        self.__config_parse(config_file)
        self.__browser_setting()

    def start_process(self):
        print("{0} 开启抢购华为 {1} 手机".format(datetime.now(), self.__config_get("product", "name")))
        self.__visit_official_website()
        self.__login()
        if self.isLogin:
            self.__visit_product_page()
            self.__choose_product()
            self.__countdown()
            self.__start_buying()

    def stop_process(self):
        print("{0} 结束抢购华为 {1} 手机".format(datetime.now(), self.__config_get("product", "name")))
        self.browser.quit()

    def __visit_official_website(self):
        print("{0} 开始进入华为官网".format(datetime.now()))
        self.browser.get('https://www.vmall.com/')
        self.browser.implicitly_wait(20)
        print("{0} 已进入华为官网".format(datetime.now()))
        time.sleep(0.01)

    def __visit_product_page(self):
        print("{0} 开始进入华为 {1} 产品详情页".format(datetime.now(), self.__config_get("product", "name")))
        self.browser.get("https://www.vmall.com/product/{0}.html".format(self.__config_get("product", "id")))
        self.browser.refresh()
        self.browser.implicitly_wait(20)
        print("{0} 已进入华为 {1} 产品详情页".format(datetime.now(), self.__config_get("product", "name")))
        time.sleep(0.01)

    def __choose_product(self):
        print("{0} 开始选择手机规格".format(datetime.now()))
        sku_color = self.__config_get("product", "color")
        sku_version = self.__config_get("product", "version")
        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.LINK_TEXT, f"{sku_color}"))
        ).click()
        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.LINK_TEXT, f"{sku_version}"))
        ).click()
        # self.browser.find_element(By.LINK_TEXT, f"{sku_color}").click()
        # self.browser.find_element(By.LINK_TEXT, f"{sku_version}").click()
        print("{0} 选择手机规格完成，颜色：{1} 版本：{2}".format(datetime.now(), sku_color, sku_version))
        time.sleep(0.01)

    def __login(self):
        print("{0} 开始登陆华为账号".format(datetime.now()))
        print("{0} 点击登录按钮".format(datetime.now()))
        login = self.browser.find_element(By.CLASS_NAME, "css-901oao")
        login.click()

        self.browser.implicitly_wait(20)
        print("{0} 已跳转登录页面".format(datetime.now()))

        print("{0} 开始输入账号及密码".format(datetime.now()))
        self.browser.find_elements(By.CLASS_NAME, "hwid-input")[0].send_keys(self.__config_get("user", "name"))
        self.browser.find_elements(By.CLASS_NAME, "hwid-input")[1].send_keys(self.__config_get("user", "password"))
        print("{0} 发起登陆请求".format(datetime.now()))
        self.browser.find_element(By.CLASS_NAME, "hwid-login-btn").click()

        """ 
            TODO：首次登陆浏览器不可信需要验证码登陆
        """

        self.browser.implicitly_wait(20)
        time.sleep(10)

        """ 
            TODO：实现cookie记录
        """

        text = self.browser.find_element(By.CLASS_NAME, "css-901oao").text
        self.isLogin = text == self.__config_get("user", "nickname")
        if self.isLogin:
            print("{0} 账号：{1} 已登陆".format(datetime.now(), text))
        else:
            print("{0} 账号登陆失败，请重试".format(datetime.now()))

        print("{0} 结束登陆华为账号".format(datetime.now()))

    def __browser_setting(self):
        print("{0} 开始设置浏览器参数".format(datetime.now()))
        options = webdriver.ChromeOptions()
        options.add_argument(r"--user-data-dir={}".format(self.__config_get("chrome", "userDataDir")))
        options.add_argument(r"--profile-directory={}".format("Profile 5"))
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("{0} 设置浏览器参数完成".format(datetime.now()))
        browser.maximize_window()
        self.browser = browser
        time.sleep(0.01)

    def __countdown(self):
        while self.isCountdown:
            countdown_times = self.__get_countdown_time()
            print("{0} 距离抢购开始还剩：{1}".format(datetime.now(), self.__format_countdown_time(countdown_times)))
            self.__set_start_buying(countdown_times)
            if not self.isStartBuying:
                time.sleep(1)

    def __start_buying(self):
        while self.isStartBuying:
            countdown_times = self.__get_countdown_time()
            print("{0} 距离抢购开始还剩：{1}".format(datetime.now(), self.__format_countdown_time(countdown_times)))
            button_element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='pro-operation']/a"))
            )
            button_element.click()
            time.sleep(0.0001)

    def __get_countdown_time(self):
        attempts = 0
        while attempts < 2:
            try:
                elements = WebDriverWait(self.browser, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@id='pro-operation-countdown']/ul/li/span"))
                )
                countdown_times = []
                for element in elements:
                    countdown_times.append(element.text)
                return countdown_times
            except StaleElementReferenceException:
                # 页面元素因为动态渲染，导致查找的元素不再是原来的元素，导致异常
                self.browser.refresh()
                self.browser.implicitly_wait(20)
                self.__choose_product()
                attempts += 1

    def __config_get(self, group_name, item_name):
        return self.configparser.get(group_name, item_name)

    def __config_parse(self, config_file):
        print("{0} 开始解析配置文件".format(datetime.now()))
        configparser = ConfigParser()
        configparser.read(config_file, "utf-8")
        self.configparser = configparser
        print("{0} 结束解析配置文件".format(datetime.now()))
        time.sleep(0.01)

    @staticmethod
    def __format_countdown_time(countdown_times):
        countdown_all_times = []
        countdown_time_units = ["天", "时", "分", "秒"]
        for index, countdown_time in enumerate(countdown_times):
            countdown_all_times.append(countdown_time)
            countdown_all_times.append(countdown_time_units[index])
        return " ".join(countdown_all_times)

    def __set_start_buying(self, countdown_times):
        if countdown_times[0] != "00" or countdown_times[1] != "00" or countdown_times[2] != "00":
            return
        if int(countdown_times[3]) < 10:
            self.isCountdown = False
            self.isStartBuying = True
