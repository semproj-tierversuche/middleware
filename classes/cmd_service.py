#!/usr/bin/env python3
# requires at least python 3.4

import pty as PTY
import shlex as Shell
import os as OS
import sys as System
import threading as Threads
import time as Time
from collections import OrderedDict
from classes.utils import PipeHelper, mergeDictionaries as merge, Mutable, StringIOEx as StringIO, LinePipeWriterThread as WriterThread, EoFPipeReaderThread as ReaderThread, DelimiterPermanentPipeReaderThread as ReaderDaemonizedThread, LinePermanentPipeWriterThread as WriterDaemonizedThread
import signal as Signal
#TODO:
#   -> Doku schreiben
class CmdServiceException(Exception):
        __AdditionalInformation = None
        Reasons = ['The connection is not established', "Cannot spawn the childproc.", "The programm is supposed to get data via stdin, but no data was given." "The given data contains illegal value - got ", "A fatal error occures during the fork."]
        ReasonCodes = [0x0, 0x1, 0x2, 0x3, 0x4]
        Reason = 0x0
        NO_CONECTION = 0x0
        NO_CHILD = 0x1
        NO_DATA = 0x2
        ILLEGAL_CONTENT = 0x3
        FATAL_FORK = 0x4

        def __init__(self, ErrorCode, AdditionalStuff=None):
            self.Reason = ErrorCode
            if AdditionalStuff:
                self.__AdditionalInformation = AdditionalStuff
        def __str__(self):
            if self.Reason not in self.ReasonCodes:
                return repr('Unkown error.')
            else:
             #   if self.__AdditionalInformation:
             #       return repr(self.Reasons[self.Reason] + self.__AdditionalInformation)
             #   else:
                return repr(self.Reasons[self.Reason])

