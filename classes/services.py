#!/usr/bin/env python3
# requires at least python 3.4

class Service(object):
    USE_NOTHING = 0x0
    USE_FORK = 0x2
    USE_VFORK = 0x2

    __Database = ''
    __TextMining = ''

    def __init__(self, Configuration):
        pass

    def callTextMining(self, JSON, Flag=self.USE_NOTHING):
        pass

    def queryDatabase(self, JSON, Flag=self.USE_NOTHING):
        pass

    def insertIntoDatabase(self, JSON, Flag=self.USE_NOTHING):
        pass
