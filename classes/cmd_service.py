#!/usr/bin/env python3
# requires at least python 3.4

import shlex as Shell
import time as Time
import os as OS
import sys as System
from threading import Lock
import subprocess as SubProcess
import pty as Pty
from collections import OrderedDict
from classes.utils import PipeHelper

class CmdServiceException(Exception):
        Reasons = ['The connection is not established', "Cannot spawn the childproc."]
        ReasonCodes = [0x0, 0x1]
        Reason = 0x0
        NO_CONECTION = 0x0
        NO_CHILD = 0x1
        def __init__(self, ErrorCode):
            self.Reason = ErrorCode
        def __str__(self):
            if self.Reason not in self.ReasonCodes:
                return repr('Unkown error.')
            else:
                return repr(self.Reasons[self.Reason])

class Mutable(object):
    __Value = None

    def __init__(self, Value=None):
        self.__Value = Value

    def set(self, Value):
        self.__Value = Value
        return self

    def assign(self, Value):
        self.__Value = Value
        return self

    def Value(self):
        return self.__Value

class CmdService(object):
    #lock parameter list
    __Timeout = 0
    __PersistentParameter = OrderedDict()
    __ParameterHadChanged = True
    __TRANSMISSION_LENGTH =  1024
    __TRANSMISSION_ENCODING = 'utf-8'

