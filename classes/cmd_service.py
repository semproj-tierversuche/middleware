#!/usr/bin/env python3
# requires at least python 3.4

import time as Time
import io as IO
import os as OS
import sys as System
from threading import Lock
import subprocess as SubProcess
import pty as Pty
import io as IO

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
    __Lock = None
    __Lock2 = None

    def __init__(self, Configuration):
        if 'timeout' in Configuration['cmd']:
            self.__Timeout = int(Configuration['cmd']['timeout'])
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

    def __normalChildProcess(self, InputData, StdIn):
        Process = None
        Stdin = None
        Stdout = None
        Stderr = None

        Parameter = self.__Parameter
        if InputData and False == StdIn:
            Parameter.append(InputData)
        elif not InputData and False==StdIn:
            pass

        print(Parameter)
        if InputData and True==StdIn:
            Process = SubProcess.Popen(Parameter, stdin=SubProcess.PIPE, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            Stdout, Stderr = Process.communicate(InputData.encode('utf-8'))
        else:
            Process = SubProcess.Popen(Parameter, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            Stdout, Stderr = Process.communicate()

        if 0<self.__Timeout:
            Process.wait(self.__Timeout)
        else:
            Process.wait()

        return [Stdout, Stderr]

    def __forkedChildProcess(self, Pipe, InputData, PasteToStdin):
        MyId = str(OS.getpid())
        MyId += "\n"
        Output = []
        self.writeToPipe(Pipe, MyId)
        Output = self.__normalChildProcess(InputData, PasteToStdin)
        self.writeToPipe(Pipe, Output[0].decode('utf-8'))
        self.writeToPipe(Pipe, "\x03\x35\x35\x02" + Output[1].decode('utf-8'))
        OS.close(Pipe)#we do not need this pipe anymore-> so close it
        OS._exit(0)

    def __ptyChildProcess(self):
        Output = []
        Instruction = []
        InputData = None
        PasteToStdin = None

        MyId = str(OS.getpid())
        print(MyId)
        Instruction = System.stdin.readlines.split("\x03\x35\x35\x02")
        #TODO nach schlagen wie man das über Tupel macht
        PasteToStdin = Instruction[0]
        InputData = Instruction[1]
        #print(bool(PasteToStdin))
        InputData = self.readFromPipe(System.stdin.fileno)
        print(PasteToStdin + "\n" + InputData)

        OS._exit(0)
        Output = self.__normalChildProcess()
        print(Output[0].decode('utf-8'))
        print(InputData + "\x03\x35\x35\x02" + Output[1].decode('utf-8'))
        OS._exit(0)

    def writeToPipe(self, Pipe, InputString):
        self.__Lock2.acquire()
        OS.dup
        OS.write(Pipe, InputString.encode('utf-8'))
        self.__Lock2.release()

    def readFromPipe(self, Pipe, OnlyToNewLine=False):
        Output = ''
        Char = None

        self.__Lock2.acquire()
        Char = OS.read(Pipe, 1)
        self.__Lock2.release()
        while Char:
            Char = Char.decode('utf-8')
            if True == OnlyToNewLine and "\n" == Char:
                 return Output
            Output += Char
            self.__Lock2.acquire()
            Char = OS.read(Pipe, 1)
            self.__Lock2.release()

        return Output

    def __doPTYFork(self, InputData, PasteToStdin):
        FD = None
        FD2 = None
        PId = None
        ChildId = None
        Char = None
        print(InputData)
        (PId, FD) = Pty.fork()
        if -1 == PId:
            pass
        elif 0 == PId:#we are the child
            self.__ptyChildProcess()
        else:#We are the parent
            ChildId = None
            print('In Parent Process: PID# %s' % OS.getpid())
            ChildId = int(self.readFromPipe(FD, True))
            print(ChildId)
            self.writeToPipe(FD, str(PasteToStdin) + "\x03\x35\x35\x02" + InputData)
            FD = OS.dup(FD)
            Awnser = self.readFromPipe(FD)
            print(Awnser)
            OS._exit(0)
            Pty.os.waitpid(int(ChildId), 0)
            print(OS.read(FD, 100000).decode('utf-8'))
            #return self.readFromPipe(MasterDescriptor)

    def __doNormalFork(self, InputData, PasteToStdin):

        PId = None
        ChildId = None
        PipeIn = None
        PipeOut = None
        Output = None

        PipeOut, PipeIn = OS.pipe()
        PId = OS.fork()

        if -1 == PId:
            pass#smt gone wrong...very wrong
        elif 0 == PId:#we are the child
            self.__forkedChildProcess(PipeIn, InputData, PasteToStdin)
        else:#We are the parent

            OS.close(PipeIn)
            ChildId = self.readFromPipe(PipeOut, True)
            OS.waitpid(int(ChildId), 0)
            Output = self.readFromPipe(PipeOut)
            OS.close(PipeOut)
            return Output


    def do(self, InputData, Flag= 0x0, PasteToStdin=False):
        self.__Lock.acquire()
        self.__ParameterLock = True
        self.__Lock.release()
        if self.FORK_PTY_PROCESS == Flag:
            return  self.__doPTYFork(InputData, PasteToStdin)
        elif self.FORK_NO_PROCESS == Flag:
            Output = self.__normalChildProcess(InputData, PasteToStdin)
            return Output[0].decode('utf-8') + "\x03\x35\x35\x02" + Output[1].decode('utf-8')
        else:
            return self.__doNormalFork(InputData, PasteToStdin)

    def reset(self):
        self.__Parameter = []
        self.__ParameterLock = False

    def removeParameter(self, Key):
        if Key in self.__Parameter and Key != next(iter(self.__Parameter)):
            del self.__Parameter[Key]
