# coding:utf-8
import EmulatorManager_simulate
import argparse
#执行模拟器cmd命令，输入为cmd命令，无输出
def emulatorCmd(args):
    if args.action == 'start':
        emulatorManager = EmulatorManager_simulate.EmulatorManager()
        emulatorManager.startEmusByTemplateName()
    else:
        print "cmd not exist"
#表明cmd命令不存在，无输入输出
def defaultCmd():
    print "cmd not exist"
#PcapCatch控制主函数，无输入输出
def main_simulate():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', type=str, help='输入template,img,emulator或apk')
    p.add_argument('action', type=str, help='输入要执行的动作')
    args = p.parse_args()
    # cf = ConfigParser.ConfigParser()
    cmdDict = {'emulator': emulatorCmd,
               'default': defaultCmd}
    cmdDict.setdefault('default')
    cmdDict.get(args.cmd)(args)

if __name__=="__main__":
    main_simulate()
