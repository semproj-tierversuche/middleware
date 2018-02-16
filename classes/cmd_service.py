#!/usr/bin/env python3
# requires at least python 3.4

import errno as Error
import pty as PTY
import shlex as Shell
import os as OS
import sys as System
import threading as Threads
import time as Time
from collections import OrderedDict
from classes.utils import PipeHelper, mergeDictionaries as merge, Mutable, BytesIOEx as BytesIO,\
    LinePipeWriterThread as WriterThread, EoFPipeReaderThread as ReaderThread, DelimiterPermanentPipeReaderThread as ReaderDaemonizedThread,\
    LinePermanentPipeWriterThread as WriterDaemonizedThread, binaryInsertSearch as binarySearch
import signal as Signal
#TODO:
#   -> Doku schreiben
class CmdServiceException(Exception):
        __AdditionalInformation = None
        Reasons = ['The connection is not established', "Cannot spawn the childproc.",\
                   "The programm is supposed to get data via stdin, but no data was given."\
                   "The given data contains illegal value - got {}",\
                   "A fatal error occures during the fork.", "There was no command given."]
        ReasonCodes = [0x0, 0x1, 0x2, 0x3, 0x4, 0x6]
        Reason = 0x0
        NO_CONECTION = 0x0
        NO_CHILD = 0x1
        NO_DATA = 0x2
        ILLEGAL_CONTENT = 0x3
        FATAL_FORK = 0x4
        NO_COMMAND = 0x5
        __AdditionalInformation = None

        def __init__(self, ErrorCode, AdditionalStuff=None):
            self.Reason = ErrorCode
            if AdditionalStuff:
                self.__AdditionalInformation = AdditionalStuff
        def __str__(self):
            if self.Reason not in self.ReasonCodes:
                return repr('Unkown error.')
            else:
                if self.ILLEGAL_CONTENT == self.Reason:
                    return repr(self.Reasons[self.Reason].format(self.__AdditionalInformation))
                else:
                   return repr(self.Reasons[self.Reason])

