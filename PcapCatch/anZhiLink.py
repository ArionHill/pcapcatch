#coding=utf-8
import os
import time
import sys
import json
from bs4 import BeautifulSoup
from mysql_manage import MysqlManage

import requests

reload(sys)
sys.setdefaultencoding('utf-8')


def get_apk(id):
    url = "http://www.anzhi.com/dl_app.php?s=" + id
    resp = requests.get(url)
    return resp.content


def get_content(url, content='content'):

    k = 0
    while True:
        try:
            if content == 'text':
                html = requests.get(url).text
                return html
            elif content == 'content':
                content = requests.get(url).content
                return content
        except Exception as e:
            print e
            if k < 10:
                time.sleep(2**k)
            else:
                return None


def save_apk(url, apkname, apk):
    if not os.path.exists(url):
        os.makedirs(url)
    with open(os.path.join(url, apkname) + '.apk', 'wb') as fp:
        fp.write(apk)
    # stream = os.popen('aapt dump badging ' + 'test.apk')
    # with open('apkinfo.txt', 'a') as fapk:
    #     fapk.write(apkname)
    #     for i in stream.readlines():
    #         if 'package: name=' in i:
    #             packgae_name = i.split("name='")[1].split("'")[0]
    #             # os.rename('test.apk', packgae_name + '.apk')
    #             fapk.write("-*-*-" + packgae_name)
    #             print packgae_name
    #             if 'versionName' in i:
    #                 versionName = i.split("versionName='")[1].split("'")[0]
    #                 fapk.write("-*-*-" + versionName)
    #                 print versionName
    #         elif 'application-label-zh-CN:' in i:
    #             fapk.write("-*-*-" + i.strip())
    #             print i.strip()
    #         elif 'application-label:' in i:
    #             fapk.write("-*-*-" + i.strip())
    #             print i.strip()
    #     fapk.write('\n')
        # path = os.path.join(DEST_DIR, filename)

def get_cat(url):
    k = 0
    html = get_content(url, 'text')
    if html is None:
        return
    soup = BeautifulSoup(html, 'html.parser')
    cats = soup.select('a')
    # print cats
    cat_set = set()
    for i in cats:
        try:
            if 'tsort' in i['href']:
                cat_set.add(i['href'])
        except KeyError:
            continue
    # cat_list = [i['href'] for i in cats if 'tsort' in i['href']]
    # return set(cat_list)
    return cat_set
    # new_cat = [f"http://www.anzhi.com/widgettsort_{i[i.find('_') + 1:i.find('_h')]}.html" for i in cat_list]
    # return new_cat

def getCat():
    url = 'http://www.anzhi.com/widgetcatetag_1.html'
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    cats = soup.select('a')
    cat_set = set()
    for i in cats:
        try:
            if 'tsort' in i['href']:
                cat_set.add(i['href'])
        except KeyError:
            continue
    # cat_list = [i['href'] for i in cats if 'tsort' in i['href']]
    # # print cat_list, 'a'
    # cat_set = set(cat_list)
    # newCat = ['http://www.anzhi.com' + i for i in cat_list]
    return cat_set


def get_apk_info(apkherf, downloadurl):
    url = 'http://www.anzhi.com' + apkherf
    while True:
        try:
            html = requests.get(url).text
            break
        except Exception as e:
            print e
            if k < 10:
                time.sleep(2**k)
            else:
                return
    soup = BeautifulSoup(html, 'html.parser')
    # links = soup.select('a.recommend_name,center')
    # cats = soup.select('a')
    divs = soup.select('div')
    name = ''
    version = ''
    category = ''
    downloads = ''
    updatetime = ''
    size = ''
    system = ''
    price = ''
    composer = ''
    language = ''
    intro = ''

    for i in divs:
        # print i
        try:
            # print i['class']
            if i['class'][0] == 'detail_line':
                # print i, 'detail_line'
                spans = i.select('span')
                for j in spans:
                    if j['class'][0] == 'app_detail_version':
                        version = j.string
                        # print version, 'version'
                        name = i.select('h3')
                        for j in name:
                            name = j.string
            if i['class'][0] == 'app_detail_infor':
                infor = i.select('p')
                # print infor
                # print i
                # print i.string
                for j in infor:
                    intro += str(j).replace('"', r'\"')
                    # print type(j)
                intro = str(j).replace('"', r'\"')
                # exit(0)
        except KeyError:
            pass
            # print 'keyerror'

    uls = soup.select('ul')
    for i in uls:
       # print i
        try:
            # print i['id']
            if i['id'] == 'detail_line_ul':
                # print i
                lis = i.select('li')
                for j in lis:
                    if '分类' in j.string:
                        category = j.string
                    elif '下载' in j.string:
                        downloads = j.string
                    elif '时间' in j.string:
                        updatetime = j.string
                    elif '大小' in j.string:
                        size = j.string
                    elif '系统' in j.string:
                        system = j.string
                    elif '资费' in j.string:
                        price = j.string
                    elif '作者' in j.string:
                        composer = j.string
                    elif '软件语言' in j.string:
                        language = j.string
        except Exception:
            pass
            # print 'keyerror'
    db = MysqlManage('anzhiapkInfo', 'apkInformation201808091102')
    db.connect()
    column = '(`name`, `version`, `category`, `downloads`, `time`,'\
        '`size`,`system`, `price`, `composer`, `language`,'\
        '`downloadurl`, `introduction`)'\
        'VALUES('\
        '"%s", "%s", "%s", "%s", "%s",'\
        '"%s", "%s", "%s", "%s", "%s",'\
        '"%s", "%s")'
    values = (name, version, category, downloads, updatetime,
            size, system, price, composer, language,
            downloadurl, intro)
    # print intro, 'intro'
    try:
        db.insert(column, values)
    except Exception as e:
        with open("dberrlog.txt", "a") as fp:
            fp.write(name + '**' + version + '**' + category + '**' + downloads  + '**' + updatetime
            + '**' + size + '**' + system + '**' + price + '**' + composer + '**' + language
            + '**' + downloadurl + '**' + intro)
            fp.write('\n=====================================================================\n')
        print e
    finally:
        return values




