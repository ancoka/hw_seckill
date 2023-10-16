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
    nickname = "游客"
    # 全局页面元素超时时间，单位S
    defaultTimeout = 60

    def __init__(self, config_file):
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self.selenium_log_path = os.path.join(log_path, "selenium.log")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        logger.info("开始解析配置文件")
        self.config = Config(config_file)
        logger.info("结束解析配置文件")
        self.__browser_setting()

    def start_process(self):
        logger.info("开启抢购华为手机 {0}".format(self.config.get("product", "name")))
        self.__visit_official_website()
        self.__get_current_page_type()
        self.__login()
        if self.isLogin:
            self.__visit_product_page()
            self.__get_current_page_type()
            self.__waiting_count()
            self.__choose_product()
            self.__countdown()
            self.__start_buying()
            self.__buy_now()

    def stop_process(self):
        logger.info("结束抢购华为手机 {0}".format(self.config.get("product", "name")))
        time.sleep(120)
        self.browser.quit()

    def __visit_official_website(self):
        logger.info("开始进入华为官网")
        self.browser.get('https://www.vmall.com/')
        logger.info("已进入华为官网")

    def __visit_product_page(self):
        logger.info("开始进入华为 {0} 产品详情页".format(self.config.get("product", "name")))
        self.browser.get("https://www.vmall.com/product/{0}.html".format(self.config.get("product", "id")))
        logger.info("已进入华为 {0} 产品详情页".format(self.config.get("product", "name")))
        self.__refresh_product_page()

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
        logger.info("选择手机套装规格完成，套装规格：{0} 销售类型：{1}".format(sets, sku_payment))

    def __choose_product_item(self):
        logger.info("开始选择手机单品规格")
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
        logger.info("选择手机单品规格完成，颜色：{0} 版本：{1} 销售类型：{1}".format(sku_color, sku_version, sku_payment))

    def __login(self):
        logger.info("开始登陆华为账号")
        self.__goto_login_page()
        self.__get_current_page_type()
        self.__submit_login()
        self.__get_current_page_type()
        self.__login_security_verification()
        self.__trust_browser()
        self.__check_is_logged_in()

        """ 
        TODO：实现cookie记录，并实现Cookie登陆
        """
        if self.isLogin:
            logger.success("当前登陆账号为：{0}".format(self.nickname))

        logger.info("结束登陆华为账号")

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
                                              ".hwid-getAuthCode-input .hwid-input-area .hwid-input").send_keys(
                        verificationCode)
                isInputVerificationCode = self.__check_is_input_verification_code()
                if isInputVerificationCode:
                    verificationCode = self.browser.find_element(By.CSS_SELECTOR,
                                                                 ".hwid-getAuthCode-input .hwid-input-area .hwid-input").get_attribute(
                        'value')
                    verificationCode.strip()
                    if len(verificationCode) != 6:
                        logger.warning("已输入验证码，验证码为【{}】长度不满足6位，继续等待输入", verificationCode)
                        time.sleep(5)
                    else:
                        logger.info("已输入验证码，验证码为【{}】", verificationCode)
                        self.browser.find_element(By.CSS_SELECTOR,
                                                  ".hwid-dialog-footer .hwid-button-base-box2 .dialogFooterBtn").click()
                        isNeedVerificationCode = False
                else:
                    time.sleep(5)
        else:
            pass

    def __browser_setting(self):
        logger.info("开始设置浏览器参数")
        browserType = self.config.get("browser", "type", 'chrome')
        self.browser = BrowserFactory.build(browserType).setting(self.config, self.selenium_log_path)
        self.browser.maximize_window()
        self.browser.implicitly_wait(10)

    def __countdown(self):
        while self.isCountdown:
            countdown_times = self.__get_countdown_time()
            if len(countdown_times) > 0:
                logger.info("距离抢购开始还剩：{}", utils.format_countdown_time(countdown_times))
                self.__set_start_buying(countdown_times)
                if not self.isStartBuying:
                    time.sleep(1)

    def __start_buying(self):
        logger.info("进入最后下单环节")

        click_times = 0
        while self.isStartBuying:
            second = utils.seconds_diff(datetime.now(), self.startBuyingTime)
            if second >= 0:
                logger.info("距离抢购开始还剩{}秒", second)
                self.__check_box_ct_pop_stage()
            elif second > -2:
                logger.info("抢购开始")
                self.__check_iframe_box_stage()
            else:
                self.isStartBuying = False

            try:
                order_btn = self.__find_element_text(By.CSS_SELECTOR, "#pro-operation > span", "立即下单")
                if order_btn is not None:
                    order_btn.click()
            except (NoSuchElementException, ElementClickInterceptedException):
                click_times += 1
                logger.info("已尝试点击立即下单 {} 次", click_times)

            time.sleep(0.001)

        logger.info("最后下单环节结束")

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
            productIsSoldOut = self.__check_product_is_sold_out(queueIsSuccess)
            if not productIsSoldOut:
                self.__check_box_ct_pop_stage()
                pageType = self.__get_current_page_type()
                if pageType == "order":
                    self.isStartBuying = False
                    self.__submit_order()
                    self.__check_box_ct_pop_stage()

    def __check_queue_stage(self):
        logger.info("尝试检查当前排队状态")
        iframe_content = self.browser.find_element(By.ID, 'iframeBox').text
        queueIsSuccess = iframe_content.find("排队中") == -1
        logger.info("尝试检查当前排队状态，排队结果：【{}】", '已排队' if queueIsSuccess else '排队中')
        return queueIsSuccess

    def __check_product_is_sold_out(self, queueIsSuccess):
        logger.info("尝试检查商品是否已售完")
        productIsSoldOut = False
        if queueIsSuccess:
            text = self.browser.find_element(By.ID, 'iframeBox').text
            logger.info("尝试检查商品是否已售完，{}", text)
            productIsSoldOut = text.find('已售完') != -1

        productSoleOutResult = '已售完' if productIsSoldOut else '未售完'
        logger.info("尝试检查商品是否已售完，锁定结果：【{}】", productSoleOutResult)
        return productIsSoldOut

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
            self.__submit_order()

    def __submit_order(self):
        if EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#checkoutSubmit > span"), "提交订单")(self.browser):
            try:
                logger.info("准备提交订单")
                self.browser.find_element(By.ID, "checkoutSubmit").click()
                logger.success("提交订单成功")
            except NoSuchElementException as noe:
                logger.info("提交订单失败； except: {}, element: {}", noe, self.browser.page_source)

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
        logger.info("点击登录按钮")
        login = self.__find_element_text(By.CLASS_NAME, "r-1a7l8x0", '请登录', True)
        if login is not None:
            login.click()
        else:
            logger.warning("登陆跳转失败，未找到登陆跳转链接", self.browser.page_source)
            exit()

        logger.info("已跳转登录页面")

    def __submit_login(self):
        logger.info("开始输入账号及密码")
        input_elements = WebDriverWait(self.browser, self.defaultTimeout).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "hwid-input"))
        )

        input_elements[0].send_keys(self.config.get("user", "name"))
        input_elements[1].send_keys(self.config.get("user", "password"))
        logger.info("已输入账号及密码")

        WebDriverWait(self.browser, self.defaultTimeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hwid-login-btn"))
        ).click()
        logger.info("发起登陆请求")

    def __check_is_need_verification_code(self):
        logger.info("检查是否需要获取验证码")
        isNeedVerificationCode = False
        try:
            isNeedVerificationCode = EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".hwid-getAuthCode .hwid-smsCode > span > span"),
                "获取验证码")(self.browser)
        except NoSuchElementException as noe:
            logger.error("检查是否需要获取验证码，页面元素不存在; except:{}", noe)
            pass
        except TimeoutException as te:
            logger.error("检查是否需要获取验证码超时; except:{} element:{}", te, self.browser.page_source)
            pass

        logger.info("检查是否需要获取验证码，检查结果：{}", "需要" if isNeedVerificationCode else "不需要")
        return isNeedVerificationCode

    def __check_is_need_jigsaw_verification(self):
        logger.info("检查是否需要拼图验证")
        isNeedJigsawVerification = False
        try:
            self.browser.find_element(By.CLASS_NAME, "yidun_modal__wrap")
            isNeedJigsawVerification = True
        except NoSuchElementException as noe:
            logger.error("检查是否需要拼图验证，页面元素不存在; except:{}", noe)
            pass
        except TimeoutException as te:
            logger.error("检查是否需要拼图验证; except:{} element:{}", te, self.browser.page_source)
            pass

        logger.info("检查是否需要拼图验证，检查结果：{}", "需要" if isNeedJigsawVerification else "不需要")
        return isNeedJigsawVerification

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
            WebDriverWait(self.browser, self.defaultTimeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "hwid-smsCode"))
            ).click()
            logger.success("短信验证码已发送")
        except TimeoutException:
            logger.warning("短信验证码已发送超时")
            pass

    def __trust_browser(self):
        logger.info("检查是否已经输入验证码")
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
            logger.success("账号登陆成功")
            try:
                self.nickname = WebDriverWait(self.browser, self.defaultTimeout).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "r-1pn2ns4"))
                ).text
            except TimeoutException:
                logger.warning("获取当前登陆账号昵称超时")
                pass
        else:
            logger.error("账号登陆失败，请重试")
            pass

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
                self.__set_end_waiting()
                if not self.isCountdown:
                    time.sleep(1)
            else:
                logger.info("当前可立即下单")
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
        else:
            pageType = 'unknown'
            pass
        logger.info("当前所在页面类型：{0} 地址：{1}".format(pageType, currentUrl))
        return pageType