class CmdService(object):
    __Command = None
    __Timeout = None
    __Enviroment = None
    __EnviromentCache = None
    __EnviromentContext = None
    __EnviromentHasChanged = None
    __EnviromentNewKeys = None
    __EnviromentRemoveals = None
    __EnviromentReplaces = None
    __Parameter = None
    __ParameterCache = None
    __ParameterContext = None
    __ParameterHasChanged = None
    __ParameterNewKeys = None
    __ParameterRemoveals = None
    __TRANSMISSION_LENGTH =  50000#4096
    __Closed = None
    __SLEEP_RATE = 0.005
    __RestoreSignals = [1, 2, 3, 4, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 29, 30, 31, 34, 64]

    #Operation modes
    FORK_NORMAL_PROCESS = 0x0
    FORK_PTY_PROCESS = 0x1
    #For permanent process
    PERMANENT_PROCESS = 0x2
    HYBRID_PROCESS = 0x4
    FULL_DAEMON_PROCESS = 0x6
    #For Piping
    NO_PIPE ='O'
    DEV_NULL_PIPE = 'Z'
    PIPE_PIPE = 'P'
    TO_STDERR_PIPE = 'E'
    TO_STDOUT_PIPE = 'S'
    STDERR_STDOUT_PIPE = 'F'
    #For Context
    SET = 0x42
    RESTORE = 0x23
    CLEAR = 0x66
    FIRST = 0x123

    __Lock = None
    __KeepAlive = None
    #only for keepAlive subprocesses
    _ReadFromStdin = None#we just need it one level above
    __Debug = None
    __Process = None
    __Stdin = None
    __Stdout = None
    __Stderr = None
    __StdinThread = None
    __StderrThread = None
    __StdoutThread = None
    __PtyFD = None
    __Delimiter = None
    __OSErrorMessage = None
    __TIMER = None
    _OK = -23
    _TERMINATED = -42
    _TIMEOUT = -666

    def __init__(self, Command, Timeout=0):
        self.__Parameter = OrderedDict()
        self.__ParameterContext = []
        self.__ParameterNewKeys = []
        self.__ParameterRemoveals = []
        self.__ParameterHasChanged = True

        self.__Lock = Threads.Lock()
        self.__Closed = False
        if not Command:
            raise CmdServiceException(CmdServiceException.NO_COMMAND)
        else:
            self.setCommand(Command, Timeout)
        self._ReadFromStdin = False#we just need it one level above
        self.__KeepAlive = False
        self.__startThreads()

        self.__Enviroment = OrderedDict()
        self.__EnviromentHasChanged = True
        self.__EnviromentContext = []
        self.__EnviromentNewKeys = []
        self.__EnviromentRemoveals = []
        self.__EnviromentReplaces = []

    def __startThreads(self, Delimiter=None, Mode=None):
        if Mode:
            if self._ReadFromStdin:
                self.__StdinThread = WriterDaemonizedThread(Pipe=self.__Stdin,\
                                                            Length=self.__TRANSMISSION_LENGTH)
            else:
                self.__StdinThread = None
            self.__StdoutThread = None
            self.__StderrThread = ReaderDaemonizedThread(Pipe=self.__Stderr,\
                                                         Length=self.__TRANSMISSION_LENGTH,\
                                                         Delimiter=Delimiter,\
                                                         Exact=self.__Debug)
        else:
            self.__StdinThread = WriterThread(Length=self.__TRANSMISSION_LENGTH)
            self.__StdoutThread = ReaderThread(Length=self.__TRANSMISSION_LENGTH)
            self.__StderrThread = ReaderThread(Length=self.__TRANSMISSION_LENGTH)
        self.__StdinThread.start()
        if self.__StdoutThread:
            self.__StdoutThread.start()
        self.__StderrThread.start()

    def setCommand(self, Command, Timeout=0):
        if not Command:
            return

        self.__Command = Command

        if not isinstance(Timeout, int) or 0 >= Timeout:
            self.__Timeout = 0
        else:
            self.__Timeout = self.__prepareTimeout(Timeout)

    def __context(self, Where, Field, Flag):
        Length = len(Where)
        if not Where and not Field:
            return
        if not Where:
            Where.append(Field.copy())
        if self.RESTORE == Flag:
            if 1 == Length:
                return Where[0].copy()
            else:
                return Where.pop()
            return True
        elif self.SET == Flag:
            Where.append(Field.copy())
        elif self.FIRST == Flag:
            return Where[0].copy()
        elif self.CLEAR:
            while 0 != len(Where):
                Where.pop()

        return None

    #add and replace
    def addParameter(self, Parameter):
        Parameter = Parameter.strip()
        if not Parameter:
            return

        Parameter = Shell.split(Parameter)
        for Param in Parameter:
            self.__Parameter[Param] = ''
            self.__ParameterNewKeys.append(Param)
        return True

    def addParameters(self, Parameter):
        if not Parameter or not isinstance(Parameter, list):
            return
        else:
            for Param in Parameter:
                if False == self.addParameter(Param):
                    return False
            return True

    def removeParameter(self, Key):
        if self.__Parameter and Key in self.__Parameter and Key not in self.__ParameterRemoveals:
            self.__ParameterRemoveals.append(Key)

    def parameterContext(self, Flag):
        ToSet = self.__context(self.__ParameterContext, self.__Parameter, Flag)
        if ToSet:
            self.__Parameter = ToSet
            self.__ParameterHasChanged = True
            self.__ParameterRemoveals = []
            self.__ParameterNewKeys = []

    def printParameter(self):
        for Key, Value in self.__Parameter.items():
            if Key in self.ParameterRemoveals:
                continue
            Value, State = Value
            print(Key + ": " + Value)

    def getParameter(self):
        Return = []
        for Key, Value in self.__Parameter.items():
            Return.append(Key)
        return Return

    def __getParameterCache(self):
        Output = []

        #build completely new
        if True == self.__ParameterHasChanged:
            Output.append(Shell.quote(self.__Command))
            for Key, Value in self.__Parameter.items():
                if Key in self.__ParameterRemoveals:
                    del self.__Parameter[Key]
                    continue
                Output.append(Shell.quote(Key))

            self.__ParameterNewKeys = []
            self.__ParameterReplaces = []
            self.__ParameterHasChanged = False
            self.__ParameterCache = Output.copy()
            return Output
        #insert
        if self.__ParameterNewKeys:
            while self.__ParameterNewKeys:
                Key = self.__ParameterNewKeys.pop(0)
                if Key in self.__ParameterRemoveals:
                    del self.__ParameterRemoveals[Key]
                    del self.__Parameter[Key]
                    continue
                self.__ParameterCache.append(Shell.quote(Key))
        #delete
        if self.__ParameterRemoveals:
            while self.__ParameterRemoveals:
                ToDelKey = self.__ParameterRemoveals.pop(0)
                i = 0
                for Key, Value in self.__Parameter:
                    if ToDelKey == Key:
                        self.__ParameterCache.pop(i)
                        del self.__Parameter[Key]
                        break
                    i += 1
            self.__ParameterRemoveals = []
        return self.__ParameterCache.copy()

    def applyParameter(self):
        self.__getParameterCache()

    def addEnviromentVariable(self, Key, Value):
        def isReplace(Env):
            i = 0
            for Key, Values in self.__Enviroment:
                if Key == Env:
                    if i not in self.__EnviromentReplaces:
                        self.__EnviromentReplaces.append(i)
                        break
                    i += 1
                else:
                    self.__EnviromentNewKeys.append(Env)

        Key = OS.fsencode(Key)
        Value = OS.fsencode(Value)
        if b'=' in Key or b'=' == Value[0:1]:
            return False

        isReplace(Key)
        self.__Enviroment[Key] = Value
        return True

    def addEnviromentVariables(self, Variables):
        if Variables and isinstance(Variables, dict):
            for Key, Value in Variables.items():
                if False == self.addEnviromentVariable(Key, Value):
                    return False
            return True
        else:
            return False

    def removeEnviromentVariable(self, Key):
        if self.__Enviroment and Key in self.__Enviroment and Key not in self.__EnviromentRemoveals:
            Key = OS.fsencode(Key)
            if b'=' in Key:
                return
            self.__EnviromentRemoveals.append(Key)

    def enviromentContext(self, Flag):
        ToSet = self.__context(self.__EnviromentContext, self.__Enviroment, Flag)
        if ToSet:
            self.__Enviroment = ToSet
            self.__EnviromentHasChanged = True
            self.__ParameterRemoveals = []
            self.__ParameterNewKeys = []

    def printEnviroment(self):
        for Key, Value in self.__Enviroment.items():
            if Key in self.__EnviromentRemoveals:
                continue
            print(Key + ": " + Value)

    def __getEnviromentCache(self):
        Output = []

        #build new
        if True == self.__EnviromentHasChanged:
            for Key, Value in self.__Enviroment.items():
                if Key in self.__EnviromentRemoveals:
                    del self.__Enviroment[Key]
                    del self.__EnviromentRemoveals[Key]
                    continue
                Output.append(Key + b'=' + Value)

            self.__EnviromentCache = Output
            self.__EnviromentHasChanged = False
            self.__EnviromentRemoveals = []
            self.__EnviromentNewKeys = []
            return self.__EnviromentCache.copy()

        #replace
        if self.__EnviromentRemoveals:
            i = 0
            for Key, Value in self.__Enviroment:
                if i in self.__EnviromentRemoveals and Key not in self.__EnviromentRemoveals:
                    self.__EnviromentCache[i] = Key + b'=' + Value
                i += 1
            self.__EnviromentRemoveals = []

        #insert
        if self.__EnviromentNewKeys:
            while self__EnviromentNewKeys:
                Key = self.__EnviromentNewKeys.pop(0)
                if Key in self.__EnviromentRemoveals:
                    del self.__EnviromentRemoveals[Key]
                    del self.__Enviroment[Key]
                    continue
                self.__EnviromentCache.append(Key + b'=' + self.__Enviroment[Value])

        #delete
        if self.__EnviromentRemoveals:
            while self__EnviromentRemoveals:
                ToDelKey = self.__EnviromentRemoveals.pop(0)
                i = 0
                for Key, Value in self.__Enviroment:
                    if ToDelKey == Key:
                        self.__EnvormentCache.pop(i)
                        del self.__Enviroment[Key]
                        break
                    i += 1

        return self.__EnviromentCache.copy()

    def applyEnviroment(self):
        self._getEnviromentCache()

    def reset(self):
        if self.__Parameter:
            self.__Parameter.clear()
            self.__ParameterHasChanged = True
        if self.__Enviroment:
            self.__Enviroment.clear()
            self.__EnviromentHasChanged = True

    def context(self, Flag):
        self.enviromentContext(Flag)
        self.parameterContext(Flag)

    def apply(self):
        self.__getParameterCache()
        self.__getEnviromentCache()

    def __prepareTimeout(self, Timeout):
        if  not isinstance(Timeout, int) or 0 >= Timeout:
            return self.__Timeout
        else:
            return Timeout/1000

    def __doChild(self, Data, Timeout, Controller,\
                  StdinPipe, StdoutPipe, StderrPipe, Stdout, Stderr):

        #read pipID
        ChildId = int(PipeHelper.read(Controller, 1024).decode('utf-8'))
        OS.close(Controller)

