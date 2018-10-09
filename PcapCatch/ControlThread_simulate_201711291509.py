#coding:utf-8
import threading
import ApkManagerThread_simulate
import subprocess
import telnetlib
import Apk_simulate
import logging
import os
import TimeoutException
import ConfigParser
import shutil
import time
import signal
from PIL import Image
import traceback

#模拟器控制线程类
class ControlThread(threading.Thread):
    #模拟器log存放目录
    logFolder = "Log/"

    def __init__(self, tEmuClient):
        threading.Thread.__init__(self)
        #是否需要启动模拟器
        self.needStart = True
        #模拟器客户端对象
        self.emuClient = tEmuClient
        #模拟器进程对象
        self.emuProcess = None
        #正在分析的apk对象
        self.apk = None
        self.apkName = None
        #是否安装成功
        self.isInstallSuccess = False
        #记录一个app出现bug的数量(异常计数)
        self.bugNum = 0
        #正在分析的apk存放log路径
        self.apkLogFolder = None
        #记录开始分析的时间
        self.startTime = None
        self.cf = ConfigParser.ConfigParser()
        self.cf.read('configuration.ini')
        #如果不存在log目录,则创建
        if not os.path.exists(ControlThread.logFolder):
            os.mkdir(ControlThread.logFolder)
        #初始化记录log
        self.__createLog(self.emuClient.avdName, ControlThread.logFolder+self.emuClient.avdName+".log")
        # 一趟分析的次数
        self.analyzeTimes = 0

    #初始化模拟器log，输入为ControlThread类本身和log日志名称以及log文件地址
    def __createLog(self, logName, logFile):                                
        self.log = logging.getLogger(logName)
        self.log.setLevel(logging.INFO)
        formatStr = "[lineNum=%(lineno)d %(levelname)s]%(message)s"
        formatter = logging.Formatter(formatStr)
        self.logHandler = logging.StreamHandler(open(logFile, 'a'))
        self.logHandler.setFormatter(formatter)
        self.log.addHandler(self.logHandler)

    #线程实体
    def run(self):
        try:
            self.runMethod()
        except Exception as ex:
            print ex
    #线程执行的控制函数，输入为ControlThread类本身，无输出
    def runMethod(self):
        print "%s monitor thread is working" % self.emuClient.avdName
        # while self.hasApk():
        while True:
            try:
                if self.needStart:
                    self.needStart = False
                    #启动模拟器
                    self.startEmu()
                    #等待模拟器启动完毕
                    self.waitForBootCompleted()
                    #解锁屏幕
                    self.unlockScreen()

                while self.isInstallSuccess == False:
                    while self.apk == None:
                        # if ApkManagerThread.ApkManagerThread.apkQueue.empty():
                        #     self.telnetShutDown()
                        #     return
                        #获得要分析的apk路径
                        apkPath = self.getApk()
                        #创建apk对象
                        self.apk = Apk_simulate.getApkInfo(apkPath, self.log)
                        # #将apk管理线程中的模拟器列表对应位置为None
                        # ApkManagerThread.ApkManagerThread.analyzingList[self.emuClient.avdNum] = None
                    #安装apk
                    self.installApk()
                #分析apk的准备工作
                self.preparAnalyzeAPK()
                #关闭飞行模式
                self.closeAirPlaneMode()
                #打开apk
                self.openApk()
                #分析apk
                self.analyzeApk()
                #关闭apk
                self.closeApk()
                #卸载apk
                self.uninstallApk()
                #分析完毕
                self.finishAnalyzeApk()

            except Exception as ex:
                print "run exception: %s" % ex
                self.log.error("[%s]%s" % (self.getFormatTime(), ex))
                self.log.error("%s" % traceback.format_exc())
                #如果出现意外则强制关闭模拟器
                self.forceShutDown()
                #重置是否安装成功为false,apk为none
                self.isInstallSuccess = False
                #如果不是因为启动太慢导致的异常
                if not "waitForBootCompleted" in str(ex):
                    self.bugNum = self.bugNum + 1
                #如果出bug次数已经大于1次,就将此apk移至apkerror路径夏
                if self.bugNum >= 2:
                    # errorApkSrcPath = ApkManagerThread.ApkManagerThread.apkAnalyzingFolderRel + self.apkName
                    errorApkSrcPath = self.apk.path
                    errorApkDesPath = ApkManagerThread_simulate.ApkManagerThread.apkErrorFolderRel
                    shutil.move(errorApkSrcPath, errorApkDesPath)
                    self.apk = None
                    self.bugNum = 0
                self.needStart = True

    #判断是否还有待分析的APK，输入为ControlThread类本身，输出为表示是否有待分析APK的boolean值
    def hasApk(self):
        if self.bugNum == 0:
            if not ApkManagerThread_simulate.ApkManagerThread.apkQueue.empty():
                return True
            else:
                #如果待分析队列为空，则有可能是第一次运行还未载入完全，等待120秒
                time.sleep(2)
                if ApkManagerThread_simulate.ApkManagerThread.apkQueue.empty():
                    return False
                else:
                    return True
        else:
            return True

    #启动模拟器，输入为ControlThread类本身，无输出
    def startEmu(self):
        #产生启动的参数
        cmd = ['emulator', '-avd', self.emuClient.avdName]
        cmd.extend(['-port', str(self.emuClient.port)])
        #设定模拟器不使用快照,擦除用户数据
        cmd.extend(['-wipe-data'])
        #记录测试开始时间
        self.startTime = time.time()
        #启动模拟器
        print cmd
        self.emuProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print "%s starts" % self.emuClient.avdName
        self.log.info("[%s]starts" % self.getFormatTime())

    #等待启动模拟器,设置最大启动时间为6000秒,超过则报错，输入为ControlThread类本身，无输出
    @TimeoutException.timelimited(600)
    def waitForBootCompleted(self):
        try:
            #等待模拟器进入device状态
            self.run_adb_cmd(["wait-for-device"])
            self.log.info("is device")
            print "is device"
            #每隔两秒,判断是否开机完成
            while True:
                print " "
                if self.isBootCompleted():
                    break
                time.sleep(1)
            self.log.info("BootCompleted")
            print "BootCompleted"
            self.isPsNotIncrease()
            self.log.info("ps same")
            print "ps same"
            #等待一段时间,防止模拟器刚开机而不稳定
            time.sleep(10)
            print "%s booted completed" % self.emuClient.avdName
            self.log.info("[%s]booted completed" % self.getFormatTime())
        except Exception as ex:
            raise Exception, 'waitForBootCompleted error'

    #判断是否开机完成，输入为ControlThread类本身，输出为表示是否开机完成的boolean值
    def isBootCompleted(self):
        #获得sys.boot_completed参数,如果为1则说明开机完成
        ret = self.run_adb_cmd(['shell', 'getprop', 'sys.boot_completed'])
        if ret and ret[0].strip() == '1':
            return True
        return False

    #等待进程数不再增加(每隔一秒获得一次进程数,连续7次相同则停止)，输入为ControlThread类本身，无输出
    def isPsNotIncrease(self):
        sameNum = 0
        psNum = 0
        isAllBlack = True
        while isAllBlack:
            while sameNum < 5:
                cmd = ['shell', 'ps']
                res = self.run_adb_cmd(cmd)
                lines = res[0].strip().split("\n")
                if psNum == len(lines):
                    sameNum = sameNum + 1
                else:
                    sameNum = 0
                    psNum = len(lines)
                time.sleep(1)
            #进程数相同5次后，判断屏幕是否仍为全黑，如果全黑，说明未启动完成，重新判断进程数
            isAllBlack = self.isPicAllBlack(self.logFolder + self.emuClient.avdName + "cap.png")

    #判断屏幕是否全黑，输入为ControlThread类本身,输出为表示屏幕是否全黑的boolean值
    def isPicAllBlack(self, picPath):
        for i in xrange(2):
            #截图并保存到本地
            self.captureScreen(picPath)
            im = Image.open(picPath, "r")
            width = im.size[0]
            height = im.size[1]
            flag = True
            #循环检查每个像素
            for h in range(0, height):
                for w in range(0, width):
                    pixel = im.getpixel((w, h))
                    if pixel != (0,0,0):
                        flag = False
                        break
                if flag == False:
                    break
            #删除截图
            os.remove(picPath)
            #如果截图全黑，则返回
            if flag == True:
                return flag
            #如果不全黑，则隔5秒再测一次
            else:
                time.sleep(5)

    #截图并保存到本地，输入为ControlThread类本身，无输出
    def captureScreen(self, picPath):
        androidScreenCapPicPath = '/data/local/tmp/' + os.path.basename(picPath)
        cmd = ['shell', 'screencap', '-p', androidScreenCapPicPath]
        self.run_adb_cmd(cmd)
        cmd = ['pull', androidScreenCapPicPath, picPath]
        self.run_adb_cmd(cmd)
        cmd = ['shell', 'rm', androidScreenCapPicPath]
        self.run_adb_cmd(cmd)

    #解锁屏幕，输入为ControlThread类本身，无输出
    def unlockScreen(self):
        cmd = ['shell', 'input', 'keyevent', '82']
        self.run_adb_cmd(cmd)
        print "unlock screen"

    #获得apk路径，输入为ControlThread类本身，输出为APK的路径
    def getApk(self):
        # 从apk管理线程的apk队列中获得要分析的apk路径
        apkName = ""
        apkPath = ""
        # 如果要从对列中取出的apk不存在了，就取下一个
        while not os.path.exists(apkPath):
            apkName = (ApkManagerThread_simulate.ApkManagerThread.apkQueue).get()
            apkPath = os.path.join(ApkManagerThread_simulate.ApkManagerThread.apkWaitFolderRel, apkName)
        # 将apk移至正在分析apk路径下
        self.apk = Apk_simulate.getApkInfo(apkPath, self.log)
        shutil.move(apkPath, ApkManagerThread_simulate.ApkManagerThread.apkAnalyzingFolderRel)
        print "%s get apk: %s" % (self.emuClient.avdName, apkName)
        self.apkLogFolder = os.path.join(ApkManagerThread_simulate.ApkManagerThread.apkLogFolderRel,self.apk.name)
        # return ApkManagerThread.ApkManagerThread.apkAnalyzingFolderRel + self.apkName
        return os.path.join(ApkManagerThread_simulate.ApkManagerThread.apkAnalyzingFolderRel + apkName)

    #安装apk，输入为ControlThread类本身，无输出
    @TimeoutException.timelimited(600)
    def installApk(self):
        cmd = ['adb', '-s', self.emuClient.emuName, 'install', self.apk.path]
        installProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret = installProcess.communicate()
        ret = ret[0].splitlines()[1]
        if "FAILED" in ret:
            self.isInstallSuccess = False
            shutil.move(self.apk.path, ApkManagerThread_simulate.ApkManagerThread.apkErrorFolderRel)
            self.apk = None
            self.log.error("[%s]%s" % (self.getFormatTime(), ret))
            print "install faile"
        else:
            self.isInstallSuccess = True
            # print "install apk: " + self.apk.path
            self.log.info("install apk")
    #打开tcpdump进程，输入为ControlThread类本身，无输出
    def preparAnalyzeAPK(self):
        #记录pcap文件,忽略host是10.0.2.2的数据包
        cmd = ['adb', '-s', self.emuClient.emuName, 'shell', 'tcpdump', '-w', '/data/local/tmp/netdata.pcap', '-s', str(0), '-vvv', 'not', 'host', '10.0.2.2']
        self.pcapProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #关闭飞行模式，打开数据开关，输入为ControlThread类本身，无输出
    def closeAirPlaneMode(self):
        cmd = ['shell', 'settings', 'put', 'global', 'airplane_mode_on', '0']
        self.run_adb_cmd(cmd)
        cmd = ['shell', 'am', 'broadcast', '-a', 'android.intent.action.AIRPLANE_MODE', '--ez', 'state', 'false']
        self.run_adb_cmd(cmd)
        cmd = ['shell', 'svc', 'data', 'enable']
        self.run_adb_cmd(cmd)

    #打开apk，输入为ControlThread类本身，无输出
    def openApk(self):
        cmd = ['shell', 'am', 'start', '-n', self.apk.startStr]
        self.run_adb_cmd(cmd)
        self.log.info("open apk")
        time.sleep(5)

    #分析apk，输入为ControlThread类本身，无输出
    def analyzeApk(self):
        print '------ start ------'
        self.log.info("start analyze apk")
        # self.apkLogFolder = ApkManagerThread_simulate.ApkManagerThread.apkLogFolderRel + os.path.basename(self.apk.path) + "/"
        self.apkLogFolder = os.path.join(ApkManagerThread_simulate.ApkManagerThread.apkLogFolderRel, self.apk.name)
        if not os.path.exists(self.apkLogFolder):
            os.mkdir(self.apkLogFolder)
        # 模拟用户交互
        self.monkey()
        print '------- end -------'
    
    @TimeoutException.timelimited(700)
    #对monkey命令调参，输入为ControlThread类本身，无输出
    def monkey(self):
        time.sleep(5)
        cmd = ['shell', 'svc', 'wifi', 'enable']
        self.run_adb_cmd(cmd)
        time.sleep(3)
        cmd = ['shell', 'monkey', '-p', self.apk.pkg, '-s', '600', '--pct-touch', '20', '2000', '--pct-motion', '20','2000', '--pct-trackball', '10', '2000', '--pct-appswitch', '50', '2000', '--ignore-crashes', '--ignore-security-exceptions', '--kill-process-after-error' '-v', '2000']
        self.run_adb_cmd(cmd)


    #关闭apk，输入为ControlThread类本身，无输出
    def closeApk(self):
        cmd = ['shell', 'am', 'force-stop', self.apk.pkg]
        self.run_adb_cmd(cmd)
