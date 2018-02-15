#!/usr/bin/env python3
# requires at least python 3.4
from io import StringIO, BytesIO
import sys as System
import os as OS
import threading as Threads
import time as Time
from math import ceil as Ceil
from functools import cmp_to_key as toKeyFunction

#it's awesome
def fastSearch(Where, What):
    if not Where:
        return -1
    else:
         Start = 0
         End = len(Where)-1

         while Start <= End:
             MBin = (Start+End)>>1
             MInt = (Where[End]-Where[Start])
             if 0 != MInt:
                 MInt = round(Start+((What - Where[Start]) * (End-Start)/(Where[End]-Where[Start])))

             if MBin > MInt:
                 MBin, MInt = MInt, MBin

             if Where[MBin] == What:
                 return MBin
             elif Where[MInt] == What:
                 return MInt
             elif Where[MBin] > What:
                 End = MBin-1
             elif Where[MInt] > What:
                 Start = MBin +1
                 End = MInt-1
             else:
                 Start = MInt+1

         return -1

def quadraticSearch(Where, What):
    if not Where:
        return -1
    else:
        Start = 0
        End = len(Where)-1

        while Start <= End:
            Mid = (Start+End)>>1
            PP = End-Start
            P1 = Start+(PP>>2)
            P2 = round(Start+(PP*0.75))

            if Where[Mid] == What:
                return Mid
            elif Where[P1] == What:
                return P1
            elif Where[P2] == What:
                return P2
            elif Where[Mid] > What and Where[P1] > What:
                End = P1-1
            elif Where[Mid] > What and Where[P1] < What:
                Start = P1+1
                End = Mid-1
            elif Where[Mid] < What and Where[P2] < What:
                Start = P2+1
            elif Where[Mid] < What and Where[P2] > What:
                Start = Mid+1
                End = P2-1

        return -1

def binarySearch(Where, What):
    if not Where:
        return -1
    else:
        Start = 0
        End = len(Where)-1

        while Start <= End:
            Mid = (Start+End)>>1
            if Where[Mid] == What:
                return Mid
            else:
                if Where[Mid] > What:
                    End = Mid-1
                else:
                    Start = Start+1
        return -1

def binaryInsertSearch(self, Where, What):
    if not Where:
        return -1

    Start = 0
    End = len(Where)-1
    while (Start <= End):
        Mid = ((Start+End) >> 1)
        if What > Where[Mid]:
            Start = Mid + 1
        elif What < Where[Mid]:
            End = Mid - 1
        else:
            return Mid

    return -(Start + 1)

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

class BadCharacter(object):
    __LookupCharacaters = None
    __Freq = None
    __JumpPositions = None

    def __init__(self, Pattern):
        self.__makeEBC(Pattern)

    def __makeEBC(self, Pattern):
        # Positions
        # Fields
        PatternLength = len(Pattern)
        PatternList = []
        for i in range(0, PatternLength):
            PatternList.append(0)

        Fields = sorted(Pattern)
        JumpTable = {}#we get Sigma and set all entries to -1
        self.__JumpPositions = []

        #init JumpPositions
        #propably there is a better way to this in python
        for i in range(0, PatternLength):
            self.__JumpPositions.append([])
            for j in range(0, PatternLength):
                self.__JumpPositions[i].append(0)


        for i in range(0, PatternLength):
            Positions = list(PatternList)
            Positions[0] = -1
            JumpTable[Pattern[i]] = Positions

        self.__LookupCharacters = []
        for i in range(0, PatternLength):
            self.__JumpPositions[0][i] = -1
            self.__LookupCharacters.append(Fields[i])

        #fill the shift table
        Positions =  JumpTable[Pattern[0]]
        Positions[0] = 0;

        JumpTable[Pattern[0]] = Positions
        for i in range(1, PatternLength):
            Positions = JumpTable[Pattern[i]]
            Positions[i] = i
            JumpTable[Pattern[i]] = Positions
            for j in range(0, PatternLength):
                self.__JumpPositions[i][j] = -1
                if j == i:
                    continue;
                else:
                    Positions = JumpTable[Pattern[j]]
                    Positions[i] = Positions[i-1]
                    JumpTable[Pattern[j]] = Positions

        for i in range(0, PatternLength):
            Positions = JumpTable[Fields[i]]
            for j in range(0, PatternLength):
                self.__JumpPositions[i][j] = Positions[j]

    def lookup(self, A, Position):
        Index = binarySearch(self.__LookupCharacters, A)
        if -1 != Index:
            return self.__JumpPositions[Index][Position]
        else:
            return -1

