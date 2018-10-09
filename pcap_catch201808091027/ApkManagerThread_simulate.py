#coding:utf-8
import os
import threading
import Queue
import time
import ConfigParser
import shutil
import hashlib

#apk管理线程类
class ApkManagerThread(threading.Thread):
    #存放apk的路径
    apkStoreFolderRel = 'ApkStore/'
    #等待分析的apk路径
    apkWaitFolderRel = "ApkWait/"
    #正在分析的apk路径
    apkAnalyzingFolderRel = "ApkAnalyzing/"
    #apk分析log路径
    apkLogFolderRel = "ApkLog/"
    #出bug次数大于3次的apk存放路径
    apkErrorFolderRel = "ApkError/"

    #待分析的apk队列
    apkQueue = None
    
    def __init__(self):
        threading.Thread.__init__(self)
        # 删除android模拟器的临时文件，防止硬盘被临时文件填满
        cf = ConfigParser.ConfigParser()
        cf.read('configuration.ini')
        tmpPath = cf.get("path", "TmpPath")
        if os.path.exists(tmpPath) and len(os.listdir(tmpPath)) != 0:
            shutil.rmtree(tmpPath)
        #如果以上目录不存在则创建
        if not os.path.exists(ApkManagerThread.apkStoreFolderRel):
            os.mkdir(ApkManagerThread.apkStoreFolderRel)
        if not os.path.exists(ApkManagerThread.apkWaitFolderRel):
            os.mkdir(ApkManagerThread.apkWaitFolderRel)
        if not os.path.exists(ApkManagerThread.apkAnalyzingFolderRel):
            os.mkdir(ApkManagerThread.apkAnalyzingFolderRel)
        if not os.path.exists(ApkManagerThread.apkLogFolderRel):
            os.mkdir(ApkManagerThread.apkLogFolderRel)
        if not os.path.exists(ApkManagerThread.apkErrorFolderRel):
            os.mkdir(ApkManagerThread.apkErrorFolderRel)
        #初始化待分析apk队列
        ApkManagerThread.apkQueue = Queue.Queue()
        #将正在分析apk路径下的apk加入待分析队列,并移至待分析apk路径下(如果断电等意外情况,正在分析路径apk下可能会有残留apk)
        apkList = os.listdir(ApkManagerThread.apkAnalyzingFolderRel)
        for apkName in apkList:
            shutil.move(ApkManagerThread.apkAnalyzingFolderRel + apkName, ApkManagerThread.apkWaitFolderRel)
        apkList = os.listdir(ApkManagerThread.apkWaitFolderRel)
        #将待分析apk路径下的apk加入待分析列表(如果断电等意外情况,这部分apk也会被忽略)
        for apkName in apkList:
            ApkManagerThread.apkQueue.put(apkName)
        
    def run(self):                          #对apk进行管理，输入为其apk类本身，输出无
        
        while True:
            #获取存放apk路径下的所有apk
            apkList =os.listdir(ApkManagerThread.apkStoreFolderRel)
            if apkList is not None:
                #将新增apk加入待分析apk队列,并移至待分析apk路径下
                for apkName in apkList:
                    oldFilePath = ApkManagerThread.apkStoreFolderRel + apkName
                    apkNameMD5 = self.getMD5(oldFilePath) + ".apk"
                    os.rename(oldFilePath, ApkManagerThread.apkStoreFolderRel + apkNameMD5)
                    try:
                        if not os.path.exists(os.path.join(ApkManagerThread.apkWaitFolderRel, apkNameMD5)):
                            shutil.move(ApkManagerThread.apkStoreFolderRel + apkNameMD5, ApkManagerThread.apkWaitFolderRel)
                            ApkManagerThread.apkQueue.put(apkNameMD5)
                    except:
                        print 'crash ,repeated'

    def getMD5(self, filePath):             #APK的获得MD5码，输入为apk类本身和APK文件路径，输出为APK文件的MD5码        
        m = hashlib.md5()   
        f = file(filePath, "rb")
        while True:
            d = f.read(1024*4)
            if not d:
                break
            m.update(d)
        f.close()
        return m.hexdigest()
