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
    SINGLE_PACKAGE = 0x0
    CONTINUOUS_PACKAGE = 0x1
    MULTIBLE_PACKAGES = 0x2
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
    def writeLineToPipe(Pipe, InputString, Lock, DefinedLength, Encoding):
        return PipeHelper.writeWithDelimterToPipe(Pipe, InputString, Lock, "\n", DefinedLength, Encoding, PipeHelper.MULTIBLE_PACKAGES)

    @staticmethod
    def writeToPipe(Pipe, InputString, Lock, DefinedLength, Encoding, Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        Blocks = 0
        if not isinstance(InputString, str):
            InputString = str(InputString)
        Length = len(InputString)
        Lock.acquire()
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            if Length > DefinedLength:
                Written = OS.write(Pipe, (InputString[0:DefinedLength]).encode(Encoding))
            else:
                Written = OS.write(Pipe, PipeHelper.padding(InputString, DefinedLength).encode(Encoding))
        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
            Written = OS.write(Pipe, (PipeHelper.padding(Length, DefinedLength) + InputString).encode(Encoding))
        else:
            Blocks = round(Length/DefinedLength+0.5)
            Written = OS.write(Pipe, PipeHelper.padding(Length, DefinedLength).encode(Encoding))
            for X in range(0, Blocks):
                if X+1 < Blocks:
                    Written += OS.write(Pipe, InputString[X*DefinedLength:(X+1)*DefinedLength].encode(Encoding))
                else:
                    Written += OS.write(Pipe, PipeHelper.padding(InputString[X*DefinedLength:], DefinedLength).encode(Encoding))
        Lock.release()
        return Written

    @staticmethod
    def writeWithDelimterToPipe(Pipe, InputString, Lock, Delimiter, DefinedLength, Encoding, Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        if not isinstance(InputString, str):
            InputString = str(InputString)
        Length = len(InputString)+1
        Blocks = 0
        if 0 == Delimiter:
            return 0
        Lock.acquire()
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            --DefinedLength
            if Length > DefinedLength:
                Written = OS.write(Pipe, (InputString[0:DefinedLength] + Delimiter).encode(Encoding))
            else:
                Written = OS.write(Pipe, (InputString + Delimiter).encode(Encoding))
        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
            Written = OS.write(Pipe, (InputString + Delimiter).encode(Encoding))
        else:
            InputString += Delimiter
            Blocks = round(Length/DefinedLength+0.5)
            for X in range(0, Blocks):
                if X+1 < Blocks:
                    Written += OS.write(Pipe, InputString[X*DefinedLength:(X+1)*DefinedLength].encode(Encoding))
                else:
                    Written += OS.write(Pipe, InputString[X*DefinedLength:].encode(Encoding))
        Lock.release()
        return Written

    @staticmethod
    def readUntilDelimiterFromPipe(Pipe, Lock, Delimiter, Encoding):
        Output = ''
        Chars = None
        Lock.acquire()
        Char = OS.read(Pipe, 1)
        EncodedDelimiter = Delimiter.encode(Encoding)
        while True:
            if EncodedDelimiter == Char:
                break
            Output += Char.decode(Encoding)
            try:
                Char = OS.read(Pipe, 1)
            except:
                break
        Lock.release()
        return Output


    @staticmethod
    def readFromPipe(Pipe, Lock, DefinedLength, Encoding, Packageing=CONTINUOUS_PACKAGE):
        Output = ''
        Package = None
        Length = 0
        Blocks = 0
        Lock.acquire()
        try:
            Package = OS.read(Pipe, DefinedLength).decode(Encoding)
        except:
            Lock.release()
            return None
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            return Package.rstrip()
        else:
            Package = Package.rstrip()
            if not Package:
                Lock.release()
                return ''
            #DebugException
            try:
                Length = int(Package)
            except:
                print(OS.read(Pipe, 10000).decode(Encoding))#throw
                OS._exit(0)
            if PipeHelper.MULTIBLE_PACKAGES == Packageing:
# Das wird wohl wichtig, wenn wir nen großen Payload haben und dass sotte von
# der aufrufenden Methode gemacht werden
                Blocks = round(Length/DefinedLength+0.5)
                for X in range(0, Blocks):
                    Package = OS.read(Pipe,  DefinedLength)
                    Output += Package.decode(Encoding)
            else:
                Output = OS.read(Pipe, Length).decode(Encoding)
            Lock.release()
            return Output.rstrip()

    @staticmethod
    def readLineFromPipe(Pipe, Lock, Encoding):
        return PipeHelper.readUntilDelimiterFromPipe(Pipe, Lock, "\n", Encoding)

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
