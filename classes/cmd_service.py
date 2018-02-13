#!/usr/bin/env python3
# requires at least python 3.4

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
    __ParameterReplaces = None
    __TRANSMISSION_LENGTH =  50000#4096
    __TransmissionEncoding = None
    __Closed = None
    __SLEEP_RATE = 0.005
    __SLEEP_EXACT = True
    __RestoreSignals = [1, 2, 3, 4, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 29, 30, 31, 34, 64]
    FORK_NORMAL_PROCESS = 0x1
    FORK_PTY_PROCESS = 0x2

    SET = 0x42
    RESTORE = 0x23
    CLEAR = 0x66
    FIRST = 0x123

    __Lock = None
    __KeepAlive = None
    #only for keepAlive subprocesses
    _ReadFromStdin = None#we just need it one level above
    _FlyingProcess = None
    _FullDeamon = None
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


    def __init__(self, Command, Timeout=0, Encoding='utf-8'):
        self.__Parameter = OrderedDict()
        self.__ParameterContext = []
        self.__ParameterNewKeys = []
        self.__ParameterRemoveals = []
        self.__ParameterReplaces = []
        self.__ParameterHasChanged = True

        self.__Lock = Threads.Lock()
        self.__Closed = False
        if not Command:
            raise CmdServiceException(CmdServiceException.NO_COMMAND)
        else:
            self.setCommand(Command, Timeout, Encoding)
        self._ReadFromStdin = False#we just need it one level above
        self._FlyingProcess = False
        self.__KeepAlive = False
        self._FullDeamon = False
        self.__startThreads()

        self.__Enviroment = OrderedDict()
        self.__EnviromentHasChanged = False
        self.__EnviromentContext = []
        self.__EnviromentNewKeys = []
        self.__EnviromentRemoveals = []
        self.__EnviromentReplaces = []

    def __startThreads(self, Delimiter=None, PermanentProcess=False):
        if True == PermanentProcess:
            self.__StdinThread = WriterDaemonizedThread(Pipe=self.__Stdin,\
                                                        Length=self.__TRANSMISSION_LENGTH,\
                                                        Encoding=self.__TransmissionEncoding)
            self.__StdoutThread = None
            self.__StderrThread = ReaderDaemonizedThread(Pipe=self.__Stderr,\
                                                         Length=self.__TRANSMISSION_LENGTH,\
                                                         Encoding=self.__TransmissionEncoding, Delimiter=Delimiter)
        else:
            self.__StdinThread = WriterThread(Encoding=self.__TransmissionEncoding, Length=self.__TRANSMISSION_LENGTH)
            self.__StdoutThread = ReaderThread(Encoding=self.__TransmissionEncoding, Length=self.__TRANSMISSION_LENGTH)
            self.__StderrThread = ReaderThread(Encoding=self.__TransmissionEncoding, Length=self.__TRANSMISSION_LENGTH)
        self.__StdinThread.start()
        if self.__StdoutThread:
            self.__StdoutThread.start()
        self.__StderrThread.start()

    def setCommand(self, Command, Timeout=0, Encoding='utf-8'):
        if not Command:
            return

        self.__Command = Command

        if not isinstance(Timeout, int) or 0 >= Timeout:
            self.__Timeout = 0
        else:
            self.__Timeout = self.__prepareTimeout(Timeout)

        if Encoding and 'utf-8' != Encoding:
            self.__TransmissionEncoding = Encoding
        else:
              self.__TransmissionEncoding = 'utf-8'

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

#    def __splitParameter(self, Parameter):
#        White = -1
#        Equal = -1
#        for i in range(0, len(Parameter)):
#            if ' ' == Parameter[i] and -1 == White:
#                White = i
#            elif '=' == Parameter[i] and -1 == Equal:
#                Equal = i
#
#        return (White, Equal)

    #add and replace
    def addParameter(self, Parameter):

        def isReplace(Param):
            i = 0
            for Key, Values in self.__Parameter:
                if Key == Param:
                    if i not in self.__ParameterReplaces:
                        self.__ParameterReplaces.append(i)
                    break
                i += 1
            else:
                self.__ParameterNewKeys.append(Param)

        Parameter = Parameter.strip()
        if not Parameter:
            return

        Parameter = Shell.split(Parameter)
        for Param in Parameter:
