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
#        Lock.acquire()
#        OS.write(Pipe, (InputString + "\n").encode(Encoding))
        return PipeHelper.writeToDelimter(Pipe, InputString, Lock, "\n", DefinedLength, Encoding, PipeHelper.MULTIBLE_PACKAGES)
#        Lock.release()

    @staticmethod
    def writeToPipe(Pipe, InputString, Lock, DefinedLength, Encoding, Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        Blocks = 0
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
    def writeToDelimter(Pipe, InputString, Lock, Delimiter, DefinedLength, Encoding, Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        Length = len(InputString)
        Blocks = 0
        LastPackage = ''
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
            Blocks = round(Length/DefinedLength+0.5)
            for X in range(0, Blocks-1):
                Written += OS.write(Pipe, InputString[X*DefinedLength:(X+1)*DefinedLength].encode(Encoding))

            LastPackage = InputString[Blocks-1*DefinedLength:]
            if len(LastPackage)+1 > DefinedLength:
                Written += OS.write(Pipe, (LastPackage[:-1]).encode(Encoding))
                Written += OS.write(Pipe, (LastPackage+Delimiter).encode(Encoding))
            else:
                Written += OS.write(Pipe, (LastPackage+Delimiter).encode(Encoding))
        Lock.release()
        return Written

    @staticmethod
    def readToDelimter(Pipe, Lock, Delimiter, Encoding):
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
            #try:
            #    Package = OS.read(Pipe, DefinedLength)
            #except:
            #    Lock.release()
            #    return None
            #Lock.release()
            return Package.rstrip()
        else:
            #try:
            #    Package = OS.read(Pipe,  DefinedLength)
            #except:
            #    Lock.release()
            #    return None
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
    def readFromPipeLine(Pipe, Lock, Encoding):
        return PipeHelper.readToDelimter(Pipe, Lock, "\n", Encoding)
#        Output = ''
 #       Char = None
#
 #       Lock.acquire()
  #      Char = OS.read(Pipe, 1)
   #     while Char:
    #        Char = Char.decode(Encoding)
     #       if "\n" == Char:
      #          Lock.release()
       #         return Output
        #    Output += Char
         #   try:
          #      Char = OS.read(Pipe, 1)
           # except:
            #    break

    #    Lock.release()
     #   return Output

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
