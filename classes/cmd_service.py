#!/usr/bin/env python3
# requires at least python 3.4

import shlex as Shell
import time as Time
#import io as IO
import os as OS
import sys as System
from threading import Lock
import subprocess as SubProcess
import pty as Pty
#import io as IO
#from classes.std_capture import StdBuffering
from collections import OrderedDict
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

#def staticVariable(**KeyWithArguments):
#        def decorate(func):
#            for Key in KeyWithArguments:
#                setattr(func, Key, KeyWithArguments[Key])
#                return func
#        return decorate
def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
            return func
    return decorate

class Mutable(object):
    __Value = None

    def __init__(self, Value=None):
        self.__Value = Value

    def set(self, Value):
        self.__Value = Value
        return self

    def Assign(self, Value):
        self.__Value = Value
        return self

    def Value(self):
        return self.__Value

class CmdService(object):
    #lock parameter list
    __ParameterLock = False
    __Timeout = 0
    __Parameter = OrderedDict()
    __ParameterHasChanged = True
    __TRANSMISSION_LENGTH =  1024
    __TRANSMISSION_ENCODING = 'utf-8'

#    FORK_NO_PROCESS = 0x0#not completly the truth
    FORK_NORMAL_PROCESS = 0x1
    FORK_PTY_PROCESS = 0x2
    __PipenameCounter = 0
    __Lock = None
    __Lock2 = None
    __Lock3 = None#at the current app not really neccessary
    __Lock4 = None

    def __init__(self, Command, Timeout=None):
        if Timeout:
            self.__Timeout = int(Timeout)
        self.__Lock = Lock()
        self.__Lock2 = Lock()
        self.__Lock3 = Lock()
        self.__Lock4 = Lock()
        self.__Parameter['cmd'] = Command
#        self.addParameter(Configuration['cmd']['name'], '')

    def addParameter(self, Key, Value):
        self.__Lock.acquire()
#        if True ==  self.__ParameterLock:
#             self.__Lock.release()
#             return

        if Key.strip():
            if 'cmd' == Key:
                Key = '\'' + Key
            self.__Parameter[Key] = Value
#            if Key.endswith('='):
#                self.__Parameter.append(Key + Value)
#            else:
#                self.__Parameter.append((Key + " " + Value).strip())
        self.__ParameterHasChanged = True
        self.__Lock.release()


    def __normalChildProcess(self, Parameter, Data, StdIn):
        Process = None
        Stdin = None
        Stdout = None
        Stderr = None

        if Data and True==StdIn:
            Process = SubProcess.Popen(Parameter, stdin=SubProcess.PIPE, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            Stdout, Stderr = Process.communicate(Data.encode(self.__TRANSMISSION_ENCODING))
        else:
            Process = SubProcess.Popen(Parameter, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            Stdout, Stderr = Process.communicate()

        if 0<self.__Timeout:
            Process.wait(self.__Timeout)
        else:
            Process.wait()

        return (Stdout,Stderr)

    def __prepareParameter(self, DataKey, Data, StdIn, EscapeShell=False, _ParameterCache=Mutable()):
        Output = []
        if False == self.__ParameterHasChanged:
            return _ParameterCache.Value()
        Parameter = self.__Parameter
        Output.append(Parameter['cmd'])

        for Key in Parameter:
            if 'cmd' == Key:
                continue
            if '\'cmd' == Key:
                Key = Key[1:]
            if Key.endswith('='):
               Output.append(Shell.quote( Key + Parameter[Key] + "'"))
#                Output.append(Key + Parameter[Key] + "'")
            else:
                Output.append((Shell.quote(Key + " " + Parameter[Key]))) if Parameter[Key] else  Output.append((Shell.quote(Key)))
#                Output.append((Key + " " + Parameter[Key])) if Parameter[Key] else  Output.append(Key)

        if Data and False == StdIn:
            if DataKey.endswith('='):
                Output.append(Shell.quote(DataKey + Data))
            else:
                Output.append(Shell.quote((DataKey + " " + str(Data))))
        elif not Data and False== StdIn:
            pass
        self.__ParameterHasChanged = False
        _ParameterCache.set(Output)
        return Output
    #Note: nur für Testzwecke
    def __forkedChildProcess(self, Pipe, Key, Data, Stdin):
        Output = []

        self.writeLineToPipe(Pipe, str(OS.getpid()), self.__Lock3)
        Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(Key, Data, Stdin), Data, Stdin)
        self.writeToPipe(Pipe, Stdout.decode(self.__TRANSMISSION_ENCODING), self.__Lock3)
        self.writeToPipe(Pipe, Stderr.decode(self.__TRANSMISSION_ENCODING), self.__Lock3)
        OS.close(Pipe)#we do not need this pipe anymore-> so close it
        OS._exit(0)

    def __ptyChildProcess(self, Key, Data, Stdin):
        Output = None

        self.writeLineToPipe(System.stdout.fileno(), str(OS.getpid()), self.__Lock3)
        #ab hier gibt es nur hässliche Lösungen...leider
        #TODO: Denke drüber nache, wie das besser zu lösen ist OHNE Parsen des Outputs und ohne doppelten Fork
        #AutorNote: die exec Familie ersetzt immer den aktuellen Programmrahmen, dass meint auch wenn vorher FD's umgebogen werden, diese wieder auf default zurückfallen...
        Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(Key, Data, Stdin), Data, Stdin)
        self.writeToPipe(System.stdout.fileno(), Stdout.decode(self.__TRANSMISSION_ENCODING), self.__Lock3)
        self.writeToPipe(System.stdout.fileno(), Stderr.decode(self.__TRANSMISSION_ENCODING), self.__Lock3)
        OS._exit(0)

    def padding(self, Input):
        if not isinstance(Input, str):
            Length = len(str(Input))
            Input = str(Input)
        else:
            Length = len(Input)

        if self.__TRANSMISSION_LENGTH == Length:
            return Input
        elif self.__TRANSMISSION_LENGTH < Length:
            Length = int(Length/self.__TRANSMISSION_LENGTH)
            Length = len(Input)-Length*self.__TRANSMISSION_LENGTH
        for x in range(Length, self.__TRANSMISSION_LENGTH):
            Input += ' '
        return Input

    def writeLineToPipe(self, Pipe, InputString, Lock):
        Lock.acquire()
        OS.write(Pipe, (InputString + "\n").encode(self.__TRANSMISSION_ENCODING))
        Lock.release()


    def writeToPipe(self, Pipe, InputString, Lock, SinglePackage=False):
        Lock.acquire()
        if True == SinglePackage:
            OS.write(Pipe, self.padding(InputString).encode(self.__TRANSMISSION_ENCODING))
        else:
            OS.write(Pipe, (self.padding(len(InputString)) + InputString).encode(self.__TRANSMISSION_ENCODING))
        Lock.release()

    def readFromPipe(self, Pipe, Lock, SinglePackage=False):
        Output = ''
        Package = None
        Length = 0
        #Blocks
        Lock.acquire()
        if True == SinglePackage:
            try:
                Package = OS.read(Pipe,  self.__TRANSMISSION_LENGTH)
            except:
                Lock.release()
                return None
            Lock.release()
            return Package.rstrip()
        else:
            try:
                Package = OS.read(Pipe,  self.__TRANSMISSION_LENGTH)
            except:
                Lock.release()
                return None
            Package = Package.rstrip()
            if not Package:
                Lock.release()
                return ''
            Length = int(Package.decode(self.__TRANSMISSION_ENCODING).rstrip())