#        if -1 != StderrPipe:
        self.__StderrThread.do(StderrPipe, Stderr)

#        if -1 != StdoutPipe:
        self.__StdoutThread.do(StdoutPipe, Stdout)

        if -1 != StdinPipe:
            self.__StdinThread.do(StdinPipe, Data)

        try:
            ReturnCode = self.__waitForChild(ChildId, Timeout)
        except OSError as e:
            ReturnCode = e.errno
            Stdout.append('')
            Stderr.append(e.strerror)
        else:
            if self._TIMEOUT == ReturnCode:
                Stdout.append('')
                Stderr.append('')
                return self._TIMEOUT
#            if -1 != StdoutPipe:
            self.__StdoutThread.waitUntilDone(Stdout)
#            if -1 != StderrPipe:
            self.__StderrThread.waitUntilDone(Stderr)
        return ReturnCode

    def __execCMD(self, Controller, Stdin, Stdout, Stderr, Parameter, Enviroment):
        #Notelike C we cannot close Std*
        OS.dup2(Controller, System.stdout.fileno())
        PipeHelper.writeLineToPipe(Controller, str(OS.getpid()).encode('utf-8'),\
                                   Length=self.__TRANSMISSION_LENGTH)
        System.stdout.flush()
        OS.close(Controller)
        if -1 != Stdin:
            OS.dup2(Stdin, System.stdin.fileno())
