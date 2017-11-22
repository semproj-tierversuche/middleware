#!/usr/bin/env python3
# requires at least python 3.4

import io as IO
import os as OS
import sys as System
from threading import Lock
import subprocess as SubProcess

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
    __CMD = ''
    __Parameter = []
    FORK_NORMAL_PROCESS = 0x0
    FORK_TTY_PROCESS = 0x1
    __PipenameCounter = 0
    __Lock = ''
    __Lock2 = ''

    def __init__(self, Configuration):
        self.__CMD = Configuration['cmd']['name']
        self.__Lock = Lock()
        self.__Lock2 = Lock()

    def addParameter(self, Key, Value):
        if True ==  self.__ParameterLock:
            return

        if Key.strip():
            self.__Lock.acquire()
            if Key.endswith('='):
                self.__Parameter.append(Key + Value)
            else:
                self.__Parameter.append((Key + " " + Value).strip())
            self.__Lock.release()

    def __NormalChildProcess(self, Pipe):
        #capture stdout
        #capture stderr
#        Stdout = System.stdout
#        Stderr = System.stderr

        StdoutBuffer = IO.StringIO()
        StderrBuffer = IO.StringIO()

 #       System.stdout = StdoutBuffer
 #       System.stderr = StderrBuffer

        MyId = str(OS.getpid())
        MyId += "\n"
        print(self.__Parameter)
        self.writeToPipe(Pipe, MyId)
        OS.execv(self.__CMD, self.__Parameter)
 #       self.writeToPipe(Pipe, "[stdout]:\n\n\r\r\n\n" + StdoutBuffer.getvalue())
 #       self.writeToPipe(Pipe, "[sterr]:\n\n\r\r\n\n" + StderrBuffer.getvalue())
        OS.close(Pipe)#we do not need this pipe anymore-> so close it
        OS._exit(0)

    def __PTYChildProcess(self):
        pass

    def cleanFIFOs(self):
        pass

    def writeToPipe(self, Pipe, InputString):
        self.__Lock2.acquire()
        OS.write(Pipe, InputString.encode('utf-8'))
        self.__Lock2.release()

    def readFromPipe(self, Pipe, OnlyToNewLine=False):
        Output = ''
        Char = ''

        self.__Lock2.acquire()
        Char = OS.read(Pipe, 1).decode('utf-8')
        self.__Lock2.release()
        while Char:
            if True == OnlyToNewLine and "\n" == Char:
                 return Output
            Output += Char
            self.__Lock2.acquire()
            Char = OS.read(Pipe, 1).decode('utf-8')
            self.__Lock2.release()

        return Output

    def __doPTYFork(self, InputData):
        MasterDescriptor = ''
        PId = ''
        #Pid, MasterDescriptor = OS.forkpty()
        if -1 == PId:
            pass#smt gone wrong...very wrong
        elif 0 == PId:#we are the child
            pass
        else:#We are the parent
            pass

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
            self.__NormalChildProcess(PipeIn)
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
        if self.FORK_TTY_PROCESS == Flag:
            self.__doPTYFork(InputData)
        else:
            self.__doNormalFork(InputData)

    def flushParameters(self):
        self.__Parameter = []
        self.__ParameterLock = False
