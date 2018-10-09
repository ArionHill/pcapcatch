# coding:utf-8
import subprocess
import time
import shutil
import ApkManagerThread_simulate

# 包含apk的各项属性的类
class Apk:
    def __init__(self):
        self.path = None
        self.mainAct = None
        self.pkg = None
        self.startStr = None
        self.name = None

def getApkInfo(apkPath, log):                       #获取APK，输入为APK存放路径和模拟器log日志，输出为一个包含apk各项属性的类
    package = ''
    mainActivity = ''
    #先用aapt dump badging分析apk
    print apkPath
    cmd = ['aapt', 'dump', 'badging', apkPath]
    aaptProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = aaptProcess.communicate()
    if res:
        for line in res[0].splitlines():
            #得到包名
            if 'package: name' in line:
                package = line.split("'")[1]
            if 'application-label:' in line:
                apkName = line.split("'")[1]
            #得到mainActivity
            if 'launchable-activity: name' in line:
                mainActivity = line.split("'")[1]
                break
    #如果上述方法得不到包名和mainActivity,则用aapt dump xmltree分析apk
    if (mainActivity == '') or (package == ''):
        # 传入apk的路径,得到该apk的AndroidManifest.xml
        cmd = ['aapt', 'dump', 'xmltree', apkPath, 'AndroidManifest.xml']
        aaptProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = aaptProcess.communicate()
        if res:
            for line in res[0].splitlines():
                # 如果"A: package="在该行内,则可得到包名
                if 'A: package=' in line:
                    package = line.split("\"")[1]
                # 如果"android.intent.action.MAIN"在该行内,则跳出循环
                if 'android.intent.action.MAIN' in line:
                    if "." not in mainActivity:
                        mainActivity = "." + mainActivity
                    break
                # 如果"A: android:name"在该行内,则记录主activity名
                if 'A: android:name' in line:
                    tempList = line.split("\"")
                    if len(tempList) > 1:
                        mainActivity = tempList[1]

    if (mainActivity == '') or (package == ''):
        shutil.move(apkPath, ApkManagerThread_simulate.ApkManagerThread.apkErrorFolderRel)
        log.error("[%s]%s" % (time.strftime('%Y-%m-%d=%H:%M:%S', time.localtime(time.time())), "apk dont have mainActivity or package"))
        print "apk dont have mainActivity or package"
        return None
    else:
        apk = Apk()
        apk.name = apkName
        apk.path = apkPath
        apk.mainAct = mainActivity
        apk.pkg = package
        apk.startStr = '%s/%s' % (package, mainActivity)
        return apk
