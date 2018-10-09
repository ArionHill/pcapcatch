#coding:utf-8

#记录模拟器各项值的类
class EmulatorClient:
    def __init__(self, avdName, port, avdNum, systemPath, userdataPath, ramdiskPath, sdcardPath, kernelPath):
        #镜像名
        self.avdName = avdName
        #端口
        self.port = port
        #模拟器名
        self.emuName = "emulator-%s" % str(self.port)
        #模拟器状态
        self.state = 0
        # 0 offline; 1 device; 2 busy; 3 dead
        #第几个启动的模拟器
        self.avdNum = avdNum
        #各种img的路径
        self.systemPath = systemPath
        self.userdataPath = userdataPath
        self.ramdiskPath = ramdiskPath
        self.sdcardPath = sdcardPath
        self.kernelPath = kernelPath