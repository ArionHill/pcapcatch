# coding:utf-8
import os
import threading
import Queue
import time
import ConfigParser
import shutil
import hashlib


# apk管理线程
class ApkManagerThread(threading.Thread):
    cf = ConfigParser.ConfigParser()
    cf.read('./PcapCatch/configuration.ini')
    projectPath = cf.get("path", "ProjectPath")
    # 存放apk的路径
    apkStoreFolderAbs = os.path.join(projectPath, 'ApkStore/')
    # 等待分析的apk路径
    apkWaitFolderAbs = os.path.join(projectPath, "ApkWait/")
    # 正在分析的apk路径
    apkAnalyzingFolderAbs = os.path.join(projectPath, "ApkAnalyzing/")
    # apk分析log路径
    apkLogFolderAbs = os.path.join(projectPath, "ApkLog/")
    # 出bug次数大于3次的apk存放路径
    apkErrorFolderAbs = os.path.join(projectPath, "ApkError/")

    # 触发APP过程中产生的UI界面XML文件存放路径
    apkXmlFolderAbs = os.path.join(projectPath, "ApkXml/")

    # 待分析的apk队列
    apkQueue = None

    # #模拟器列表,用于存储正在分析的apk
    # analyzingList = None

    def __init__(self):
        threading.Thread.__init__(self)
        # 如果以上目录不存在则创建
        if not os.path.exists(ApkManagerThread.apkStoreFolderAbs):
            os.mkdir(ApkManagerThread.apkStoreFolderAbs)
        if not os.path.exists(ApkManagerThread.apkWaitFolderAbs):
            os.mkdir(ApkManagerThread.apkWaitFolderAbs)
        if not os.path.exists(ApkManagerThread.apkAnalyzingFolderAbs):
            os.mkdir(ApkManagerThread.apkAnalyzingFolderAbs)
        if not os.path.exists(ApkManagerThread.apkLogFolderAbs):
            os.mkdir(ApkManagerThread.apkLogFolderAbs)
        if not os.path.exists(ApkManagerThread.apkErrorFolderAbs):
            os.mkdir(ApkManagerThread.apkErrorFolderAbs)
        # 初始化待分析apk队列
        ApkManagerThread.apkQueue = Queue.Queue()
        # 将正在分析apk路径下的apk加入待分析队列,并移至待分析apk路径下(如果断电等意外情况,正在分析路径apk下可能会有残留apk)
        apkList = os.listdir(ApkManagerThread.apkAnalyzingFolderAbs)
        for apkName in apkList:
            shutil.move(ApkManagerThread.apkAnalyzingFolderAbs + apkName, ApkManagerThread.apkWaitFolderAbs)
        apkList = os.listdir(ApkManagerThread.apkWaitFolderAbs)
        # 将待分析apk路径下的apk加入待分析列表(如果断电等意外情况,这部分apk也会被忽略)
        for apkName in apkList:
            ApkManagerThread.apkQueue.put(apkName)

    def run(self):
        while True:
            # 获取存放apk路径下的所有apk
            apkList = os.listdir(ApkManagerThread.apkStoreFolderAbs)
            if apkList is not None:
                # 将新增apk加入待分析apk队列,并移至待分析apk路径下
                for apkName in apkList:
                    oldFilePath = ApkManagerThread.apkStoreFolderAbs + apkName
                    apkNameSHA256 = self.getSHA256(oldFilePath) + ".apk"
                    os.rename(oldFilePath, ApkManagerThread.apkStoreFolderAbs + apkNameSHA256)
                    ApkManagerThread.apkQueue.put(apkNameSHA256)
                    # 移至待分析apk路径下
                    targetPath = os.path.join(ApkManagerThread.apkWaitFolderAbs, apkNameSHA256)
                    if os.path.exists(targetPath):
                        os.remove(targetPath)
                    shutil.move(os.path.join(ApkManagerThread.apkStoreFolderAbs, apkNameSHA256),
                                ApkManagerThread.apkWaitFolderAbs)
            time.sleep(2)

    def getSHA256(self, filePath):
        m = hashlib.sha256()
        f = file(filePath, "rb")
        while True:
            d = f.read(1024 * 4)
            if not d:
                break
            m.update(d)
        f.close()
        return m.hexdigest()
