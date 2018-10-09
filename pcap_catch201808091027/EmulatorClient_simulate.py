#coding:utf-8

#记录模拟器各项值的类
class EmulatorClient:
    def __init__(self, avdName, port):
        #镜像名
        self.avdName = avdName
        #模拟器名
        self.emuName = "emulator-%s" % str(port)
        self.port = str(port)