# Das wird wohl wichtig, wenn wir nen großen Payload haben und dass sotte von
# der aufrufenden Methode gemacht werden
#            Blocks = round(Length/self.__TRANSMISSION_LENGTH+0.5)
#            for X in range(0, Blocks):
#                Package = OS.read(Pipe,  self.__TRANSMISSION_LENGTH)
#                Output += Package.decode(self.__TRANSMISSION_ENCODING)
            Output = OS.read(Pipe, Length).decode(self.__TRANSMISSION_ENCODING)
            Lock.release()
            return Output.rstrip()

    def readFromPipeLine(self, Pipe, Lock):
        Output = ''
        Char = None

        Lock.acquire()
        Char = OS.read(Pipe, 1)
        while Char:
            Char = Char.decode(self.__TRANSMISSION_ENCODING)
            if "\n" == Char:
                Lock.release()
                return Output
            Output += Char
            try:
                Char = OS.read(Pipe, 1)
            except:
                break

        Lock.release()
        return Output

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
            #Time.sleep(0.01)
            ChildId = self.readFromPipeLine(FD, self.__Lock2)
            OS.waitpid(int(ChildId), 0)
            Stdout = self.readFromPipe(FD, self.__Lock2)
            Stderr = self.readFromPipe(FD, self.__Lock2)
            OS.close(FD)
            return (Stdout, Stderr)

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
            ChildId = self.readFromPipeLine(PipeOut, self.__Lock2)
            OS.waitpid(int(ChildId), 0)
            Stdout = self.readFromPipe(PipeOut, self.__Lock2)
            Stderr = self.readFromPipe(PipeOut, self.__Lock2)
            OS.close(PipeOut)
            return (Stdout, Stderr)

    def do(self, ParameterKey, Data, Flag= 0x0, PasteToStdin=False):
        if not self.__Parameter:
            return None

        if self.FORK_PTY_PROCESS == Flag:
            return  self.__doPTYFork(ParameterKey, Data, PasteToStdin)
       # elif self.FORK_NO_PROCESS == Flag:
        else:
            Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(ParameterKey, Data, PasteToStdin), Data, PasteToStdin)
            return (Stdout.decode(self.__TRANSMISSION_ENCODING), Stderr.decode(self.__TRANSMISSION_ENCODING))

        #nur zu Testzwecken
        #else:
 #       return self.__doNormalFork(ParameterKey, Data, PasteToStdin)

    def printParam(self):
        for Key, Value in self.__Parameter.items():
            print(Key + ": " + Value)

    def reset(self):
        self.__Parameter = {}
        self.__ParameterHasChanged = False

    def removeParameter(self, Key):
        self.__Lock.acquire()
        if Key in self.__Parameter and 'cmd' != Key:
            del self.__Parameter[Key]
        self.__Lock.release()
