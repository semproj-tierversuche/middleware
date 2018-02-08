import os as OS

class PatricaTrieNode(object):
    __Value = None
    _Childes = None
    __Parent = None
    __IsEnding = None

    def __init__(self, Value, Parent=None):
        if Parent and isinstance(Parent, PatricaTrieNode):
            self.__Parent = Parent
        if Value:
            self.__Value = str(Value)
            self.__IsEnding = True
        else:
            self.__IsEnding = False

        self._Childes = []
        self.__FistLetters = []

    @staticmethod
    def sortChildes(Child):
        return Child.getValue()

    def getValue(self):
        return self.__Value

    def hasChildes(self):
        if self._Childes:
            return True
        else:
            return False

    def isAEnd(self):
        return self.__IsEnding

    def unsetEnd(self):
        self.__IsEnding = False

    def __findLongesPrefix(self, String, l1, l2):
        To = min(l1, l2)

        for i in range(1, To):
            if String[i] != self.__Value[i]:
                return i
        return To

    def __Contains(self, String):
        Letter = String[0]
        if not self.__FistLetters:
            return -1
        else:
            Start = 0
            End = len(self.__FistLetters)-1
            while Start <= End:
                Mid = Start+((End-Start)>>1)
                if Letter == self.__FistLetters[Mid]:
                    return Mid
                else:
                    if self.__FistLetters[Mid] > Letter:
                        End = Mid-1
                    else:
                        Start = Start+1
            return -1

    def insert(self, String):
        String = str(String)
        if not self.__Value:
            Index = self.__Contains(String)
            if -1 != Index:
                return self._Childes[Index].insert(String)
            NewChild = PatricaTrieNode(String, self)
            self._Childes.append(NewChild)
            self.__FistLetters.append(String[0])
            self._Childes.sort(key = PatricaTrieNode.sortChildes)
            self.__FistLetters.sort()
            return True
        else:
            if self.__Value[0] != String[0]:
                return False
            else:
                LengthInsert = len(String)
                LengthValue = len(self.__Value)

                Index = self.__findLongesPrefix(String,\
                                                LengthInsert,\
                                                LengthValue)

                if LengthInsert==LengthValue and Index == LengthValue:
                    if False == self.__IsEnding:
                        self.__IsEnding = True
                    return True
                else:
                    if Index == LengthValue:
                        String = String[Index:]
                        Index2 = self.__Contains(String)
                        if -1 != Index2:
                            return self._Childes[Index2].insert(String)
                        NewChild = PatricaTrieNode(String, self)
                        self._Childes.append(NewChild)
                        self._Childes.sort(key = PatricaTrieNode.sortChildes)
                        self.__FistLetters.append(String[0])
                        self.__FistLetters.sort()
                        return True
                    elif Index == LengthInsert:
                        NewChild = PatricaTrieNode(self.__Value[Index:], self)
                        self.__Value = String
                        if False == NewChild._importChildes(self._Childes):
                            return False
                        if False == self.__IsEnding:
                            self.__IsEnding = True
                            NewChild.unsetEnd()
                        self._Childes = [NewChild]
                        self.__FistLetters = [NewChild.getValue()[0]]
                        return True
                    else:
                        Common = self.__Value[0:Index]
                        NewNode = PatricaTrieNode(self.__Value[Index:], self)
                        if False == NewNode._importChildes(self._Childes):
                            return False
                        if False == self.__IsEnding:
                            NewChild.unsetEnd()
                        self.__Value = Common
                        self.__IsEnding = False
                        self._Childes = []
                        self.__FistLetters = []
                        self._Childes.append(NewNode)
                        self.__FistLetters.append(NewNode.getValue()[0])
                        NewNode = PatricaTrieNode(String[Index:], self)
                        self._Childes.append(NewNode)
                        self.__FistLetters.append(NewNode.getValue()[0])
                        self._Childes.sort(key = PatricaTrieNode.sortChildes)
                        self.__FistLetters.sort()
                        return True

    def _importChildes(self, Childes):
        if not isinstance(Childes, list):
            return False
        else:
            for Child in Childes:
                if -1 != self.__Contains(Child.getValue()):
                    return False
                self._Childes.append(Child)
                self.__FistLetters.append(Child.getValue()[0])
            self._Childes.sort(key = PatricaTrieNode.sortChildes)
            self.__FistLetters.sort()
            return True

    def delete(self, String):
        String = str(String)
        ToDel = self.find(String)
        if not ToDel:
            return
        if ToDel.hasChildes():
            if ToDel.isAEnd:
                ToDel.unsetEnd()
        else:
            ToDel._removeFromTrie()

    def _removeFromTrie(self):
         FormerValue = self.__Value[0]
         del self.__Value
         self.__Parent._clean(FormerValue)

    def _clean(self, FormerValue):
        Index = self.__Contains(FormerValue)
        if -1 == Index:
            return

        self._Childes.pop(Index)
        self.__FistLetters.pop(Index)

        if not self.__Value:
            return

        if not self._Childes and False == self.__IsEnding:
            FromerValue = self.__Value[0]
            del self.__Value
            self.__Parent._clean(FormerValue)
        elif 1 == len(self._Childes)\
            and False == self._Childes[0].hasChildes():
            self.__Value += self._Childes[0].getValue()
            self._Childes.pop()
            self.__FistLetters.pop()
            self.__IsEnding = True

    def find(self, String):
        String = str(String)
        if self.__Value:
            if self.__Value.startswith(String):
                return self
            elif String.startswith(self.__Value):
                if self._Childes:
                    String = String[len(self.__Value):]
                    Index = self.__Contains(String)
                    if -1 != Index:
                        return self._Childes[Index].find(String)
                    else:
                        return None
                else:
                    return None
            else:
                return None
        else:
            Index = self.__Contains(String)
            if -1 != Index:
                return self._Childes[Index].find(String)
            else:
                return None

    def contains(self, String):
        if not self.find(String):
            return False
        else:
            return True

    def _serialize(self):
        Output = '[{}:{}'.format(len(self.__Value), self.__Value)
        if self.__IsEnding:
            Output += ':1'
        else:
            Output += ':0'
        for Child in self._Childes:
            Output += Child._serialize()
        return Output + ']'

    def getValues(self):
        Output = []
        if self._Childes:
            for Child in self._Childes:
                Output += Child.getValues()
        if Output:
            if self.__Value:
                for I in range(0, len(Output)):
                    Output[I] = self.__Value + Output[I]
        if self.__IsEnding and self.__Value:
            Output.append(self.__Value)

        return sorted(Output)

