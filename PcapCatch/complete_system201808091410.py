#encoding:utf-8
import os
import sys
import anZhiLink
import threading
import time

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
  reload(sys)
  sys.setdefaultencoding(default_encoding)

def spider():
    '''
    函数作用:启动爬虫程序
    输入:无
    输出:线程实体
    '''
    thread_spider = threading.Thread(target=anZhiLink.start,args=())
    thread_spider.start()
    return thread_spider

def autoTouch(mode):
    if mode == 'real':
        thread_autoTouch = threading.Thread(target=os.system,args=('python auto_touch.py emulator start 0',))
        thread_autoTouch.start()
    elif mode == 'simulate':
        thread_autoTouch = threading.Thread(target=os.system,args=('python auto_touch.py emulator start 1',))
        thread_autoTouch.start()
    else:
        return None
    return thread_autoTouch

if __name__ == '__main__':
    thread_autoTouch = autoTouch('simulate')
    time.sleep(60)
    thread_spider = spider()
    # if thread_spider != None:
    #     i = 0
    #     while(i<20):
    #         print 'Has been ' + str(i) + ' s'
    #         time.sleep(1)
    #         i += 1
    #     thread_spider._Thread__stop()
    #     print 'Thread stop'