def get_apk_url(url, apklink_get, name_url_dic, downloaded):
    k = 0
    while True:
        try:
            html = requests.get(url).text
            break
        except Exception as e:
            print e
            if k < 10:
                time.sleep(2**k)
            else:
                return
    soup = BeautifulSoup(html, 'html.parser')
    # links = soup.select('a.recommend_name,center')
    # cats = soup.select('a')
    li = soup.select('li')
    id = ''
    apkn = ''
    dones = set()
    dones.add('')
    for i in li:
        spanclass = i.select('span')
        # print spanclass, 'span'
        for apkname in spanclass:
            if apkname['class'][0] == 'app_name':
                apkn = apkname.select('a')[0]['title'] # apk name
                apkherf = apkname.select('a')[0]['href']
                # print repr(apkn)
                # print apkn.encode('utf8') in name_url_dic
                if apkn.encode('utf8') in name_url_dic:
                    downloadurl = name_url_dic[apkn.encode('utf8')]
                    if downloadurl not in downloaded:
                        downloaded.add(downloadurl)
                        values = get_apk_info(apkherf, downloadurl)
                        if values is not None:
                            content = get_content(downloadurl)
                            category = values[2]
                            path = '/home/cy/Data/中期考核相关代码数据/combined_system201808091407/PcapCatch/ApkStore/'
                            save_apk(path, apkn, content)
                            time.sleep(5)
                            with open('downloaded.txt', 'a') as fp:
                                fp.write(apkn)
                                fp.write(': ')
                                fp.write(downloadurl)
                                fp.write('\n')
                break

def read_kv(fl):
    name_url = dict()
    with open(fl, 'a+') as fp:
        for ln in fp:
            ln = ln.strip()
            name = ln.split(': ')[0]
            name_url[name] = ln.split(': ')[1]
    return name_url

def start():
    '''
    函数作用:爬虫启动主程序
    输入:无
    输出:无
    '''
    name_url_dic = read_kv('apkline.txt')
    apklink_get = set()
    with open("apkline.txt") as fa:
        for line in fa:
            line = line.strip()
            link = line.split(': ')[1]
            apklink_get.add(link)
    cats = getCat()
    catsd = set()
    with open('log.txt', 'a+') as fg:
        downloaded = set()
        for line in fg:
            line = line.strip()
            downloaded.add(line)
        while len(cats) > 0:
            print len(cats), 'pages'
            newlinks = set()
            for i in cats:
                print len(cats)
                if i not in catsd and i not in downloaded:
                    fg.write(i + '\n')
                    catsd.add(i)
                    print 'http://www.anzhi.com' + i
                    downloaded_kv = read_kv('downloaded.txt')
                    downloaded = set()
                    for k, v in downloaded_kv.items():
                        downloaded.add(v)
                    print len(downloaded), 'of', len(name_url_dic), 'done'
                    get_apk_url('http://www.anzhi.com' + i, apklink_get, name_url_dic, downloaded)
                    new_page = get_cat('http://www.anzhi.com' + i)
                    print new_page
                    newlinks = newlinks | new_page
            cats = newlinks - catsd
            print 'cats size: ', len(cats), '; newlinks size: ', len(newlinks), '; catsd size: ', len(catsd)

if __name__ == '__main__':
    name_url_dic = read_kv('apkline.txt')
    apklink_get = set()
    with open("apkline.txt") as fa:
        for line in fa:
            line = line.strip()
            link = line.split(': ')[1]
            apklink_get.add(link)
    cats = getCat()
    catsd = set()
    with open('log.txt', 'a+') as fg:
        downloaded = set()
        for line in fg:
            line = line.strip()
            downloaded.add(line)
        while len(cats) > 0:
            print len(cats), 'pages'
            newlinks = set()
            for i in cats:
                print len(cats)
                if i not in catsd and i not in downloaded:
                    fg.write(i + '\n')
                    catsd.add(i)
                    print 'http://www.anzhi.com' + i
                    downloaded_kv = read_kv('downloaded.txt')
                    downloaded = set()
                    for k, v in downloaded_kv.items():
                        downloaded.add(v)
                    print len(downloaded), 'of', len(name_url_dic), 'done'
                    get_apk_url('http://www.anzhi.com' + i, apklink_get, name_url_dic, downloaded)
                    new_page = get_cat('http://www.anzhi.com' + i)
                    print new_page
                    newlinks = newlinks | new_page
            cats = newlinks - catsd
            print 'cats size: ', len(cats), '; newlinks size: ', len(newlinks), '; catsd size: ', len(catsd)
