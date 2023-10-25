# -*- coding: utf-8 -*-
# !/usr/bin/python
import locale
import os.path
import sys
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
from loguru import logger


class HuaWei:
    config = None
    browser = None
    isLogin = False
    isWaiting = True
    isCountdown = True
    isStartBuying = False
    startBuyingTime = None
    isBuyNow = False
    # 全局页面元素超时时间，单位S
    defaultTimeout = 30
    secKillTime = None
    hwServerTimestamp = None
    localTimestamp = None
    driverWait = None
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

    def __init__(self, config_file):
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self.selenium_log_path = os.path.join(log_path, "selenium.log")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        logger.info("开始解析配置文件")
        self.config = Config(config_file)
        logger.info("结束解析配置文件")
        self.__browser_setting()
        self.__get_local_and_hw_server_time_diff()
        self.driverWait = WebDriverWait(self.browser, 2, 0.01)

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

    def __browser_setting(self):
        logger.info("开始设置浏览器参数")
        browserType = self.config.get("browser", "type", 'chrome')
        self.browser = BrowserFactory.build(browserType).setting(self.config, self.selenium_log_path)
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
        logger.info("开始登陆华为账号")
        self.__goto_login_page()
        self.__do_login()

        loginTimes = 1
        while not self.isLogin and loginTimes < 3:
            logger.info("开始第 {} 次尝试登陆华为账号", loginTimes)
            loggedResult = self.__check_logged_result()
            if loggedResult > 0:
                self.isLogin = True
            elif loggedResult == 0:
                self.__login_security_verification()
                self.__trust_browser()
                self.isLogin = self.__current_is_login_page()
            else:
                self.isLogin = False
            loginDesc = '失败' if self.isLogin else '成功'
            logger.info("第 {} 次尝试登陆华为账号，登陆结果：{}", loginTimes, loginDesc)
            loginTimes += 1

        if not self.isLogin:
            logger.warning("登陆华为账号失败，程序将在3秒后退出...")
            time.sleep(3)
            exit()

        """
        TODO：实现cookie记录，并实现Cookie登陆
        """

        nickname = self.__get_logged_nickname()
        logger.success("当前登陆账号昵称为：{0}".format(nickname))
        logger.info("结束登陆华为账号")

    def __goto_login_page(self):
        currentUrl = self.browser.current_url
        loginLink = None
        times = 1
        while loginLink is None and times < 3:
            loginLink = self.__find_element_text(By.CLASS_NAME, "r-1a7l8x0", '请登录', True)
            times += 1

        if loginLink is None:
            logger.warning("登陆跳转失败，未找到登陆跳转链接，程序将在3秒后退出...")
            time.sleep(3)
            exit()

        logger.info("开始点击登录按钮")
        loginLink.click()

        try:
            self.driverWait.until(EC.title_contains('华为帐号-登录'))
            logger.info("已跳转登录页面")
            self.__get_current_page_type()
        except TimeoutException:
            logger.warning("登陆跳转失败，未找到登陆跳转链接，程序将在3秒后退出...")
            time.sleep(3)
            exit()

    def __do_login(self):
        logger.info("开始输入账号及密码")
        inputElements = self.driverWait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "hwid-input")))

        inputElements[0].send_keys(self.config.get("user", "name"))
        inputElements[1].send_keys(self.config.get("user", "password"))
        logger.info("已输入账号及密码")

        self.driverWait.until(EC.presence_of_element_located((By.CLASS_NAME, "hwid-login-btn"))).click()
        logger.info("发起登陆请求")

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
                self.__find_element_text(By.CSS_SELECTOR, ".hwid-trustBrowser .hwid-dialog-textBtnBox .normalBtn",
                                         "信任", True).click()
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
        self.isLogin = self.__current_is_login_page()
        if self.isLogin:
            logger.success("账号登陆成功")
            self.nickname = self.__get_logged_nickname()
        else:
            logger.warning("账号登陆失败，请重试...")

    def __get_logged_nickname(self):
        nickname = '游客'
        try:
            nickname = self.driverWait.until(EC.presence_of_element_located((By.CLASS_NAME, "r-1a7l8x0"))).text
        except TimeoutException:
            logger.warning("获取当前登陆账号昵称超时")
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
        while self.isWaiting:
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
                self.__set_end_count_down()
                self.__set_buy_now()

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
            countdown_times = utils.calc_countdown_times(self.secKillTime, self.localTimestamp - self.hwServerTimestamp)
            if len(countdown_times) > 0:
                logger.info("距离抢购开始还剩：{}", utils.format_countdown_time(countdown_times))
                self.__set_start_buying(countdown_times)
                if not self.isStartBuying:
                    time.sleep(1)

    def __start_buying(self):
        logger.info("进入抢购活动最后排队下单环节")
        click_times = 0
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
                logger.info("抢购活动最后下单环节，开始抢购中")
                try:
                    order_btn = self.__find_element_text(By.CSS_SELECTOR, "#pro-operation > span", "立即下单", True)
                    if order_btn is not None:
                        order_btn.click()
                except (NoSuchElementException, ElementClickInterceptedException):
                    click_times += 1
                    logger.info("抢购活动最后下单环节，已尝试点击立即下单 {} 次", click_times)

                self.__submit_order("__start_buying")
                time.sleep(0.001)
        logger.info("抢购活动最后排队下单环节结束")

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
        except NoSuchElementException:
            pass

        if not actIsStarted:
            logger.warning("动作太快了，活动未开始，关闭弹窗重试中")
            try:
                box_btn = self.__find_element_text(By.CSS_SELECTOR, ".box-ct .box-cc .box-content .box-button .box-ok",
                                                   '知道了', None)
                if box_btn is not None:
                    box_btn.click()
            except (NoSuchElementException, ElementClickInterceptedException) as e:
                logger.error("动作太快了，活动未开始，知道了按钮未找到：except: {} element: {}", e,
                             self.browser.page_source)
                pass

    def __check_box_ct_pop_product_is_not_buy(self):
        productIsNotBuy = False
        try:
            activity_text = self.browser.find_element(By.CSS_SELECTOR, ".box-ct .box-cc .box-content").text
            productIsNotBuy = activity_text.find('抱歉，没有抢到') != -1
        except NoSuchElementException:
            pass

        if productIsNotBuy:
            logger.warning("抱歉，没有抢到，再试试")
            try:
                box_btn = self.__find_element_text(By.CSS_SELECTOR, ".box-ct .box-cc .box-content .box-button .box-ok",
                                                   '再试试', None)
                if box_btn is not None:
                    box_btn.click()
                    self.isStartBuying = True
            except (NoSuchElementException, ElementClickInterceptedException) as e:
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
        logger.info("结束检查是否出现排队弹窗")
        return iframeBoxExists

    def __check_can_submit_order(self):
        logger.info("检查是否可以进行下单操作")
        iframeBoxExists = self.__check_iframe_box_pop_exists()
        checkResult = 1
        iframeText = ""
        if iframeBoxExists:
            iframe = self.browser.find_element(By.CSS_SELECTOR, '#iframeBox #queueIframe')
            self.browser.switch_to.frame(iframe)
            iframeText = self.browser.find_element(By.CSS_SELECTOR, '.ecWeb-queue .queue-tips').text
            logger.info("检查是否可以进行下单操作，当前 iframe 弹窗具体 HTML 内容：{}",
                        self.browser.find_element(By.CSS_SELECTOR, '.ecWeb-queue').get_attribute('outerHTML'))
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
                            btnOk = self.__find_element_text(By.CSS_SELECTOR, ".ecWeb-queue .queue-btn .btn-ok",
                                                             '继续等待', None)
                            if btnOk is not None:
                                btnOk.click()
                                self.browser.switch_to.default_content()
                        except (NoSuchElementException, ElementClickInterceptedException) as e:
                            logger.error("检查是否可以进行下单操作，继续等待按钮未找到：except: {} element: {}", e,
                                         self.browser.page_source)
                            pass
                        break
                    else:
                        logger.warning("检查是否可以进行下单操作，当前提醒内容：【{}】", tipMsg)
                        checkResult = -1
                        break
                else:
                    pass

            self.browser.switch_to.default_content()
        checkResultDict = {-1: '抢购结束', 0: '排队中', 1: '已排队，待提交订单'}
        if checkResult == 1:
            logger.info("检查是否可以进行下单操作，当前提醒内容：【{}】, 检查结果：【{}】", iframeText,
                        checkResultDict[checkResult])
        else:
            logger.info("检查是否可以进行下单操作，检查结果：【{}】", checkResultDict[checkResult])
        return checkResult

    def __buy_now(self):
        if self.isBuyNow:
            logger.info("开始立即购买")
            try:
                order_btn = self.__find_element_text(By.CSS_SELECTOR, "#pro-operation > a", "立即下单")
                if order_btn is not None:
                    order_btn.click()
                else:
                    logger.error("未找到【立即下单】按钮")
            except (NoSuchElementException, ElementClickInterceptedException) as e:
                logger.info("未找到【立即下单】按钮或按钮不可点击； except:{} element: {}", e, self.browser.page_source)
            logger.info("结束立即购买")
            self.__submit_order("__buy_now")

    def __submit_order(self, source):
        if source == '__start_buying':
            self.__check_box_ct_pop_stage()
            canSubmitOrder = self.__check_can_submit_order()
            pageType = self.__get_current_page_type()
            if canSubmitOrder and pageType == 'order':
                clickSuccess = self.__click_submit_order()
                if clickSuccess:
                    self.isStartBuying = False
        else:
            self.__click_submit_order()

    def __click_submit_order(self):
        logger.info("开始点击提交订单")
        clickSuccess = False
        try:
            if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#checkoutSubmit > span"), "提交订单")(self.browser):
                try:
                    self.browser.find_element(By.ID, "checkoutSubmit").click()
                    logger.info("已点击提交订单")
                    boxCtPopIsExists = self.__check_box_ct_pop_stage()
                    if boxCtPopIsExists:
                        clickSuccess = False
                        logger.warning("已点击提交订单，提交订单不成功，重试中...")
                    else:
                        clickSuccess = True
                        logger.success("已点击提交订单，提交订单成功")
                except NoSuchElementException as noe:
                    logger.error("点击提交订单异常，提交订单不存在； except: {}, element: {}", noe,
                                 self.browser.page_source)
                    clickSuccess = False
        except Exception as e:
            logger.error("点击提交订单异常: {}", e)
            clickSuccess = False
        return clickSuccess

    def __set_start_buying(self, countdown_times):
        if (countdown_times[0] != "00" or countdown_times[1] != "00" or
                countdown_times[2] != "00" or int(countdown_times[3]) > 5):
            pass
        else:
            self.isCountdown = False
            self.isStartBuying = True

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
            items = []
            try:
                items = self.driverWait.until(EC.presence_of_all_elements_located((by, value)))
            except TimeoutException:
                pass
        element = None
        for item in items:
            if text == item.text:
                element = item
        if element is None:
            return
        return element

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