#        if -1 != Stdout:
        OS.dup2(Stdout, System.stdout.fileno())
#        if -1 != Stderr:
        OS.dup2(Stderr, System.stderr.fileno())

        if not Enviroment:
            OS.execvp(Parameter[0], Parameter)
        else:
            OS.execvpe(Parameter[0], Parameter, Enviroment)
        #error: child did not spawn
        raise CmdServiceException(CmdServiceException.NO_CHILD)

    def __waitForChild(self, ProcessId, Timeout):
        ReturnCode = None
        TrashMe = None
        Slept = 0.000
        Start = Time.time()
        SleepTime = self.__SLEEP_RATE
        if 0 >= Timeout:#we wait until the process is over -> thats not in every case a good idea
            TrashMe, ReturnCode = OS.waitpid(ProcessId, 0)
        else:
            while True:
                if Slept >= Timeout:
                    OS.kill(ProcessId, Signal.SIGKILL)#==kill -9 pid
                    return self._TIMEOUT
                TrashMe, ReturnCode = OS.waitpid(ProcessId, OS.WNOHANG)
                if 0 == TrashMe:#the child is not terminated by now
                    Now = Time.time()
                    Slept += Now-Start
                    Start = Now
                    Time.sleep(SleepTime)
                else:
                    break
        return ReturnCode

    def __restoreSignals(self):
        for SignalNumber in self.__RestoreSignals:
            Signal.signal(SignalNumber, Signal.SIG_DFL)

    def __doExecPreparation(self, AdditionalParameter, AdditionalEnviroment):
        Parameter = self.__getParameterCache()
        AdditionalEnviromentOut = OrderedDict()
        if AdditionalParameter and isinstance(AdditionalParameter, list):
            for Param in AdditionalParameter:
                Parameter.append(Shell.quote(Param))

        Enviroment = self.__getEnviromentCache()
        if AdditionalEnviroment and isinstance(AddionalEnviroment, dict):
            for Key, Value in AdditionalEnviroment.items():
                Key2 = OS.fsencode(Key)
                Value = OS.fsencode(Value)
                if b'=' == Key2[-1]:
                    raise ValueError("Got = as last char of enviroment key " + Key)
                elif b'=' == Value[0]:
                    raise ValueError("Got = as first char of as value at enviroment key " + Key)
                else:
                    if Key2 not in self.__Enviroment and Key2 not in AdditionalEnviromentOut:
                        Enviroment.append(Key2 + b'=' + Value)

        return (Parameter, Enviroment)

    def __makePipes(self, Stdin=NO_PIPE, Stdout=NO_PIPE, Stderr=NO_PIPE):
        StdinOut = -1
        StdinIn = -1
        StdoutOut = -1
        StdoutIn = -1
        StderrOut = -1
        SterrIn = -1
        DevZ = None

        ControllerOut, ControllerIn = OS.pipe()

        if self.NO_PIPE == Stdin:
            pass
        elif self.PIPE_PIPE == Stdin:
            StdinOut, StdinIn = OS.pipe()
