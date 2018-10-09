# coding:utf-8
import threading
import ApkManagerThread_real
import subprocess
import telnetlib
import Apk_real
import logging
import os
import TimeoutException
import ConfigParser
import shutil
import time
import signal
from PIL import Image
import SimlateSystemEvent
import traceback
import json
from ftplib import FTP
import UITreeYcao





# 模拟器控制线程
class ControlThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.cf = ConfigParser.ConfigParser()
        self.cf.read('./PcapCatch/configuration.ini')
        self.projectPath = self.cf.get("path", "ProjectPath")
        self.ftpAddress = self.cf.get("ftp","Address")
        self.ftpPort = self.cf.get("ftp", "Port")
        self.ftpUserName = self.cf.get("ftp", "UserName")
        self.ftpPassWord = self.cf.get("ftp", "PassWord")
        # 正在分析的apk对象
        self.apk = None
        # 是否安装成功
        self.isInstallSuccess = False
        # 记录一个app出现bug的数量(异常计数)
        self.bugNum = 0
        # 正在分析的apk存放log路径
        self.apkLogFolder = None
        # 记录开始分析的时间
        self.startTime = None
        # 初始化记录log
        self.__createLog('zhenji', "haha.log")
        # init FTP
        #self.createFTPConn()
        # 记录触发次数，超过三次，表明该APP无法成功触发
        self.touchCount = 0

    def createFTPConn(self):
        self.ftp=FTP()
        self.ftp.set_debuglevel(0)#打开调试级别2，显示详细信息;0为关闭调试信息
        self.ftp.connect(self.ftpAddress,self.ftpPort)#连接
        self.ftp.login(self.ftpUserName,self.ftpPassWord)#登录，如果匿名登录则用空串代替即可

    # 初始化模拟器log
    def __createLog(self, logName, logFile):
        self.log = logging.getLogger(logName)
        self.log.setLevel(logging.INFO)
        formatStr = "[lineNum=%(lineno)d %(levelname)s]%(message)s"
        formatter = logging.Formatter(formatStr)
        self.logHandler = logging.StreamHandler(open(logFile, 'a'))
        self.logHandler.setFormatter(formatter)
        self.log.addHandler(self.logHandler)

    # 线程实体
    def run(self):
        try:
            self.runMethod()
        except Exception as ex:
            print ex

    def runMethod(self):
        print "monitor thread is working"
        # 执行su操作
        # self.su()
        while self.hasApk():
            try:
                # 解锁屏幕
                # self.unlockScreen()
                while self.isInstallSuccess == False:
                    while self.apk == None:
                        if ApkManagerThread_real.ApkManagerThread.apkQueue.empty():
                            print "there is no apk, analyse finish"
                            #self.ftp.quit()
                            return
                        # 获得要分析的apk路径
                        apkPath = self.getApk()
                        # 创建apk对象
                        self.apk = Apk_real.getApkInfo(apkPath, self.log)
                    # 安装apk
                    self.installApk()
                # 记录模拟器当前状态为busy
                self.setBusy(1)
                # 分析apk的准备工作
                self.preparAnalyzeAPK()
                # 打开apk
                self.openApk()
                # 分析apk
                self.myMonkeyTest()
                # 关闭apk
                self.closeApk()
                # 卸载apk
                self.uninstallApk()
                # 分析完毕
                self.finishAnalyzeApk()
                # 取消模拟器当前busy状态
                self.setBusy(0)












            except Exception as ex:
                print "run exception: %s" % ex
                self.log.error("[%s]%s" % (self.getFormatTime(), ex))
                self.log.error("%s" % traceback.format_exc())
                # 重置是否安装成功为false,apk为none
                self.isInstallSuccess = False
                # if 'timeout for myMonkeyTest' in str(ex):
                #     self.bugNum += 1
                # if "timeout for run_adb_cmd" in str(ex):
                #     self.bugNum += 1
                self.bugNum += 1
                try:
                    self.killApk(self.apk)
                    self.uninstallApk()
                    os.kill(self.adbProcess.pid, signal.SIGKILL)
                    os.kill(self.pcapProcess.pid, signal.SIGKILL)
                except Exception as ex:
                    self.log.error("inner error : %s" % ex)
                    self.log.error("%s" % traceback.format_exc())
                # 如果出bug次数已经大于1次,就将此apk移至apkerror路径夏
                if self.bugNum >= 2:
                    # errorApkSrcPath = ApkManagerThread.ApkManagerThread.apkAnalyzingFolderRel + self.apkName
                    errorApkSrcPath = self.apk.path
                    errorApkDesPath = ApkManagerThread_real.ApkManagerThread.apkErrorFolderAbs
                    shutil.move(errorApkSrcPath, errorApkDesPath)
                    self.apk = None
                    self.bugNum = 0

    # 判断是否还有待分析的APK
    def hasApk(self):
        if self.bugNum == 0:
            if len(os.listdir(ApkManagerThread_real.ApkManagerThread.apkStoreFolderAbs)) + len(
                    os.listdir(ApkManagerThread_real.ApkManagerThread.apkWaitFolderAbs)) == 0:
                print 'monitor thread ends'
                #self.ftp.quit()
                return False
            else:
                return True
                # if not ApkManagerThread.ApkManagerThread.apkQueue.empty():
                #     return True
                # else:
                #     #如果待分析队列为空，则有可能是第一次运行还未载入完全，等待2秒
                #     time.sleep(2)
                #     if ApkManagerThread.ApkManagerThread.apkQueue.empty():
                #         print '%s monitor thread ends' % self.emuClient.avdName
                #         return False
                #     else:
                #         return True
        else:
            return True

    # 截图并保存到本地
    # def captureScreen(self, picPath):
    #     androidScreenCapPicPath = os.path.join('/data/local/tmp/', os.path.basename(picPath))
    #     cmd = ['shell', 'screencap', '-p', androidScreenCapPicPath]
    #     self.run_adb_cmd(cmd)
    #     cmd = ['pull', androidScreenCapPicPath, picPath]
    #     self.run_adb_cmd(cmd)
    #     cmd = ['shell', 'rm', androidScreenCapPicPath]



















    # 执行su
    def su(self):
        cmd = ['shell', 'mount', '-o', 'remount', '-o', 'rw', '/system']
        self.run_adb_cmd(cmd)
        cmd = ['shell', 'chmod', '4755', '/system/xbin/su']
        self.run_adb_cmd(cmd)
        cmd = ['shell', 'chmod', '4777', '/data/local/tmp']
        self.run_adb_cmd(cmd)
        cmd = ['shell', 'chmod', '4777', '/storage/sdcard']
        self.run_adb_cmd(cmd)

    # 解锁屏幕
    # def unlockScreen(self):
    #     cmd = ['shell', 'input', 'keyevent', '82']
    #     self.run_adb_cmd(cmd)

    # 获得apk路径
    def getApk(self):
        # 记录测试开始时间
        self.startTime = time.time()
        # 从apk管理线程的apk队列中获得要分析的apk路径
        apkName = ""
        apkPath = ""
        # 如果要从对列中取出的apk不存在了(apk文件被删除了)，就取下一个
        while not os.path.exists(apkPath):
            apkName = (ApkManagerThread_real.ApkManagerThread.apkQueue).get()
            apkPath = os.path.join(ApkManagerThread_real.ApkManagerThread.apkWaitFolderAbs, apkName)
        self.apk = Apk_real.getApkInfo(apkPath, self.log)
        # 将apk移至正在分析apk路径下
        shutil.move(apkPath, ApkManagerThread_real.ApkManagerThread.apkAnalyzingFolderAbs)
        # 创建apk分析结果目录
        self.apkLogFolder = os.path.join(ApkManagerThread_real.ApkManagerThread.apkLogFolderAbs,self.apk.name)
        if not os.path.exists(self.apkLogFolder):
            os.mkdir(self.apkLogFolder)

        print "get apk: %s" % (apkName)
        self.log.info("[%s]get apk: %s" % (self.getFormatTime(), apkName))
        # return ApkManagerThread.ApkManagerThread.apkAnalyzingFolderRel + self.apkName
        return os.path.join(ApkManagerThread_real.ApkManagerThread.apkAnalyzingFolderAbs, apkName)

    # 设置模拟器状态为busy
    def setBusy(self, flag):
        cmd = ['shell', 'setprop', 'rw.is.busy', str(flag)]
        self.run_adb_cmd(cmd)

    # 安装apk
    def installApk(self):
        cmd = ['install', self.apk.path]
        ret = self.run_adb_cmd(cmd)
        retLines = ret[0].splitlines()
        if len(retLines) > 1:
            ret = retLines[1]
            if "FAILED" in ret:
                # 如果安装一次失败了，则再装一次试试
                ret = self.run_adb_cmd(cmd)
                retLines = ret[0].splitlines()
                if len(retLines) > 1:
                    ret = retLines[1]
                    if "FAILED" in ret:
                        self.isInstallSuccess = False
                    else:
                        self.isInstallSuccess = True
                else:
                    self.isInstallSuccess = False
            else:
                self.isInstallSuccess = True
        else:
            self.isInstallSuccess = False

        if self.isInstallSuccess == False:
            shutil.move(self.apk.path, ApkManagerThread_real.ApkManagerThread.apkErrorFolderAbs)
            self.apk = None
            self.log.error("[%s]%s" % (self.getFormatTime(), ret))
            print "install failed"
        elif self.isInstallSuccess == True:
            # print "install apk: " + self.apk.path
            self.log.info("install apk")

    def preparAnalyzeAPK(self):
        # 记录pcap文件,忽略host是10.0.2.2的数据包
        # cmd = ['adb', 'root']
        # p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p.communicate()
        cmd = ['adb', 'shell', '/data/local/tmp/tcpdump', '-i', 'wlan0','-w', '/sdcard/netdata.pcap', '-s',str(0), '-vvv', 'not', 'host', '10.0.2.2']
        self.pcapProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 打开apk
    def openApk(self):
        cmd = ['shell', 'am', 'start', '-n', self.apk.startStr]
        self.run_adb_cmd(cmd)
        self.log.info("open apk")
        time.sleep(5)

    # 分析apk
    # def analyzeApk(self):
    #     print '------ start ------'
    #     self.log.info("start analyze apk")
    #     # 模拟用户交互
    #     self.myMonkeyTest()
    #     print '------- end -------'

    @TimeoutException.timelimited(300)
    def myMonkeyTest(self):
        print 'start my monkey test'
        count = 0
        ###关闭飞行模式
        cmd = ['shell', 'settings', 'put', 'global', 'airplane_mode_on', '0']
        self.run_adb_cmd(cmd)
        time.sleep(3)
        ###打开wifi开关
        cmd = ['shell', 'svc', 'wifi', 'enable']
        self.run_adb_cmd(cmd)
        time.sleep(3)
        ###新的固定出发逻辑:滑动、点击和文本输入
        ###首先，从右至左，滑动屏幕8次，每次间隔一秒

        for i in range(0,5):
            cmd = ['shell', 'input', 'tap', '1100', '1350']
            self.run_adb_cmd(cmd)
            time.sleep(1)
        for i in range(0, 5):
            cmd = ['shell', 'input', 'swipe', '1000', '1300', '100', '1300']
            self.run_adb_cmd(cmd)
        # x_list = ['100', '300', '500', '700', '900', '1000', '1200']
        # y_list = ['300', '500', '700', '900', '1100', '1300', '1500', '1700','1900']

        # UITreeYcao.mains('',self.apk.startStr,ApkManagerThread_real.ApkManagerThread.apkXmlFolderAbs)
        # for rt,dirs,files in os.walk(ApkManagerThread_real.ApkManagerThread.apkXmlFolderAbs):
        #     if len(files) < 5:
        #         raise Exception("Touch invalidly")
        for i in range(0,2):
            cmd = ['shell', 'monkey', '-p', self.apk.pkg, '-s', '600', '--pct-touch', '20', '2000', '--pct-motion', '20', '2000', '--pct-trackball', '10', '2000', '--pct-appswitch', '50', '2000','--ignore-crashes', '--ignore-security-exceptions', '--kill-process-after-error' '-v', '2000']
            self.run_adb_cmd(cmd)

    # 关闭apk
    def closeApk(self):
        cmd = ['shell', 'am', 'force-stop', self.apk.pkg]
        self.run_adb_cmd(cmd)
        #         print "close Apk"
        self.log.info("close apk")

    # 卸载apk
    def uninstallApk(self):
        cmd = ['uninstall', self.apk.pkg]
        self.run_adb_cmd(cmd)
        #         print "uninstall Apk"
        self.log.info("uninstall apk")

    # 完成分析
    def finishAnalyzeApk(self):
        # 结束logcat记录进程和pcap捕捉进程
        try:
            os.kill(self.pcapProcess.pid, signal.SIGKILL)
        except OSError as ex:
            pass
        # 将pcap保存进APKLog的对应路径下
        pcapPath = os.path.join(self.apkLogFolder, self.apk.name + '_' + time.strftime('%Y%m%d%H%M', time.localtime(time.time())) + '.pcap')
        print pcapPath
        cmd = ['pull', '/sdcard/netdata.pcap', pcapPath]
        self.run_adb_cmd(cmd)
        # 将本次触发得到的Pcap文件删除
        cmd = ['shell','rm','-rf','/sdcard/netdata.pcap']
        self.run_adb_cmd(cmd)
        # 运行pcap解析程序
        # self.parsePcap()
        # save APK
        apkPath = os.path.join(self.apkLogFolder, self.apk.name + '.apk')
        print apkPath
        shutil.move(self.apk.path, apkPath)
        # 成功分析完成,将bugNum置为0
        self.bugNum = 0
        self.isInstallSuccess = False
        # send to ftp
        #self.sendToFTP(apkPath, pcapPath)
        print "analyze finish %s" % (os.path.basename(self.apk.path))
        self.log.info("[%s]analyze finish %s[cost %d]" % (
            self.getFormatTime(), os.path.basename(self.apk.path), time.time() - self.startTime))
        self.apk = None

    def parsePcap(self):
        print 'parse pcap'

    def sendToFTP(self, apkPath, pcapPath):
        bufsize = 1024#设置缓冲块大小
        file_handler = open(pcapPath,'rb')#以读模式在本地打开文件
        self.ftp.storbinary('STOR %s' % os.path.basename(pcapPath), file_handler, bufsize)#上传文件
        file_handler.close()
        print 'send to ftp'

    # 运行各种adb命令
    @TimeoutException.timelimited(120)
    def run_adb_cmd(self, cmd):
        # 设定接受adb命令的模拟器名
        args = ['adb']
        args.extend(cmd)
        ret = None
        # 运行adb命令
        self.adbProcess = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret = self.adbProcess.communicate()
        # 判断是否有设备无法找到的错误
        if "error: device not found" in ret[1]:
            raise Exception(ret[1].splitlines()[0] + str(args))
        else:
            return ret

    # 强制关闭超时的adb命令
    def kill_adb_cmd(self):
        try:
            os.kill(self.adbProcess.pid, signal.SIGKILL)
        except Exception as ex:
            self.log.error("%s" % ex)
            # pass

    # 获得当前时间
    def getFormatTime(self):
        cur_time = time.time()
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cur_time))

    # 获取apk的uid
    def getUid(self):
        cmd = ['shell', 'dumpsys', 'package', self.apk.pkg]
        ret = self.run_adb_cmd(cmd)
        lines = ret[0].splitlines()
        uid = 0
        for line in lines:
            if 'userId' in line:
                uid = (line.split("=")[1]).split(" ")[0]
                break
        # 如果没有获取到uid,则报错
        if uid == 0:
            raise Exception("APK dont have uid")
        return uid

    def killApk(self, apk):
        cmd = ['shell', 'ps']
        ret = self.run_adb_cmd(cmd)
        pss = ret[0].split('\r\n')
        pid = 0
        for ps in pss:
            if apk.pkg in ps:
                pid = ps.split()[1]
        if pid != 0:
            cmd = ['shell', 'kill', pid]
            self.run_adb_cmd(cmd)
