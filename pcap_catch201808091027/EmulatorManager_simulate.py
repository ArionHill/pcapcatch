#coding:utf-8
import EmulatorClient_simulate
import ControlThread_simulate
import ApkManagerThread_simulate
import os
import ConfigParser

#模拟器总管理
class EmulatorManager:
    
    #输入模板名和数量,启动一系列模拟器
    def startEmusByTemplateName(self):
        #启动apk管理线程
        apkManagerThread = ApkManagerThread_simulate.ApkManagerThread()
        apkManagerThread.setDaemon(True)
        apkManagerThread.start()

        cf = ConfigParser.ConfigParser()
        cf.read("configuration.ini")
        avdNames = cf.get("path", "AvdName")
        avdNameList = avdNames.split(',')
        for i in xrange(len(avdNameList)):
            #创建模拟器对象
            port = 5554 + i*2
            emuClient = EmulatorClient_simulate.EmulatorClient(avdNameList[i], port)
            #启动模拟器控制进程
            mThread = ControlThread_simulate.ControlThread(emuClient)
            mThread.start()