#            if 1<len(Param):
#                isReplace(Param[0])
#                self.__Parameter[Param[0]] = (Param[1], 1)
#                return
#            if "'" == Param[0] or '"' == Param[0]:
#                State = 1
#            else:
#                State = 2
#
#            Param = Param[0].split('=',1)
#            if 1<len(Param):
#                isReplace(Param[0])
#                self.__Parameter[Param[0]] = (Param[1], State+2)
#                return
#            else:
#                Param = Param[0]
#
#            isReplace(Param)
            if Param not in self.__Parameter:
                self.__Parameter[Param] = ''
                self.__ParameterNewKeys.append(Param)
                return True
            else:
                return False

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

    def __getParameterCache(self):
        Output = []

        if not self.__Parameter:
            return Output

        #build completely new
        if True == self.__ParameterHasChanged:
            Output.append(Shell.quote(self.__Command))
            for Key, Value in self.__Parameter.items():
                if Key in self.__ParameterRemoveals:
                    del self.__Parameter[Key]
                    continue
#                Value, State = Value
#                if 0 == State:
                Output.append(Shell.quote(Key))
#                    continue
#                elif 1 == State:
#                    Output.append(Shell.quote(Key + ' ' + Value))
#                    continue
#                else:
#                    if 1 == State&1:
#                        Output.append(Shell.quote(Value[-1] + Key + '=' + Value)
#                    else:
#                        Output.append(Shell.quote(Key + '=' + Value))
            self.__ParameterRemoveals = []
            self.__ParameterNewKeys = []
            self.__ParameterReplaces = []
            self.__ParameterHasChanged = False
            self.__ParameterCache = Output
            return self.__ParameterCache.copy()
       #replace
#       if self.__ParameterReplaces:
#           i = 0
#           for Key, Value in self.__Parameter.items():
#               if i in self.__ParameterReplaces and Key not in self.__ParameterRemoveals:
#                   Value, State = Value
#                   if 0 == State:
#                       self.__ParameterCache[i] = Shell.quote(Key)
#                   elif 1 == State:
#                       self.__ParameterCache[i] = Shell.quote(Key + ' ' + Value)
#                   else:
#                       self.__ParameterCache[i] = Shell.quote(Key + '=' + Value)
#
#               i +=1
#           self.__ParameterReplaces = []

       #insert
       if self.__ParameterNewKeys:
           while self.__ParameterNewKeys:
               Key = self.__ParameterNewKeys.pop(0)
               if Key in self.__ParameterRemoveals:
                   del self.__ParameterRemoveals[Key]
                   del self.__Parameter[Key]
                   continue
#               Value, State = self.__Parameter[Key]
#               if 0 == State:
                self.__ParameterCache.append(Shell.quote(Key))
#                   continue
#               elif 1 == State:
#                   self.__ParameterCache.append(Shell.quote(Key + ' ' + Value))
#                   continue
#               else:
#                   self.__ParameterCache.append(Shell.quote(Key + '=' + Value))

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
        if not self__EnviromentCache:
            return Output

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
        if not Timeout or not isinstance(Timeout, int) or 0 >= Timeout:
            return self.__Timeout
        else:
            return Timeout/1000

    def __doChild(self, Data, Timeout, StdinPipe, StdoutPipe, StderrPipe, Stdout, Stderr, Stdin):
        ChildId = int(PipeHelper.readLineFromPipe(StdoutPipe, Encoding=self.__TransmissionEncoding))
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
        PipeHelper.writeLineToPipe(Stdout, str(OS.getpid()), Encoding=self.__TransmissionEncoding, Length=self.__TRANSMISSION_LENGTH)
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
        if 0 <= Timeout:#we wait until the process is over -> thats not in every case a good idea
            TrashMe, ReturnCode = OS.waitpid(ProcessId, 0)
        else:
            while True:
