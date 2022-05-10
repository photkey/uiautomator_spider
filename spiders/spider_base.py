# -*- coding: UTF-8 -*-

import hashlib
import json
import logging
import os
import random
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime

import uiautomator2 as u2

logging.basicConfig(
    level=logging.INFO
)

home_dir = os.path.join(os.path.expanduser('~'), "uiautomator_spider")
if not os.path.exists(home_dir):
    os.makedirs(home_dir, exist_ok=True)

log = logging.getLogger()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
log.addHandler(console_handler)

filename = datetime.now().strftime('%Y-%m-%d')
file_handler = logging.FileHandler("{}/{}.log".format(home_dir, filename))
file_handler.setFormatter(formatter)
log.addHandler(file_handler)


class SpiderBase:
    name = 'base'
    keyword = None
    package_name = None
    activity = None
    prices = [0, 100, 500, 1000, 10000, 300000]
    page_limit = 40

    search_keyword_xpath = None
    search_keyword_confirm_xpath = None
    page_list_xpath = None

    product_choose_xpath = None
    start_price_xpath = None
    end_price_xpath = None
    product_choose_confirm_xpath = None
    watchers = [

    ]

    stop = True

    def __init__(self, keyword):
        self.keyword = keyword
        self._index = 1
        try:
            self.app = u2.connect()
        except:
            logging.info("Can't find any android device. exit")
            sys.exit(-1)

        self.restart()
        logging.info("Init uiautomator2 success，✈️️️")
        for watcher in self.watchers:
            self.app.watcher.when(watcher).click()

    def restart(self):
        self.app.app_start(self.package_name, stop=True, activity=self.activity)
        self.sleep(20)  # 等待 app 重启，取决于设备性能，设置久一点

    @staticmethod
    def _error(msg):
        log.error(msg)
        sys.exit()

    @staticmethod
    def uuid():
        return str(uuid.uuid4())

    def screen_debug(self):
        file_name = os.path.join(home_dir, self.uuid() + '.png')
        self.app.screenshot(file_name)
        return file_name

    @staticmethod
    def get_image_size(texts):
        for _ in texts:
            z = re.match("^[1-9]\d*\/[1-9]\d*$", _)
            if z:
                return int(z.group().split('/')[-1])
        return 1

    def get_all_text(self, xpath=None):
        if not xpath:
            xpath = '//android.widget.TextView'
        return [_.text.strip() for _ in self.xpath(xpath).all() if _.text.strip()]

    @staticmethod
    def get_product_id(product_name):
        return hashlib.md5(product_name.encode('utf-8')).hexdigest()

    @staticmethod
    def sleep(seconds):
        time.sleep(seconds)

    @staticmethod
    def sleep_random(start=None, end=None):
        if not start:
            start = 1
        if not end:
            end = 5
        time.sleep(random.randint(start, end))

    def do_search_keyword(self):
        logging.info("set text: {}".format(self.keyword))
        self.xpath(self.search_keyword_xpath).set_text(self.keyword)
        self.xpath(self.search_keyword_confirm_xpath).click()

    def click_sale(self, xpath):
        """
        销量排序
        :param xpath:
        :return:
        """
        logging.info("click sale desc ....")
        self.xpath(xpath).click()

    def range_price(self, start_price, end_price):
        # 展开 筛选 操作
        self.xpath(self.product_choose_xpath).click()

        # 输入 【start_price， end_price】
        self.xpath(self.start_price_xpath).set_text(str(start_price))
        self.sleep(3)
        self.xpath(self.end_price_xpath).set_text(str(end_price))

        # https://www.cnblogs.com/yoyoketang/p/10850591.html 隐藏键盘
        self.app.press(4)

        # 确认按钮
        self.xpath(self.product_choose_confirm_xpath).click()

    def pass_item(self, item):
        return False

    @staticmethod
    def run_system_cmd(cmd):
        out, error = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()
        if error:
            logging.error("run_system_cmd: {}, error: {}".format(cmd, error))
            return False, None
        logging.info("run_system_cmd: {}, success!".format(cmd))
        return True, out.decode('utf-8').strip()

    def return_pre(self, times=1):
        """
        返回上一页
        :return:
        """
        for i in range(times):
            self.swipe_right()

    def swipe_left(self):
        """
        左滑
        :return:
        """
        self.app.swipe(300, 600, 0, 600, 0.1)
        self.sleep(1)

    def swipe_down(self):
        """
        下滑
        :return:
        """
        self.app.swipe(300, 1000, 300, 400, 0.08)
        self.sleep(3)

    def swipe_right(self):
        """
        右滑
        :return:
        """
        self.app.swipe(0, 600, 300, 600, 0.1)
        self.sleep(1)

    def process_page_list(self, start_price, end_price):
        index = 0
        while index < self.page_limit:
            temp_lists = self.xpath(self.page_list_xpath).all()
            for item in temp_lists:
                if self.pass_item(item):
                    continue
                item.click()
                self.sleep(5)
                logging.info('start process new item.....')
                if start_price and end_price:
                    self._process_item("{}_{}".format(start_price, end_price))
                else:
                    self._process_item(None)
                self.return_pre()
            index += 1
            # 向下滑动
            self.app.swipe(300, 1000, 300, 400, 0.08)
            self.app.implicitly_wait(10)

    def base_dir(self, price_str, product_id):
        if price_str:
            result = home_dir + "/{}/{}/{}/{}".format(self.name, self.keyword, price_str, product_id)
        else:
            result = home_dir + "/{}/{}/{}".format(self.name, self.keyword, product_id)
        os.makedirs(result, exist_ok=True)
        return result

    def xpath(self, xpath):
        elm = self.app.xpath(xpath)
        self.sleep(1)
        return elm

    def xpaths(self, xpaths):
        for _xpath in xpaths:
            elm = self.xpath(_xpath)
            if elm.exists:
                return elm

    def xpath_text(self, xpath):
        elm = self.app.xpath(xpath)
        self.sleep(1)
        if elm.exists:
            return elm.text

    def xpath_text_by_swipe(self, xpath):
        elm = self.app.xpath(xpath)
        index = 0
        while not elm.exists:
            index = index + 1
            self.app.swipe(300, 800, 300, 400, 0.1)
            elm = self.app.xpath(xpath)
            if index > 10:
                return
        return elm.text

    @staticmethod
    def get_result_path(base_dir):
        return os.path.join(base_dir, 'result.json')

    def save_result(self, base_dir, data):
        data['_index'] = self._index
        with open(self.get_result_path(base_dir), 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        logging.info('🎉🎉🎉 。。。\n')
        self._index = self._index + 1

    def process(self):
        price_len = len(self.prices)
        for index in range(price_len - 1):
            start_price = self.prices[index]
            end_price = self.prices[index + 1] + 1
            self._process_keyword(start_price, end_price)
            self.restart()

    def _process_item(self, price_str):
        pass

    def _process_keyword(self, start_price, end_price):
        pass
