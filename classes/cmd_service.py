#!/usr/bin/env python3
# requires at least python 3.4

import time as Time
import io as IO
import os as OS
import sys as System
from threading import Lock
import subprocess as SubProcess
import pty as Pty

class CmdServiceException(Exception):
        Reasons = ['The connection is not established']
        ReasonCodes = [0x0]
        Reason = 0x0
        NO_CONECTION = 0x0
        def __init__(self, ErrorCode):
            self.Reason = ErrorCode
        def __str__(self):
            if self.Reason not in self.ReasonCodes:
                return repr('Unkown error.')
            else:
                return repr(self.Reasons[self.Reason])


class CmdService(object):
    #lock parameter lisk
    __ParameterLock = False
    __Timeout = 0
    __Parameter = []
    FORK_NO_PROCESS = 0x0#not completly the truth
    FORK_NORMAL_PROCESS = 0x1
    FORK_PTY_PROCESS = 0x2
    __PipenameCounter = 0
    __Lock = ''
    __Lock2 = ''

    def __init__(self, Configuration):
        if 'timeout' in Configuration['cmd']:
            self.__Timeout = Configuration['cmd']['timeout']
        self.__Lock = Lock()
        self.__Lock2 = Lock()
        self.addParameter(Configuration['cmd']['name'], '')

    def addParameter(self, Key, Value):
        self.__Lock.acquire()
        if True ==  self.__ParameterLock:
             self.__Lock.release()
             return

        self.__Lock.release()
        if Key.strip():
            self.__Lock.acquire()
            if Key.endswith('='):
                self.__Parameter.append(Key + Value)
            else:
                self.__Parameter.append((Key + " " + Value).strip())
            self.__Lock.release()

    def __normalChildProcess(self, InputData):
        Process = ''
        Stdout = ''
        Stderr = ''

        Parameter = self.__Parameter
        Parameter.append(InputData)
        Process = SubProcess.Popen(Parameter, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
        Stdout, Stderr = Process.communicate()
        if 0<self.__Timeout:
            Process.wait(self.__Timeout)
        else:
            Process.wait()

        return [Stdout, Stderr]

    def __forkedChildProcess(self, Pipe, InputData):
        MyId = str(OS.getpid())
        MyId += "\n"
        Output = []
        self.writeToPipe(Pipe, MyId)
        Output = self.__noChildProcess(InputData)
        self.writeToPipe(Pipe, "[stdout]:\n\n\r\r\n" + Output[0].decode('utf-8'))
        self.writeToPipe(Pipe, "[sterr]:\n\n\r\r\n" + Output[1].decode('utf-8'))
        OS.close(Pipe)#we do not need this pipe anymore-> so close it
        OS._exit(0)

    def __ptyChildProcess(self, Pipe):
        Output = []
        InputData = ''

        MyId = str(OS.getpid())
        MyId += "\n"
        print(MyId)
        OS._exit(0)
        InputData = System.stdin.readline().strip()
        Output = self.__normalChildProcess(InputData)
        print("[stdout]:\n\n\r\r\n" + Output[0].decode('utf-8'))
        print("[sterr]:\n\n\r\r\n" + Output[1].decode('utf-8'))
        OS._exit(0)


    def writeToPipe(self, Pipe, InputString):
        self.__Lock2.acquire()
        OS.write(Pipe, InputString.encode('utf-8'))
        self.__Lock2.release()

    def readFromPipe(self, Pipe, OnlyToNewLine=False):
        Output = ''
        Char = ''

        self.__Lock2.acquire()
        Char = OS.read(Pipe, 1)
        self.__Lock2.release()
        while Char:
            if True == OnlyToNewLine and "\n" == Char:
                 return Output
            Output += Char.decode('utf-8')
            self.__Lock2.acquire()
            Char = OS.read(Pipe, 1)
            self.__Lock2.release()

        return Output

    def __doPTYFork(self, InputData):
        FD = ''
        PId = ''
        ChildId = ''
        Char = ''
        (Pid, FD) = Pty.fork()
        if 0 == PId:#we are the child
            print("TEEEEEEEEEEEESSSSSSSSSSSSSSSSSSSSTTTTTTTTTTTTTT")
            System.stdout.flush()
           # self.__ptyChildProcess()
        else:#We are the parent
            ChildId = ''
            Time.sleep(1)
            print('In Parent Process: PID# %s' % OS.getpid())
            print(FD)
            print(OS.read(FD, 100))
    #        Time.sleep(1)
    #        Char = OS.read(3,1000000000)
    #        Time.sleep(1)
           # while Char:
           #         ChildId += Char.decode('utf-8')
           #         Char = OS.read(MasterDescriptor,1 )

            #self.writeToPipe(MasterDescriptor, InputData)
   #         print(Char)
   #         Char = OS.read(FD,1000000000)
   #         print(Char)
            #OS.waitpid(int(ChildId), 0)
            #return self.readFromPipe(MasterDescriptor)


    def __doNormalFork(self, InputData):

        PId = ''
        ChildId = ''
        PipeIn = ''
        PipeOut = ''
        Output = ''

        PipeOut, PipeIn = OS.pipe()
        PId = OS.fork()

        if -1 == PId:
            pass#smt gone wrong...very wrong
        elif 0 == PId:#we are the child
            self.__forkedChildProcess(PipeIn, InputData)
        else:#We are the parent
            OS.close(PipeIn)

            ChildId = self.readFromPipe(PipeOut, True)
            OS.waitpid(int(ChildId), 0)
            Output = self.readFromPipe(PipeOut)
            OS.close(PipeOut)
            print(Output)

    def do(self, InputData, Flag= 0x0):
        self.__Lock.acquire()
        self.__ParameterLock = True
        self.__Lock.release()
        if self.FORK_PTY_PROCESS == Flag:
            self.__doPTYFork(InputData)
        elif self.FORK_NO_PROCESS == Flag:
            Output = self.__normalChildProcess(InputData)
            Output[0] = "[stdout]:\n\n\r\r\n" + Output[0].decode('utf-8')
            Output[1] = "[stderr]:\n\n\r\r\n" + Output[1].decode('utf-8')
            Output = Output[0] + Output[1]
            return Output
        else:
            self.__doNormalFork(InputData)

    def flushParameters(self):
        self.__Parameter = []
        self.__ParameterLock = False
