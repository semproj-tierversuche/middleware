#!/usr/bin/env python3
# requires at least python 3.4
from io import StringIO
import sys as System
import os as OS

def staticVariable(**KeyWithArguments):
        def decorate(func):
            for Key in KeyWithArguments:
                setattr(func, Key, KeyWithArguments[Key])
                return func
        return decorate

def mergeDictionaries(D1, D2):
        Merge = D1.copy()
        Merge.update(D2)
        return Merge

class PipeHelper(object):
    @staticmethod
    def padding(Input, DefinedLength):
        if not isinstance(Input, str):
            Length = len(str(Input))
            Input = str(Input)
        else:
            Length = len(Input)

        if DefinedLength == Length:
            return Input
        elif DefinedLength < Length:
            Length = int(Length/DefinedLength)
            Length = len(Input)-Length*DefinedLength
        for x in range(Length, DefinedLength):
            Input += ' '
        return Input

    @staticmethod
    def writeLineToPipe(Pipe, InputString, Lock, Encoding):
        Lock.acquire()
        OS.write(Pipe, (InputString + "\n").encode(Encoding))
        Lock.release()

    @staticmethod
    def writeToPipe(Pipe, InputString, Lock, DefinedLength, Encoding, SinglePackage=False):
        Lock.acquire()
        if True == SinglePackage:
            if len(InputString) > DefinedLength:
                OS.write(Pipe, (InputString[0:DefinedLength]).encode(Encoding))
            else:
                OS.write(Pipe, PipeHelper.padding(InputString, DefinedLength).encode(Encoding))
        else:
            OS.write(Pipe, (PipeHelper.padding(len(InputString), DefinedLength) + InputString).encode(Encoding))
        Lock.release()

    @staticmethod
    def readFromPipe(Pipe, Lock, DefinedLength, Encoding, SinglePackage=False):
        Output = ''
        Package = None
        Length = 0
        #Blocks
        Lock.acquire()
        if True == SinglePackage:
            try:
                Package = OS.read(Pipe, DefinedLength)
            except:
                Lock.release()
                return None
            Lock.release()
            return Package.rstrip()
        else:
            try:
                Package = OS.read(Pipe,  DefinedLength)
            except:
                Lock.release()
                return None
            Package = Package.rstrip()
            if not Package:
                Lock.release()
                return ''
            #DebugException
            try:
                Length = int(Package.decode(Encoding).rstrip())
            except:
                print(Package)
                print(OS.read(Pipe, 10000).decode(Encoding))
                OS._exit(0)
# Das wird wohl wichtig, wenn wir nen großen Payload haben und dass sotte von
# der aufrufenden Methode gemacht werden
#            Blocks = round(Length/self.__TRANSMISSION_LENGTH+0.5)
#            for X in range(0, Blocks):
#                Package = OS.read(Pipe,  self.__TRANSMISSION_LENGTH)
#                Output += Package.decode(self.__TRANSMISSION_ENCODING)
            Output = OS.read(Pipe, Length).decode(Encoding)
            Lock.release()
            return Output.rstrip()

    @staticmethod
    def readFromPipeLine(Pipe, Lock, Encoding):
        Output = ''
        Char = None

        Lock.acquire()
        Char = OS.read(Pipe, 1)
        while Char:
            Char = Char.decode(Encoding)
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

class StdBuffering(list):
        __StdoutCapture = StringIO()
        __StderrCapture = StringIO()
        __Stdout = None
        __Stderr = None
        StdoutFlush = True
        StderrFlush = True
        CaptureStdout=True
        CaptureStderr=True

        def __init__(self, Stdout=True, Stderr=True):
            self.CaptureStderr = Stderr
            self.CaptureStdout = Stdout

        def start(self):
            if True == self.CaptureStdout:
                self.__Stdout = System.stdout
                if True == self.StdoutFlush and self.__StderrCapture:
                    self.__StdoutCapture.close()
                    System.stdout = self.__StdoutCapture = StringIO()
                else:
                    System.stdout = self.__StdoutCapture

            if True == self.CaptureStderr:
                self.__Stderr = System.stderr
                if True == self.StderrFlush and self.__StderrCapture:
                    self.__StderrCapture.close()
                    System.sterr = self.__StderrCapture = StringIO()
                else:
                    System.stderr = self.__StderrCapture

        def stop(self):
            if self.__Stdout:
                System.stdout = self.__Stdout
                self.__Stdout = None
            if self.__Stderr:
                System.stderr = self.__Stderr
                self.__Stderr = None

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.stop()

        def getStdout(self):
            return self.__StdoutCapture.getvalue()

        def getStderr(self):
            return self.__StderrCapture.getvalue()

        def __del__(self):
            if self.__StdoutCapture:
                self.__StdoutCapture.close()
            if self.__StdoutCapture:
                self.__StderrCapture.close()