class PatricaTrie(PatricaTrieNode):
    def __init__(self):
        PatricaTrieNode.__init__(self, None)

    def serialize(self):
        Output = '[root'
        for Child in self._Childes:
            Output += Child._serialize()
        return Output + ']'

    def fromString(self, String):
        String = str(String)
        NotValid = "The given string is not valid. - Exspecetd {} got {} at Index {}"
        Length = len(String)
        if 6 > Length:
            raise ValueError("The given string cannot be valid.")
        if '[' != String[0]:
            raise ValueError(NotValid.format('[', String[0], '0'))

        if 'root' != String[1:5]:
            raise ValueError(NotValid.format('root', String[1:5], '1'))

        def _parse(String, Index, Length, Parent):
            def _parseNodeValue(String, I):
                Collector = ''
                for J in range(I, Length):
                    #print(String[J])
                    if ':' == String[J]:
                        break
                    Collector += String[J]#I know its slow
                    if J+1 >= Length:
                        raise ValueError("The given string cannot be valid.")
                    else:
                        if not Collector:
                            raise ValueError(NotValid.format('sequence of numbers', ':', I))
                        L2 = len(Collector)
                        Collector = int(Collector)
                        if L2+J+1+Collector>=Length:
                            raise ValueError("The given string cannot be valid.")
                        else:
                     #       print('-----'
                      #            + str(I) + '||' + str(J) + "||" + str(Collector)\
                       #           + "\n" + '--> ' + \
                        #          String[J+L2+1:J+1+L2+Collector] + '######\n' +\
                         #         String[J:]
                          #        + "\n" + '----')

                            return (String[J+L2+1:J+1+L2+Collector], L2+1+Collector)

            GoForEnd = False
            Node = None
            Childes = []
            I = Index
            while I < Length:
                #print(String[I])
                if '[' == String[I]:
                    if not Node:
                        raise ValueError(NotValid.format('node definition', '[', I))
                    Child, New = _parse(String, I+1, Length, Node)
                    if Child:
                        Childes.append(Child)
                    I = New
                    continue
                if ']' == String[I]:
                    if not Node:
                        return (None, I+1)
                    else:
                        if True == GoForEnd:
                            del Node
                            raise ValueError(NotValid.format('endingflag', ']', I))
                        else:
                            #print(Childes)
                            if Childes:
                                Node._importChildes(Childes)
                        I = I+1
                        return Node, I

                        #return (Node, I+1)
                elif True == GoForEnd:
                    if ':' == String[I]:
                        if I+2 >= Length:
                            raise ValueError("The given string cannot be valid.")
                        if '0' ==  String[I+1]:
                            Node.unsetEnd()
                        I = I+2
                        GoForEnd = False
                else:
                    (Value, Add) = _parseNodeValue(String, I)
                    GoForEnd = True
                    Node = PatricaTrieNode(Value, Parent)
                    I = I+Add


        Index = 5
        Childes = []
        while Index<Length:
            if '[' == String[Index]:
                (Child, New) = _parse(String, Index+1, Length, self)
                Index = New
                if Child:
                    Childes.append(Child)
                continue
            elif ']' == String[Index]:
                self._Childes = []
                self.__FistLetters = []
                self._importChildes(Childes)
                return
            else:
                raise ValueError(NotValid.format('[ or ]', String[5], 5))

    def load(self, File):
        Input = ''
        if OS.path.isfile(File)\
           and OS.access(OS.path.dirname(OS.path.abspath(File)), OS.R_OK):
            with open(File, 'r') as FH:
                Input = FH.read()
            self.fromString(Input)
            return True
        else:
            return False

    def save(self, File):
        if OS.access(OS.path.dirname(OS.path.abspath(File)), OS.W_OK):
            with open(File, 'w') as FH:
                FH.write(self.serialize())
            return True
        else:
            return False

