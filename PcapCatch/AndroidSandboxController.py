# coding:utf-8
import ConfigParser
import argparse
import subprocess
import os
import Apk_real
import signal
import ControlThread_real
import ApkManagerThread_real
import time

def emulatorCmd(args):
    #cmd = ['adb', 'start-server']
    #subprocess.Popen(cmd).wait()
    if args.action == 'start':
        cmd = ['ps', '-ax']
        psProcess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = psProcess.communicate()
        psList = res[0].strip().split("\n")
        pNum = 0
        for ps in psList:
            if 'AndroidSandboxController.py emulator start' in ps:
                pNum = pNum + 1
                if pNum > 1:
                    print 'emulator is already running!'
                    return
        apkManagerThread = ApkManagerThread_real.ApkManagerThread()
        apkManagerThread.setDaemon(True)
        apkManagerThread.start()
        time.sleep(2)
        mThread = ControlThread_real.ControlThread()
        mThread.start()
    else:
        print "cmd not exist"


def defaultCmd():
    print "cmd not exist"

def main_real():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', type=str, help='输入template,img,emulator或apk')
    p.add_argument('action', type=str, help='输入要执行的动作')
    args = p.parse_args()
    cmdDict = {'emulator': emulatorCmd,
               'default': defaultCmd}
    cmdDict.setdefault('default')
    cmdDict.get(args.cmd)(args)

if __name__=="__main__":
    main_real()