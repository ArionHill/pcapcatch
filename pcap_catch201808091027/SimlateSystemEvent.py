# coding:utf-8
import subprocess
import telnetlib
import time
import TimeoutException

#模拟开机广播
def simulateBootComplete(emuName, pkgName):
    print "simulate BootComplete"
    cmd = ['shell', 'am', 'broadcast', '-p', pkgName, '-a', 'android.intent.action.BOOT_COMPLETED']
    run_adb_cmd(emuName, cmd)

#模拟锁定屏幕
def simulateLockScreen(emuName, pkgName):
    print "simulate LockScreen"
    cmd = ['shell', 'am', 'broadcast', '-p', pkgName, '-a', 'android.intent.action.SCREEN_OFF']
    run_adb_cmd(emuName, cmd)

#模拟解锁屏幕
def simulateUnlockScreen(emuName, pkgName):
    print "simulate UnlockScreen"
    cmd = ['shell', 'am', 'broadcast', '-p', pkgName, '-a', 'android.intent.action.USER_PRESENT']
    run_adb_cmd(emuName, cmd)

#模拟收到短信
def simulateReceiveSMS(emuPort, phoneNumber, content):
    print "simulate Receive SMS"
    tn = telnetlib.Telnet('localhost' ,emuPort)
    tn.read_until("")
    cmd = "sms send " + phoneNumber + " " + content + "\n"
    tn.write(cmd)
    tn.write("exit\n")

#模拟发送短信
def simulateSendSMS(emuName, phoneNumber, content):
    print "simulate Send SMS"
    cmd = ['shell', 'am', 'start', '-a', 'android.intent.action.SENDTO', '-d', 'sms:' + phoneNumber, '--es', 'sms_body', content, '--ez', 'exit_on_sent', 'true']
    run_adb_cmd(emuName, cmd)
    time.sleep(10)
    cmd = ['shell', 'input', 'keyevent', '66']
    run_adb_cmd(emuName, cmd)

#模拟拨打电话
def simulateCall(emuName, phoneNumber):
    print "simulate Call"
    cmd = ['shell', 'am', 'start', '-a', 'android.intent.action.CALL', '-d', 'tel:' + phoneNumber]
    run_adb_cmd(emuName, cmd)
    time.sleep(10)
    cmd = ['shell', 'input', 'keyevent', 'KEYCODE_ENDCALL']
    run_adb_cmd(emuName, cmd)

#模拟收到电话
def simulatorAcceptCall(emuPort, phoneNumber):
    print "simulator Accept Call"
    tn = telnetlib.Telnet('localhost' ,emuPort)
    tn.read_until("")
    cmd = "gsm call " + phoneNumber + "\n"
    tn.write(cmd)
    time.sleep(10)
    cmd = "gsm accept " + phoneNumber + "\n"
    tn.write(cmd)
    time.sleep(10)
    cmd = "gsm cancel " + phoneNumber + "\n"
    tn.write(cmd)
    tn.write("exit\n")

#模拟位置改变
def simulatorLocation(emuPort, longitude, latitude):
    print "simulator Location"
    tn = telnetlib.Telnet('localhost' ,emuPort)
    tn.read_until("")
    cmd = "geo fix " + longitude + " " + latitude + "\n"
    tn.write(cmd)
    tn.write("exit\n")

# 运行各种adb命令
@TimeoutException.noExceptionTimelimited(60)
def run_adb_cmd(emuName, cmd):
    # 设定接受adb命令的模拟器名
    args = ['adb', '-s', emuName]
    args.extend(cmd)
    ret = None
    # 运行adb命令
    adbProcess = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = adbProcess.communicate()
    # 判断是否有设备无法找到的错误
    if "error: device not found" in ret[1]:
        raise Exception(ret[1].splitlines() + str(args))
    else:
        return ret

# emuName = "emulator-5554"
# pkgName = "com.example.phoneinfotest"
# emuPort = "5554"
# phoneNumber = "12332132131"
# content = "hello"
# longitude = "34.43"
# latitude = "98.12"
# simulateBootComplete(emuName, pkgName)
# simulateLockScreen(emuName, pkgName)
# simulateUnlockScreen(emuName, pkgName)
# simulateReceiveSMS(emuPort, phoneNumber, content)
# simulateSendSMS(emuName, phoneNumber, content)
# simulateCall(emuName, phoneNumber)
# simulatorAcceptCall(emuPort, phoneNumber)
# simulatorLocation(emuPort, longitude, latitude)