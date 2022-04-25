# -*- coding: UTF-8 -*-


import uiautomator2 as u2


def get_all_text(app):
    return [_.text.strip() for _ in app.xpath('//android.widget.TextView').all() if _.text.strip()]


if __name__ == '__main__':
    app = u2.connect()
    app.app_start('com.instagram.android', stop=False)
    all_text = get_all_text(app)
    app.swipe(300, 1000, 300, 400, 0.08)
    print()
    print(all_text)