#        elif isinstance(Stdin, int):#it is a fd
#            StdinOut = OS.dup(Stdin)
#            StdinIn = OS.dup(Stdin)
#        else:#it is a file
#            StdinOut = OS.dup(Stdin.fileno())
#            StdinIn = OS.dup(Stdin.fileno())

        if self.NO_PIPE == Stdout:
            pass
        elif self.PIPE_PIPE == Stdout:#Normal Pipe
            StdoutOut, StdoutIn = OS.pipe()
#        elif self.DEV_NULL_PIPE == Stdout:#we should pipe everything to devnull
#            DevZ = open(OS.devnull).fileno()
#            StdoutIn = DevZ
#        elif self.TO_STDOUT_PIPE == Stdout:
#            StdoutIn = OS.dup(System.stdout.fileno())
#        elif self.TO_STDERR_PIPE == Stdout:
#            StdoutIn = OS.dup(System.stderr.fileno())
#        elif isinstance(Stdout, int):#it is a fd
#            StdoutOut = OS.dup(Stdout)
#            StdoutIn = OS.dup(Stdout)
#        else:#it is a file
#            StdoutOut = OS.dup(Stdout.fileno())
#            StdoutIn = OS.dup(Stdout.fileno())

        if self.NO_PIPE == Stderr:
            pass
        elif self.PIPE_PIPE == Stderr:
            StderrOut, StderrIn = OS.pipe()
#        elif self.DEV_NULL_PIPE == Stderr:
#            if DevZ is None:
#                DevZ = open(OS.devnull).fileno()
#                StderrIn = DevZ
#            else:
#                StderrIn = OS.dup(DevZ)
#        elif self.TO_STDOUT == Stderr:
#            StderrIn = OS.dup(System.stdout.fileno())
#        elif self.TO_STDERR_PIPE == Stderr:
#            StderrIn = OS.dup(System.stderr.fileno())
#        elif self.STDERR_STDOUT_PIPE == Stderr:
#            if -1 != StdoutOut:
#                StderrOut = OS.dup(StdoutOut)
#            if -1 != StdoutInt:
#                StderrIn = OS.dup(StderrIn)
#        elif isinstance(Stderr, int):#it is a fd
#            StdoutOut = OS.dup(Stderr)
#            StdoutIn = OS.dup(Stderr)
#        else:#it is a file
#            StderrOut = OS.dup(Stderr.fileno())
#            StderrIn = OS.dup(Stderr.fileno())

        return (ControllerIn, ControllerOut,\
                StdinIn, StdinOut,\
                StdoutIn, StdoutOut,\
                StderrIn, StderrOut)

    def __doPTYForkAndExec(self, ControllIn, ControllOut, StdinIn, StdinOut,\
                           StdoutIn, StdoutOut, StderrIn, StderrOut,\
                           Data, Timeout, Parameter, Enviroment, RestoreSignals):
        FD = None
        PId = None
        ReturnCode = None
        Stderr = []
        Stdout = []

        (PId, FD) = PTY.fork()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            OS.close(ControllOut)
            if -1 != StdinIn:
                OS.close(StdinIn)
