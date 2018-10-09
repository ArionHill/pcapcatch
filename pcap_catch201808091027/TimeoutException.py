#coding:utf-8
from threading import Thread

#获取Thread的私有函数
ThreadStop = Thread._Thread__stop

class TimeoutException(Exception):
    pass

#有报错的限时执行
#修饰带参函数的带参装饰器
def timelimited(timeout):
    #传入被修饰的函数
    def handleFunc(function):
        #传入被修饰函数的参数
        def handleArgs(*args,**kwargs):
            #将被修饰的方法构造在一个线程中
            class TimeLimitedThread(Thread):
                #初始化线程
                def __init__(self,_error= None,):
                    Thread.__init__(self)
                    self._error =  _error
                #线程实体,运行被修饰的函数
                def run(self):
                    try:
                        self.result = function(*args,**kwargs)
                    except Exception as ex:
                        self._error = ex
                #停止线程方法
                def _stop(self):
                    if self.isAlive():
                        ThreadStop(self)
            #启动线程
            t = TimeLimitedThread()
            t.start()
            #设置阻塞主进程的时间
            t.join(timeout)

            if t.isAlive():
                t._stop()
                raise TimeoutException('timeout for %s' % function.__name__)
            #没报错则返回运行结果
            elif hasattr(t, "result"):
                return t.result

        return handleArgs
    return handleFunc

#无报错的限时执行
def noExceptionTimelimited(timeout):
    def handleFunc(function):
        def handleArgs(*args,**kwargs):

            class TimeLimitedThread(Thread):
                def __init__(self,_error= None,):
                    Thread.__init__(self)
                    self._error =  _error
                def run(self):
                    try:
                        self.result = function(*args,**kwargs)
                    except Exception as ex:
                        self._error = ex
                def _stop(self):
                    if self.isAlive():
                        ThreadStop(self)

            t = TimeLimitedThread()
            t.start()
            #设置阻塞主进程的时间
            t.join(timeout)

            if t.isAlive():
                t._stop()
                #raise TimeoutException('timeout for %s' % function.__name__)
            #没报错则返回运行结果
            elif hasattr(t, "result"):
                return t.result

        return handleArgs
    return handleFunc
