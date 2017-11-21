#!/usr/bin/env python3
# requires at least python 3.4

import os


class CmdServiceException(Exception):
        Reasons = ['The connection is not established']
        ReasonCodes = [0x0]
        Reason = 0x0
        NO_CONECTION = 0x0
        def __init__(self, ErrorCode):
            self.Reason = ErrorCode
        def __str__(self):
            if self.Reason not in self.ReasonCodes:
                return repr('Unkown error.')
            else:
                return repr(self.Reasons[self.Reason])



class CmdServce(Object):
    __CMD = ''
    __Parameter = []
    NO_FORK_PROGRESS = 0x0
    FORK_PROGRESS = 0x1

    def __ini__(self, Configuration):
        self.__CMD = Configuration['name']

    def addParameter(self, ParameterString):
        if ParameterString.strip():
            self.__Parameter.append(ParameterString.strip())