#                if False == self.__SLEEP_EXACT:
#                    Timeout = Timeout/2#we cannot do a shift, otherwise we lose the floatpoint
#                    SleepTime = float("{:.4f}".format(Timeout))

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

    def __doExecPreparation(self, AdditionalParameter, AdditionalEnviroment, RestoreSignals):
        if True == RestoreSignals:
            self.__restoreSignals()

        Parameter = self.__getParameterCache()
        if AdditionalParameter:
            for Param in AdditionalParameter:
                Parameter.append(Shell.quote(Param))

        Enviroment = self.__getEnviromentCache()
        if AdditionalEnviroment:
            for Key, Value in AdditionalEnviroment:
                Enviroment.append(Key + b'=' + Value)

        return (Parameter, Enviroment)

    def __doPTYForkAndExec(self, Data, Timeout, AdditionalParameter, AdditionalEnviroment, RestoreSignals, Stdin):
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

            Parameter, Enviroment = self.__doExecPreparation(AdditionalParameter, AdditionalEnviroment, RestoreSignals)

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

    def __doForkAndExec(self, Data, Timeout, AdditionalParameter, AdditionalEnviroment, RestoreSignals, Stdin):
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

            Parameter, Enviroment = self.__doExecPreparation(AdditionalParameter, AdditionalEnviroment, RestoreSignals)
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
        AdditionalParameterOut = []
        AdditionalEnviromentOut = OrderedDict()
        if AdditionalParameter:
            AdditionalParameter = AdditionalParameter.strip()
            Parameter = Shell.split(AdditionalParameter)
            for Param in Parameter:
                if Param in AdditionalParameterOut or in self.__Parameter:
                    continue
                else:
                    AdditionalParameterOut.append(Param)

        if AdditionalEnviroment and isinstance(AddionalEnviroment, dict):
            for Key, Value in AdditionalEnviroment.items():
                Key2 = OS.fsencode(Key)
                Value = OS.fsencode(Value)
                if b'=' in Key2:
                    raise ValueError("Got = as last char of enviroment key " + Key)
                elif b'=' == Value[0:1]:
                    raise ValueError("Got = as first char of as value at enviroment key " + Key)
                else:
                    if Key2 not in self.__Enviroment and Key2 not in AdditionalEnviromentOut:
                        AdditionalEnviromentOut[Key2] = Value
                        del AdditionalEnviroment[Key]
        return (AdditionalParameterOut, AdditionalEnviromentOut)

    def startPermanentProcess(self, Delimiter, Flag=0x0, AdditionalParameter=None,\
                              AdditionalEnviroment=None, RestoreSignals=False,\
                              Stdin=False):
        if True == self.__KeepAlive:#we skip if a process is allready running
            return False
        if not Delimiter:#if we have no delimiter, we skip
            return False
        if isinstance(Delimiter, str) and 1 == len(Delimiter):#if we have no valid delimiter -> throw a error
            self.__Delimiter = Delimiter
        else:
            raise ValueError("The given delimiter was invalid.")

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

            Parameter, Enviroment = self.__doExecPreparation('', '', Parameter, AdditionalParameter,\
                                                             Enviroment, AdditionalEnviroment,\
                                                             RestoreSignals, Stdin)

            self.__execCMD(StdinOut, StdoutIn, StderrIn, Parameter, Enviroment, Stdin)
        else:
            if True == Stdin:
                OS.close(StdinOut)
                self.__Stdin = StdinIn
            OS.close(StdoutIn)
            OS.close(StderrIn)
            self.__Stdout = StdoutOut
            self.__Stderr = StderrOut

            self.__Process = int(PipeHelper.readLineFromPipe(Pipe=self.__Stdout,\
                                                             Encoding=self.__TransmissionEncoding))

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
            self.__Process = int(PipeHelper.readLineFromPipe(Pipe=self.__Stdout,\
                                                             Encoding=self.__TransmissionEncoding))

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
            self.__StdinThread.do(StringIO(Data+self.__Delimiter))
        Stdout = PipeHelper.readUntilDelimiterFromPipe(Pipe=self.__Stdout,\
                                                       Delimiter=self.__Delimiter,\
                                                       Encoding=self.__TransmissionEncoding,\
                                                       Length=self.__TRANSMISSION_LENGTH)
        self.__StderrThread.waitUntilDone(Stderr)
        self.__Lock.release()
        return (Status, Stdout, Stderr[0])

    def __kill(self):
        if False == self.__KeepAlive:
            return
        else:
            if self._OK == self.getStatus():
                OS.kill(self.__Process, Signal.SIGKILL)

    def do(self, StdinData=None, AdditionalParameter=None, AdditionalEnviroment=None,\
           Timeout=None, RestoreSignals=False, Flag=0x0):

        if True == self.__Closed:
            return None

        if StdinData and False == self.__KeepAlive:
            Data = BytesIO(StdinData)
            WriteToStdin = True
        else:
            Date = None

        Timeout = self.__prepareTimeout(Timeout)

        if False == self.__KeepAlive:
            Timeout = self.__prepareTimeout(Timeout)
            self.apply()

            AdditionalParameter, AdditionalEnviroment = self.__prepareAddtionals(AdditionalParameter, AdditionalEnviroment)

            if self.FORK_PTY_PROCESS == Flag:
                ReturnCode, Stdout, Stderr = self.__doPTYForkAndExec(Data, Timeout,\
                                                                     AdditionalParameter,\
                                                                     AdditionalEnviroment,\
                                                                     RestoreSignals, WriteToStdin)
            else:
               ReturnCode, Stdout, Stderr = self.__doForkAndExec(Data, Timeout,\
                                                                 AdditionalParameter,\
                                                                 AdditionalEnviroment,\
                                                                 RestoreSignals, WriteToStdin)
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
        if self.__StdoutThread:
            self.__StdoutThread.die()
            self.__StdoutThread = None
        if True == self.__StderrThread._IsActive:
            self.__StderrThread.die()
            self.__StderrThread = None
        if True == self.__StdinThread._IsActive:
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
        self._FlyingProcess = False
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
