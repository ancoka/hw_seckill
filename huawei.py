# -*- coding: utf-8 -*-
# !/usr/bin/python
import json
import locale
import os.path
import sys
import threading
import time
from datetime import datetime
from urllib.parse import unquote

from selenium.common import StaleElementReferenceException, NoSuchElementException, TimeoutException, \
    ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from browser.browser_factory import BrowserFactory
from config import Config
import utils
from loguru import logger

from huawei_thread import HuaWeiThread


class HuaWei:
    projectPath = os.path.dirname(os.path.abspath(__file__))
    logPath = os.path.join(projectPath, "logs")
    seleniumLogFile = os.path.join(logPath, "selenium.log")
    baseProfilePath = os.path.join(projectPath, "profiles")
    cookiesFile = os.path.join(projectPath, "hw_cookies.txt")
    configFile = os.path.join(projectPath, "config.ini")
    config = None
    browser = None
    isLogin = False
    isWaiting = True
    isCountdown = True
    isStartBuying = False
    isCanSubmitOrder = False
    isBuyNow = False
    secKillTime = None
    hwServerTimestamp = None
    localTimestamp = None
    driverWait = None
    browserType = None
    tipMsgs = [
        '抱歉，已售完，下次再来',
        '抱歉，没有抢到',
        '抱歉，仅限预约用户购买',
        '抢购活动未开始，看看其他商品吧',
        '本次发售商品数量有限，您已超过购买上限，请勿重复抢购，将机会留给其他人吧',
        '抱歉，您不符合购买条件',
        '登记排队，有货时通知您',
        '抱歉，库存不足',
        '您已超过购买上限，本场活动最多还能买',
        '当前排队人数过多，是否继续排队等待？',
        '排队中',
        '秒杀活动已结束',
        '秒杀火爆<br/>该秒杀商品已售罄',
    ]

    def __init__(self, profilePath=None):
        logger.info("开始解析配置文件")
        self.config = Config(self.configFile)
        logger.info("结束解析配置文件")
        self.browserType = self.config.get("browser", "type", 'chrome')
        self.__pre_browser_setting()
        if profilePath is None or profilePath == '':
            profilePath = utils.get_profile_path(self.baseProfilePath, self.browserType, 1)
        self.__browser_setting(profilePath)
        self.__get_local_and_hw_server_time_diff()
        self.driverWait = WebDriverWait(self.browser, 5, 0.01)

    def start_process(self):
        logger.info("开启抢购华为手机 {0}".format(self.config.get("product", "name")))
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
        logger.info("结束抢购华为手机 {0}".format(self.config.get("product", "name")))
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
        if not os.path.exists(self.logPath):
            os.makedirs(self.logPath)

        threadCount = max(int(self.config.get("process", "thread", '1')), 1)
        for i in range(1, threadCount + 1):
            profilePath = utils.get_profile_path(self.baseProfilePath, self.browserType, i)
            if not os.path.exists(profilePath):
                os.makedirs(profilePath)

    def __browser_setting(self, profilePath):
        logger.info("开始设置浏览器参数")
        self.browser = BrowserFactory.build(self.browserType).setting(self.config, self.seleniumLogFile, profilePath)
        self.browser.maximize_window()

    def __visit_official_website(self):
        logger.info("开始进入华为官网")
        self.browser.get('https://www.vmall.com/')
        try:
            self.driverWait.until(EC.url_changes)
            logger.info("已进入华为官网")
            self.__get_current_page_type()
        except TimeoutException:
            logger.warning("进入华为官网失败，程序将在3秒后退出...")
            time.sleep(3)
            self.browser.quit()

    def __login(self):
        logger.info("开始登录华为账号")
        self.isLogin = self.__check_is_logged_in()
        if not self.isLogin:
            self.__goto_login_page()
            self.__do_login()

            loginTimes = 1
            while not self.isLogin and loginTimes < 3:
                logger.info("开始第 {} 次尝试登录华为账号", loginTimes)
                loggedResult = self.__check_logged_result()
                if loggedResult > 0:
                    self.isLogin = True
                elif loggedResult == 0:
                    self.__login_security_verification()
                    self.__trust_browser()
                    self.isLogin = self.__check_is_logged_in()
                else:
                    self.isLogin = False
                loginDesc = '成功' if self.isLogin else '失败'
                logger.info("第 {} 次尝试登录华为账号，登录结果：{}", loginTimes, loginDesc)
                loginTimes += 1

        if not self.isLogin:
            logger.warning("登录华为账号失败，程序将在3秒后退出...")
            time.sleep(3)
            exit()

        self.__cookies_save()

        nickname = self.__get_logged_nickname()
        logger.success("当前登录账号昵称为：{0}".format(nickname))
        logger.info("结束登录华为账号")

    def __cookies_save(self):
        cookies = self.browser.get_cookies()
        with open(self.cookiesFile, 'w') as f:
            f.write(json.dumps(cookies))
            f.close()

    def __load_cookies(self):
        with open(self.cookiesFile, 'r') as f:
            cookies = json.load(f)
            for cookie in cookies:
                self.browser.add_cookie(cookie)
            f.close()

    def __goto_login_page(self):
        loginLink = None
        times = 1
        while loginLink is None and times < 3:
            menu_links = self.driverWait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.r-1a7l8x0')))
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
            self.driverWait.until(EC.title_contains('华为帐号-登录'))
            logger.info("已跳转登录页面")
            self.__get_current_page_type()
        except TimeoutException:
            logger.warning("登录跳转失败，未找到登录跳转链接，程序将在3秒后退出...")
            time.sleep(3)
            exit()

    def __do_login(self):
        logger.info("开始输入账号及密码")
        inputElements = self.driverWait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "hwid-input")))

        inputElements[0].send_keys(self.config.get("user", "name"))
        inputElements[1].send_keys(self.config.get("user", "password"))
        logger.info("已输入账号及密码")

        self.driverWait.until(EC.presence_of_element_located((By.CLASS_NAME, "hwid-login-btn"))).click()
        logger.info("发起登录请求")

    def __check_logged_result(self):
        loggedResult = 0
        isLoginPage = self.__current_is_login_page()
        isNeedVerificationCode = self.__check_is_need_verification_code()
        if not isLoginPage:
            loggedResult = 1
        elif isLoginPage and not isNeedVerificationCode:
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
            isNeedVerificationCode = self.driverWait.until(EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".hwid-dialog-main .hwid-getAuthCode .hwid-smsCode"),
                "获取验证码"))
        except TimeoutException:
            pass

        logger.info("检查是否需要获取验证码，检查结果：{}", "需要" if isNeedVerificationCode else "不需要")
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
            self.driverWait.until(EC.presence_of_element_located((By.CLASS_NAME, "hwid-smsCode"))).click()
            logger.success("短信验证码已发送")
        except TimeoutException:
            logger.warning("短信验证码已发送超时")

    def __check_is_need_trust_browser(self):
        logger.info("检查是否需要信任浏览器")
        isNeedTrustBrowser = False
        try:
            isNeedTrustBrowser = self.driverWait.until(EC.text_to_be_present_in_element(
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
                buttons = self.driverWait.until(EC.presence_of_all_elements_located(
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
            isLoginPage = self.driverWait.until_not(EC.url_contains("id1.cloud.huawei.com/CAS/portal/loginAuth.html"))
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
        self.browser.get("https://www.vmall.com/product/{0}.html".format(self.config.get("product", "id")))
        try:
            self.driverWait.until(EC.url_changes(currentUrl))
            logger.info("已进入华为 {0} 产品详情页".format(self.config.get("product", "name")))
            self.__get_current_page_type()
        except TimeoutException:
            logger.info("进入华为 {0} 产品详情页失败，程序将在3秒后退出...".format(self.config.get("product", "name")))
            time.sleep(3)
            self.browser.quit()

    def __waiting_count(self):
        times = 1
        while self.isWaiting and times <= 3:
            try:
                if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-operation > a"), "暂不售卖")(
                        self.browser):
                    logger.info("【{}】倒计时未开始，等待中...", "暂不售卖")
                    time.sleep(120)
                    self.__refresh_product_page()
                elif EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-operation > a"), "暂时缺货")(
                        self.browser):
                    logger.info("【{}】倒计时未开始，等待中...", "暂时缺货")
                    time.sleep(120)
                    self.__refresh_product_page()
                elif EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-operation > a"), "即将开始")(
                        self.browser):
                    logger.info("倒计时即将开始")
                    self.__get_sec_kill_time()
                    if self.secKillTime is not None:
                        self.__set_end_waiting()
                        time.sleep(1)
                else:
                    logger.info("当前可立即下单")
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
        for sku in set_skus:
            self.driverWait.until(EC.presence_of_element_located((By.LINK_TEXT, f"{sku}"))).click()
        sku_payment = '无'
        if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-skus > dl:last-child > label"), "选择销售类型")(
                self.browser):
            sku_payment = self.config.get("product", "payment", "全款购买")
            self.driverWait.until(EC.presence_of_element_located((By.LINK_TEXT, f"{sku_payment}"))).click()
        logger.info("选择手机套装规格完成，套装规格：{0} 销售类型：{1}".format(sets, sku_payment))

    def __choose_product_item(self):
        logger.info("开始选择手机单品规格")
        sku_color = self.config.get("product", "color")
        sku_version = self.config.get("product", "version")
        self.driverWait.until(EC.presence_of_element_located((By.LINK_TEXT, f"{sku_color}"))).click()
        self.driverWait.until(EC.presence_of_element_located((By.LINK_TEXT, f"{sku_version}"))).click()
        sku_payment = '无'
        if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#pro-skus > dl:last-child > label"), "选择销售类型")(
                self.browser):
            sku_payment = self.config.get("product", "payment")
            self.driverWait.until(EC.presence_of_element_located((By.LINK_TEXT, f"{sku_payment}"))).click()
        logger.info("选择手机单品规格完成，颜色：{0} 版本：{1} 销售类型：{1}".format(sku_color, sku_version, sku_payment))

    def __countdown(self):
        while self.isCountdown:
            currentUrl = self.browser.current_url
            countdownMsDiff = utils.calc_countdown_ms_diff(self.secKillTime,
                                                           self.localTimestamp - self.hwServerTimestamp)
            countdownTimes = utils.calc_countdown_times(self.secKillTime,
                                                        self.localTimestamp - self.hwServerTimestamp)

            if countdownMsDiff > 120000:
                logger.info("距离抢购开始还剩：{}", utils.format_countdown_time(countdownTimes))
                time.sleep(5)
            else:
                self.__set_end_countdown()

    def __start_buying(self):
        logger.info("进入抢购活动最后排队下单环节")
        self.__create_and_start_thread()
        clickTimes = 1
        while self.isStartBuying:
            countdownMsDiff = utils.calc_countdown_ms_diff(self.secKillTime,
                                                           self.localTimestamp - self.hwServerTimestamp)
            countdown_times = utils.calc_countdown_times(self.secKillTime,
                                                         self.localTimestamp - self.hwServerTimestamp)
            if countdownMsDiff > 1000:
                logger.info("距离抢购活动最后下单环节开始还剩：{}", utils.format_countdown_time(countdown_times))
                time.sleep(1)
            elif countdownMsDiff > 100:
                logger.info("距离抢购活动最后下单环节开始还剩：{}", utils.format_countdown_time(countdown_times))
                time.sleep(0.1)
            elif countdownMsDiff > 10:
                logger.info("距离抢购活动最后下单环节开始还剩：{}", utils.format_countdown_time(countdown_times))
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
        threadCount = max(int(self.config.get("process", "thread", '1')), 1)
        currentThread = threading.current_thread()
        if currentThread is threading.main_thread() and threadCount > 1:
            logger.info("开始创建多线程，需要创建线程数：{}", threadCount)
            for i in range(2, threadCount + 1):
                profilePath = os.path.join(os.path.join(self.baseProfilePath, self.browserType),
                                           'profile_{0}'.format(i))
                t = HuaWeiThread(i, HuaWei(profilePath))
                t.start()
        else:
            logger.warning("非主线程或配置线程数不大于1，无需创建多线程")
            pass

    def __do_start_buying(self):
        if not self.isCanSubmitOrder:
            try:
                buttons = self.browser.find_elements(By.CSS_SELECTOR, '#pro-operation > span')
                orderBtn = None
                for button in buttons:
                    if '立即下单' == button.text:
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
                        self.isStartBuying = True
            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                logger.error("抱歉，没有抢到，再试试按钮未找到：except: {} element: {}", e,
                             self.browser.page_source)
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
        if self.isCanSubmitOrder:
            pass
        else:
            logger.info("检查是否可以进行下单操作")
            self.__check_box_ct_pop_stage()
            self.__get_current_page_type()
            isOrderSubmitPage = EC.url_contains("www.vmall.com/order/nowConfirmcart")(self.browser)
            checkResult = 1
            if not isOrderSubmitPage:
                iframeBoxExists = self.__check_iframe_box_pop_exists()
                if iframeBoxExists:
                    iframe = self.browser.find_element(By.CSS_SELECTOR, '#iframeBox #queueIframe')
                    self.browser.switch_to.frame(iframe)
                    iframeText = self.browser.find_element(By.CSS_SELECTOR, '.ecWeb-queue .queue-tips').text
                    for tipMsg in self.tipMsgs:
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
        if self.isBuyNow:
            currentUrl = self.browser.current_url
            logger.info("开始立即购买")
            try:
                buttons = self.driverWait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#pro-operation > a')))
                orderBtn = None
                for button in buttons:
                    if '立即下单' == button.text:
                        orderBtn = button
                if orderBtn is not None:
                    orderBtn.click()
                    time.sleep(1)
                    self.__click_submit_order(currentUrl)
            except (NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                logger.info("未找到【立即下单】按钮或按钮不可点击； except:{}", e)
            logger.info("结束立即购买")

    def __submit_order(self):
        if self.isCanSubmitOrder:
            currentUrl = self.browser.current_url
            while self.isCanSubmitOrder:
                clickSuccess = self.__click_submit_order(currentUrl)
                if clickSuccess:
                    self.isCanSubmitOrder = False
                time.sleep(float(self.config.get('process', 'interval', '0.001')))

    def __click_submit_order(self, currentUrl):
        logger.info("开始点击提交订单")
        clickSuccess = False
        try:
            self.__check_box_ct_pop_stage()
            if EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#checkoutSubmit > span'), '提交订单')(self.browser):
                self.browser.find_element(By.CSS_SELECTOR, '#checkoutSubmit').click()
                boxCtPopIsExists = self.__check_box_ct_pop_stage()
                if boxCtPopIsExists:
                    logger.warning("已点击提交订单，提交订单不成功，重试中...")
                else:
                    if EC.url_changes(currentUrl)(self.browser) and EC.url_contains("payment.vmall.com/cashier/web/pcIndex.htm")(self.browser):
                        clickSuccess = True
                        logger.success("已点击提交订单，提交订单成功")
                    else:
                        pass
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

    def __set_end_countdown(self):
        self.isWaiting = False
        self.isCountdown = False
        self.isStartBuying = True

    def __set_end_start_buying(self):
        self.isStartBuying = False
        self.isCanSubmitOrder = True

    def __set_end_waiting(self):
        self.isWaiting = False
        self.isCountdown = True

    def __set_buy_now(self):
        self.isStartBuying = False
        self.isBuyNow = True

    def __get_current_page_type(self):
        currentUrl = self.browser.current_url
        if currentUrl.find('www.vmall.com/index.html') != -1:
            pageType = 'index'
        elif currentUrl.find('id1.cloud.huawei.com/CAS/portal/loginAuth.html') != -1:
            pageType = 'login'
        elif currentUrl.find("www.vmall.com/product/{0}.html".format(self.config.get("product", "id", ""))) != -1:
            pageType = 'product'
        elif currentUrl.find("www.vmall.com/order/nowConfirmcart") != -1:
            pageType = 'order'
        elif currentUrl.find("payment.vmall.com/cashier/web/pcIndex.htm") != -1:
            pageType = 'payment'
        else:
            pageType = 'unknown'
            pass
        logger.info("当前所在页面类型：{0} 地址：{1}".format(pageType, currentUrl))
        return pageType

    def __get_sec_kill_time(self):
        logger.info("开始获取抢购开始时间")
        tryTimes = 1
        while self.secKillTime is None and tryTimes < 3:
            try:
                if sys.platform.startswith('win'):
                    locale.setlocale(locale.LC_ALL, 'en')
                    locale.setlocale(locale.LC_CTYPE, 'chinese')
                countdownStr = self.browser.find_element(By.CSS_SELECTOR, "#pro-operation-countdown > p").text
                countdownStr = datetime.now().strftime("%Y年") + countdownStr[:-3]
                self.secKillTime = datetime.strptime(countdownStr, "%Y年%m月%d日 %H:%M")
                logger.info("抢购开始时间为：[{}]", self.secKillTime)
            except (StaleElementReferenceException, NoSuchElementException):
                pass
            tryTimes += 1

        logger.info("获取抢购开始时间结束")

    def __get_local_and_hw_server_time_diff(self):
        logger.info("开始获取华为服务器时间及本地时间")
        self.hwServerTimestamp = utils.get_hw_server_timestamp()
        self.localTimestamp = utils.get_local_timestamp()

        logger.info("当前华为服务器时间为：[{}]", utils.timestamp2time(self.hwServerTimestamp))
        logger.info("当前本地时间为：【{}】", utils.timestamp2time(self.localTimestamp))

        timeDiff = self.localTimestamp - self.hwServerTimestamp
        compareRes = "晚于" if timeDiff >= 0 else "早于"
        logger.info("结束获取华为服务器时间及本地时间，结果：本地时间【{}】华为服务器时间【{}】毫秒", compareRes,
                    abs(timeDiff))
