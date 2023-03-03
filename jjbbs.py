# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import json
import time
import requests
import re
import pandas as pd
from collections import Counter

headers = {
    'user-agent': ""
}

cookies = {
    'cookies': ""
}


def progress_bar(i, scale, start_time):
    c = (i / scale) * 100
    dur = time.perf_counter() - start_time
    print("\r{:^3.0f}% {:.2f}s".format(c, dur), end="")


def get_jj_bbs(post_id, cookies=None, headers=None, interval=1.0):
    url = "https://bbs.jjwxc.net/showmsg.php?board=3&id=%s&page=%s" % (post_id, "0")

    s = requests.Session()
    requests.adapters.DEFAULT_RETRIES = 5
    s.trust_env = False
    s.keep_alive = False

    req = s.get(url, cookies=cookies, headers=headers)
    text = req.content.decode('GB2312', 'ignore')
    soup = BeautifulSoup(text, features='lxml')
    title = ''.join(soup.find("title").text.split())
    try:
        page_top = soup.find(name='div', attrs={'id': 'pager_top'}).text
        page_count_text = re.findall(r'\d+(?:\.\d+)?', page_top)
        page_count = int(page_count_text[0])
        print('该帖子一共：' + str(page_count) + '页')  # 帖子大于1页时
    except:
        page_count = 1
        print('该帖子一共：' + str(page_count) + '页')  # 帖子只有1页
    start_time = time.perf_counter()
    reply_list = []
    reply_no = 0
    try:
        for i in range(page_count):
            url = "https://bbs.jjwxc.net/showmsg.php?board=3&id=%s&page=%s" % (post_id, str(i))
            req = requests.get(url, cookies=cookies, headers=headers)
            text = req.content.decode('GB2312', 'ignore')

            if page_count - 1:
                progress_bar(i, scale=page_count - 1, start_time=start_time)

            soup = BeautifulSoup(text, features='lxml')
            reply_table = soup.find(name='table', attrs={'id': "replies"})
            if not reply_table:
                print("no reply table", url)
                continue
            trs = reply_table.find_all('tr')
            current_no = 0
            while trs:
                reply_no += 1
                current_no += 1
                reply = trs[0:7]
                trs = trs[8:]

                authorname = reply[5].find(name="td", attrs={'class': "authorname"})
                body = reply[4].find(name='div', attrs={'class': "replybodyinner"})

                reply_dict = {
                    "no": reply_no,
                    "current_no": current_no,
                    "time": reply[3].get("id"),
                    "body": body.string if body else None,
                    "nickname": authorname.contents[3],
                    "nickid": authorname.find(attrs={"color": "#999999"}).string,
                    "loc": authorname.find(attrs={"style": "font-size: 12px"}).string.replace("来自", ""),
                }

                reply_list.append(reply_dict)


    except ConnectionError:
        print("ConnectionError:", url)

    id_list = [x.get("nickid") for x in reply_list]
    unique_id_counter = Counter(id_list)

    print("去重id", len(unique_id_counter))

    with open(title + ".json", "w", encoding="utf-8") as f:
        f.write(json.dumps(reply_list, ensure_ascii=False))

    df = pd.json_normalize(reply_list)
    df.to_excel(title + ".xlsx", index=False)


get_jj_bbs(post_id="", cookies=cookies, headers=headers, interval=0.5)