#            if -1 != StdoutOut:
            OS.close(StdoutOut)
#            if -1 != StderrOut:
            OS.close(StderrOut)

            if True == RestoreSignals:
                self.__restoreSignals()

            self.__execCMD(ControllIn ,StdinOut, StdoutIn, StderrIn, Parameter, Enviroment)
        else:#We are the parent
            OS.close(ControllIn)
            if -1 != StdinOut:
                OS.close(StdinOut)
#            if -1 != StdoutIn:
            OS.close(StdoutIn)
#            if -1 != StderrIn:
            OS.close(StderrIn)

            ReturnCode = self.__doChild(Data, Timeout, ControllOut,\
                                        StdinIn, StdoutOut, StderrOut, Stdout, Stderr)

            OS.close(FD)
            if -1 != StdinIn:
                OS.close(StdinOut)
#            if -1 != StdoutOut:
            OS.close(StdoutOut)
#            if -1 != StderrOut:
            OS.close(StderrOut)

            return (ReturnCode, Stdout[0], Stderr[0])

    def __doForkAndExec(self, ControllIn, ControllOut, StdinIn, StdinOut,\
                        StdoutIn, StdoutOut, StderrIn, StderrOut,\
                        Data, Timeout, Parameter, Enviroment, RestoreSignals):
        PId = None
        ReturnCode = None
        Stderr = []
        Stdout = []

        PId = OS.fork()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            OS.close(ControllOut)
            if -1 != StdinIn:
                OS.close(StdinIn)
#            if -1 != StdoutOut:
            OS.close(StdoutOut)
#            if -1 != StderrOut:
            OS.close(StderrOut)

            if True == RestoreSignals:
                self.__restoreSignals()

            self.__execCMD(ControllIn, StdinOut, StdoutIn, StderrIn, Parameter, Enviroment)
        else:#We are the parent
            #closing the Pipeends we do not need
            OS.close(ControllIn)
            if -1 != StdinOut:
                OS.close(StdinOut)
#            if -1 != StdoutIn:
            OS.close(StdoutIn)
 #           if -1 != StderrIn:
            OS.close(StderrIn)

            ReturnCode = self.__doChild(Data, Timeout, ControllOut,\
                                        StdinIn, StdoutOut, StderrOut, Stdout, Stderr)
#            if -1 != StdoutOut:
            OS.close(StdoutOut)
