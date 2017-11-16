#!/usr/bin/env python3
# requires at least python 3.4
from ftplib import FTP
from ftplib import FTP_TLS


#ToDo: ->Disclamer
#      ->Exception handlig -> gleich mit dem Logger dann verheiraten oder
#      erstmal den Fehler weiter schmeißen?
class ftpBasicDownloader:
#    _ReturnAsDOM = False
#    _Base = ''
#    _Dirs = ''
    __Con = ''
#    User = ''
#    PW = ''
    __IsActiv = False

    def __init__(self, BaseAddr, ReturnAsDOM):
        self._Base = BaseAddr
        self._ResturnAsDOM = bool(ReturnAsDOM)
        self.User = ''
        self.PW = ''
        self.__Con = ''

    def initCon(self, WithTLS):
        #try:
        if True == bool(WithTLS):
            self.__Con = FTP_TLS(self._Base)
        else:
            self.__Con = FTP(self._Base)
        #except ftplib.all_errors as e:
        self._IsActiv = True

        #folgendes solltes später geloggt werden
        #try:
        if not self.User:
            self.__Con.login()
        else:
            self.__Con.login(user = self.User, passwd = self.PW)
        #except ftplib.all_errors as e:

    def getFileList(self, Dir):
        DepCounter = 0
        Return = []
        Scroller = ''

        DepCounter = Dir.count("/")
#       try:
        self.__Con.cwd(Dir)
        #except ftplib.all_errors as e
            #dosmt
        self.__Con.retrlines('LIST', Return.append)

        for i in range(0,DepCounter):
            Scroller += '../'
#       try:
        self.__Con.cwd(Scroller)
        #except ftplib.all_errors as e
        return Return

    def downloadFile(self, FileName, OutputFile):
       with open(OutputFile, 'wb') as WriteInto:
            def push(block):
                WriteInto.write(block)
            #try:
            self.__Con.retrbinary("RETR " + FileName, push)
            #except ftplib.all_errors as e

#Schliessen der Verbindung nicht vergessen
    def __del__(self):
        if True == self.__IsActiv:
            try:
                self.__Con.quit()
            except:
                self.__Con.close()

