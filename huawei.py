# -*- coding: utf-8 -*-
# !/usr/bin/python
import json
import threading
import time
from datetime import datetime
from urllib.parse import unquote

from loguru import logger
from selenium.common import StaleElementReferenceException, NoSuchElementException, TimeoutException, \
    ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import constants
from browser.browser_factory import BrowserFactory
from config import Config
from huawei_thread import HuaWeiThread
from tools import utils, time_utils


def title_contains_any(titles: list) -> EC.Callable[[EC.AnyDriver], bool]:
    """An expectation for checking that the title contains any of the case-sensitive
    substrings from the given list.

    titles is a list of fragments of title expected.
    Returns True if the title matches any fragment in the list, False otherwise.
    """

    def _predicate(driver):
        return any(title in driver.title for title in titles)

    return _predicate

class HuaWei:
    config = None
    browser = None
    browser_type = None
    driver_wait = None
    is_login = False
    is_waiting = True
    is_countdown = True
    is_start_buying = False
    is_can_submit_order = False
    is_buy_now = False
    sec_kill_time = None
    hw_server_timestamp = None
    local_timestamp = None
    thread_browsers = []

    def __init__(self, profile_path=None):
        self.config = Config(constants.CONFIG_FILE)
        self.browser_type = self.config.get("browser", "type", constants.DEFAULT_BROWSER_TYPE)
        self.__pre_browser_setting()

        if profile_path is None or profile_path == '':
            profile_path = utils.get_profile_path(constants.BASE_PROFILE_PATH, self.browser_type, 1)

        self.__browser_setting(profile_path)
        server_timestamp, local_timestamp, ms_diff = time_utils.local_hw_time_diff()
        self.hw_server_timestamp = server_timestamp
        self.local_timestamp = local_timestamp
        self.driver_wait = WebDriverWait(self.browser, 5, 0.01)
        utils.set_locale_chinese()

    def start_process(self):
        logger.info("开启抢购华为手机")
        self.__visit_official_website()
        self.__login()
        if self.is_login:
            self.__visit_product_page()
            self.__choose_product()
            self.__waiting_count()
            self.__countdown()
            self.__start_buying()
            self.__buy_now()

    def stop_process(self):
        logger.info("结束抢购华为手机")
        time.sleep(120)
        self.browser.quit()

    def thread_process(self):
        self.__visit_product_page()
        self.__load_cookies()
        self.__refresh_product_page()
        self.__choose_product()
        self.__get_sec_kill_time()
        self.__set_end_countdown()
        self.__start_buying()

    def __pre_browser_setting(self):
        utils.create_directory(constants.LOG_PATH)

        threadCount = max(int(self.config.get("process", "thread", constants.DEFAULT_THREAD_NUM)), 1)
        for i in range(1, threadCount + 1):
            profile_path = utils.get_profile_path(constants.BASE_PROFILE_PATH, self.browser_type, i)
            utils.create_directory(profile_path)

    def __browser_setting(self, profile_path):
        logger.info("开始设置浏览器参数")
        self.browser = (BrowserFactory.build(self.browser_type)
                        .setting(self.config, constants.SELENIUM_LOG_FILE, profile_path))
        self.browser.maximize_window()

    def __visit_official_website(self):
        logger.info("开始进入华为官网")
        self.browser.get('https://www.vmall.com/')
        try:
            self.driver_wait.until(EC.url_changes)
            logger.info("已进入华为官网")
            self.__get_current_page_type()
        except TimeoutException:
            logger.warning("进入华为官网失败，程序将在3秒后退出...")
            time.sleep(3)
            self.browser.quit()

    def __login(self):
        logger.info("开始登录华为账号")
        self.is_login = self.__check_is_logged_in()
        if not self.is_login:
            self.__goto_login_page()
            self.__do_login()

            loginTimes = 1
            while not self.is_login and loginTimes < constants.RETRY_TIMES:
                logger.info("开始第 {} 次尝试登录华为账号", loginTimes)
                loggedResult = self.__check_logged_result()
                if loggedResult > 0:
                    self.is_login = True
                elif loggedResult == 0:
                    self.__login_security_verification()
                    self.__trust_browser()
                    self.is_login = self.__check_is_logged_in()
                else:
                    self.is_login = False
                loginDesc = '成功' if self.is_login else '失败'
                logger.info("第 {} 次尝试登录华为账号，登录结果：{}", loginTimes, loginDesc)
                loginTimes += 1

        if not self.is_login:
            logger.warning("登录华为账号失败，程序将在3秒后退出...")
            time.sleep(3)
            exit()

        utils.write_cookies(self.browser.get_cookies())
        nickname = self.__get_logged_nickname()
        logger.success("当前登录账号昵称为：{0}".format(nickname))
        logger.info("结束登录华为账号")

    def __load_cookies(self):
        cookies = utils.read_cookies()
        if cookies is not None:
            for cookie in cookies:
                self.browser.add_cookie(cookie)
        else:
            logger.warning("未读取到 Cookie 数据")
            exit()

    def __goto_login_page(self):
        loginLink = None
        times = 1
        while loginLink is None and times < constants.RETRY_TIMES:
            menu_links = self.driver_wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.css-901oao.r-1a7l8x0.r-1enofrn.r-ueyrd6.r-1pn2ns4.r-gy4na3')))
            for menu_link in menu_links:
                if '请登录' == menu_link.text:
                    loginLink = menu_link
            times += 1

        if loginLink is None:
            logger.warning("登录跳转失败，未找到登录跳转链接，程序将在3秒后退出...")
            time.sleep(3)
            exit()

        logger.info("开始点击登录按钮")
        loginLink.click()

        try:
            self.driver_wait.until(title_contains_any(['华为账号-登录', 'HUAWEI ID-Log in']))
            logger.info("已跳转登录页面")
            self.__get_current_page_type()
        except TimeoutException:
            logger.warning("登录跳转失败，未找到登录跳转链接，程序将在3秒后退出...")
            time.sleep(3)
            exit()

    def __do_login(self):
        logger.info("开始输入账号及密码")
        inputElements = self.driver_wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "hwid-input")))

        inputElements[0].send_keys(self.config.get("user", "name"))
        inputElements[1].send_keys(self.config.get("user", "password"))
        logger.info("已输入账号及密码")

        self.driver_wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hwid-login-btn"))).click()
        logger.info("发起登录请求")

    def __check_logged_result(self):
        loggedResult = 0
        isLoginPage = self.__current_is_login_page()
        isNeedVerificationCode = self.__check_is_need_verification_code()
        isNeedVerificationDeviceCode = self.__check_is_need_verification_device_code()
        if not isLoginPage:
            loggedResult = 1
        elif isLoginPage and not isNeedVerificationCode and not isNeedVerificationDeviceCode:
            loggedResult = - 1
        else:
            pass
        return loggedResult

    def __login_security_verification(self):
        isNeedJigsawVerification = self.__check_is_need_jigsaw_verification()
        while isNeedJigsawVerification:
            logger.info("等待进行拼图验证中......")
            time.sleep(5)
            isNeedJigsawVerification = self.__check_is_need_jigsaw_verification()

        isNeedVerificationDeviceCode = self.__check_is_need_verification_device_code()
        while isNeedVerificationDeviceCode:
            logger.info("等待进行设备验证码验证中......")
            time.sleep(5)
            isNeedVerificationDeviceCode = self.__check_is_need_verification_device_code()

        isNeedVerificationCode = self.__check_is_need_verification_code()
        if isNeedVerificationCode:
            self.__click_send_verification_code()
            while isNeedVerificationCode:
                logger.info("等待输入验证码中......")
                if self.config.getboolean("browser", "headless", False):
                    verificationCode = input("请输入验证码：")
                    verificationCode.strip()
                    self.browser.find_element(By.CSS_SELECTOR,
                                              ".hwid-dialog-main .hwid-getAuthCode-input .hwid-input-area .hwid-input").send_keys(
                        verificationCode)
                isInputVerificationCode = self.__check_is_input_verification_code()
                if isInputVerificationCode:
                    verificationCode = self.browser.find_element(By.CSS_SELECTOR,
                                                                 ".hwid-dialog-main .hwid-getAuthCode-input .hwid-input-area .hwid-input").get_attribute(
                        'value')
                    verificationCode.strip()
                    if len(verificationCode) != 6:
                        logger.warning("已输入验证码，验证码为【{}】长度不满足6位，继续等待输入", verificationCode)
                        time.sleep(5)
                    else:
                        logger.info("已输入验证码，验证码为【{}】", verificationCode)
                        self.browser.find_element(By.CSS_SELECTOR,
                                                  ".hwid-dialog-main .hwid-dialog-footer .hwid-button-base-box2 .dialogFooterBtn").click()
                        isNeedVerificationCode = False
                else:
                    time.sleep(5)
        else:
            pass

    def __check_is_need_jigsaw_verification(self):
        logger.info("检查是否需要拼图验证")
        isNeedJigsawVerification = False
        try:
            self.browser.find_element(By.CLASS_NAME, "yidun_modal__wrap")
            isNeedJigsawVerification = True
        except NoSuchElementException:
            pass

        logger.info("检查是否需要拼图验证，检查结果：{}", "需要" if isNeedJigsawVerification else "不需要")
        return isNeedJigsawVerification

    def __check_is_need_verification_code(self):
        logger.info("检查是否需要获取验证码")
        isNeedVerificationCode = False
        try:
            isNeedVerificationCode = self.driver_wait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".hwid-dialog-main .hwid-getAuthCode .hwid-smsCode"),
                "获取验证码"))
        except TimeoutException:
            pass

        logger.info("检查是否需要获取验证码，检查结果：{}", "需要" if isNeedVerificationCode else "不需要")
        return isNeedVerificationCode

    def __check_is_need_verification_device_code(self):
        logger.info("检查是否需要获取验证码")
        isNeedVerificationCode = False

        try:
            target = self.browser.find_element(
                By.CSS_SELECTOR, ".hwid-sixInputArea-line")
            isNeedVerificationCode = True if target else False
        except:
            pass

        logger.info("检查是否需要设备验证码，检查结果：{}",
                    "需要" if isNeedVerificationCode else "不需要")
        return isNeedVerificationCode

    def __check_is_input_verification_code(self):
        logger.info("检查是否已经输入验证码")
        isInputVerificationCode = False
        try:
            self.browser.find_element(By.CSS_SELECTOR, ".hwid-dialog-footer .hwid-button-base-box2 .dialogFooterBtn "
                                                       ".hwid-disabled").click()
        except NoSuchElementException:
            isInputVerificationCode = True
            pass

        logger.info("检查是否已经输入验证码，检查结果：{}", "是" if isInputVerificationCode else "否")
        return isInputVerificationCode

    def __click_send_verification_code(self):
        logger.info("进行短信验证码发送")
        try:
            self.driver_wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hwid-smsCode"))).click()
            logger.success("短信验证码已发送")
        except TimeoutException:
            logger.warning("短信验证码已发送超时")

    def __check_is_need_trust_browser(self):
        logger.info("检查是否需要信任浏览器")
        isNeedTrustBrowser = False
        try:
            isNeedTrustBrowser = self.driver_wait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".hwid-trustBrowser"), "是否信任此浏览器？"))
        except TimeoutException:
            pass

        logger.info("检查是否需要信任浏览器，检查结果：{}", "是" if isNeedTrustBrowser else "否")
        return isNeedTrustBrowser

    def __trust_browser(self):
        isNeedTrustBrowser = self.__check_is_need_trust_browser()
        while isNeedTrustBrowser:
            logger.info("等待信任浏览器中......")
            try:
                buttons = self.driver_wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, '.hwid-trustBrowser .hwid-dialog-textBtnBox .normalBtn')))
                for button in buttons:
                    if '信任' == button.text:
                        button.click()
                        isNeedTrustBrowser = False
            except (NoSuchElementException, TimeoutException):
                pass
            time.sleep(5)

    def __current_is_login_page(self):
        try:
            isLoginPage = self.driver_wait.until_not(EC.url_contains(constants.LOGIN_PAGE_URL))
        except TimeoutException:
            isLoginPage = True
            pass
        return isLoginPage

    def __check_is_logged_in(self):
        nickname = self.__get_logged_nickname()
        isLogged = not '游客' == nickname
        return isLogged

    def __get_logged_nickname(self):
        nickname = '游客'
        for cookie in self.browser.get_cookies():
            if cookie['name'] == 'displayName':
                nickname = unquote(cookie['value'])
        return nickname

    def __visit_product_page(self):
        currentUrl = self.browser.current_url
        logger.info("开始进入华为 {0} 产品详情页".format(self.config.get("product", "name")))
        self.browser.get(
            "https://{0}?prdId={1}".format(constants.PRODUCT_PAGE_URL, self.config.get("product", "id")))
        try:
            self.driver_wait.until(EC.url_changes(currentUrl))
            logger.info("已进入华为 {0} 产品详情页".format(self.config.get("product", "name")))
            self.__get_current_page_type()
        except TimeoutException:
            logger.info("进入华为 {0} 产品详情页失败，程序将在3秒后退出...".format(self.config.get("product", "name")))
            time.sleep(3)
            self.browser.quit()

    def __waiting_count(self):
        times = 1
        while self.is_waiting and times <= constants.RETRY_TIMES:
            try:
                if EC.text_to_be_present_in_element((By.ID, "prd-botnav-rightbtn"), "暂不售卖")(
                        self.browser):
                    logger.info("【{}】倒计时未开始，等待中...", "暂不售卖")
                    time.sleep(120)
                    self.__refresh_product_page()
                    self.__choose_product()
                elif EC.text_to_be_present_in_element((By.ID, "prd-botnav-rightbtn"), "暂时缺货")(
                        self.browser):
                    logger.info("【{}】倒计时未开始，等待中...", "暂时缺货")
                    time.sleep(120)
                    self.__refresh_product_page()
                    self.__choose_product()
                elif EC.text_to_be_present_in_element((By.ID, "prd-botnav-rightbtn"), "开始")(
                        self.browser):
                    logger.info("倒计时即将开始")
                    self.__get_sec_kill_time()
                    if self.sec_kill_time is not None:
                        self.__set_end_waiting()
                        time.sleep(1)
                else:
                    logger.info("当前可立即购买")
                    self.__set_end_countdown()
                    self.__set_buy_now()
            except NoSuchElementException:
                time.sleep(1)
                times += 1

    def __refresh_product_page(self):
        logger.info("开始刷新 {0} 产品详情页".format(self.config.get("product", "name")))
        self.browser.refresh()
        logger.info("结束刷新 {0} 产品详情页".format(self.config.get("product", "name")))

    def __choose_product(self):
        sets = self.config.get("product", "sets", "")
        if len(sets) > 0:
            self.__choose_product_sets(sets)
        else:
            self.__choose_product_item()

    def __choose_product_sets(self, sets):
        logger.info("开始选择手机套装规格")
        set_skus = sets.split(",")
        sku_buttons = self.driver_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                                                  ".css-1dbjc4n.r-1h0z5md.r-9aemit .css-1dbjc4n.r-18u37iz.r-1w6e6rj .css-1dbjc4n.r-1loqt21.r-1otgn73")))
        for sku in set_skus:
            for sku_button in sku_buttons:
                if sku_button.text == sku:
                    sku_button.click()
        logger.info("选择手机套装规格完成，套装规格：{0}".format(sets))

    def __choose_product_item(self):
        logger.info("开始选择手机单品规格")
        sku_color = self.config.get("product", "color")
        sku_version = self.config.get("product", "version")

        sku_buttons = self.driver_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                                                  ".css-1dbjc4n.r-1h0z5md.r-9aemit .css-1dbjc4n.r-18u37iz.r-1w6e6rj .css-1dbjc4n.r-1loqt21.r-1otgn73")))
        for sku_button in sku_buttons:
            if sku_button.text == sku_color or sku_button.text == sku_version:
                time.sleep(0.002)
                sku_button.click()
        logger.info("选择手机单品规格完成，颜色：{0} 版本：{1}".format(sku_color, sku_version))

    def __countdown(self):
        waitTimes = 1
        while self.is_countdown:
            countdownMsDiff = time_utils.calc_countdown_ms_diff(self.sec_kill_time,
                                                                self.local_timestamp - self.hw_server_timestamp)
            countdownTimes = time_utils.calc_countdown_times(self.sec_kill_time,
                                                             self.local_timestamp - self.hw_server_timestamp)

            if countdownMsDiff > 180000:
                logger.info("距离抢购开始还剩：{}", time_utils.format_countdown_time(countdownTimes))
                time.sleep(10)
                waitTimes += 1
                if waitTimes > 10:
                    self.__refresh_product_page()
                    self.__choose_product()
                    waitTimes = 1

                self.is_login = self.__check_is_logged_in()
                if not self.is_login:
                    self.__login()

                    if self.is_login:
                        self.__visit_product_page()
                        self.__choose_product()
            else:
                self.__set_end_countdown()

    def __start_buying(self):
        logger.info("进入抢购活动最后排队下单环节")
        self.__create_and_start_thread()
        clickTimes = 1
        while self.is_start_buying:
            countdownMsDiff = time_utils.calc_countdown_ms_diff(self.sec_kill_time,
                                                                self.local_timestamp - self.hw_server_timestamp)
            countdown_times = time_utils.calc_countdown_times(self.sec_kill_time,
                                                              self.local_timestamp - self.hw_server_timestamp)
            if countdownMsDiff > 1000:
                logger.info("距离抢购活动最后下单环节开始还剩：{}", time_utils.format_countdown_time(countdown_times))
                time.sleep(1)

            elif countdownMsDiff > 100:
                logger.info("距离抢购活动最后下单环节开始还剩：{}", time_utils.format_countdown_time(countdown_times))
                time.sleep(0.1)
            elif countdownMsDiff > 10:
                logger.info("距离抢购活动最后下单环节开始还剩：{}", time_utils.format_countdown_time(countdown_times))
                time.sleep(0.01)
            else:
                logger.info("抢购活动最后下单环节，进行第 {} 次尝试立即下单", clickTimes)
                self.__do_start_buying()
                self.__check_can_submit_order()
                self.__submit_order()
                clickTimes += 1
                time.sleep(float(self.config.get('process', 'interval', '0.001')))
        logger.info("抢购活动最后排队下单环节结束")

    def __create_and_start_thread(self):
        threadCount = max(int(self.config.get("process", "thread", constants.DEFAULT_THREAD_NUM)), 1)
        currentThread = threading.current_thread()
        if currentThread is threading.main_thread() and threadCount > 1:
            logger.info("开始创建多线程，需要创建线程数：{}", threadCount)
            for i in range(2, threadCount + 1):
                profile_path = utils.get_profile_path(constants.BASE_PROFILE_PATH, self.browser_type, i)
                t = HuaWeiThread(i, HuaWei(profile_path))
                t.setDaemon(True)
                t.start()
                self.thread_browsers.append(t.huawei.browser)
        else:
            logger.warning("非主线程或配置线程数不大于1，无需创建多线程")
            pass

    def __do_start_buying(self):
        if not self.is_can_submit_order:
            try:
                buttons = self.browser.find_elements(By.ID, 'prd-botnav-rightbtn')
                orderBtn = None
                for button in buttons:
                    if '立即购买' == button.text:
                        orderBtn = button

                if orderBtn is not None:
                    orderBtn.click()
            except (StaleElementReferenceException, NoSuchElementException, ElementClickInterceptedException):
                logger.warning("当前尝试下单失败，立即下单按钮不存在或当前不可点击")

    def __check_box_ct_pop_exists(self):
        boxCtPopIsExists = False
        try:
            self.browser.find_element(By.CSS_SELECTOR, "#show_risk_msg_box .box-ct .box-cc .box-content")
            boxCtPopIsExists = True
        except NoSuchElementException:
            pass
        return boxCtPopIsExists

    def __check_box_ct_pop_stage(self):
        boxCtPopIsExists = self.__check_box_ct_pop_exists()
        if boxCtPopIsExists:
            self.__check_box_ct_pop_act_is_started()
            self.__check_box_ct_pop_product_is_not_buy()
            self.__check_box_ct_pop_address_not_selected()

        return boxCtPopIsExists

    def __check_box_ct_pop_act_is_started(self):
        actIsStarted = True
        try:
            activity_text = self.browser.find_element(By.CSS_SELECTOR, ".box-ct .box-cc .box-content").text
            actIsStarted = activity_text.find('活动未开始') == -1
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        if not actIsStarted:
            logger.warning("动作太快了，活动未开始，关闭弹窗重试中")
            try:
                buttons = self.browser.find_elements(By.CSS_SELECTOR,
                                                     '.box-ct .box-cc .box-content .box-button .box-ok')
                for button in buttons:
                    if '知道了' == button.text:
                        button.click()
            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                logger.error("动作太快了，活动未开始，知道了按钮未找到：except: {}", e)
                pass

    def __check_box_ct_pop_product_is_not_buy(self):
        productIsNotBuy = False
        try:
            activity_text = self.browser.find_element(By.CSS_SELECTOR, ".box-ct .box-cc .box-content").text
            productIsNotBuy = activity_text.find('抱歉，没有抢到') != -1
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        if productIsNotBuy:
            logger.warning("抱歉，没有抢到，再试试")
            try:
                buttons = self.browser.find_elements(By.CSS_SELECTOR,
                                                     '.box-ct .box-cc .box-content .box-button .box-ok')
                for button in buttons:
                    if '再试试' == button.text:
                        button.click()
                        self.is_start_buying = True
            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                logger.error("抱歉，没有抢到，再试试按钮未找到：except: {} ", e)
                pass

    def __check_box_ct_pop_address_not_selected(self):
        addressIsSelected = False
        try:
            activity_text = self.browser.find_element(By.CSS_SELECTOR, ".box-ct .box-cc .box-content").text
            addressIsSelected = activity_text.find('请您选择收货地址') != -1
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        if addressIsSelected:
            logger.warning("收获地址未完全加载")
            try:
                buttons = self.browser.find_elements(By.CSS_SELECTOR,
                                                     '.box-ct .box-cc .box-content .box-button .box-ok')
                for button in buttons:
                    if '确定' == button.text:
                        button.click()
            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                logger.error("收获地址未完全加载：except: {}", e)
                pass

    def __check_iframe_box_pop_exists(self):
        logger.info("开始检查是否出现排队弹窗")
        iframeBoxExists = False
        try:
            self.browser.find_element(By.CSS_SELECTOR, '#iframeBox #queueIframe')
            iframeBoxExists = True
        except NoSuchElementException:
            pass
        logger.info("结束检查是否出现排队弹窗，结果：【{}】", '是' if iframeBoxExists else '否')
        return iframeBoxExists

    def __check_can_submit_order(self):
        if self.is_can_submit_order:
            pass
        else:
            logger.info("检查是否可以进行下单操作")
            self.__check_box_ct_pop_stage()
            self.__get_current_page_type()

            isOrderPage = self.__check_is_order_page()
            if isOrderPage:
                self.__set_end_start_buying()
            else:
                window_size = len(self.browser.window_handles)
                checkResult = 1
                if window_size <= 1:
                    iframeBoxExists = self.__check_iframe_box_pop_exists()
                    if iframeBoxExists:
                        iframe = self.browser.find_element(By.CSS_SELECTOR, '#RushBuyQueue')
                        self.browser.switch_to.frame(iframe)
                        iframeText = self.browser.find_element(By.CSS_SELECTOR, '.ecWeb-queue .queue-tips').text
                        for tipMsg in constants.TIP_MSGS:
                            if iframeText.find(tipMsg) != -1:
                                if tipMsg == '排队中':
                                    logger.warning("检查是否可以进行下单操作，排队状态：【{}】", tipMsg)
                                    checkResult = 0
                                    break
                                elif tipMsg == '当前排队人数过多，是否继续排队等待？':
                                    logger.warning("检查是否可以进行下单操作，排队状态：【{}】", tipMsg)
                                    checkResult = 0
                                    try:
                                        buttons = self.browser.find_elements(By.CSS_SELECTOR,
                                                                             '.ecWeb-queue .queue-btn .btn-ok')
                                        waitBtn = None
                                        for button in buttons:
                                            if '继续等待' == button.text:
                                                waitBtn = button

                                        if waitBtn is not None:
                                            waitBtn.click()
                                    except (NoSuchElementException, ElementClickInterceptedException,
                                            StaleElementReferenceException) as e:
                                        logger.error("检查是否可以进行下单操作，继续等待按钮未找到：except: {}", e)
                                        pass
                                    break
                                else:
                                    logger.warning("检查是否可以进行下单操作，当前提醒内容：【{}】", tipMsg)
                                    checkResult = -1
                                    break
                            else:
                                checkResult = 0
                                pass
                        self.browser.switch_to.default_content()
                    else:
                        iframeText = '未开始'
                        checkResult = -2
                        pass
                else:
                    iframeText = '待提交订单'
                    pass
                checkResultDict = {-2: '活动未开始', -1: '抢购结束', 0: '排队中', 1: '已排队，待提交订单'}
                logger.info("检查是否可以进行下单操作，当前提醒内容：【{}】, 检查结果：【{}】", iframeText,
                            checkResultDict[checkResult])
                if checkResult == 1:
                    self.__set_end_start_buying()

    def __buy_now(self):
        if self.is_buy_now:
            logger.info("开始立即购买")
            try:
                buttons = self.driver_wait.until(
                    EC.presence_of_all_elements_located((By.ID, 'prd-botnav-rightbtn')))
                orderBtn = None
                for button in buttons:
                    if '立即购买' == button.text:
                        orderBtn = button
                if orderBtn is not None:
                    orderBtn.click()

                    # 等待新标签页打开并切换到新标签页
                    times = 0
                    while len(self.browser.window_handles) == 1 and times < 1000:
                        time.sleep(0.01)
                        times += 1

                    if len(self.browser.window_handles) > 1:
                        # 切换到新打开的标签页
                        new_tab = self.browser.window_handles[-1]
                        self.browser.switch_to.window(new_tab)

                        # 检查当前是否是下单页面
                        isOrderPage = False
                        times = 0
                        while not isOrderPage:
                            if times > 1000:
                                break
                            isOrderPage = self.__check_is_order_page()
                            time.sleep(0.01)
                            times += 1

                    currentUrl = self.browser.current_url
                    if isOrderPage and currentUrl.find(constants.RUSH_ORDER_PAGE_URL):
                        self.__click_submit_order(currentUrl)
                    elif isOrderPage and currentUrl.find(constants.ORDER_PAGE_URL):
                        new_tab = self.browser.window_handles[-1]
                        self.browser.switch_to.window(new_tab)
                        self.__click_submit_order(currentUrl)
                    else:
                        logger.error("进入下单页面失败")
            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                logger.info("未找到【立即购买】按钮或按钮不可点击； except:{}", e)
            logger.info("结束立即购买")

    def __submit_order(self):
        if self.is_can_submit_order:
            self.__get_current_page_type()
            currentUrl = self.browser.current_url
            while self.is_can_submit_order:
                clickSuccess = self.__click_submit_order(currentUrl)
                if clickSuccess:
                    self.is_can_submit_order = False
                time.sleep(float(self.config.get('process', 'interval', '0.001')))

    def __click_submit_order(self, currentUrl):
        logger.info("开始点击提交订单")
        clickSuccess = False
        try:
            self.__check_box_ct_pop_stage()
            if EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#checkoutSubmit'), '提交订单')(self.browser):
                clickSuccess = self.__click_submit_order2(currentUrl)
            elif EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#checkoutSubmit'), '提交预约申购单')(self.browser):
                if not EC.element_located_to_be_selected((By.CSS_SELECTOR, '#agreementChecked'))(self.browser):
                    self.browser.find_element(By.CSS_SELECTOR, '#agreementChecked').click()
                clickSuccess = self.__click_submit_order2(currentUrl)
            else:
                logger.info("未找到【提交订单】按钮或按钮，尝试使用脚本提交。")
                self.browser.execute_script("if(typeof ec != 'undefined')ec.order.submit();")
            boxCtPopIsExists = self.__check_box_ct_pop_stage()
            if boxCtPopIsExists:
                logger.warning("已点击提交订单，提交订单不成功，重试中...")
            else:
                if EC.url_changes(currentUrl)(self.browser) and EC.url_contains(constants.PAYMENT_PAGE_URL)(self.browser):
                    clickSuccess = True
                    logger.success("已点击提交订单，提交订单成功")
                else:
                    pass
        except NoSuchElementException as noe:
            logger.error("点击提交订单异常，提交订单按钮不存在； except: {}", noe)
        except ElementClickInterceptedException as cie:
            logger.error("点击提交订单异常，提交订单按钮不可点击； except: {}", cie)
        except StaleElementReferenceException as sre:
            logger.error("点击提交订单异常，提交订单按钮状态已刷新； except: {}", sre)
            pass
        return clickSuccess

    def __click_submit_order2(self, currentUrl):
        clickSuccess = False
        try:
            self.browser.find_element(By.CSS_SELECTOR, '#checkoutSubmit').click()
        except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
            logger.info("未找到【提交订单】按钮或按钮不可点击，尝试使用脚本提交； except:{}", e)
            self.browser.execute_script("if(typeof ec != 'undefined')ec.order.submit();")
        boxCtPopIsExists = self.__check_box_ct_pop_stage()
        if boxCtPopIsExists:
            logger.warning("已点击提交订单，提交订单不成功，重试中...")
        else:
            if EC.url_changes(currentUrl)(self.browser) and EC.url_contains(constants.PAYMENT_PAGE_URL)(self.browser):
                clickSuccess = True
                logger.success("已点击提交订单，提交订单成功")
            else:
                pass
        return clickSuccess

    def __set_end_countdown(self):
        self.is_waiting = False
        self.is_countdown = False
        self.is_start_buying = True

    def __set_end_start_buying(self):
        self.is_start_buying = False
        self.is_can_submit_order = True

    def __set_end_waiting(self):
        self.is_waiting = False
        self.is_countdown = True

    def __set_buy_now(self):
        self.is_start_buying = False
        self.is_buy_now = True

    def __get_current_page_type(self):
        currentUrl = self.browser.current_url
        pageName = '未知页面'
        for page in constants.PAGES:
            if currentUrl.find(page.get("url")) != -1:
                pageName = page.get("pageDesc")
                break
        logger.info("当前所在页面类型：{0} 地址：{1}".format(pageName, currentUrl))

    def __check_is_order_page(self):
        currentUrl = self.browser.current_url
        return currentUrl.find(constants.ORDER_PAGE_URL) != -1 or currentUrl.find(constants.RUSH_ORDER_PAGE_URL) != -1

    def __get_sec_kill_time(self):
        logger.info("开始获取抢购开始时间")
        tryTimes = 1
        while self.sec_kill_time is None and tryTimes < constants.RETRY_TIMES:
            try:
                countdownStr = self.browser.find_element(By.CSS_SELECTOR, "#prd-detail  .css-901oao.r-jwli3a.r-1b43r93.r-13uqrnb.r-16dba41.r-oxtfae.r-hjklzo.r-6dt33c")
                countdownStr = datetime.now().strftime("%Y年") + countdownStr.text[5:]
                self.sec_kill_time = datetime.strptime(countdownStr, "%Y年%m月%d日 %H:%M")
                logger.info("抢购开始时间为：[{}]", self.sec_kill_time)
            except (StaleElementReferenceException, NoSuchElementException):
                pass
            tryTimes += 1

        logger.info("获取抢购开始时间结束")

    def close_browser(self):
        self.browser.quit()
        # 关掉所有线程中窗口
        for browser in self.thread_browsers:
            browser.quit()