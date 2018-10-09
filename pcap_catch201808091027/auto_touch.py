#encoding=utf-8

import EmulatorManager_simulate
import sys
import argparse
import ConfigParser
import argparse
import subprocess
import os
import Apk_real
import signal
import ControlThread_real
import ApkManagerThread_real
import time

def main(flag):
    p = argparse.ArgumentParser()
    p.add_argument('cmd', type=str, help='输入template,img,emulator或apk')
    p.add_argument('action', type=str, help='输入要执行的动作')
    p.add_argument('type', type=str, help='输入要执行的方式，输入0或1')
    args = p.parse_args()
    if args.type == '1':
        if args.action == 'start':
            emulatorManager = EmulatorManager_simulate.EmulatorManager()
            emulatorManager.startEmusByTemplateName()
        else:
            print 'cmd do not exist'
    elif args.type == '0':
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
    else:
        print 'Error : 参数出错'
        print '1 对应 执行模拟器触发'
        print '0 对应 执行真机触发'
        return None


if __name__ == '__main__':
    main(sys.argv[1])
