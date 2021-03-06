# -*- coding: UTF-8 -*-


import uiautomator2 as u2


def get_all_text(app, xpath=None):
    if not xpath:
        xpath = '//android.widget.TextView'
    return [_.text.strip() for _ in app.xpath(xpath).all() if _.text.strip()]


if __name__ == '__main__':
    app = u2.connect()
    # app.app_start('com.xingin.xhs', stop=False)

    app.screenshot().save('1.png')

    with open('2.png', 'wb') as f:
        f.write(app.screenshot(format="raw"))
    exit()

    all_text = get_all_text(app)
    # app.swipe(300, 1000, 300, 400, 0.08)
    # print()
    # print(all_text)
    s = app.dump_hierarchy()
    print(s)

    with open('demo.xml', 'w') as f:
        f.write(s)
    app.screenshot().save('demo.png')
