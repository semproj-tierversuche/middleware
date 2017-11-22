#!/usr/bin/env python3
# requires at least python 3.4

import io as IO
import os as OS
import sys as System
from threading import Lock

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
    __CMD = ''
    __Parameter = []
    FORK_NORMAL_PROCESS = 0x0
    FORK_TTY_PROCESS = 0x1
    __PipenameCounter = 0
    __Lock = ''

    def __init__(self, Configuration):
        self.__CMD = Configuration['cmd']['name']
        self.__Lock = Lock()

    def addParameter(self, Key, Value):
        if ParameterString.strip():
            if Key.endswith('='):
                self.__Parameter.append(Key + Value)
            else:
                self.__Parameter.append(Key + " " + Value)

    def __NormalChildProcess(self, IdPipe, StdOut, StdErr):
        #capture stdout
        #capture stderr
        MyId = str(OS.getpid()).encode('utf-8')
        OS.write(IdPipe, MyId)
        OS.close(IdPipe)#we do not need this pipe anymore-> so close it

        OS._exit(0)

    def __PTYChildProcess(self):
        pass

    def cleanFIFOs(self):
        pass

    def readFromPipe(self, Pipe):
        Output = ''
        Char = ''

        Char = OS.read(Pipe, 1)
        while Char:
            Output += Char.decode('utf-8')
            Char = OS.read(Pipe, 1)
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
        IdNameIn = ''
        IdNameOut = ''
        StdErrIn = ''
        StdErrOut = ''
        StdOutIn = ''
        StdOutOut = ''


        IdNameOut, IdNameIn = OS.pipe()
        StdOutOut, StdOutIn = OS.pipe()
        StdErrOut, StdErrIn = OS.pipe()
        PId = OS.fork()

        if -1 == PId:
            pass#smt gone wrong...very wrong
        elif 0 == PId:#we are the child
            self.__NormalChildProcess(IdNameIn, StdOutIn, StdErrIn)
        else:#We are the parent
            OS.close(IdNameIn)
            OS.close(StdOutIn)
            OS.close(StdErrIn)

            ChildId = self.readFromPipe(IdNameOut)
            OS.close(IdNameOut)
            print('A:' + ChildId)
            OS.waitpid(int(ChildId), 0)

    def do(self, InputData, Flag= 0x0):

        if self.FORK_TTY_PROCESS == Flag:
            self.__doPTYFork(InputData)
        else:
            self.__doNormalFork(InputData)

    def flushParameters(self):
        self.__Parameter = []