class Frequence(object):
    __Frequences = None

    class FrequenceTupel(object):
        _Key = None
        _Frequence = None
        _Positions = None

        def __init__(self, Frequence):
            self._Key = Frequence._Key
            self._Frequence = Frequence._Frequence
            self._Positions = []
            for Position in Frequence._Positions:
                self._Positions.append(Position)

    class FrequenceHelper(object):
        _Key = None
        _Frequence = None
        _Positions = None

        def __init__(self, Key):
            self._Key = Key
            self._Frequence = 0
            self._Positions = []

        def countUp(self):
            self._Frequence = self._Frequence+1

        def addPosition(self, Position):
            self._Positions.append(Position)

    def __containsKey(self, Key, Helpers):
        if not Helpers:
            return -1

        for Helper in Helpers:
            if Helper._Key == Key:
                return i

        return -1;

    def __init__(self, Pattern):
        def frequenceHelperSort(Helper1, Helper2):
            if Helper1._Frequence == Helper2._Frequence:
                if Helper1._Positions[-1] > Helper2._Positions[-1]:
                    return -1
                else:
                    return 1
            else:
                return Helper1._Frequence-Helper2._Frequence

        Frequences = []
        Helper = None
        Helpers = []
        PatternLength = len(Pattern)

        for i in range(0, PatternLength):
            j = self.__containsKey(Pattern[i], Frequences)
            if -1 == j:
                Helper = self.FrequenceHelper(Pattern[i])
                Helper.addPosition(i)
                Helpers.append(Helper)
            else:
                Frequences[j].countUp()
                Frequences[j].addPosition(i)

        Helpers = sorted(Helpers, key=toKeyFunction(frequenceHelperSort))
        self.__Frequences = []
        for Helper in Helpers:
            self.__Frequences.append(self.FrequenceTupel(Helper))

    def frequenceMatch(self, Haystack, CurrentPosition):
        for Frequence in self.__Frequences:
            for Position in Frequence._Positions:
                if Haystack[CurrentPosition+ Position] != Frequence._Key:
                    return Position

        return -1;

def sundayFX(Pattern, Haystack, From=0, Length=0, _BadCharacters=Mutable()):
    Found = []

    HaystackLength = len(Haystack)
    if 0 >= Length:
        Length = HaystackLength
        if 0>= Length:
            return []

    PatternLength = len(Pattern)

    if not _BadCharacters.value():
        _BadCharacters.set({})

    if Pattern not in _BadCharacters.value():
        BadCharacterRules = BadCharacter(Pattern)
        Frequences = Frequence(Pattern)
        _BadCharacters.value()[Pattern] = (BadCharacterRules, Frequences)
    else:
        BadCharacterRules, Frequences = _BadCharacters.value()[Pattern]

    i = From
    while i<= (Length-PatternLength):
        j = Frequences.frequenceMatch(Haystack, i);
        if 0 > j:
            #report + shiften auf das naechste
            Found.append(i)
            if i+1 < HaystackLength:
                i += max(1, (BadCharacterRules.lookup(Haystack[i+1], 0)+1))
            else:
                i += 1
        else:
            if HaystackLength > i+PatternLength:
                i += max(1, j-(BadCharacterRules.lookup(Haystack[i+PatternLength], j)+1))
            else:
                return Found

    return Found

