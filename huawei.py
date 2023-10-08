# -*- coding: utf-8 -*-
# !/usr/bin/python
import os.path
import time

from selenium import webdriver
from datetime import datetime

from selenium.common import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import Config
from utils import format_countdown_time


class HuaWei:
    config = None
    browser = None
    isLogin = False
    isWaiting = True
    isCountdown = True
    isStartBuying = False
    isBuyNow = False
    nickname = "游客"
    # 全局页面元素超时时间，单位S
    defaultTimeout = 60

    def __init__(self, config_file):
        print("{0} 开始解析配置文件".format(datetime.now()))
        self.config = Config(config_file)
        print("{0} 结束解析配置文件".format(datetime.now()))
        self.__browser_setting()

    def start_process(self):
        print("{0} 开启抢购华为手机 {1}".format(datetime.now(), self.config.get("product", "name")))
        self.__visit_official_website()
        self.__login()
        if self.isLogin:
            self.__visit_product_page()
            self.__waiting_count()
            self.__choose_product()
            self.__countdown()
            self.__start_buying()
            self.__buy_now()
            self.__submit_order()

    def stop_process(self):
        print("{0} 结束抢购华为手机 {1}".format(datetime.now(), self.config.get("product", "name")))
        time.sleep(120)
        self.browser.quit()

    def __visit_official_website(self):
        print("{0} 开始进入华为官网".format(datetime.now()))
        self.browser.get('https://www.vmall.com/')
        self.browser.implicitly_wait(20)
        print("{0} 已进入华为官网".format(datetime.now()))

    def __visit_product_page(self):
        print("{0} 开始进入华为 {1} 产品详情页".format(datetime.now(), self.config.get("product", "name")))
        self.browser.get("https://www.vmall.com/product/{0}.html".format(self.config.get("product", "id")))
        print("{0} 已进入华为 {1} 产品详情页".format(datetime.now(), self.config.get("product", "name")))
        self.__refresh_product_page()

    def __refresh_product_page(self):
        print("{0} 开始刷新 {1} 产品详情页".format(datetime.now(), self.config.get("product", "name")))
        self.browser.refresh()
        self.browser.implicitly_wait(20)
        print("{0} 结束刷新 {1} 产品详情页".format(datetime.now(), self.config.get("product", "name")))

    def __choose_product(self):
        sets = self.config.get("product", "sets", "")
        if len(sets) > 0:
            self.__choose_product_sets(sets)
        else:
            self.__choose_product_item()

    def __choose_product_sets(self, sets):
        print("{0} 开始选择手机套装规格".format(datetime.now()))
        set_skus = sets.split(",")
        for sku in set_skus:
            WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_element_located((By.LINK_TEXT, f"{sku}"))
            ).click()
        sku_payment = '无'
        if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-skus > dl:last-child > label"), "选择销售类型")(
                self.browser):
            sku_payment = self.config.get("product", "payment", "全款购买")
            WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_element_located((By.LINK_TEXT, f"{sku_payment}"))
            ).click()
        print("{0} 选择手机套装规格完成，套装规格：{1} 销售类型：{2}".format(datetime.now(), sets, sku_payment))

    def __choose_product_item(self):
        print("{0} 开始选择手机单品规格".format(datetime.now()))
        sku_color = self.config.get("product", "color")
        sku_version = self.config.get("product", "version")
        WebDriverWait(self.browser, self.defaultTimeout).until(
            EC.presence_of_element_located((By.LINK_TEXT, f"{sku_color}"))
        ).click()
        WebDriverWait(self.browser, self.defaultTimeout).until(
            EC.presence_of_element_located((By.LINK_TEXT, f"{sku_version}"))
        ).click()
        sku_payment = '无'
        if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-skus > dl:last-child > label"), "选择销售类型")(
                self.browser):
            sku_payment = self.config.get("product", "payment")
            WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_element_located((By.LINK_TEXT, f"{sku_payment}"))
            ).click()
        print("{0} 选择手机单品规格完成，颜色：{1} 版本：{2} 销售类型：{3}".format(datetime.now(), sku_color, sku_version,
                                                                               sku_payment))

    def __login(self):
        print("{0} 开始登陆华为账号".format(datetime.now()))
        self.__goto_login_page()
        self.__submit_login()
        self.__login_security_verification()
        self.__check_is_logged_in()

        """ 
        TODO：实现cookie记录，并实现Cookie登陆
        """
        if self.isLogin:
            print("{0} 当前登陆账号为：{1}".format(datetime.now(), self.nickname))

        print("{0} 结束登陆华为账号".format(datetime.now()))

    def __login_security_verification(self):
        isNeedJigsawVerification = self.__check_is_need_jigsaw_verification()
        while isNeedJigsawVerification:
            print("{0} 等待进行拼图验证中......".format(datetime.now()))
            time.sleep(5)
            isNeedJigsawVerification = self.__check_is_need_jigsaw_verification()

        isNeedVerificationCode = self.__check_is_need_verification_code()
        if isNeedVerificationCode:
            self.__click_send_verification_code()
            while isNeedVerificationCode:
                print("{0} 等待输入验证码中......".format(datetime.now()))
                isInputVerificationCode = self.__check_is_input_verification_code()
                if isInputVerificationCode:
                    verificationCode = self.browser.find_element(By.CSS_SELECTOR,
                                                                 ".hwid-getAuthCode-input .hwid-input-area .hwid-input").get_attribute(
                        'value')
                    verificationCode.strip()
                    if len(verificationCode) != 6:
                        print("{0} 已输入验证码，验证码为【{1}】长度不满足6位，继续等待输入".format(datetime.now(),
                                                                                                verificationCode))
                        time.sleep(5)
                    else:
                        print("{0} 已输入验证码，验证码为【{1}】".format(datetime.now(), verificationCode))
                        self.browser.find_element(By.CSS_SELECTOR,
                                                  ".hwid-dialog-footer .hwid-button-base-box2 .dialogFooterBtn").click()
                        isNeedVerificationCode = False
                else:
                    time.sleep(5)
        else:
            pass

    def __browser_setting(self):
        print("{0} 开始设置浏览器参数".format(datetime.now()))
        browserType = self.config.get("browser", "type", 'chrome')
        if browserType == 'chrome':
            self.__chrome_setting()
        elif browserType == 'firefox':
            self.__firefox_setting()
        else:
            print("{0} 不支持的浏览器类型，浏览器类型为：{1}".format(datetime.now(), browserType))
            exit()

        print("{0} 设置浏览器参数完成".format(datetime.now()))
        self.browser.maximize_window()

    def __firefox_setting(self):
        options = webdriver.FirefoxOptions()
        if self.config.getboolean("browser", "headless", False):
            options.add_argument('--headless')
            userAgent = self.config.get("browser", "userAgent",
                                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0")
            options.set_preference("general.useragent.override", userAgent)

        # options.add_argument(r"--profile-root={}".format(os.path.dirname(os.path.abspath(__file__))))
        # options.add_argument(r"-profile={}".format("profiles"))

        driverPath = self.config.get("browser", "driverPath", '')
        executable_path = None if len(driverPath) < 1 else driverPath
        self.browser = webdriver.Firefox(
            service=Service(executable_path=executable_path,
                            log_path=r"{0}/selenium.log".format(os.path.dirname(os.path.abspath(__file__)))),
            options=options)
        self.browser.set_window_size(1920, 1080)

    def __chrome_setting(self):
        options = webdriver.ChromeOptions()
        options.add_argument(r"--user-data-dir={}".format(self.config.get("chrome", "userDataDir")))
        options.add_argument(r"--profile-directory={}".format("Profile 5"))
        if self.config.getboolean("browser", "headless", False):
            options.add_argument('--headless')
            # headless 模式下需要设置user_agent及窗口大小，否则会被识别成移动端访问
            userAgent = self.config.get("browser", "userAgent",
                                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
            options.add_argument(r"user-agent={}".format(userAgent))
            options.add_argument("--start-maximized")

        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-ssl-error')
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')

        driverPath = self.config.get("browser", "driverPath", '')
        executable_path = None if len(driverPath) < 1 else driverPath
        self.browser = webdriver.Chrome(
            service=Service(executable_path=executable_path,
                            log_path=r"{0}/selenium.log".format(os.path.dirname(os.path.abspath(__file__)))),
            options=options)

    def __countdown(self):
        while self.isCountdown:
            countdown_times = self.__get_countdown_time()
            if len(countdown_times) > 0:
                print("{0} 距离抢购开始还剩：{1}".format(datetime.now(), format_countdown_time(countdown_times)))
                self.__set_start_buying(countdown_times)
                if not self.isStartBuying:
                    time.sleep(1)

    def __start_buying(self):
        while self.isStartBuying:
            countdown_times = self.__get_countdown_time()
            if len(countdown_times) > 0:
                print("{0} 距离抢购开始还剩：{1}".format(datetime.now(), format_countdown_time(countdown_times)))
                button_element = WebDriverWait(self.browser, self.defaultTimeout).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='pro-operation']/a"))
                )
                button_element.click()
                time.sleep(0.0001)

    def __buy_now(self):
        if self.isBuyNow:
            button_element = WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#pro-operation > a"))
            )[1]
            button_element.click()

    def __get_countdown_time(self):
        attempts = 0
        countdown_times = []
        while attempts < 5:
            countdown_times = []
            try:
                elements = WebDriverWait(self.browser, self.defaultTimeout).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@id='pro-operation-countdown']/ul/li/span"))
                )
                for element in elements:
                    countdown_times.append(element.text)
                return countdown_times
            except (StaleElementReferenceException, TimeoutException):
                # 页面元素因为动态渲染，导致查找的元素不再是原来的元素，导致异常
                self.__refresh_product_page()
                self.__choose_product()
                attempts += 1
        return countdown_times

    def __set_start_buying(self, countdown_times):
        if countdown_times[0] != "00" or countdown_times[1] != "00" or countdown_times[2] != "00":
            return
        if int(countdown_times[3]) < 10:
            self.isCountdown = False
            self.isStartBuying = True

    def __goto_login_page(self):
        print("{0} 点击登录按钮".format(datetime.now()))
        login = WebDriverWait(self.browser, self.defaultTimeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "r-1a7l8x0"))
        )
        login.click()
        print("{0} 已跳转登录页面".format(datetime.now()))

    def __submit_login(self):
        print("{0} 开始输入账号及密码".format(datetime.now()))
        input_elements = WebDriverWait(self.browser, self.defaultTimeout).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "hwid-input"))
        )

        input_elements[0].send_keys(self.config.get("user", "name"))
        input_elements[1].send_keys(self.config.get("user", "password"))
        print("{0} 已输入账号及密码".format(datetime.now()))

        WebDriverWait(self.browser, self.defaultTimeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hwid-login-btn"))
        ).click()
        print("{0} 发起登陆请求".format(datetime.now()))
        self.browser.implicitly_wait(20)

    def __check_is_need_verification_code(self):
        print("{0} 检查是否需要获取验证码".format(datetime.now()))
        isNeedVerificationCode = False
        try:
            isNeedVerificationCode = EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".hwid-getAuthCode .hwid-smsCode > span > span"),
                "获取验证码")(self.browser)
        except NoSuchElementException:
            pass
        except TimeoutException:
            print("{0} 检查是否需要获取验证码超时".format(datetime.now()))
            pass

        print("{0} 检查是否需要获取验证码，检查结果：{1}".format(datetime.now(),
                                                               "需要" if isNeedVerificationCode else "不需要"))
        return isNeedVerificationCode

    def __check_is_need_jigsaw_verification(self):
        print("{0} 检查是否需要拼图验证".format(datetime.now()))
        isNeedJigsawVerification = False
        try:
            self.browser.find_element(By.CLASS_NAME, "yidun_modal__wrap")
            isNeedJigsawVerification = True
        except NoSuchElementException:
            pass
        except TimeoutException:
            print("{0} 检查是否需要获取验证码超时".format(datetime.now()))
            pass

        print("{0} 检查是否需要拼图验证，检查结果：{1}".format(datetime.now(),
                                                             "需要" if isNeedJigsawVerification else "不需要"))
        return isNeedJigsawVerification

    def __check_is_input_verification_code(self):
        print("{0} 检查是否已经输入验证码".format(datetime.now()))
        isInputVerificationCode = False
        try:
            self.browser.find_element(By.CSS_SELECTOR,
                                      ".hwid-dialog-footer .hwid-button-base-box2 .dialogFooterBtn .hwid-disabled").click()
        except NoSuchElementException:
            isInputVerificationCode = True
            pass

        print("{0} 检查是否已经输入验证码，检查结果：{1}".format(datetime.now(),
                                                               "是" if isInputVerificationCode else "否"))
        return isInputVerificationCode

    def __click_send_verification_code(self):
        print("{0} 进行短信验证码发送".format(datetime.now()))
        try:
            WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "hwid-smsCode"))
            ).click()
            print("{0} 短信验证码已发送".format(datetime.now()))
        except TimeoutException:
            print("{0} 短信验证码已发送超时".format(datetime.now()))
            pass

    def __check_is_logged_in(self):
        try:
            self.browser.find_element(By.LINK_TEXT, "请登录")
            self.isLogin = False
            print("{0} 账号登陆失败，请重试".format(datetime.now()))
        except NoSuchElementException:
            self.isLogin = True
            print("{0} 账号登陆成功".format(datetime.now()))
            self.nickname = WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "r-1pn2ns4"))
            ).text

    def __waiting_count(self):
        while self.isWaiting:
            if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-operation > a > span"), "暂不售卖")(
                    self.browser):
                print("{0}【{1}】倒计时未开始，等待中...".format(datetime.now(), "暂不售卖"))
                time.sleep(120)
                self.__refresh_product_page()
            elif EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-operation > a > span"), "暂时缺货")(
                    self.browser):
                print("{0}【{1}】倒计时未开始，等待中...".format(datetime.now(), "暂时缺货"))
                time.sleep(120)
                self.__refresh_product_page()
            elif EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-operation > a > span"), "即将开始")(
                    self.browser):
                print("{0} 倒计时即将开始".format(datetime.now()))
                self.__set_end_waiting()
                if not self.isCountdown:
                    time.sleep(1)
            else:
                print("{0} 当前可立即下单".format(datetime.now()))
                self.__set_end_count_down()
                self.__set_buy_now()

    def __submit_order(self):
        if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#checkoutSubmit > span"), "提交订单")(self.browser):
            try:
                print("{0} 准备提交订单".format(datetime.now()))
                self.browser.find_element(By.ID, "checkoutSubmit").click()
                print("{0} 提交订单成功".format(datetime.now()))
            except NoSuchElementException:
                print("{0} 提交订单失败".format(datetime.now()))

    def __set_end_waiting(self):
        self.isWaiting = False
        self.isCountdown = True

    def __set_end_count_down(self):
        self.isWaiting = False
        self.isCountdown = False

    def __set_buy_now(self):
        self.isStartBuying = False
        self.isBuyNow = True
