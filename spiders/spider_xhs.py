# -*- coding: UTF-8 -*-
import os

from spiders.spider_base import SpiderBase, log as logging

"""
穿戴甲  美甲 美甲片
"""


class SpiderXhs(SpiderBase):
    name = "xhs"
    package_name = 'com.xingin.xhs'

    page_list_xpath = '//*[@resource-id="com.xingin.xhs:id/csn"]/android.widget.FrameLayout//android.view.View'

    # 三种排序方式：
    sort_items = {
        '综合': '//*[@resource-id="com.xingin.xhs:id/csn"]/android.view.ViewGroup[1]/android.widget.TextView[1]',
        '最热': '//*[@resource-id="com.xingin.xhs:id/csn"]/android.view.ViewGroup[1]/android.widget.TextView[2]',
        '最新': '//*[@resource-id="com.xingin.xhs:id/csn"]/android.view.ViewGroup[1]/android.widget.TextView[3]',
    }

    item_limit = 80

    def process(self):
        for sort_key, sort_xpath in self.sort_items.items():
            self._index = 1
            logging.info("start process: {} - {}".format(self.keyword, sort_key))
            self._process_keyword(sort_key, sort_xpath)
            self.restart()

    def _process_keyword(self, sort_key, sort_xpath):
        # search btn
        self.xpath('//*[@resource-id="com.xingin.xhs:id/ebt"]').click()
        # 输入 keyword
        self.xpath('//*[@resource-id="com.xingin.xhs:id/ct1"]').set_text(self.keyword)
        # 触发搜索
        self.xpath('//*[@resource-id="com.xingin.xhs:id/ct4"]').click()

        self.xpath(sort_xpath).click()

        logging.info("click 图文。。。")

        # 筛选图文
        tu_wen = self.xpath('//*[@resource-id="com.xingin.xhs:id/csn"]/android.view.ViewGroup[1]/android.widget.LinearLayout[2]/android.widget.TextView[1]')
        if tu_wen.exists:
            tu_wen.click()
        else:
            exit()

        self.process_page_list(sort_key, None)

    def process_page_list(self, sort_key, _):
        while True:
            current_count = self.get_current_count(sort_key)
            logging.info(f"current_count: {current_count}")
            if current_count > self.item_limit:
                break
            temp_lists = self.xpath(self.page_list_xpath).all()
            pre_len = len(temp_lists)
            for item in temp_lists:
                if self.pass_item(item):
                    continue
                logging.info('start process new item.....index: {}'.format(self._index))

                item.click()
                self._process_item(sort_key)

                while True:
                    current_len = len(self.app.xpath(self.page_list_xpath).all())
                    if current_len == 0:  # 只要没回到列表页，就再次返回 pre_len 会变
                        logging.info(f"current {current_len} , pre: {pre_len}, try return pre ...")
                        self.return_pre()
                        self.sleep(5)
                    else:
                        break
            self.swipe_down()
            self.sleep(10)  # 控制速率

    def get_auth_info(self):
        logging.info("开始获取个人信息。。。start")
        # 点击头像进入个人主页
        avatar_layout = self.xpath('//*[@resource-id="com.xingin.xhs:id/avatarLayout"]')
        if avatar_layout.exists:
            avatar_layout.click()
        else:
            return {}
        cyq = self.get_all_text('//*[@resource-id="com.xingin.xhs:id/cyq"]/android.view.ViewGroup[3]//*')
        extra_info = []
        if cyq:
            extra_info = cyq[:6]  # 关注/粉丝/点赞
        data = {
            'nickname': self.xpath_text('//*[@resource-id="com.xingin.xhs:id/dqs"]'),
            '_id': self.xpath_text('//*[@resource-id="com.xingin.xhs:id/dqt"]'),
            'desc': self.xpath_text('//*[@resource-id="com.xingin.xhs:id/fih"]'),
            'tag_info': self.get_all_text('//*[@resource-id="com.xingin.xhs:id/cyh"]//*'),
            'extra_info': extra_info
        }
        self.return_pre()
        logging.info("开始获取个人信息。。。end")
        return data

    def _process_item(self, price_str):
        logging.info("start process_item ...")
        self.sleep_random()

        buk = self.xpath('//*[@resource-id="com.xingin.xhs:id/buk"]')
        if not buk.exists or not buk.text.startswith('说点什么'):
            logging.error("可能是 视频内容 skip")
            self.sleep_random(5, 10)  # 控制速率
            return

        title = self.xpath_text('//*[@resource-id="com.xingin.xhs:id/dcg"]')
        if not title:
            logging.error("获取 title 失败, skip {}".format(self.screen_debug()))
            return

        like_count = self.xpath_text('//*[@resource-id="com.xingin.xhs:id/dbt"]')
        collect_count = self.xpath_text('//*[@resource-id="com.xingin.xhs:id/dam"]')
        comment_count = self.xpath_text('//*[@resource-id="com.xingin.xhs:id/das"]')

        product_id = self.get_product_id(title)
        base_dir = self.base_dir(price_str, product_id)
        logging.info("result: {}".format(base_dir))
        self.app.screenshot(os.path.join(base_dir, 'main.png'))

        if os.path.exists(self.get_result_path(base_dir)):
            logging.info("cache... skip\n")
            return

        image_size = 1
        image_xpath = self.xpath('//*[@resource-id="com.xingin.xhs:id/noteContentLayout"]/android.widget.LinearLayout[1]/android.widget.ImageView')
        if image_xpath.exists:
            image_size = len(image_xpath.all())

        for index in range(image_size):
            image_elm = self.xpath('//*[@resource-id="com.xingin.xhs:id/noteContentLayout"]/android.widget.FrameLayout[1]')
            image_name = os.path.join(base_dir, '{}.png'.format(index))
            if image_elm.exists:
                image_elm.screenshot().save(image_name)
            if index != image_size - 1:
                self.swipe_left()

        logging.info("image save end ...")

        # 不能放在前面，需要 swipe 获取
        content = self.xpath_text_by_swipe('//*[@resource-id="com.xingin.xhs:id/brq"]')
        if not content:
            logging.error("获取 content 失败, skip {}".format(self.screen_debug()))
            return
        last_update = self.xpath_text_by_swipe('//*[@resource-id="com.xingin.xhs:id/dc2"]')
        auth_info = self.get_auth_info()
        data = {
            'title': title,
            'content': content,
            'last_update': last_update,
            'comment_count': comment_count,
            'like_count': like_count,
            'collect_count': collect_count,
            'auth_info': auth_info
        }
        self.save_result(base_dir, data)
