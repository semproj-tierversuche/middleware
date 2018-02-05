#!/usr/bin/env python3
# requires at least python 3.4
from io import StringIO
import sys as System
import os as OS
import threading as Threads
import time as Time

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

class Mutable(object):
    __Value = None

    def __init__(self):
        self.__Value = None

    def set(self, Value):
        self.__Value = Value
        return self

    def value(self):
        return self.__Value

class PipeReaderThread(Threads.Thread):
    _Encoding = None
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __PIPE = 0
    __OUTPUT = 1
    __DIE = 2

    def __init__(self, Length, Encoding):
        self._Encoding = Encoding
        self._Length = Length
        self.__Lock = Threads.Lock()
        self.__DoLock = Threads.Lock()
        self.__Cache = [None, None, False]
        Threads.Thread.__init__(self)
        self.daemon = True
        self._IsActive = True

    def run(self):
        self.__Lock.acquire()
        self.__controller()

    def __controller(self, Pipe=None, Output=None, Die=False):
        TmpPipe = None
        TmpOutput = None

        if isinstance(Pipe, int) and isinstance(Output, list):
            self.__DoLock.acquire()
            self.__Cache[self.__PIPE] = Pipe
            self.__Cache[self.__OUTPUT] = Output
            self.__Lock.release()
            return

        if True == Die:
            self.__DoLock.acquire()
            self._IsActive = False
            self.__Cache[self.__DIE] = True
            self.__Lock.release()
            return

        while True:
            self.__Lock.acquire()
            if True == self.__Cache[self.__DIE]:
                self.__DoLock.release()
                return

            TmpPipe = self.__Cache[self.__PIPE]
            TmpOutput = self.__Cache[self.__OUTPUT]
            self.__Cache[self.__PIPE] = None
            self.__Cache[self.__OUTPUT] = None
            self.__readRelease(TmpPipe, TmpOutput)

    def __readRelease(self, Pipe, Output):
        self.__DoLock.release()
        self._read(Pipe, Output)

    def _read(self, Pipe, Output):
        pass

    def waitUntilDone(self, Output, startLen=0):
        while(True):
            if startLen == len(Output):
                Time.sleep(0)
            else:
                break

    def do(self, Pipe, Output):
        self.__controller(Pipe=Pipe, Output=Output)

    def die(self):
        if True == self._IsActive:
            self.__controller(Die=True)

    def __del__(self):
        self.die()

class PermanentPipeReaderThread(Threads.Thread):
    _Pipe = None
    _Encoding = None
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __OUTPUT = 0
    __DIE = 1

    def __init__(self, Pipe, Length, Encoding):
        self._Encoding = Encoding
        self._Length = Length
        self._Pipe = Pipe
        self.__Lock = Threads.Lock()
        self.__DoLock = Threads.Lock()
        Threads.Thread.__init__(self)
        self.daemon = True
        self._IsActive = True
        self.__Cache = [None, False]

    def run(self):
        self.__Lock.acquire()
        self.__controller()

    def __controller(self, Output=None, Die=False):
        TmpOutput = None

        if isinstance(Output, list):
            self.__DoLock.acquire()
            self.__Cache[self.__OUTPUT] = Output
            self.__Lock.release()
            return

        if True == Die:
            self.__DoLock.acquire()
            self._IsActive = False
            self.__Cache[self.__DIE] = True
            self.__Lock.release()
            return

        while True:
            self.__Lock.acquire()
            if True == self.__Cache[self.__DIE]:
                self.__DoLock.release()
                return

            TmpOutput = self.__Cache[self.__OUTPUT]
            self.__Cache[self.__OUTPUT] = None
            self.__readRelease(TmpOutput)

    def __readRelease(self, Output):
        self.__DoLock.release()
        self._read(Output)

    def _read(self, Output):
        pass

    def waitUntilDone(self, Output, startLen=0):
        while(True):
            if startLen == len(Output):
                Time.sleep(0)
            else:
                break

    def do(self, Output):
        self.__controller(Output=Output)

    def die(self):
        if True == self._IsActive:
            self.__controller(Die=True)

    def __del__(self):
        self.die()

