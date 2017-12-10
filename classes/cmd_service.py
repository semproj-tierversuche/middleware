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
import tempfile as TMP
#import io as IO
#from classes.std_capture import StdBuffering
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

#class PipeAsTemporaryFile(SpooledTemporaryFile):
 #   __PackageLength = 1024
  #  __Lock = Lock()
   # __Lock2 = Lock()
    #__File = None
    #__PackageCounter = 0

    #def __init__(self, mode='w+b', packageLength=0, buffering=None, encoding=None, newline=None, suffix=None, prefix=None, dir=None):
    #    if self.__PackageLength < packageLength:
    #        self.__PackageLength = packageLength
    #    super().__init__(mode=mode, buffering=buffering, encoding=encoding, newline=newline, suffix=suffix, prefix=prefix, dir=dir)
    #def read(self):
    #    Return = None
        #self.__Lock.acquire()
        #Return = super().read(*args)
        #self.__Lock.release()
        #return Return
     #   self.__Lock2.acquire()
      #  super().seek(0)
       # Return = self.readPackage()
        #super().turnicate()
        #self.__PackageCounter = 0
        #self.__Lock2.release()
        #return Return

    #def readline(self, *args):
        #Return = None
        #self.__Lock.acquire()
        #Return = self._file.readline(*args)
        #self.__Lock.release()
        #return Return
     #   self.__Lock2.acquire()

      #  self.__Lock2.aquire()

   # def readlines(self, *args):
        #Return = None
        #self.__Lock.acquire()
        #Return = self._file.readlines(*args)
        #self.__Lock.release()
        #return Return
    #    pass

    #def write(self, String):
     #   Return = None
      #  self.__Lock.acquire()
       # self.__Lock2.aquire()
        #Return = super().write(String)
        #self.__Lock2.release()
        #self.__Lock.release()
        #return Return

    #def writelines(self, iterable):
     #   Return = None
      #  self.__Lock.acquire()
       # self.__Lock2.acquire()
        #Return = super().writelines(self, iterable)
        #self.__Lock2.acquire()
        #self.__Lock.release()
        #return Return

    #def writePackage(self, String):
     #   Return = False
      #  if not isinstance(Input, str):
       #     Length = len(str(Input))
        #    Input = str(Input)
        #else:
         #   Length = len(Input)
        #if 0 == Length:
         #   return Return
        #else:
         #   self.__Lock.acquire()
          #  self.__Lock2.acquire()
           # Return = super().write(PipeHelper.padding(len(String), self.__PackageLength) + String)
            #++self.__PackageCounter
            #self.__Lock2.release()
            #self.__Lock.release()
            #return Return

    #def readPackage(self):
     #   Output = ''
      #  Package = None
       # Length = 0
        #Blocks
        #self.__Lock.acquire()
        #try:
         #   Package = super().read(self.__PackageLength)
        #except:
         #   self.__Lock.release()
          #  return None
        #Package = Package.rstrip()
        #if not Package:
         #   self.__Lock.release()
          #  return ''
        #try:
         #   Length = int(Package.decode(Encoding).rstrip())
        #except:
         #   print(Package)
          #  print(super().read(10000))
           # OS._exit(0)
        #Output = super().read(Length)
        #self.__Lock.release()
        #return Output.rstrip()

    #def seek(self):
     #   pass

    #def seekToStart(self):
     #   super().seek(0)

    #def seekToTheEnd(self):
     #   pass

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
    __KeepAlive = False
    #only for keepAlive subprocesses
    __Process = None
    __Stdin = None
    __Stdout = None
    __Stderr = None
    __Delimiter = None
    __Flow = -1

    def __init__(self, Command):
        self.__Lock = Lock()
        self.__Lock2 = Lock()
        self.__Lock3 = Lock()
        self.__Lock4 = Lock()
        self.__Lock5 = Lock()
        self.__Lock6 = Lock()
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
            if 0<self.__Timeout:
                Stdout, Stderr = Process.communicate(Data.encode(self.__TRANSMISSION_ENCODING), timeout=self.__Timeout)
            else:
                Stdout, Stderr = Process.communicate(Data.encode(self.__TRANSMISSION_ENCODING))
        else:
            Process = SubProcess.Popen(Parameter, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            if 0<self.__Timeout:
                Stdout, Stderr = Process.communicate(timeout=self.__Timeout)
            else:
                Stdout, Stderr = Process.communicate(timeout=self.__Timeout)

        return (Stdout,Stderr)
    #Note: nur für Testzwecke
    def __forkedChildProcess(self, Pipe, Key, Data, Stdin):
        Output = []
        PipeHelper.writeLineToPipe(Pipe=Pipe, InputString=str(OS.getpid()), Lock=self.__Lock3, Encoding=self.__TRANSMISSION_ENCODING, DefinedLength=self.__TRANSMISSION_LENGTH)
        Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(Key, Data, Stdin), Data, Stdin)
 #       if not Stdout:#we cannot write nothing
 #           PipeHelper.writeToPipe(Pipe=Pipe, InputString=' ', Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)
 #       else:
        PipeHelper.writeToPipe(Pipe=Pipe, InputString=Stdout.decode(self.__TRANSMISSION_ENCODING), Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
 #       if not Stderr:
 #           PipeHelper.writeToPipe(Pipe=Pipe, InputString=' ', Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING)
 #       else:
        PipeHelper.writeToPipe(Pipe=Pipe, InputString=Stderr.decode(self.__TRANSMISSION_ENCODING), Lock=self.__Lock3, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
        OS.close(Pipe)#we do not need this pipe anymore-> so close it
        OS._exit(0)

    #AutorNote: In späteren Python versionen sollte das folgende obsolet sein -> das lässt ich über subprocess.CREATE_NEW_CONSOLE klären (siehe do Methode)
    def __ptyChildProcess(self, Key, Data, Stdin):
        Output = None
        PipeHelper.writeLineToPipe(Pipe=System.stdout.fileno(),InputString=str(OS.getpid()), Lock=self.__Lock3, Encoding=self.__TRANSMISSION_ENCODING, DefinedLength=self.__TRANSMISSION_LENGTH)
        Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(Key, Data, Stdin), Data, Stdin)
 #       if not Stdout:
 #           Stdout = ' '
 #       if not Stderr:
 #           Stderr = ' '
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
            #Time.sleep(0.01)
            ChildId = PipeHelper.readFromPipeLine(Pipe=FD, Lock=self.__Lock2, Encoding=self.__TRANSMISSION_ENCODING)
            OS.waitpid(int(ChildId), 0)
            Stdout = PipeHelper.readFromPipe(Pipe=FD, Lock=self.__Lock2, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            Stderr = PipeHelper.readFromPipe(Pipe=FD, Lock=self.__Lock2, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
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
            ChildId = PipeHelper.readFromPipeLine(PipeOut, self.__Lock2, self.__TRANSMISSION_ENCODING)
            OS.waitpid(int(ChildId), 0)
            Stdout = PipeHelper.readFromPipe(PipeOut, self.__Lock2, self.__TRANSMISSION_LENGTH, self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            Stderr = PipeHelper.readFromPipe(Pipe=FD, Lock=self.__Lock2, DefinedLength=self.__TRANSMISSION_LENGTH, Encoding=self.__TRANSMISSION_ENCODING, Packageing=PipeHelper.MULTIBLE_PACKAGES)
            OS.close(PipeOut)
            return (Stdout, Stderr)

    def __startPtyProcess(self):
        pass

    def __startFrokProcess(self):
        pass

#    def __startSubPorcess(self, ParameterKey, Data, PasteToStdin):
    def __startSubPorcess(self,PasteToStdin):
        if True == self.__KeepAlive  or not self.__Delimiter:
            return

        print(self.__prepareParameter('', '', True) + "aaa")
        OS._exit(0)
        if True == PasteToStdin:
#            self.__Process = SubProcess.Popen(self.__prepareParameter(ParameterKey, Data, True), stdin=SubProcess.PIPE, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            self.__Process = SubProcess.Popen(self.__prepareParameter('', '', True), stdin=SubProcess.PIPE, stdout=SubProcess.PIPE,stderr=SubProcess.PIPE)
            self.__Stdin = OS.dup(self.__Process.stdin.fileno())
        else:
#            self.__Process = SubProcess.Popen(self.__prepareParameter(ParameterKey, Data, False), stdout=self.__Stdout,stderr=self.__Stderr)
            self.__Process = SubProcess.Popen(self.__prepareParameter('', '', False), stdout=self.__Stdout,stderr=self.__Stderr)
        self.__Stdout = OS.dup(self.__Process.stdout.fileno())
        self.__Stderr = OS.dup(self.__Process.stderr.fileno())

    def __communicator(self, Data):
        self.__Lock5.acquire()
        if  self.__Stdin:
            PipeHelper.writeToDelimter(self.__Stdin, Data, self.__Lock6, self.__Delimiter, self.__TRANSMISSION_LENTGTH, self.__TRANSMISSION_ENCODING)
        Stdout = PipeHelper.readToDelimter(self.__Stdout, self.__Lock6, self.__Delimiter, self.__TRANSMISSION_ENCODING)
        Stderr = PipeHelper.readToDelimter(self.__Stderr, self.__Lock6, self.__Delimiter, self.__TRANSMISSION_ENCODING)
        self.__Lock5.release()
        return (Stdout, Stderr)

    def __close(self):
        if False == self.__KeepAlive:
            return
        self.__Lock5.acquire()
        if self.__Process:
            self.__Process.terminate()
        self.__Lock5.release()


#    def startPermanentProcess(self, ParameterKey, Data, Flag=0x0, PasteToStdin=False):
    def startPermanentProcess(self, Delimiter, Flag=0x0, PasteToStdin=False):
        if True == self.__KeepAlive:
            return False
        if Delimiter and isinstance(Delimiter, string) and 1 == len(Delimiter):
            self.__Delimiter = Delimiter
#        if not isinstance(ParameterKey, str):
#            ParameterKey = str(ParameterKey)
#        if not isinstance(Data, str):
#            Data = str(Data)
        self.__Flow = Flag
        if self.FORK_PTY_PROCESS == Flag:
            pass
        else:
            self.__startSubPorcess(PasteToStdin)
        #else
        self.__KeepAlive = True
        print('hier')

    def do(self, ParameterKey, Data, Flag= 0x0, PasteToStdin=False, Timeout=None):
        if not isinstance(ParameterKey, str):
            ParameterKey = str(ParameterKey)
        if not isinstance(Data, str):
            Data = str(Data)
        if Timeout:
            self.__Timeout = int(Timeout)

        print(self.__KeepAlive)
        if False == self.__KeepAlive:
            if self.FORK_PTY_PROCESS == Flag:
                Stdout, Stderr =  self.__doPTYFork(ParameterKey, Data, PasteToStdin)
# That should do it in newer Python versions
#                Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(ParameterKey, Data, PasteToStdin), Data, PasteToStdin, SubProcess.CREATE_NEW_CONSOLE)
#                return (Stdout.decode(self.__TRANSMISSION_ENCODING), Stderr.decode(self.__TRANSMISSION_ENCODING))
           # elif self.FORK_NO_PROCESS == Flag:
            else:
                Stdout, Stderr = self.__normalChildProcess(self.__prepareParameter(ParameterKey, Data, PasteToStdin), Data, PasteToStdin)
                Stdout = Stdout.decode(self.__TRANSMISSION_ENCODING)
                Stderr = Stderr.decode(self.__TRANSMISSION_ENCODING)
#            nur zu Testzwecken
#            else:
#                return self.__doNormalFork(ParameterKey, Data, PasteToStdin)
        else:
            if self.FORK_PTY_PROCESS == self.__Flow:
                Stdout, Stderr = self.__communicator(Data)
            #else:

            #else:
        self.__Timeout = None
        return (Stdout, Stderr)
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
        self.__close()
        self.__KeepAlive =False

    def __del__(self):
        self.reset()
        self.close()