class CmdService(object):
    __Timeout = None
    __Enviroment = None
    __EnviromentCache = None
    __EnviromentContext = None
    __EnviromentHasChanged = None
    __Parameter = None
    __ParameterCache = None
    __ParameterContext = None
    __ParameterHasChanged = None
    __TRANSMISSION_LENGTH =  50000#4096
    __TRANSMISSION_ENCODING = None
    __SLEEP_RATE = 0.005
    __SLEEP_EXACT = True
    __RestoreSignals = [1, 2, 3, 4, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 29, 30, 31, 34, 64]
    FORK_NORMAL_PROCESS = 0x1
    FORK_PTY_PROCESS = 0x2

    SET = 0x42
    RESTORE = 0x23
    CLEAR = 0x66

    __ClassLock = Threads.Lock()
    __Lock = None
    __KeepAlive = None
    #only for keepAlive subprocesses
    _ReadFromStdin = None#we just need it one level above
    _FlyingProcess = None
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
    _ReadAtLeast = None
    __EndOfStream = None
    __ReadStderrAnyCase = None
    ReadStdoutAfterKill = None
    ReadStderrAfterKill = None

    def __init__(self, Command, Enviroment=None, Timeout=0, Encoding='utf-8'):
        self.__Parameter = OrderedDict()
        self.__ParameterContext = []
        self.__Lock = Threads.Lock()
        self.__Parameter['cmd'] = Command
        self.__TRANSMISSION_ENCODING = Encoding
        self.__ParameterHasChanged = True
        self._ReadFromStdin = False#we just need it one level above
        self._FlyingProcess = False
        self.__KeepAlive = False
        self.__startThreads()
        if not isinstance(Timeout, int) or 0 >= Timeout:
            self.__Timeout = 0
        else:
            self.__Timeout = self.__prepareTimeout(Timeout)
        if Enviroment and isinstance(Enviroment, dict):
            self.__Enviroment = Enviroment
            self.__EnviromentHasChanged = True
        else:
            self.__Enviroment = {}
            self.__EnviromentHasChanged = False
        self.__EnviromentContext = []
        self.__ReadAtLeast= False

    def __startThreads(self, Delimiter=None, PermanentProcess=False):
        if True == PermanentProcess:
            self.__StdinThread = WriterDaemonizedThread(Pipe=self.__Stdin, Length=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)
            self.__StdoutThread = None
            self.__StderrThread = ReaderDaemonizedThread(Pipe=self.__Stderr, Length=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Delimiter=Delimiter)
        else:
            self.__StdinThread = WriterThread(Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH)
            self.__StdoutThread = ReaderThread(Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH)
            self.__StderrThread = ReaderThread(Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH)
        self.__StdinThread.start()
        if self.__StdoutThread:
            self.__StdoutThread.start()
        self.__StderrThread.start()

    def addParameter(self, Key, Value):
        if Key.strip():
            if 'cmd' == Key:
                Key = '\'' + Key
            self.__Parameter[Key] = Value
        self.__ParameterHasChanged = True

    def addParameters(self, Parameters):
        if Parameters or isinstance(Parametes, dict):
            for Key, Value in Parameters.items():
                self.addParameter(Key, Value)
            return True
        else:
            return False

    def parameterContext(self, Flag):
        Length = len(self.__ParameterContext)
        if not Enviroment and 0 == Length:
            return
        if not self.__ParameterContext:
            self.__ParameterContext.append(self.__Parameter.copy())
            if self.SET == Flag:
                return
        if self.RESTORE == Flag:
            if 1 == Length:
                self.__Parameter = self.__ParameterContext[0].copy()
            else:
                self.__Parameter = self.__ParameterContext.pop()
        elif self.SET == Flag:
            self.__ParameterContext.append(self.__Parameter.copy())
            return
        elif self.CLEAR == Flag:
            if 1 < Length:
                for i in range(1, Length):
                    del self.__ParameterContext[i]
            self.__Parameter = self.__ParameterContext[0].copy()
        self.__ParameterHasChanged = True

    def addEnviromentVariable(self, Key, Value):
        Key = OS.fsencode(Key)
        Value = OS.fsencode(Value)
        if b'=' in Key or b'=' == Value[0:1]:
            return False

        self.__Enviroment[Key] = Value
        self.__EnviromentHasChanged = True
        return True

    def addEnviromentVariables(self, Variables):
        if Variables and isinstance(Variables, dict):
            for Key, Value in Variables.items():
                if False == self.addEnviromentVariable(Key, Value):
                    return False
            return True
        else:
            return False

    def enviromentContext(self, Flag):
        Length = len(self.__EnviromentContext)
        if not self.__Enviroment and 0 == Length:
            return
        if not self.__EnviromentContext:
            self.__EnviromentContext.append(self.__Enviroment.copy())
        if self.RESTORE == Flag:
            if 1 == Length:
                self.__Enviroment = self.__EnviromentContext[0].copy()
            else:
                self.__Enviroment = self.__EnviromentContext.pop()
        elif self.SET == Flag:
            self.__EnviromentContext.append(self.__Enviroment.copy())
            return
        elif self.CLEAR == Flag:
            if 1 < Length:
                for i in range(1, Length):
                    del self.__EnviromentContext[i]
            self.__Enviroment = self.__EnviromentContext[0].copy()
        self.__EnviromentHasChanged = True

    def context(self, Flag):
        self.enviromentContext(Flag)
        self.parameterContext(Flag)

    def restoreFirstContext(self):
        self.enviromentContext(self.CLEAR)
        self.parameterContext(self.CLEAR)

    def __prepareTimeout(self, Timeout):
        if not Timeout or not isinstance(Timeout, int) or 0 >= Timeout:
            return self.__Timeout
        else:
            return Timeout/1000

    def __getParameterCache(self):
        Output = []

        if not self.__Parameter:
            return Output

        if True == self.__ParameterHasChanged:
            Output.append(self.__Parameter['cmd'])
            for Key, Value in self.__Parameter.items():
                if 'cmd' == Key:
                    continue
                if '\'cmd' == Key:
                    Key = Key[1:]
                if Key.endswith('='):
                    Output.append(Shell.quote( Key + Value))
                else:
                    Output.append((Shell.quote(Key + " " + Value))) if Value else Output.append((Shell.quote(Key)))
                    self.__ParameterCache = Output
                    self.__ParameterHasChanged = False
            return Output
        else:
            return self.__ParameterCache.copy()

    def __prepareParameter(self, ParameterKey, Data, Output, StdIn):
        if Data and False == StdIn:
            if ParameterKey.endswith('='):
                Output.append(Shell.quote(ParameterKey + Data))
            else:
                Output.append(Shell.quote((ParameterKey + " " + str(Data))))
        elif not Data and False == StdIn:
            Output.append(Shell.quote((ParameterKey)))
        elif ParameterKey and True == StdIn:
            Output.append(Shell.quote(ParameterKey))
        elif not Data and True == StdIn:
            raise CmdServiceException(CmdServiceException.NO_DATA)
        return Output

    def __getEnviromentCache(self):
        Output = []
        if not self.__EnviromentCache:
            return Output

        if True == self.__EnviromentHasChanged:
            for Key, Value in self.__Enviroment.items():
                Output.append(Key + b'=' + Value)
            self.__EnviromentCache = Output
            self.__EnviromentHasChanged = False
            return Output
        else:
            return self.__EnviromentCache.copy()

    def __doChild(self, Data, Timeout, StdinPipe, StdoutPipe, StderrPipe, Stdout, Stderr, Stdin):
        ChildId = int(PipeHelper.readLineFromPipe(StdoutPipe, Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH))
        self.__StderrThread.do(StderrPipe, Stderr)
        self.__StdoutThread.do(StdoutPipe, Stdout)
        if True == Stdin and Data:
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
            self.__StdoutThread.waitUntilDone(Stdout)
            self.__StderrThread.waitUntilDone(Stderr)
        return ReturnCode

    def __execCMD(self, Stdin, Stdout, Stderr, Parameter, Enviroment, ToStdin):
        #Notelike C we cannot close Std*
        if True == ToStdin:
            OS.dup2(Stdin, System.stdin.fileno())
        OS.dup2(Stdout, System.stdout.fileno())
        OS.dup2(Stderr, System.stderr.fileno())
        PipeHelper.writeLineToPipe(Stdout, str(OS.getpid()), Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH)
        System.stdout.flush()
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
        SleepTime = self.__SLEEP_RATE
        if 0 >= Timeout:#we wait until the process is over -> thats not in every case a good idea
            TrashMe, ReturnCode = OS.waitpid(ProcessId, 0)
        else:
            while True:
                if False == self.__SLEEP_EXACT:
                    Timeout = Timeout/2#we cannot do a shift, otherwise we lose the floatpoint
                    SleepTime = float("{:.4f}".format(Timeout))

                if Slept >= Timeout:
                    OS.kill(ProcessId, Signal.SIGKILL)#==kill -9 pid
                    return self._TIMEOUT
                TrashMe, ReturnCode = OS.waitpid(ProcessId, OS.WNOHANG)
                if 0 == TrashMe:#the child is not terminated by now
                    Slept += SleepTime
                    Time.sleep(SleepTime)
                else:
                    break
        return ReturnCode

    def __restoreSignals(self):
        for SignalNumber in self.__RestoreSignals:
            Signal.signal(SignalNumber, Signal.SIG_DFL)

    def __doExecPreparation(self, Key, Data, Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin):
        if True == RestoreSignals:
            self.__restoreSignals()

        if not Parameter:
            self.__Parameter = merge(self.__Parameter, AdditionalParameter)
            self.__ParameterHasChanged = True
            Parameter = self.__getParameterCache()
        if False == self.__KeepAlive:
            Parameter = self.__prepareParameter(Key, Data, Parameter, Stdin)

        if not Enviroment and AdditionalEnviroment:
            self.__Enviroment = merge(self.__Enviroment, AdditionalEnviroment)
            self.__EnviromentHasChanged = True
            Enviroment = self.__getEnviromentCache()

        return (Parameter, Enviroment)

    def __doPTYForkAndExec(self, Key, Data, Parameter, Timeout, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin):
        FD = None
        PId = None
        ReturnCode = None
        Stderr = []
        Stdout = []
        StdinOut = None
        StdinIn = None

        if True == Stdin:
            StdinOut, StdinIn = OS.pipe()
        StdoutOut, StdoutIn = OS.pipe()
        StderrOut, StderrIn = OS.pipe()

        (PId, FD) = PTY.fork()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            if True == Stdin:
                OS.close(StdinIn)
            OS.close(StdoutOut)
            OS.close(StderrOut)

            Parameter, Enviroment = self.__doExecPreparation(Key, Data, Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin)

            self.__execCMD(StdinOut, StdoutIn, StderrIn, Parameter, Enviroment, Stdin)
        else:#We are the parent
            if True == Stdin:
                OS.close(StdinOut)
            OS.close(StdoutIn)
            OS.close(StderrIn)

            ReturnCode = self.__doChild(Data, Timeout, StdinIn, StdoutOut, StderrOut, Stdout, Stderr, Stdin)

            OS.close(FD)
            OS.close(StdoutOut)
            OS.close(StderrOut)
            if True == Stdin:
                OS.close(StdinIn)
            return (ReturnCode, Stdout[0], Stderr[0])

    def __doForkAndExec(self, Key, Data, Parameter, Timeout, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin):
        PId = None
        ReturnCode = None
        Stderr = []
        Stdout = []
        StdinOut = None
        StdinIn = None

        if True == Stdin:
            StdinOut, StdinIn = OS.pipe()
        StdoutOut, StdoutIn = OS.pipe()
        StderrOut, StderrIn = OS.pipe()

        PId = OS.fork()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            if True == Stdin:
                OS.close(StdinIn)
            OS.close(StdoutOut)
            OS.close(StderrOut)

            Parameter, Enviroment = self.__doExecPreparation(Key, Data, Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin)

            self.__execCMD(StdinOut, StdoutIn, StderrIn, Parameter, Enviroment, Stdin)
        else:#We are the parent
            #closing the Pipeends we do not need
            if True == Stdin:
                OS.close(StdinOut)
            OS.close(StdoutIn)
            OS.close(StderrIn)

            ReturnCode = self.__doChild(Data, Timeout, StdinIn, StdoutOut, StderrOut, Stdout, Stderr, Stdin)

            OS.close(StdoutOut)
            OS.close(StderrOut)
            if True == Stdin:
                OS.close(StdinIn)
            return (ReturnCode, Stdout[0], Stderr[0])

    def __prepareAddtionals(self, AdditionalParameter, AdditionalEnviroment):
        Parameter = None
        if AdditionalParameter and isinstance(AdditionalParameter, dict):
            if 'cmd' in AdditionalParameter:
                AdditionalParameter['\'cmd'] = AdditionalParameter['cmd']
                del AdditionalParameter['cmd']
        else:
            Parameter = self.__getParameterCache()

        if AdditionalEnviroment and isinstance(AddionalEnviroment, dict):
            for Key, Value in AdditionalEnviroment.items():
                Key2 = OS.fsencode(Key)
                Value = OS.fsencode(Value)
                if b'=' in Key2:
                    raise ValueError("Got = as last char of enviroment key " + Key)
                elif b'=' == Value[0:1]:
                    raise ValueError("Got = as first char of as value at enviroment key " + Key)
                else:
                    AdditionalEnviroment[Key2] = Value
                    del AdditionalEnviroment[Key]
                    return (Parameter, AdditionalParameter, None, AdditionalEnviroment)
        elif AdditionalEnviroment:
            raise TypeError("Unexspected type - got " + type(Enviroment) + " and dictonary was exspected.")
        else:
            return (Parameter, AdditionalParameter, self.__getEnviromentCache(), None)

    def startPermanentProcess(self, Delimiter, Flag=0x0, AdditionalParameter=None, AdditionalEnviroment=None, RestoreSignals=False, Stdin=False, StreamEnd=None, ReadStderrAnyCase=False):
        if True == self.__KeepAlive:#we skip if a process is allready running
            return False
        if not Delimiter:#if we have no delimiter, we skip
            return False
        if isinstance(Delimiter, str) and 1 == len(Delimiter):#if we have no valid delimiter -> throw a error
            self.__Delimiter = Delimiter
        else:
            raise ValueError("The given delimiter was invalid.")
        if StreamEnd:
            if isinstance(StreamEnd, str) and 1 == len(StreamEnd):
                self.__EndOfStream = StreamEnd
                self.__ReadAtLeast = True
                self.__ReadStderrAnyCase = ReadStderrAnyCase
            else:
                raise ValueError("The given streamdelimiter was invalid.")

        self.__KeepAlive = True
        self._ReadFromStdin = Stdin
        self._FlyingProcess = True

        self.__StdoutThread.die()
        self.__StderrThread.die()
        self.__StdinThread.die()

        Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment = self.__prepareAddtionals(AdditionalParameter, AdditionalEnviroment)

        if self.FORK_NORMAL_PROCESS == Flag:
            self.__startForkProcess(Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin)
        else:
            self.__startPTYProcess(Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin)
        self.__startThreads(Delimiter=Delimiter, PermanentProcess=True)
        return True

    def __startForkProcess(self, Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin):
        PId = None
        StdinIn = None
        StdinOut = None
        if True == Stdin:
            StdinOut, StdinIn = OS.pipe()
        StdoutOut, StdoutIn = OS.pipe()
        StderrOut, StderrIn = OS.pipe()

        PId = OS.fork()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            if True == Stdin:
                OS.close(StdinIn)
            OS.close(StdoutOut)
            OS.close(StderrOut)

            Parameter, Enviroment = self.__doExecPreparation('', '', Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin)

            self.__execCMD(StdinOut, StdoutIn, StderrIn, Parameter, Enviroment, Stdin)
        else:
            if True == Stdin:
                OS.close(StdinOut)
                self.__Stdin = StdinIn
            OS.close(StdoutIn)
            OS.close(StderrIn)
            self.__Stdout = StdoutOut
            self.__Stderr = StderrOut

            self.__Process = int(PipeHelper.readLineFromPipe(Pipe=self.__Stdout, Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH))

    def __startPTYProcess(self, Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin):
        PId = None
        StdinOut = None
        StdinIn = None

        if True == Stdin:
            StdinOut, StdinIn, = OS.pipe()
        StdoutOut, StdoutIn = OS.pipe()
        StderrOut, StderrIn = OS.pipe()

        (PId, self.__PtyFD) = OS.forkpty()
        if -1 == PId:
            raise CmdServiceException(CmdServiceException.FATAL_FORK)
        elif 0 == PId:#we are the child
            if True == Stdin:
                OS.close(StdinIn)
            OS.close(StdoutOut)
            OS.close(StderrOut)

            Parameter, Enviroment = self.__doExecPreparation('', '', Parameter,  AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, Stdin)

            self.__execCMD(StdinOut, StdoutIn, StderrIn, Parameter, Enviroment, Stdin)
        else:
            if True == Stdin:
                OS.close(StdinOut)
                self.__Stdin = StdinIn
            OS.close(StdoutIn)
            OS.close(StderrIn)

            self.__Stdout = StdoutOut
            self.__Stderr = StderrOut
            self.__Process = int(PipeHelper.readLineFromPipe(Pipe=self.__Stdout, Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH))

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
        Stderr = ['']

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
        if not self.__ReadAtLeast or self.__ReadStderrAnyCase:
            self.__Lock.acquire()
            self.__StderrThread.do(Stderr)
        if True == self._ReadFromStdin:
            self.__StdinThread.do(StringIO(Data+self.__Delimiter))

        if self.__ReadAtLeast:
            if self.__ReadStderrAnyCase:
                self.__StderrThread.waitUntilDone(Stderr)
                self.__Lock.release()

            return (Status, '', Stderr[0])
        Stdout = PipeHelper.readUntilDelimiterFromPipe(Pipe=self.__Stdout, Delimiter=self.__Delimiter, Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH)
        self.__StderrThread.waitUntilDone(Stderr)
        self.__Lock.release()
        return (Status, Stdout, Stderr[0])

    def interruptStream(self):
        if self.__ReadAtLeast:
            Stderr = []
            if True == self._ReadFromStdin:
                self.__StdinThread.do(StringIO(self.__EndOfStream))
            self.__StderrThread.do(Stderr)
            Stdout = PipeHelper.readUntilDelimiterFromPipe(Pipe=self.__Stdout, Delimiter=self.__EndOfStream, Encoding=self.__TRANSMISSION_ENCODING, Length=self.__TRANSMISSION_LENGTH)
            self.__StderrThread.waitUntilDone(Stderr)
            return (Stdout, Stderr[0])

    def __kill(self):
        if False == self.__KeepAlive:
            return
        else:
            if self._OK == self.getStatus():
                if not self.__ReadAtLeast:
                    OS.kill(self.__Process, Signal.SIGKILL)
                else:
                    self.ReadStdoutAfterKill, self.ReadStderrAfterKill = self.interruptStream()

    def do(self, ParameterKey, Data=None, Flag= 0x0, WriteToStdin=False, Timeout=None, AdditionalParameter=None, AdditionalEnviroment=None, RestoreSignals=False):
        if not self.__StderrThread:
            self.__startThreads()

        if not isinstance(ParameterKey, str):
            ParameterKey = str(ParameterKey)

        if not isinstance(Data, str):
            Data = str(Data)

        if True == WriteToStdin and False == self.__KeepAlive:
            Data = StringIO(Data)

        Timeout = self.__prepareTimeout(Timeout)

        if False == self.__KeepAlive:

            Parameter, AdditionalParameter, Enviroment, AdditionalEnviroment = self.__prepareAddtionals(AdditionalParameter, AdditionalEnviroment)

            if self.FORK_PTY_PROCESS == Flag:
                ReturnCode, Stdout, Stderr = self.__doPTYForkAndExec(ParameterKey, Data, Parameter, Timeout, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, WriteToStdin)
            else:
                ReturnCode, Stdout, Stderr = self.__doForkAndExec(ParameterKey, Data, Parameter, Timeout, AdditionalParameter, Enviroment, AdditionalEnviroment, RestoreSignals, WriteToStdin)
        else:
            ReturnCode, Stdout, Stderr = self.__communicator(Data)
            if self.__OSErrorMessage:
                self.__OSErrorMessage = None
        return (ReturnCode, Stdout, Stderr)

    def printParameter(self):
        for Key, Value in self.__Parameter.items():
            print(Key + ": " + Value)

    def printEnviroment(self):
        for Key, Value in self.__Enviroment.items():
            print(Key + ": " + Value)

    def reset(self):
        if self.__Parameter:
            Cmd = self.__Parameter['cmd']
            self.__Parameter.clear()
            self.__Parameter['cmd'] = Cmd
            self.__ParameterHasChanged = True
        if self.__Enviroment:
            self.__Enviroment.clear()
            self.__EnviromentHasChanged=True

    def removeParameter(self, Key):
        if self.__Parameter:
            if 'cmd' == Key:
                Key = '\'cmd'
            if Key in self.__Parameter:
                del self.__Parameter[Key]
                self.__ParameterHasChanged = True

    def removeEnviromentVariable(self, Key):
        if self.__Enviroment:
            if Key in self.__Enviroment:
                del self.__Enviroment[Key]
                self.__EnviromentHasChanged = True

    def stop(self):
        if False == self.__KeepAlive:
            return
        self.__kill()
        if self.__StdoutThread:
            self.__StdoutThread.die()
        self.__StderrThread.die()
        self.__StdinThread.die()
        OS.close(self.__Stdin)
        self.__Stdout = None
        OS.close(self.__Stdout)
        self.__Stdout = None
        OS.close(self.__Stderr)
        self.__Stderr = None
        if self.__PtyFD:
            OS.close(self.__PtyFD)
            self.__PtyFD = None
        self.__KeepAlive = False

    def close(self):
        if self.__StdoutThread:
            self.__StdoutThread.die()
        self.__StderrThread.die()
        self.__StdinThread.die()
        if False == self.__KeepAlive:
            return
        self.__kill()
        self.__KeepAlive =False
        self._FlyingProcess = False
        self._ReadFromStdin = False
        self.__OSErrorMessage = None
        self.__Process = None

        if self.__Stdin:
            OS.close(self.__Stdin)
            self.__Stdin = None
        if self.__Stdout:
            OS.close(self.__Stdout)
            self.__Stdout = None
        if self.__Stderr:
            OS.close(self.__Stderr)
            self.__Stderr = None
        if self.__PtyFD:
            OS.close(self.__PtyFD)
            self.__PtyFD = None
        self.reset()

    def __del__(self):
        self.close()