class PipeWriterThread(Threads.Thread):
    _Encoding = None
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __PIPE = 0
    __TOWRITE = 1
    __DIE = 2

    def __init__(self, Length, Encoding):
        self._Encoding = Encoding
        self._Length = Length
        self.__Lock = Threads.Lock()
        self.__DoLock = Threads.Lock()
        Threads.Thread.__init__(self)
        self.daemon = True
        self._IsActive = True
        self.__Cache = [None, None, False]

    def run(self):
        self.__Lock.acquire()
        self.__controller()

    def __controller(self, Pipe=None, ToWrite=None, Die=False):
        TmpPipe = None
        TmpStringBuffer = None

        if isinstance(Pipe, int) and isinstance(ToWrite, StringIOEx):
            self.__DoLock.acquire()
            self.__Cache[self.__PIPE] = Pipe
            self.__Cache[self.__TOWRITE] = ToWrite
            self.__Lock.release()
            return

        if True == Die:
            self.__DoLock.acquire()
            self._IsActive = False
            self.__Cache[self.__DIE] = True
            self.__Lock.release()
            return

        while True:
            self.__Lock.acquire()
            if True == self.__Cache[self.__DIE]:
                self.__DoLock.release()
                return

            TmpPipe = self.__Cache[self.__PIPE]
            TmpStringBuffer = self.__Cache[self.__TOWRITE]
            self.__Cache[self.__PIPE] = None
            self.__Cache[self.__TOWRITE] = None
            self.__writeRelease(TmpPipe, TmpStringBuffer)

    def __writeRelease(self, Pipe, ToWrite):
        self.__DoLock.release()
        self._write(Pipe, ToWrite)

    def _write(self, Pipe, ToWrite):
        pass

    def do(self, Pipe, ToWrite):
        self.__controller(Pipe=Pipe, ToWrite=ToWrite)

    def die(self):
        if True == self._IsActive:
            self.__controller(Die=True)

    def __del__(self):
        self.die()

class PermanentPipeWriterThread(Threads.Thread):
    _Pipe = None
    _Encoding = None
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __TOWRITE = 0
    __DIE = 1

    def __init__(self, Pipe, Length, Encoding):
        self._Pipe = Pipe
        self._Encoding = Encoding
        self._Length = Length
        self.__Lock = Threads.Lock()
        self.__DoLock = Threads.Lock()
        Threads.Thread.__init__(self)
        self.daemon = True
        self._IsActive = True
        self.__Cache = [None, False]

    def run(self):
        self.__Lock.acquire()
        self.__controller()

    def __controller(self, ToWrite=None, Die=False, _ControllStore=Mutable()):
        TmpStringBuffer = None

        if isinstance(ToWrite, StringIOEx):
            self.__DoLock.acquire()
            self.__Cache[self.__TOWRITE] = ToWrite
            self.__Lock.release()
            return

        if True == Die:
            self.__DoLock.acquire()
            self._IsActive = False
            self.__Cache[self.__DIE] = True
            self.__Lock.release()
            return

        while True:
            self.__Lock.acquire()
            if True == self.__Cache[self.__DIE]:
                self.__DoLock.release()
                return

            TmpStringBuffer = self.__Cache[self.__TOWRITE]
            self.__Cache[self.__TOWRITE] = None
            self.__writeRelease(TmpStringBuffer)

    def __writeRelease(self, ToWrite):
        self.__DoLock.release()
        self._write(ToWrite)

    def _write(self, ToWrite):
        pass

    def do(self, ToWrite):
        self.__controller(ToWrite=ToWrite)

    def die(self):
        if True == self._IsActive:
            self.__controller(Die=True)

    def __del__(self):
        self.die()

class PipeException(Exception):
    __Reasons = ['Unexspected result, while reading pipe. Got: {}', 'The given length must at least as long as the delimiter.']
    __ReasonCodes = [0x0, 0x1]
    __Reason = None
    __Additional = None
    _UNEXSPECTED_RESULT = 0x0
    _INVALID_LENGTH = 0x1

    def __int__(self, Reason, Additional=None):
        self.__Reason = Reason
        self.__Additional = Additional

    def __str__(self):
        if self.__Reason not in self.__ReasonCodes:
            return repr('Unkown error.')
        else:
            if self._UNEXSPECTED_RESULT == self.__Reason:
                return repr(self.__Reasons[self.__Reason].format(self.__Additional))
            else:
                return repr(self.__Reasons[self.__Reason])

