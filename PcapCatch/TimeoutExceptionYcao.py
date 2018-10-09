#encoding:utf-8
import os
import sys
from threading import Thread

ThreadStop = Thread._Thread__stop

def timelimited(timeout):
    def handleFunc(func):
        def handleArg(*args,**kwargs):
            class TimeLimitedThread(Thread):
                def __init__(self):
                    Thread.__init__(self)
                    self.error = ''

                def run(self):
                    try:
                        self.result = func(*args,**kwargs)
                    except Exception as e:
                        self.error = e

                def stop(self):
                    if self.isAlive():
                        print '执行时间截至，函数终止'
                        ThreadStop(self)
            t = TimeLimitedThread()
            t.start()
            t.join(timeout)
            if t.isAlive():
                t.stop()
        return handleArg
    return handleFunc