#         print "close Apk"
        self.log.info("close apk")

    #卸载apk，输入为ControlThread类本身，无输出
    def uninstallApk(self):
        cmd = ['uninstall', self.apk.pkg]
        self.run_adb_cmd(cmd)
#         print "uninstall Apk"
        self.log.info("uninstall apk")

    #完成分析，输入为ControlThread类本身，无输出
    def finishAnalyzeApk(self):
        # 结束logcat记录进程和pcap捕捉进程
        try:
            os.kill(self.pcapProcess.pid, signal.SIGKILL)
        except OSError as ex:
            pass
        #将pcap保存进APKLog的对应路径下
        cmd = ['aapt', 'dump', 'badging', self.apk.path]
        ret = None
        adbProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret = adbProcess.communicate()
        retlist = ret[0].splitlines()
        for line in ret[0].splitlines():
            if 'application: label' in line:
                self.apkName = line.split("'")[1]
        pcapPath = os.path.join(self.apkLogFolder, self.apk.name + '_' + time.strftime('%Y%m%d%H%M', time.localtime(time.time())) + '.pcap')
        cmd = ['pull', '/data/local/tmp/netdata.pcap', pcapPath]
        #cmd = ['pull', '/data/local/tmp/netdata.pcap', self.apkLogFolder]
        self.run_adb_cmd(cmd)
        #删除分析完的apk
        #os.remove(self.apk.path)
        apkPath = os.path.join(self.apkLogFolder, self.apk.name + '.apk')
        shutil.move(self.apk.path, apkPath)
        #成功分析完成,将bugNum置为0
        self.bugNum = 0
        self.isInstallSuccess = False
        print "%s analyze finish %s" % (self.emuClient.avdName, self.apkName)
        self.log.info("[%s]analyze finish %s[cost %d]" % (self.getFormatTime(), os.path.basename(self.apk.path), time.time()-self.startTime))
        self.apk = None

        self.analyzeTimes = self.analyzeTimes + 1
        if self.analyzeTimes >= 20:
            self.needStart = True
            self.telnetShutDown()
            self.analyzeTimes = 0

    #使用telnet关闭，输入为ControlThread类本身，无输出
    def telnetShutDown(self):
        #使用python的telnet方法与模拟器通信
        tn = telnetlib.Telnet('localhost' ,self.emuClient.port)
        #等待telnet完毕
        tn.read_until("")
        #输入kill命令,关闭模拟器
        tn.write("kill\n")
        time.sleep(10)
        #如果关闭失败,就使用强制关闭
        if subprocess.Popen.poll(self.emuProcess) != 0:
            self.forceShutDown()
        else:
            print self.emuClient.avdName + " telnet shutdown"
            self.log.info("[%s]telnet shutdown" % self.getFormatTime())

    #强制关闭，输入为ControlThread类本身，无输出
    def forceShutDown(self):
        #记录模拟器进程的pid
        pid = self.emuProcess.pid
        #防止模拟器进程已经关闭,发生异常
        try:
            #强制关闭模拟器进程
            os.kill(pid, signal.SIGKILL)
        except OSError as ex:
            pass;
        #置模拟器进程为None
        self.emuProcess = None
        print self.emuClient.avdName + " force shutdown"
        self.log.info("[%s]force shutdown" % self.getFormatTime())
        time.sleep(10)

    #运行各种adb命令，输入为ControlThread类本身，输出为存有shell输出信息的列表
    @TimeoutException.timelimited(60)
    def run_adb_cmd(self, cmd):
        #设定接受adb命令的模拟器名
        args = ['adb', '-s', self.emuClient.emuName]
        args.extend(cmd)
        ret = None
        #运行adb命令
        adbProcess = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ret = adbProcess.communicate()
        #判断是否有设备无法找到的错误
        if "error: device not found" in ret[1]:
            raise Exception(ret[1].splitlines()[0] + str(args))
        else:
            return ret

    #获得当前时间，输入为ControlThread类本身，输出为表示当前时间的字符串
    def getFormatTime(self):
        cur_time = time.time()
        return time.strftime('%Y-%m-%d=%H:%M:%S', time.localtime(cur_time))