class PipeReaderThread(Threads.Thread):
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __PIPE = 0
    __OUTPUT = 1
    __DIE = 2

    def __init__(self, Length):
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
        if False == self._IsActive:
            return
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
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __OUTPUT = 0
    __DIE = 1

    def __init__(self, Pipe, Length):
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
        if False == self._IsActive:
            return
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
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __PIPE = 0
    __TOWRITE = 1
    __DIE = 2

    def __init__(self, Length):
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
        if False == self._IsActive:
            return
        TmpPipe = None
        TmpStringBuffer = None

        if isinstance(Pipe, int) and isinstance(ToWrite, BytesIOEx):
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
    _Length = None
    __Lock = None
    __DoLock = None
    __Cache = None
    _IsActive = None
    __TOWRITE = 0
    __DIE = 1

    def __init__(self, Pipe, Length):
        self._Pipe = Pipe
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

    def __controller(self, ToWrite=None, Die=False):
        TmpStringBuffer = None

        if isinstance(ToWrite, BytesIOEx):
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
    def padding(Input, Length, LengthIn):
        if Length == LengthIn:
            return Input
        LengthC = Ceil(Length/LengthIn)
        print(LengthC)
        for x in range(LengthIn, LengthC):
            Input += b' '
        return Input

    @staticmethod
    def write(Pipe, InputString):
        return OS.write(Pipe, InputString)

    @staticmethod
    def writePackagesToPipe(Pipe, Input, Length=1024, Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        Blocks = 0
        LengthIn = len(Input)
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            if LengthIn > Length:
                Written = OS.write(Pipe, (InputString[0:Length]))
            else:
                Written = OS.write(Pipe, PipeHelper.padding(Input, Length, LengthIn))
        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
            Suffix = str(LengthIn).encode('utf-8')
            Written = OS.write(Pipe, (PipeHelper.padding(Suffix, Length, len(Suffix)) + Input))
        else:
            Blocks = Ceil(LengthIn/Length)
            Suffix = str(LengthIn).encode('utf-8')
            Written = OS.write(Pipe, PipeHelper.padding(Suffix, Length, len(Suffix)))
            for X in range(0, Blocks):
                if X+1 < Blocks:
                    Written += OS.write(Pipe, Input[X*Length:(X+1)*Length])
                else:
                    Sub = Input[X*Length:]
                    Written += OS.write(Pipe, PipeHelper.padding(Sub, Length, len(Sub)))
        return Written

    @staticmethod
    def writeWithDelimterToPipe(Pipe, Input, Delimiter, Length=1024, Packageing=CONTINUOUS_PACKAGE):
        Written = 0
        InputLength = len(Input)+len(Delimiter)
        Blocks = 0
        if PipeHelper.SINGLE_PACKAGE == Packageing:
            if Length < InputLength:
                Written = OS.write(Pipe, (Input[0:Length-len(Delimiter)] + Delimiter))
            else:
                Written = OS.write(Pipe, (Input + Delimiter))
        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
            Written = OS.write(Pipe, (Input + Delimiter))
        else:
            Input += Delimiter
            Blocks = Ceil(InputLength/Length)
            for X in range(0, Blocks):
                if X+1 < Blocks:
                    Written += OS.write(Pipe, Input[X*Length:(X+1)*Length])
                else:
                    Written += OS.write(Pipe, Input[X*Length:]+Delimiter)
        return Written

    @staticmethod
    def writeLineToPipe(Pipe, Input, Length=1024, Packageing=CONTINUOUS_PACKAGE):
        return PipeHelper.writeWithDelimterToPipe(Pipe, Input, b'\n',\
                                                  Length, Packageing)
# oes not work as exspected
#    @staticmethod
#    def writeUntilEOFToPipe(Pipe, Input, Length=1024, Packageing=CONTINUOUS_PACKAGE):
#        Written = 0
#        LengthIn = len(Input)
#        Blocks = 0
#        if PipeHelper.SINGLE_PACKAGE == Packageing:
#            --Length
#            if LengthIn > Length:
#                Written = OS.write(Pipe, (Input[0:Length]))
#            else:
#                Written = OS.write(Pipe, (Input))
#        elif PipeHelper.CONTINUOUS_PACKAGE == Packageing:
#            Written = OS.write(Pipe, Input)
#        else:
#            Blocks = Ceil(LengthIn/Length)
#            for X in range(0, Blocks):
#                if X+1 < Blocks:
#                    Written += OS.write(Pipe, Input[X*Length:(X+1)*Length])
#                else:
#                    Written += OS.write(Pipe, InputString[X*Length:])
#        OS.write(Pipe, b'')
#        return Written

    @staticmethod
    def read(Pipe, Length=1024):
        return OS.read(Pipe, Length)

    @staticmethod
    def readUntilDelimiterFromPipe(Pipe, Delimiter, Exact=True,Length=1024, Close=None, __DirtyHack=Mutable()):
        if not __DirtyHack.value():
            __DirtyHack.set({})
        if Close is not None:
            if Close in __DirtyHack.value():
                del __DirtyHack.value()[Close]
            return

        DelimiterLength = len(Delimiter)

        if True == Exact:
            if Pipe in __DirtyHack.value() and 'found' in __DirtyHack.value()[Pipe]\
                    and __DirtyHack.value()[Pipe]['found']:
                if __DirtyHack.value()[Pipe]['delimiter'] == Delimiter:
                    if __DirtyHack.value()[Pipe]['indicies']:
                        Index = __DirtyHack.value()[Pipe]['indicies'].pop(0)
                        for i in range(0, len(__DirtyHack.value()[Pipe]['indicies'])):
                            __DirtyHack.value()[Pipe]['indicies'][i] -= DelimiterLength
                        Return = __DirtyHack.value()[Pipe]['found'][0:Index]
                        __DirtyHack.value()[Pipe]['found'] = __DirtyHack.value()[Pipe]['found'][Index+DelimiterLength:]
                        return Return
                    else:
                        Output = __DirtyHack[Pipe]['found']
                else:
                    Output = __DirtyHack.value()[Pipe]['found']
                    __DirtyHack.value()[Pipe]['delimiter'] = Delimiter
                    if DelimiterLength<Output:
                        Found = sundayFX(Delimiter, Output)
                        if Found:
                            Index = Found.pop(0)
                            __DirtyHack.value()[Pipe]['indicies'] = Found
                            for i in range(0, len(__DirtyHack.value()[Pipe]['indicies'])):
                                __DirtyHack.value()[Pipe]['indicies'][i] -= DelimiterLength
                                Return = __DirtyHack.value()[Pipe]['found'][0:Index]
                            __DirtyHack.value()[Pipe]['found'] = __DirtyHack.vale()[Pipe]['found'][Index+DelimiterLength:]
                            return Return

                    __DirtyHack[Pipe]['found'] = None
            else:
                __DirtyHack.value()[Pipe] = {}
                __DirtyHack.value()[Pipe]['delimiter'] = Delimiter
                Output = b''

            LastLength = 0
            Chars = OS.read(Pipe, Length)
            while True:
                Output += Chars
                if b'' == Chars:#EOF -> otherwise we stuck
                    return Output
                if LastLength<DelimiterLength:
                    Start = 0
                else:
                    Start = LastLength-DelimiterLength#we must start earlier, otherwise we propably miss something
                Found = sundayFX(Delimiter, Output, From=Start)
                if Found:
                    Index = Found.pop(0)
                    __DirtyHack.value()[Pipe]['found'] = Output
                    __DirtyHack.value()[Pipe]['indicies'] = Found
                    for i in range(0, len(__DirtyHack.value()[Pipe]['indicies'])):
                        __DirtyHack.value()[Pipe]['indicies'][i] -= DelimiterLength
                    Return = __DirtyHack.value()[Pipe]['found'][0:Index]
                    __DirtyHack.value()[Pipe]['found'] = __DirtyHack.value()[Pipe]['found'][Index+DelimiterLength:]
                    return Return
                else:
                    LastLength = len(Output)
                    Output += Chars
                    try:
                        Chars = OS.read(Pipe, Length)
                    except:
                        return None
        else:
            Output = b''
            Chars = OS.read(Pipe, Length)
            while True:
                Output += Chars
                #EOF -> otherwise we stuck
                if b'' == Chars[-1:]\
                or Chars[-DelimiterLength:] == Delimiter\
                or Chars[-1-DelimiterLength:-1] == Delimiter:#we must do that to avoid println
                    return Output
                else:
                    try:
                        Chars = OS.read(Pipe, Length)
                    except:
                        return None
    @staticmethod
    def readLineFromPipe(Pipe, Exact=True, Length=1024, Close=None):
        return PipeHelper.readUntilDelimiterFromPipe(Pipe, Delimiter=b'\n', Exact=Exact, Length=Length, Close=Close)

    @staticmethod
    def readPackagesFromPipe(Pipe, Length=1024, Packageing=CONTINUOUS_PACKAGE):
        Output = b''
        Package = None
        OutputLength = 0
        Blocks = 0
        try:
            Package = OS.read(Pipe, Length)
        except:
            return None

        if PipeHelper.SINGLE_PACKAGE == Packageing:
            return Package
        else:
            if not Package or b' ' == Package:
                return ''
            #DebugException
            try:
                OutputLength = int(Package)
            except:
                Error = OS.read(Pipe, 50000)
                raise PipeException(PipeException.UNEXSPECTED_RESULT, Error.decode('utf-8'))
            if PipeHelper.MULTIBLE_PACKAGES == Packageing:
# Das wird wohl wichtig, wenn wir nen großen Payload haben und dass sotte von
# der aufrufenden Methode gemacht werden
                Blocks = Ceil(OutputLength/Length)
                for X in range(0, Blocks):
                    Package = OS.read(Pipe, Length)
                    Output += Package
            else:
                Output = OS.read(Pipe, OutputLength)
            return Output

    @staticmethod
    #EOF in Python means -> os.read(Pipe, 1) == b''
    def readUntilEOFFromPipe(Pipe, Length=1024):
        Output = b''
        Chars = OS.read(Pipe, Length)
        while True:
            if b'' == Chars[0:1]:
                break
            else:
                Output += Chars
                Chars = OS.read(Pipe, Length)

        return Output
#============
class SimplePipeWriterThread(PipeWriterThread):
    def __init__(self, Length, Encoding):
        PipeWriterThread.__init__(self, Length, Encoding)

    def _write(self, Pipe, ToWrite):
        try:
            PipeHelper.write(Pipe, ToWrite.getvalue(), self._Encoding)
        except BrokenPipeError:#ignore that -> The programm close before
            pass

#-------------
class PackagesPipeWriterThread(PipeWriterThread):
    __Packageing = None

    def __init__(self, Length, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        self.__Packageing = Packageing
        PipeWriterThread.__init__(self, Length)

    def _write(self, Pipe, ToWrite):
        try:
            PipeHelper.writePackagesToPipe(Pipe, ToWrite.getvalue(), self._Length, self.__Packageing)
        except BrokenPipeError:#ignore that -> The programm close before
            pass
#-------------
class DelimiterPipeWriterThread(PipeWriterThread):
    __Packageing = None
    __Delimiter = None
    def __init__(self, Delimiter, Length, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        if not Delimiter or not isinstance(Delimiter, bytes):
             raise TypeError("Exspected bytes as Delimiter.")
        else:
            self.__Delimiter = Delimiter
        self.__Packageing = Packageing
        PipeWriterThreadContinuousBase.__init__(self, Length)

    def _write(self, Pipe, ToWrite):
        try:
            PipeHelper.writeWithDelimterToPipe(Pipe, ToWrite.getvalue(), self.__Delimiter, self._Length, self.__Packageing)
        except BrokenPipeError:#ignore that -> The programm close before
            pass

class DelimiterPermanentPipeWriterThread(PermanentPipeWriterThread):
    __Delimiter = None
    __Packageing = None
    def __init__(self, Pipe, Delimiter, Length, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        if not Delimiter or not isinstance(Delimiter, bytes):
            raise TypeError("Exspected bytes as Delimiter.")
        else:
             self.__Delimiter = Delimiter
        self.__Packageing = Packageing
        PermanentPipeWriterThread.__init__(self, Pipe, Length)

    def _write(self, ToWrite):
        try:
            PipeHelper.writeWithDelimterToPipe(self._Pipe, ToWrite.getvalue(), self.__Delimiter, self._Length, self.__Packageing)
        except BrokenPipeError:#ignore that -> The programm close before
            pass
#-------------
class LinePipeWriterThread(PipeWriterThread):
    def __init__(self, Length):
        PipeWriterThread.__init__(self, Length)

    def _write(self, Pipe, ToWrite):
        try:
            PipeHelper.writeLineToPipe(Pipe, ToWrite.getvalue(), self._Length)
        except BrokenPipeError:#ignore that -> The programm close before
            pass

class LinePermanentPipeWriterThread(PermanentPipeWriterThread):
    def __init__(self, Pipe,  Length):
        PermanentPipeWriterThread.__init__(self, Pipe, Length)

    def _write(self, ToWrite):
        try:
            PipeHelper.writeLineToPipe(Pipe=self._Pipe, Input=ToWrite.getvalue(), Length=self._Length)
        except BrokenPipeError:#ignore that -> The programm close before
            pass
#=============
class SimplePipeReaderThread(PipeReaderThread):
    def __init__(self, Length):
        PipeReaderThread.__init__(self, Length)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.read(Pipe, self._Length))
#-------------
class PackagesPipeReaderThread(PipeReaderThread):
    __Packageing = None

    def __init__(self, Length, Packageing=PipeHelper.MULTIBLE_PACKAGES):
        self.__Packageing = Packageing
        PipeReaderThread.__init__(self, Length)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readPackagesFromPipe(Pipe, self._Length, self.__Packageing))
#-------------
class DelimiterPipeReaderThread(PipeReaderThread):
    __Delimiter = None
    __Exact = None

    def __init__(self, Delimiter, Length, Exact=True):
        if not Delimiter or not isinstance(Delimiter, bytes):
            raise TypeError("Exspected bytes as Delimiter.")
        else:
            self.__Delimiter = Delimiter
            self.__Exact = Exact
        PipeReaderThread.__init__(self, Length)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readUntilDelimiterFromPipe(Pipe=Pipe, Delimiter=self.__Delimiter, Length=self._Length, Exact=self.__Exact))

class DelimiterPermanentPipeReaderThread(PermanentPipeReaderThread):
    __Delimiter = None
    __Exact = None
    def __init__(self, Pipe, Delimiter, Length, Exact=True):
        if not Delimiter or not isinstance(Delimiter, bytes):
            raise TypeError("Exspected bytes as Delimiter.")
        else:
            self.__Delimiter = Delimiter
            self.__Exact = Exact
        PermanentPipeReaderThread.__init__(self, Pipe, Length)

    def _read(self, Output):
        Output.append(PipeHelper.readUntilDelimiterFromPipe(Pipe=self._Pipe, Delimiter=self.__Delimiter, Length=self._Length, Exact=self.__Exact))

#-------------
class LinePipeReaderThread(PipeReaderThread):
    __Exact = None
    def __init__(self, Lengtg=1024, Exact=True):
        PipeReaderThread.__init__(self, Length)
        self.__Exact = Exact

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readLineFromPipe(Pipe, Length=self._Length, Exact=self.__Exact))
#-------------
class EoFPipeReaderThread(PipeReaderThread):
    def __init__(self, Length):
        PipeReaderThread.__init__(self, Length)

    def _read(self, Pipe, Output):
        Output.append(PipeHelper.readUntilEOFFromPipe(Pipe, self._Length))

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

#RawBase wäre besser...funktionier nur leider nicht so
class BytesIOEx(object):
    __Length = None
    __Raw = None
    def __init__(self, InitValue=None):
        self.__Length = 0
        if InitValue:
            self.write(InitValue)

    def write(self, Bytes):
        if b'0' == Bytes:
            Length = self.size() + 1
        else:
            Length = self.size() + len(Bytes)
        if self.__Raw:
            self.__Raw = BytesIO(self.getValue() + Bytes)
        else:
            self.__Raw = BytesIO(Bytes)
        self.__Length = Length

    def read(self, Size):
        if 0 >= Size:
            return b''
        elif Size > self.__Length:
            self.__Length = 0
        else:
            self.__Length -= Size
        return self.__Raw.read(Size)

    def getValue(self):
        Bytes = self.__Raw.read(self.__Length)
        self.__Length = 0
        return Bytes

    def getvalue(self):
        return self.getValue()

    def size(self):
        return self.__Length
