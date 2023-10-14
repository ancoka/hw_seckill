# -*- coding: utf-8 -*-
# !/usr/bin/python
import os.path
import time
from datetime import datetime

from selenium.common import StaleElementReferenceException, NoSuchElementException, TimeoutException, \
    ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from browser.browser_factory import BrowserFactory
from config import Config
import utils


class HuaWei:
    config = None
    browser = None
    isLogin = False
    isWaiting = True
    isCountdown = True
    isStartBuying = False
    startBuyingTime = None
    isBuyNow = False
    nickname = "游客"
    # 全局页面元素超时时间，单位S
    defaultTimeout = 60

    def __init__(self, config_file):
        print("{0} 开始解析配置文件".format(datetime.now()))
        self.config = Config(config_file)
        print("{0} 结束解析配置文件".format(datetime.now()))

        log_path = self.config.get("logs", "path", "")
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs") if len(log_path) == 0 else log_path
        self.log_path = os.path.join(log_path, "selenium.log")
        if not os.path.exists(log_path):
            os.makedirs(log_path)

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

    def stop_process(self):
        print("{0} 结束抢购华为手机 {1}".format(datetime.now(), self.config.get("product", "name")))
        time.sleep(120)
        self.browser.quit()

    def __visit_official_website(self):
        print("{0} 开始进入华为官网".format(datetime.now()))
        self.browser.get('https://www.vmall.com/')
        print("{0} 已进入华为官网".format(datetime.now()))

    def __visit_product_page(self):
        print("{0} 开始进入华为 {1} 产品详情页".format(datetime.now(), self.config.get("product", "name")))
        self.browser.get("https://www.vmall.com/product/{0}.html".format(self.config.get("product", "id")))
        print("{0} 已进入华为 {1} 产品详情页".format(datetime.now(), self.config.get("product", "name")))
        self.__refresh_product_page()

    def __refresh_product_page(self):
        print("{0} 开始刷新 {1} 产品详情页".format(datetime.now(), self.config.get("product", "name")))
        self.browser.refresh()
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
        self.__trust_browser()
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
                if self.config.getboolean("browser", "headless", False):
                    verificationCode = input("请输入验证码：")
                    verificationCode.strip()
                    self.browser.find_element(By.CSS_SELECTOR,
                                              ".hwid-getAuthCode-input .hwid-input-area .hwid-input").send_keys(
                        verificationCode)
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
        self.browser = BrowserFactory.build(browserType).setting(self.config, self.log_path)
        self.browser.maximize_window()
        self.browser.implicitly_wait(10)

    def __countdown(self):
        while self.isCountdown:
            countdown_times = self.__get_countdown_time()
            if len(countdown_times) > 0:
                print("{0} 距离抢购开始还剩：{1}".format(datetime.now(), utils.format_countdown_time(countdown_times)))
                self.__set_start_buying(countdown_times)
                if not self.isStartBuying:
                    time.sleep(1)

    def __start_buying(self):
        print("{0} 进入最后下单环节".format(datetime.now()))

        click_times = 0
        while self.isStartBuying:
            second = utils.seconds_diff(datetime.now(), self.startBuyingTime)
            if second >= 0:
                print("{0} 距离抢购开始还剩{1}秒".format(datetime.now(), second))
                self.__check_box_ct_pop_stage()
            elif second > -2:
                print("{0} 抢购开始".format(datetime.now(), second))
                self.__check_iframe_box_stage()
            else:
                self.isStartBuying = False

            try:
                order_btn = self.__find_element_text(By.CSS_SELECTOR, "#pro-operation > span", "立即下单")
                if order_btn is not None:
                    order_btn.click()
            except (NoSuchElementException, ElementClickInterceptedException):
                click_times += 1
                print("{0} 已尝试点击立即下单 {1} 次".format(datetime.now(), click_times))

            time.sleep(0.001)

        print("{0} 最后下单环节结束".format(datetime.now()))

    def __check_box_ct_pop_exists(self):
        boxCtPopIsExists = False
        try:
            self.browser.find_element(By.CSS_SELECTOR, ".box-ct .box-cc .box-content")
            boxCtPopIsExists = True
        except NoSuchElementException:
            pass
        return boxCtPopIsExists

    def __check_box_ct_pop_stage(self):
        boxCtPopIsExists = self.__check_box_ct_pop_exists()
        if boxCtPopIsExists:
            self.__check_box_ct_pop_act_is_started()
            self.__check_box_ct_pop_product_is_not_buy()

    def __check_box_ct_pop_act_is_started(self):
        actIsStarted = True
        try:
            activity_text = self.browser.find_element(By.CSS_SELECTOR, ".box-ct .box-cc .box-content").text
            actIsStarted = activity_text.find('活动未开始') != -1
        except NoSuchElementException:
            pass

        if not actIsStarted:
            print("{0} 动作太快了，活动未开始，关闭弹窗重试中".format(datetime.now()))
            try:
                box_btn = self.__find_element_text(By.CSS_SELECTOR, ".box-ct .box-cc .box-content .box-button .box-ok",
                                                   '知道了', None)
                if box_btn is not None:
                    box_btn.click()
            except (NoSuchElementException, ElementClickInterceptedException):
                pass

    def __check_box_ct_pop_product_is_not_buy(self):
        productIsNotBuy = False
        try:
            activity_text = self.browser.find_element(By.CSS_SELECTOR, ".box-ct .box-cc .box-content").text
            productIsNotBuy = activity_text.find('抱歉，没有抢到') != -1
        except NoSuchElementException:
            pass

        if productIsNotBuy:
            print("{0} 抱歉，没有抢到，再试试".format(datetime.now()))
            try:
                box_btn = self.__find_element_text(By.CSS_SELECTOR, ".box-ct .box-cc .box-content .box-button .box-ok",
                                                   '再试试', None)
                if box_btn is not None:
                    box_btn.click()
                    self.isStartBuying = True
            except (NoSuchElementException, ElementClickInterceptedException):
                pass

    def __check_iframe_box_pop_exists(self):
        iframeBoxExists = False
        try:
            self.browser.find_element(By.ID, 'iframeBox')
            iframeBoxExists = True
        except NoSuchElementException:
            pass
        return iframeBoxExists

    def __check_iframe_box_stage(self):
        iframeBoxExists = self.__check_iframe_box_pop_exists()
        if iframeBoxExists:
            queueIsSuccess = self.__check_queue_stage()
            lockInventoryIsSuccess = self.__check_lock_inventory_is_success(queueIsSuccess)
            if lockInventoryIsSuccess:
                self.isStartBuying = False
                self.__submit_order()
                self.__check_box_ct_pop_stage()

    def __check_queue_stage(self):
        print("{0} 尝试检查当前排队状态".format(datetime.now()))
        iframe_content = self.browser.find_element(By.ID, 'iframeBox').text
        queueIsSuccess = iframe_content.find("排队中") == -1
        print(
            "{0} 尝试检查当前排队状态，排队结果：【{1}】".format(datetime.now(), '已排队' if queueIsSuccess else '排队中'))
        return queueIsSuccess

    def __check_lock_inventory_is_success(self, queueIsSuccess):
        print("{0} 尝试检查库存锁定状态".format(datetime.now()))
        lockInventoryIsSuccess = False
        if queueIsSuccess:
            text = self.browser.find_element(By.ID, 'iframeBox').text
            print("{0} 尝试检查库存锁定状态，{1}".format(datetime.now(), text))
            lockInventoryIsSuccess = text.find('已售完') == -1

        lockInventoryResult = '已锁定' if lockInventoryIsSuccess else '未锁定'
        print("{0} 尝试检查库存锁定状态，锁定结果：【{1}】".format(datetime.now(), lockInventoryResult))
        return lockInventoryIsSuccess

    def __buy_now(self):
        if self.isBuyNow:
            print("{0} 开始立即购买".format(datetime.now()))
            try:
                order_btn = self.__find_element_text(By.CSS_SELECTOR, "#pro-operation > a", "立即下单")
                if order_btn is not None:
                    order_btn.click()
                else:
                    print("{0} 未找到【立即下单】按钮".format(datetime.now()))
            except (NoSuchElementException, ElementClickInterceptedException):
                print("{0} 未找到【立即下单】按钮或按钮不可点击".format(datetime.now()))
            print("{0} 结束立即购买".format(datetime.now()))
            self.__submit_order()

    def __submit_order(self):
        if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#checkoutSubmit > span"), "提交订单")(self.browser):
            try:
                print("{0} 准备提交订单".format(datetime.now()))
                self.browser.find_element(By.ID, "checkoutSubmit").click()
                print("{0} 提交订单成功".format(datetime.now()))
            except NoSuchElementException:
                print("{0} 提交订单失败".format(datetime.now()))

    def __get_countdown_time(self):
        attempts = 0
        countdown_times = []
        while attempts < 5:
            countdown_times = []
            try:
                elements = self.browser.find_elements(By.CSS_SELECTOR, "#pro-operation li > span")
                element_length = len(elements)
                for i in range(element_length):
                    try:
                        countdown_times.append(elements[i].text)
                    except StaleElementReferenceException:
                        # 页面元素因为动态渲染，导致查找的元素不再是原来的元素，导致异常
                        element = self.browser.find_elements(By.CSS_SELECTOR, "#pro-operation li > span")[i]
                        countdown_times.append(element.text)

                return countdown_times
            except (TimeoutException, NoSuchElementException):
                self.__refresh_product_page()
                self.__choose_product()
                attempts += 1
        return countdown_times

    def __set_start_buying(self, countdown_times):
        if countdown_times[0] != "00" or countdown_times[1] != "00" or countdown_times[2] != "00":
            return
        if int(countdown_times[3]) <= 5:
            self.isCountdown = False
            self.isStartBuying = True
            self.startBuyingTime = utils.get_start_buying_time(countdown_times)

    def __goto_login_page(self):
        print("{0} 点击登录按钮".format(datetime.now()))
        login = self.__find_element_text(By.CLASS_NAME, "r-1a7l8x0", '请登录', True)
        if login is not None:
            login.click()
        else:
            print("{0} 登陆跳转失败，未找到登陆跳转链接".format(datetime.now()))
            exit()

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
            self.browser.find_element(By.CSS_SELECTOR, ".hwid-dialog-footer .hwid-button-base-box2 .dialogFooterBtn "
                                                       ".hwid-disabled").click()
        except NoSuchElementException:
            isInputVerificationCode = True
            pass

        print(
            "{0} 检查是否已经输入验证码，检查结果：{1}".format(datetime.now(), "是" if isInputVerificationCode else "否"))
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

    def __trust_browser(self):
        print("{0} 检查是否已经输入验证码".format(datetime.now()))
        isNeedTrustBrowser = False
        try:
            self.browser.find_element(By.CLASS_NAME, "hwid-trustBrowser")
            isNeedTrustBrowser = True
        except NoSuchElementException:
            pass

        if isNeedTrustBrowser:
            self.browser.find_elements(By.CSS_SELECTOR, ".hwid-trustBrowser .hwid-dialog-textBtnBox .normalBtn")[
                0].click()

    def __check_is_logged_in(self):
        try:
            self.browser.find_element(By.LINK_TEXT, "请登录")
        except NoSuchElementException:
            try:
                element = self.__find_element_text(By.CLASS_NAME, "r-1a7l8x0", "请登录")
                self.isLogin = element is None
            except NoSuchElementException:
                self.isLogin = True

        if self.isLogin:
            print("{0} 账号登陆成功".format(datetime.now()))
            try:
                self.nickname = WebDriverWait(self.browser, self.defaultTimeout).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "r-1pn2ns4"))
                ).text
            except TimeoutException:
                print("{0} 获取当前登陆账号昵称超时".format(datetime.now()))
                pass
        else:
            print("{0} 账号登陆失败，请重试".format(datetime.now()))
            pass

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

    def __set_end_waiting(self):
        self.isWaiting = False
        self.isCountdown = True

    def __set_end_count_down(self):
        self.isWaiting = False
        self.isCountdown = False

    def __set_buy_now(self):
        self.isStartBuying = False
        self.isBuyNow = True

    def __find_element_text(self, by, value, text, wait=None):
        if wait is None:
            items = self.browser.find_elements(by, value)
        else:
            items = WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_all_elements_located((by, value)))
        element = None
        for item in items:
            if text == item.text:
                element = item
        if element is None:
            return
        return element