#    FORK_NO_PROCESS = 0x0#not completly the truth
    FORK_NORMAL_PROCESS = 0x1
    FORK_PTY_PROCESS = 0x2
    __PipenameCounter = 0
    __Lock = None
    __Lock2 = None
    __Lock3 = None
    __Lock4 = None
    __Lock5 = None
    __Lock6 = None
    __Lock7 = None
    __KeepAlive = False
    #only for keepAlive subprocesses
    __Process = None
    __ProcessStatus = None
    __Stdin = None
    __Stdout = None
    __Stderr = None
    __Delimiter = None
    __Flow = -1
    __ControllPipeIn = None
    __ControllPipeOut = None
    __OutputPipeIn = None
    __OutputPipeOut = None
    #pipecmds
    __KILL = 0x42
    __NOTHING = 0x0
    __GET_STATUS = 0x23
    __OK = -23

    def __init__(self, Command):
        self.__Lock = Lock()
        self.__Lock2 = Lock()
        self.__Lock3 = Lock()
        self.__Lock4 = Lock()
        self.__Lock5 = Lock()
        self.__Lock6 = Lock()
        self.__Lock7 = Lock()
        self.__PersistentParameter['cmd'] = Command

    def addParameter(self, Key, Value):
        self.__Lock.acquire()
        if Key.strip():
            if 'cmd' == Key:
                Key = '\'' + Key
            self.__PersistentParameter[Key] = Value
        self.__ParameterHadChanged = True
        self.__Lock.release()

    def __prepareParameter(self, ParameterKey, Data, StdIn, _ParameterCache=Mutable()):
        Output = []
        if False == self.__ParameterHadChanged:
            return _ParameterCache.Value()
        Parameter = self.__PersistentParameter
        Output.append(Parameter['cmd'])

        for Key in Parameter:
            if 'cmd' == Key:
                continue
            if '\'cmd' == Key:
                Key = Key[1:]
            if Key.endswith('='):
                Output.appe1nd(Shell.quote( Key + Parameter[Key]))
            else:
                Output.append((Shell.quote(Key + " " + Parameter[Key]))) if Parameter[Key] else  Output.append((Shell.quote(Key)))

        _ParameterCache.set(Output)
        if Data and False == StdIn:
            if ParameterKey.endswith('='):
                Output.append(Shell.quote(ParameterKey + Data))
            else:
                Output.append(Shell.quote((ParameterKey + " " + str(Data))))
        elif not Data and False== StdIn:
            pass#throw error
        elif ParameterKey and True == StdIn:
            Output.append(Shell.quote(ParameterKey))

        self.__ParameterHadChanged = False
        return Output

    def __normalChildProcess(self, Parameter, Data, StdIn, CreationFlag=0):
        Process = None
        Stdin = None
        Stdout = None
        Stderr = None
        if Data and True==StdIn:
            Process = SubProcess.Popen(Parameter, stdin=SubProcess.PIPE, stdout=SubProcess.PIPE, stderr=SubProcess.PIPE, creationflags=CreationFlag)
            if self.__Timeout and 0<self.__Timeout:
                Stdout, Stderr = Process.communicate(Data.encode(self.__TRANSMISSION_ENCODING), timeout=self.__Timeout)
            else:
                Stdout, Stderr = Process.communicate(Data.encode(self.__TRANSMISSION_ENCODING))
        else:
            Process = SubProcess.Popen(Parameter, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            if self.__Timeout and 0<self.__Timeout:
                Stdout, Stderr = Process.communicate(timeout=self.__Timeout)
            else:
                Stdout, Stderr = Process.communicate()

        return (Process.returncode, Stdout, Stderr)
    #Note: nur für Testzwecke
    def __forkedChildProcess(self, Pipe, Key, Data, Stdin):
        PipeHelper.writeLineToPipe(Pipe=Pipe, InputString=str(OS.getpid()), Lock=self.__Lock3, Encoding=self.__TRANSMISSION_ENCODING, DefinedLength=self.__TRANSMISSION_LENGTH)
        ReturnCode, Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(Key, Data, Stdin), Data, Stdin)
        PipeHelper.writeLineToPipe(Pipe=Pipe, InputString=ReturnCode, Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)
        PipeHelper.writeToPipe(Pipe=Pipe, InputString=Stdout.decode(self.__TRANSMISSION_ENCODING), Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
        PipeHelper.writeToPipe(Pipe=Pipe, InputString=Stderr.decode(self.__TRANSMISSION_ENCODING), Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
        OS.close(Pipe)#we do not need this pipe anymore-> so close it
        OS._exit(0)

    #AutorNote: In späteren Python versionen sollte das folgende obsolet sein -> das lässt ich über subprocess.CREATE_NEW_CONSOLE klären (siehe do Methode)
    def __ptyChildProcess(self, Key, Data, Stdin):
        PipeHelper.writeLineToPipe(Pipe=System.stdout.fileno(),InputString=str(OS.getpid()), Lock=self.__Lock3, Encoding=self.__TRANSMISSION_ENCODING, DefinedLength=self.__TRANSMISSION_LENGTH)
        ReturnCode, Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(Key, Data, Stdin), Data, Stdin)
        PipeHelper.writeLineToPipe(Pipe=System.stdout.fileno(),InputString=ReturnCode, Lock=self.__Lock3, Encoding=self.__TRANSMISSION_ENCODING,DefinedLength=self.__TRANSMISSION_LENGTH)
        PipeHelper.writeToPipe(Pipe=System.stdout.fileno(), InputString=Stdout.decode(self.__TRANSMISSION_ENCODING), Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
        PipeHelper.writeToPipe(Pipe=System.stdout.fileno(), InputString=Stderr.decode(self.__TRANSMISSION_ENCODING), Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
        OS._exit(0)

    def __doPTYFork(self, Key, Data, Stdin):
        FD = None
        PId = None
        ChildId = None
        Char = None
        Parameters = ''
        (PId, FD) = Pty.fork()
        if -1 == PId:
            pass
        elif 0 == PId:#we are the child
            self.__ptyChildProcess(Key, Data, Stdin)
        else:#We are the parent
            ChildId = PipeHelper.readLineFromPipe(Pipe=FD, Lock=self.__Lock2, Encoding=self.__TRANSMISSION_ENCODING)
            OS.waitpid(int(ChildId), 0)
            ReturnCode = PipeHelper.readLineFromPipe(Pipe=FD, Lock=self.__Lock2, Encoding=self.__TRANSMISSION_ENCODING)
            Stdout = PipeHelper.readFromPipe(Pipe=FD, Lock=self.__Lock2, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            Stderr = PipeHelper.readFromPipe(Pipe=FD, Lock=self.__Lock2, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            OS.close(FD)
            return (ReturnCode.rstrip(), Stdout, Stderr)

    #Note: nur für Testzwecke
    def __doNormalFork(self, Key, Data, Stdin):

        PId = None
        ChildId = None
        PipeIn = None
        PipeOut = None
        Stderr = ''
        Stdout = ''

        PipeOut, PipeIn = OS.pipe()
        PId = OS.fork()

        if -1 == PId:
            pass#smt gone wrong...very wrong
        elif 0 == PId:#we are the child
            OS.close(PipeOut)
            self.__forkedChildProcess(PipeIn, Key, Data, Stdin)
        else:#We are the parent
            ChildId = PipeHelper.readLineFromPipe(PipeOut, self.__Lock2, self.__TRANSMISSION_ENCODING)
            OS.waitpid(int(ChildId), 0)
            ReturnCode = PipeHelper.readLineFromPipe(Pipe=PipeOut, Lock=self.__Lock2, Encoding=self.__TRANSMISSION_ENCODING)
            Stdout = PipeHelper.readFromPipe(PipeOut, self.__Lock2, self.__TRANSMISSION_LENGTH, self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            Stderr = PipeHelper.readFromPipe(PipeOut, Lock=self.__Lock2, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            OS.close(PipeOut)
            return (ReturnCode.rstrip(), Stdout, Stderr)

    def __startPtyProcess(self, PasteToStdin):
        PId = None

        self.__ControllPipeOut, self.__ControllPipeIn = OS.pipe()
        self.__OutputPipeOut, self.__OutputPipeIn = OS.pipe()
        (PId, FD) = Pty.fork()
        if -1 == PId:
            pass#smt gone wrong...very wrong
        elif 0 == PId:#we are the child
            OS.close(self.__ControllPipeIn)
            OS.close(self.__OutputPipeOut)
            #we have to do this to spawn the child
            PipeHelper.writeLineToPipe(Pipe=System.stdout.fileno(),InputString=str(OS.getpid()), Lock=self.__Lock3, Encoding=self.__TRANSMISSION_ENCODING, DefinedLength=self.__TRANSMISSION_LENGTH)
            self.__startSubPorcess(PasteToStdin)
            self.__controller()
        else:
            OS.close(self.__ControllPipeOut)
            OS.close(self.__OutputPipeIn)
            #we just ignore it
            ChildId = PipeHelper.readLineFromPipe(Pipe=FD, Lock=self.__Lock2, Encoding=self.__TRANSMISSION_ENCODING)
            self.__Stdin = PasteToStdin

    def __startFrokProcess(self, PasteToStdin):
        PId = None

        self.__ControllPipeOut, self.__ControllPipeIn = OS.pipe()
        self.__OutputPipeOut, self.__OutputPipeIn = OS.pipe()
        PId = OS.fork()
        if -1 == PId:
            pass#smt gone wrong...very wrong
        elif 0 == PId:#we are the child
            OS.close(self.__ControllPipeIn)
            OS.close(self.__OutputPipeOut)
            self.__startSubPorcess(PasteToStdin)
            self.__controller()
        else:
            OS.close(self.__ControllPipeOut)
            OS.close(self.__OutputPipeIn)
            self.__Stdin = PasteToStdin

        return

    def __startSubPorcess(self, PasteToStdin):

        if True == PasteToStdin:
            self.__Process = SubProcess.Popen(self.__prepareParameter('', '', True), stdin=SubProcess.PIPE, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
#            self.__Stdin = OS.dup(self.__Process.stdin.fileno())
            self.__Stdin = self.__Process.stdin
        else:
            self.__Process = SubProcess.Popen(self.__prepareParameter('', '', False), stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
#        self.__Stdout = OS.dup(self.__Process.stdout.fileno())
        self.__Stdout = self.__Process.stdout
#        self.__Stderr = OS.dup(self.__Process.stderr.fileno())
        self.__Stderr = self.__Process.stderr

    def __communicator(self, Data):
        self.__Lock5.acquire()
        if self.__Stdin:
            if not Data:
                return (None, None)
            PipeHelper.writeLineToPipe(self.__Stdin.fileno(), Data + self.__Delimiter, self.__Lock6, self.__TRANSMISSION_LENGTH, self.__TRANSMISSION_ENCODING)
 #           self.__Stdin.flush()
        Stdout = PipeHelper.readUntilDelimiterFromPipe(self.__Stdout.fileno(), self.__Lock6, self.__Delimiter, self.__TRANSMISSION_ENCODING)
        Stderr = PipeHelper.readUntilDelimiterFromPipe(self.__Stderr.fileno(), self.__Lock6, self.__Delimiter, self.__TRANSMISSION_ENCODING)
        self.__Stdout.flush()
        self.__Stderr.flush()
        self.__Lock5.release()
        return (Stdout, Stderr)

    def __getProcessStatus(self):
        if not self.__Process.returncode:
            return self.__OK
        else:
            return self.__Process.returncode
    def __getRemoteProcessStatus(self):
        return self.__ProcessStatus

    def __remoteCommunicator(self, Data):
        if True == self.__Stdin and not Data:
            return (None, None)
        PipeHelper.writeLineToPipe(Pipe=self.__ControllPipeIn, InputString=self.__GET_STATUS, Lock=self.__Lock6, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)
        Status = int(PipeHelper.readLineFromPipe(Pipe=self.__OutputPipeOut, Lock=self.__Lock6, Encoding=self.__TRANSMISSION_ENCODING))
        if self.__OK != Status:
            self.__ProcessStatus = Status
            return (None, None)
        PipeHelper.writeLineToPipe(Pipe=self.__ControllPipeIn, InputString=self.__NOTHING, Lock=self.__Lock6, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)
        if True == self.__Stdin and Data:
            PipeHelper.writeToPipe(Pipe=self.__ControllPipeIn, InputString=Data, Lock=self.__Lock6, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
 #           ReturnCode = PipeHelper.readFromPipe(Pipe=self.__OutputPipeOut, Lock=self.__Lock6, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.SINGLE_PACKAGE)
        Stdout = PipeHelper.readFromPipe(Pipe=self.__OutputPipeOut, Lock=self.__Lock6, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
        Stderr = PipeHelper.readFromPipe(Pipe=self.__OutputPipeOut, Lock=self.__Lock6, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
 #           return (ReturnCode, Stdout, Stderr)
        return (Stdout, Stderr)

    def __controller(self):
        Cmd = self.__NOTHING
        Data = None
        Stdin = None
        Stdout = None
        Cmd = int(PipeHelper.readLineFromPipe(Pipe=self.__ControllPipeOut, Lock=self.__Lock7, Encoding=self.__TRANSMISSION_ENCODING))
        if self.__KILL == Cmd:
            self.__close()
            OS._exit(0)
        elif self.__GET_STATUS == Cmd:
            PipeHelper.writeLineToPipe(Pipe = self.__OutputPipeIn, InputString=self.__getProcessStatus(), Lock=self.__Lock7, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)
        else:
            if self.__Stdin:
                Data = PipeHelper.readFromPipe(Pipe=self.__ControllPipeOut, Lock=self.__Lock7, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
                Stdout, Stderr = self.__communicator(Data)
            else:
                Stdout, Stderr = self.__communicator()
 #           PipeHelper.writeToPipe(Pipe=self.__OutputPipeIn, InputString=RetrunCode, Lock=self.__Lock7, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.SINGLE_PACKAGE)
            PipeHelper.writeToPipe(Pipe=self.__OutputPipeIn, InputString=Stdout, Lock=self.__Lock7, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            PipeHelper.writeToPipe(Pipe=self.__OutputPipeIn, InputString=Stderr, Lock=self.__Lock7, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
        self.__controller()

    def __close(self):
        if False == self.__KeepAlive:
            return
        self.__Lock5.acquire()
        if self.__Process:
 #           self.__Process.terminate()
            self.__Process.kill()
            self.__Process = None
        self.__Lock5.release()

    def __remoteClose(self):
        PipeHelper.writeLineToPipe(Pipe=self.__ControllPipeIn, InputString=self.__KILL, Lock=self.__Lock6, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)

    def startPermanentProcess(self, Delimiter, Flag=0x0, PasteToStdin=False):
        if True == self.__KeepAlive:
            return False
        if not Delimiter:
            return False
        if Delimiter and isinstance(Delimiter, str) and 1 == len(Delimiter):
            self.__Delimiter = Delimiter
        self.__Flow = Flag
        self.__ProcessStatus = self.__OK
        self.__KeepAlive = True
        if self.FORK_PTY_PROCESS == Flag:
 #           self.__startFrokProcess(PasteToStdin)
            self.__startPtyProcess(PasteToStdin)
        else:
            self.__startSubPorcess(PasteToStdin)
        #else
        return True

    def do(self, ParameterKey, Data=None, Flag= 0x0, PasteToStdin=False, Timeout=None):
        if not isinstance(ParameterKey, str):
            ParameterKey = str(ParameterKey)
        if not isinstance(Data, str):
            Data = str(Data)
        if Timeout:
            self.__Timeout = int(Timeout)

        if False == self.__KeepAlive:
            if self.FORK_PTY_PROCESS == Flag:
                ReturnCode, Stdout, Stderr = self.__doPTYFork(ParameterKey, Data, PasteToStdin)
# That should do it in newer Python versions
#                Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(ParameterKey, Data, PasteToStdin), Data, PasteToStdin, SubProcess.CREATE_NEW_CONSOLE)
#                Stdout = Stdout.decode(self.__TRANSMISSION_ENCODING)
#                Stderr = Stderr.decode(self.__TRANSMISSION_ENCODING)
           # elif self.FORK_NO_PROCESS == Flag:
#            else:
#                Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(ParameterKey, Data, PasteToStdin), Data, PasteToStdin)
#                Stdout = Stdout.decode(self.__TRANSMISSION_ENCODING)
#                Stderr = Stderr.decode(self.__TRANSMISSION_ENCODING)
#            nur zu Testzwecken
            else:
                ReturnCode, Stdout, Stderr = self.__doNormalFork(ParameterKey, Data, PasteToStdin)
        else:
            if self.FORK_NORMAL_PROCESS == self.__Flow:
                Stdout, Stderr = self.__communicator(Data)
                ReturnCode = self.__getProcessStatus()
            else:
                 Stdout, Stderr = self.__remoteCommunicator(Data)
                 ReturnCode = self.__getRemoteProcessStatus()
            #else:
        self.__Timeout = None
        return (ReturnCode, Stdout, Stderr)
    def printParam(self):
        for Key, Value in self.__PersistentParameter.items():
            print(Key + ": " + Value)

    def reset(self):
        for Key in self.__PersistentParameter:
            if 'cmd' == Key:
                continue
            del self.__PersistentParameter[Key]
        self.__ParameterHadChanged = True

    def removeParameter(self, Key):
        self.__Lock.acquire()
        if Key in self.__PersistentParameter and 'cmd' != Key:
            del self.__PersistentParameter[Key]
        self.__Lock.release()

    def close(self):
        if False == self.__KeepAlive:
            return
        if self.FORK_NORMAL_PROCESS == self.__Flow:
            self.__close()
        else:
            self.__remoteClose()
        self.__KeepAlive =False

    def __del__(self):
        self.reset()
        self.close()