class PipeHelper(object):
    SINGLE_PACKAGE = 0x0
    CONTINUOUS_PACKAGE = 0x1
    MULTIBLE_PACKAGES = 0x2
    @staticmethod
    def padding(Input, Length):
        if not isinstance(Input, str):
            Length = len(str(Input))
            Input = str(Input)
        else:
            Length = len(Input)

        if Length == Length:
            return Input
        elif Length < Length:
            Length = int(Length/Length)
            Length = len(Input)-Length*Length
        for x in range(Length, Length):
            Input += ' '
        return Input

    @staticmethod
    def write(Pipe, InputString, Encoding='utf-8'):
        if not isinstance(InputString, str):
            InputString = str(InputString)
        return OS.write(Pipe, InputString.encode(Encoding))

    @staticmethod
    def writePackagesToPipe(Pipe, InputString, Length=1024, Encoding='utf-8', Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        Blocks = 0
        if not isinstance(InputString, str):
            InputString = str(InputString)
        Length = len(InputString)
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            if Length > Length:
                Written = OS.write(Pipe, (InputString[0:Length]).encode(Encoding))
            else:
                Written = OS.write(Pipe, PipeHelper.padding(InputString, Length).encode(Encoding))
        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
            Written = OS.write(Pipe, (PipeHelper.padding(Length, Length) + InputString).encode(Encoding))
        else:
            Blocks = round(Length/Length+0.5)
            Written = OS.write(Pipe, PipeHelper.padding(Length, Length).encode(Encoding))
            for X in range(0, Blocks):
                if X+1 < Blocks:
                    Written += OS.write(Pipe, InputString[X*Length:(X+1)*Length].encode(Encoding))
                else:
                    Written += OS.write(Pipe, PipeHelper.padding(InputString[X*Length:], Length).encode(Encoding))
        return Written

    @staticmethod
    def writeWithDelimterToPipe(Pipe, InputString, Delimiter, Length=1024, Encoding='utf-8', Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        if not isinstance(InputString, str):
            InputString = str(InputString)
        InputLength = len(InputString)+len(Delimiter)
        Blocks = 0
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            if Length < InputLength:
                Written = OS.write(Pipe, (InputString[0:Length] + Delimiter).encode(Encoding))
            else:
                Written = OS.write(Pipe, (InputString + Delimiter).encode(Encoding))
        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
            Written = OS.write(Pipe, (InputString + Delimiter).encode(Encoding))
        else:
            InputString += Delimiter
            Blocks = round(InputLength/Length+0.5)
            for X in range(0, Blocks):
                if X+1 < Blocks:
                    Written += OS.write(Pipe, InputString[X*Length:(X+1)*Length].encode(Encoding))
                else:
                    Written += OS.write(Pipe, InputString[X*Length:].encode(Encoding))
        return Written

    @staticmethod
    def writeLineToPipe(Pipe, InputString, Length=1024, Encoding='utf-8'):
        return PipeHelper.writeWithDelimterToPipe(Pipe, InputString, "\n",\
                                                  Length, Encoding,\
                                                  PipeHelper.MULTIBLE_PACKAGES)

    @staticmethod
    def writeUntilEOFFromPipe(Pipe, InputString, Length=1024, Encoding='utf-8', Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        if not isinstance(InputString, str):
            InputString = str(InputString)
        Length = len(InputString)
        Blocks = 0
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            --Length
            if Length > Length:
                Written = OS.write(Pipe, (InputString[0:Length]).encode(Encoding))
            else:
                Written = OS.write(Pipe, (InputString).encode(Encoding))
        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
            Written = OS.write(Pipe, (InputString).encode(Encoding))
        else:
            Blocks = round(Length/Length+0.5)
            for X in range(0, Blocks):
                if X+1 < Blocks:
                    Written += OS.write(Pipe, InputString[X*Length:(X+1)*Length].encode(Encoding))
                else:
                    Written += OS.write(Pipe, InputString[X*Length:].encode(Encoding))
        OS.write(Pipe, b'')
        return Written

    @staticmethod
    def read(Pipe, Length=1024, Encoding='utf-8'):
        return OS.read(Pipe, Length).decode(Encoding)

    @staticmethod
    def readUntilDelimiterFromPipe(Pipe, Delimiter, Length=1024, Encoding='utf-8', __DirtyHack=Mutable()):
        EncodedDelimiter = Delimiter.encode(Encoding)
        DelimiterLength = len(EncodedDelimiter)
        if DelimiterLength > Length:
            raise PipeException(PipeException._INVALID_LENGTH)
        if DelimiterLength == Length:
            Output = b''
            Chars = OS.read(Pipe, Length)
            EncodedDelimiter = Delimiter.encode(Encoding)
            DelimiterLength = len(EncodedDelimiter)
            while True:
#                if EncodedDelimiter == Chars[-DelimiterLength:] or b'' == Chars[-1:]:#the 2nd one is to kepp us save, if the process died
                if  EncodedDelimiter == Chars or b'' == Chars:
#                    Output += Chars[0:-DelimiterLength]
                    break
#                elif EncodedDelimiter == Chars[-1-DelimiterLength:-1]:#we have to do this to avoid a newline stuck by println, everything after it will dumped
#                    Output += Chars[0:-1-DelimiterLength]
#                    break
                else:
                    Output += Chars
                try:
                    Chars = OS.read(Pipe, Length)
                except:
                    break
            return Output.decode(Encoding)
        else:#this is just a dirty hack, but needed, coz there is no other way to be sure, this method works correctly
            Output = ''

            if not __DirtyHack.value():
                __DirtyHack.set({})
                Chars = OS.read(Pipe, Length)
                Chars = Chars.decode(Encoding)
            else:
                if Pipe in __DirtyHack.value() and __DirtyHack.value()[Pipe]:
                    Chars = __DirtyHack.value()[Pipe]
                    del __DirtyHack.value()[Pipe]
                else:
                    Chars = OS.read(Pipe, Length)
                    Chars = Chars.decode(Encoding)

            while True:
                Output += Chars
                if Delimiter in Output:
                    break
                try:
                    Chars = OS.read(Pipe, Length)
                except:
                    break
                if b'' == Chars:
                    break
                Chars = Chars.decode(Encoding)
            Output = Output.split(Delimiter, 1)
            O2 = Output[1].strip()
            if O2:
                __DirtyHack.value()[Pipe] = O2
            return Output[0]

    @staticmethod
    def readLineFromPipe(Pipe, Encoding='utf-8'):
        return PipeHelper.readUntilDelimiterFromPipe(Pipe, "\n",\
                                                    len("\n".encode(Encoding)),\
                                                    Encoding)

    @staticmethod
    def readPackagesFromPipe(Pipe, Length=1024, Encoding='utf-8', Packageing=CONTINUOUS_PACKAGE):
        Output = ''
        Package = None
        Length = 0
        Blocks = 0
        try:
            Package = OS.read(Pipe, Length).decode(Encoding)
        except:
            return None
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            return Package
        else:
            Package = Package
            if not Package or "\n" == Package:
                return ''
            #DebugException
            try:
                Length = int(Package)
            except:
                Error = OS.read(Pipe, 50000).decode(Encoding)
                raise PipeException(PipeException.UNEXSPECTED_RESULT, Error)
            if PipeHelper.MULTIBLE_PACKAGES == Packageing:
# Das wird wohl wichtig, wenn wir nen großen Payload haben und dass sotte von
# der aufrufenden Methode gemacht werden
                Blocks = round(Length/Length+0.5)
                for X in range(0, Blocks):
                    Package = OS.read(Pipe,  Length)
                    Output += Package.decode(Encoding)
            else:
                Output = OS.read(Pipe, Length).decode(Encoding)
            return Output

    @staticmethod
    #EOF in Python means -> os.read(Pipe, 1) == b''
    def readUntilEOFFromPipe(Pipe, Length=1024, Encoding='utf-8'):
        Output = b''
        Chars = OS.read(Pipe, Length)
        while True:
            if b'' == Chars[0:1]:
                break
            else:
                Output += Chars
                Chars = OS.read(Pipe, Length)

        if b'' == Output:
            return ''
        else:
            return Output.decode(Encoding)
#============
class SimplePipeWriterThread(PipeWriterThread):
    def __init__(self, Length, Encoding):
        PipeWriterThread.__init__(self, Length, Encoding)

    def _write(self, Pipe, ToWrite):
        PipeHelper.write(Pipe, ToWrite.getvalue(), self._Encoding)
#-------------
class PackagesPipeWriterThread(PipeWriterThread):
    __Packageing = None

    def __init__(self, Length, Encoding, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        self.__Packageing = Packageing
        PipeWriterThread.__init__(self, Length, Encoding)

    def _write(self, Pipe, ToWrite):
        PipeHelper.writePackagesToPipe(Pipe, ToWrite.getvalue(), self._Length, self._Encoding, self.__Packageing)
#-------------
class DelimiterPipeWriterThread(PipeWriterThread):
    __Packageing = None
    __Delimiter = None
    def __init__(self, Delimiter, Length, Encoding, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        if not Delimiter or not isinstance(Delimiter, str) or 1 != len(Delimiter):
             raise TypeError("Exspected a singel Char as Delimiter.")
        else:
            self.__Delimiter = Delimiter
        self.__Packageing = Packageing
        PipeWriterThreadContinuousBase.__init__(self, Length, Encoding)

    def _write(self, Pipe, ToWrite):
        PipeHelper.writeWithDelimterToPipe(Pipe, ToWrite.getvalue(), self.__Delimiter, self._Length, self._Encoding, self.__Packageing)

class DelimiterPermanentPipeWriterThread(PermanentPipeWriterThread):
    __Delimiter = None
    __Packageing = None
    def __init__(self, Pipe, Delimiter, Length, Encoding, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        if not Delimiter or not isinstance(Delimiter, str) or 1 != len(Delimiter):
            raise TypeError("Exspected a singel Char as Delimiter.")
        else:
             self.__Delimiter = Delimiter
        self.__Packageing = Packageing
        PermanentPipeWriterThread.__init__(self, Pipe, Length, Encoding)

    def _write(self, ToWrite):
        PipeHelper.writeWithDelimterToPipe(self._Pipe, ToWrite.getvalue(), self.__Delimiter, self._Length, self._Encoding, self.__Packageing)
#-------------
class LinePipeWriterThread(PipeWriterThread):
    def __init__(self, Length, Encoding):
        PipeWriterThread.__init__(self, Length, Encoding)

    def _write(self, Pipe, ToWrite):
        PipeHelper.writeLineToPipe(Pipe, ToWrite.getvalue(), self._Length, self._Encoding)

class LinePermanentPipeWriterThread(PermanentPipeWriterThread):
    def __init__(self, Pipe,  Length, Encoding):
        PermanentPipeWriterThread.__init__(self, Pipe, Length, Encoding)

    def _write(self, ToWrite):
        PipeHelper.writeLineToPipe(Pipe=self._Pipe, InputString=ToWrite.getvalue(), Length=self._Length, Encoding=self._Encoding)
#-------------
class EoFPipeWriterThread(PipeWriterThread):
    __Packageing = None
    def __init__(self, Length, Encoding, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        self.__Packageing = Packageing
        PipeWriterThread.__init__(self, Length, Encoding)

    def _write(self, Pipe, ToWrite):
        PipeHelper.writeUntilEOFFromPipe(ipe, ToWrite.getvalue(), self._Length, self._Encoding, self.__Packageing)

#=============
class SimplePipeReaderThread(PipeReaderThread):
    def __init__(self, Length, Encoding):
        PipeReaderThread.__init__(self, Length, Encoding)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.read(Pipe, self._Length, self._Encoding))
#-------------
class PackagesPipeReaderThread(PipeReaderThread):
    __Packageing = None

    def __init__(self, Length, Encoding, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        self.__Packageing = Packageing
        PipeReaderThread.__init__(self, Length, Encoding)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readPackagesFromPipe(Pipe, self._Length, self._Encoding, self.__Packageing))
#-------------
class DelimiterPipeReaderThread(PipeReaderThread):
    __Delimiter = None

    def __init__(self, Delimiter, Length, Encoding):
        if not Delimiter or not isinstance(Delimiter, str) or 1 != len(Delimiter):
            raise TypeError("Exspected a singel Char as Delimiter.")
        else:
            self.__Delimiter = Delimiter
        PipeReaderThread.__init__(self, Length, Encoding)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readUntilDelimiterFromPipe(Pipe=Pipe, Delimiter=self.__Delimiter, Length=self._Length, Encoding=self._Encoding))

class DelimiterPermanentPipeReaderThread(PermanentPipeReaderThread):
    __Delimiter = None
    def __init__(self, Pipe, Delimiter, Length, Encoding):
        if not Delimiter or not isinstance(Delimiter, str) or 1 != len(Delimiter):
            raise TypeError("Exspected a singel Char as Delimiter.")
        else:
            self.__Delimiter = Delimiter
        PermanentPipeReaderThread.__init__(self, Pipe, Length, Encoding)

    def _read(self, Output):
        Output.append(PipeHelper.readUntilDelimiterFromPipe(Pipe=self._Pipe, Delimiter=self.__Delimiter, Length=self._Length, Encoding=self._Encoding))

#-------------
class LinePipeReaderThread(PipeReaderThread):
    def __init__(self, Encoding):
        PipeReaderThread.__init__(self, Encoding)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readLineFromPipe(Pipe, self._Encoding))
#-------------
class EoFPipeReaderThread(PipeReaderThread):
    def __init__(self, Length, Encoding):
        PipeReaderThread.__init__(self, Length, Encoding)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readUntilEOFFromPipe(Pipe, self._Length, self._Encoding))

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

class StringIOEx(StringIO):
    __Length = None
    def __init__(self, initial_value='', newline='\n'):
        StringIO.__init__(self, initial_value, newline)
        self.__Length = len(initial_value)

    def write(self, Value):
        StringIO.write(Value)
        self.__Length += len(Value)

    def size(self):
        return self.__Length