#            if -1 != StderrOut:
            OS.close(StderrOut)
            if -1 != StdinIn:
                OS.close(StdinIn)
            return (ReturnCode, Stdout[0], Stderr[0])

    def startPermanentProcess(self, Delimiter=None, AdditionalParameter=None,\
                              AdditionalEnviroment=None, RestoreSignals=False,\
                              Mode=0x0, Debug=False):
        if True == self.__KeepAlive:#we skip if a process is allready running
            return False

        if self.FORK_PTY_PROCESS == self.FORK_PTY_PROCESS&Mode:
            UsePTY = True
            Mode ^= self.FORK_PTY_PROCESS
        else:
            UsePTY = False
            Mode ^= self.FORK_NORMAL_PROCESS


        if self.PERMANENT_PROCESS == Mode or self.HYBRID_PROCESS == Mode:
            if not Delimiter or not isinstance(Delimiter, bytes):
                 raise ValueError("The given delimiter was invalid.")
            else:
                self.__Delimiter = Delimiter

        self.__KeepAlive = True

        self.__StdoutThread.die()
        self.__StderrThread.die()
        self.__StdinThread.die()

        if self.PERMANENT_PROCESS == Mode:
            self._ReadFromStdin = True
            Sin = self.PIPE_PIPE
        elif self.HYBRID_PROCESS:
            self._ReadFromStdin = False
            Sin = self.NO_PIPE
        else:#full deamon
            self._ReadFromStdin = True
            Sin = self.NO_PIPE

        self.__Debug = Debug

        Parameter, Enviroment = self.__doExecPreparation(AdditionalParameter, AdditionalEnviroment)
        ControllerIn, ControllerOut, StdinIn, StdinOut, StdoutIn, StdoutOut,\
        StderrIn, StderrOut = self.__makePipes(Sin, self.PIPE_PIPE, self.PIPE_PIPE)

        if False == UsePTY:
            self.__startForkProcess(ControllerIn, ControllerOut, StdinIn, StdinOut,\
                                    StdoutIn, StdoutOut, StderrIn, StderrOut,\
                                    Parameter, Enviroment, RestoreSignals)
        else:
            self.__startPTYProcess(ControllerIn, ControllerOut, StdinIn, StdinOut,\
                                   StdoutIn, StdoutOut, StderrIn, StderrOut,\
                                   Parameter, Enviroment, RestoreSignals)

        if self.PERMANENT_PROCESS == Mode or self.HYBRID_PROCESS == Mode:
            self.__startThreads(Delimiter=Delimiter, Mode=True)

        return True

    def __startForkProcess(self, ControllIn, ControllOut, StdinIn, StdinOut,\
                           StdoutIn, StdoutOut, StderrIn, StderrOut,\
                           Parameter, Enviroment, RestoreSignals):
        PId = None

        PId = OS.fork()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            OS.close(ControllOut)

            if -1 != StdinIn:
                OS.close(StdinIn)
            OS.close(StdoutOut)
            OS.close(StderrOut)

            if True == RestoreSignals:
                self.__restoreSignals()

            self.__execCMD(ControllIn, StdinOut, StdoutIn, StderrIn, Parameter, Enviroment)
        else:
            OS.close(ControllIn)
            if -1 != StdinOut:
                OS.close(StdinOut)
                self.__Stdin = StdinIn
            OS.close(StdoutIn)
            OS.close(StderrIn)
            self.__Stdout = StdoutOut
            self.__Stderr = StderrOut

            self.__Process = int(PipeHelper.read(ControllOut, 1024).decode('utf-8'))
            OS.close(ControllOut)

    def __startPTYProcess(self, ControllIn, ControllOut, StdinIn, StdinOut,\
                          StdoutIn, StdoutOut, StderrIn, StderrOut,\
                          Parameter, Enviroment, RestoreSignals):
        PId = None

        (PId, self.__PtyFD) = OS.forkpty()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            OS.close(ControllOut)
            if -1 != StdinIn:
                OS.close(StdinIn)
            OS.close(StdoutOut)
            OS.close(StderrOut)

            if True == RestoreSignals:
                self.__restoreSignals()

            self.__execCMD(ControllIn, StdinOut, StdoutIn, StderrIn, Parameter, Enviroment)
        else:
            OS.close(ControllIn)
            if -1 != StdinOut:
                OS.close(StdinOut)
                self.__Stdin = StdinIn
            OS.close(StdoutIn)
            OS.close(StderrIn)

            self.__Stdout = StdoutOut
            self.__Stderr = StderrOut
            self.__Process = int(PipeHelper.read(ControllOut, 1024).decode('utf-8'))
            OS.close(ControllOut)

    def getStatus(self):
        if False == self.__KeepAlive or not self.__Process:
            return self._TERMINATED
        TrashMe = None
        ReturnCode = None
        try:
            TrashMe, ReturnCode = OS.waitpid(self.__Process, OS.WNOHANG)
        except OSError as e:
            self.__OSErrorMessage = e.strerror
            return e.errno
        if 0 != TrashMe or 0 != ReturnCode:
            return ReturnCode
        else:
            return self._OK

    def __communicator(self, Data):
        Stdout = []
        Stderr = []

        if not Data and True == self._ReadFromStdin:
            raise CmdServiceException(CmdServiceException.NO_DATA, type(Data))
        Status = self.getStatus()
        if self._OK != Status:
            if self.__OSErrorMessage:
                return (Status, None, self.__OSErrorMessage)
            else:
                return (Status, None, None)
        if not self.__Stdout:
            return (self._TERMINATED, None, None)

        self.__Lock.acquire()
        self.__StderrThread.do(Stderr)

        if True == self._ReadFromStdin:
            Data.write(self.__Delimiter)
            self.__StdinThread.do(Data)

        Stdout = PipeHelper.readUntilDelimiterFromPipe(Pipe=self.__Stdout,\
                                                       Delimiter=self.__Delimiter,\
                                                       Length=self.__TRANSMISSION_LENGTH,\
                                                       Exact=self.__Debug)
        self.__StderrThread.waitUntilDone(Stderr)
        self.__Lock.release()
        return (Status, Stdout, Stderr[0])

    def __kill(self):
        if False == self.__KeepAlive:
            return
        else:
            if self._OK == self.getStatus():
                OS.kill(self.__Process, Signal.SIGKILL)

    def do(self, StdinData=None, AdditionalParameter=[], AdditionalEnviroment=[],\
           Timeout=None, RestoreSignals=False, Mode=0x0):

        if True == self.__Closed:
            return None

        if StdinData or b'0' == StdinData:
            Data = BytesIO(StdinData)
            Sin = self.PIPE_PIPE
        else:
            Data = None
            Sin = self.NO_PIPE

        if False == self.__KeepAlive:
            Timeout = self.__prepareTimeout(Timeout)

            Parameter, Enviroment = self.__doExecPreparation(AdditionalParameter, AdditionalEnviroment)

            ControllerIn, ControllerOut, StdinIn, StdinOut, StdoutIn, StdoutOut,\
            StderrIn, StderrOut = self.__makePipes(Sin, self.PIPE_PIPE, self.PIPE_PIPE)

            if self.FORK_PTY_PROCESS == Mode:
                ReturnCode, Stdout, Stderr = self.__doPTYForkAndExec(ControllerIn, ControllerOut,\
                                                                     StdinIn, StdinOut,\
                                                                     StdoutIn, StdoutOut,\
                                                                     StderrIn, StderrOut,\
                                                                     Data,\
                                                                     Timeout,\
                                                                     Parameter,\
                                                                     Enviroment,\
                                                                     RestoreSignals)
            else:
                ReturnCode, Stdout, Stderr = self.__doForkAndExec(ControllerIn, ControllerOut,\
                                                                  StdinIn, StdinOut,\
                                                                  StdoutIn, StdoutOut,\
                                                                  StderrIn, StderrOut,\
                                                                  Data,\
                                                                  Timeout,\
                                                                  Parameter,\
                                                                  Enviroment,\
                                                                  RestoreSignals)
        else:
            ReturnCode, Stdout, Stderr = self.__communicator(Data)
            if self.__OSErrorMessage:
                self.__OSErrorMessage = None
        return (ReturnCode, Stdout, Stderr)

    def stop(self):
        if False == self.__KeepAlive:
            return
        if self._TERMINATED != self.getStatus():
           self.__kill()
        if self.__StdoutThread and True == self.__StdoutThread.isAlive:
            self.__StdoutThread.die()
            self.__StdoutThread = None
        if True == self.__StderrThread._IsActive:
            self.__StderrThread.die()
            self.__StderrThread = None
        if self.__StdinThread and True == self.__StdinThread._IsActive:
            self.__StdinThread.die()
            self.__StdinThread = None
        if self.__Stdout:
            OS.close(self.__Stdout)
            self.__Stdout = None
        if self.__Stdin:
            OS.close(self.__Stdin)
            self.__Stdin = None
        if self.__Stderr:
            OS.close(self.__Stderr)
            self.__Stderr = None
        if self.__PtyFD:
            OS.close(self.__PtyFD)
            self.__PtyFD = None
        self.__KeepAlive = False
        self._ReadFromStdin = False
        self.__OSErrorMessage = None
        self.__Process = None
        self.__startThreads()

    def close(self):
        if self._TERMINATED == self.getStatus():
            return
        self.stop()
        if self.__StdoutThread:
            self.__StdoutThread.die()
        self.__StderrThread.die()
        self.__StdinThread.die()
        if False == self.__KeepAlive:
            return
        self.reset()
        del self.__Command
        self.__Closed = True

    def __del__(self):
        self.close()
