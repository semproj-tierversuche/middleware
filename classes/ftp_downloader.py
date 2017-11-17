#!/usr/bin/env python3
# requires at least python 3.4
from ftplib import FTP
from ftplib import FTP_TLS

#ToDo: ->Disclamer
#      ->Exception handlig -> gleich mit dem Logger dann verheiraten oder
#      erstmal den Fehler weiter schmeißen?
class FTPBasicDownloader:
#    _ReturnAsDOM = False
#    _Base = ''
#    _Dirs = ''
    __Connectionnection= ''
#    User = ''
#    PW = ''
    __IsActiv = False
    UseTLS = false

    def __init__(self, BaseAddr, ReturnAsDOM):
        self._Base = BaseAddr
        self._ReturnAsDOM = bool(ReturnAsDOM)
        self.User = ''
        self.PW = ''
        self.__Connection = ''

    def initializeConnection(self):
        #try:
        if True == bool(UseTLS):
            self.__Connection = FTP_TLS(self._Base)
        else:
            self.__Connection = FTP(self._Base)
        #except ftplib.all_errors as e:
        self._IsActiv = True

        #folgendes solltes später geloggt werden
        #try:
        if not self.User:
            self.__Connection.login()
        else:
            self.__Connection.login(user = self.User, passwd = self.PW)
        #except ftplib.all_errors as e:

    def reconnect(self):
        #try:
        if True == bool(UseTLS):
            self.__Connection = FTP_TLS(self._Base)
        else:
            self.__Connection = FTP(self._Base)
        #except ftplib.all_errors as e:

    def getFileList(self, Dir):
        Return = []

#       try:
        self.__Connection.cwd(Dir)
        #except ftplib.all_errors as e
            #dosmt
        self.__Connection.retrlines('LIST', Return.append)

#       try:
        self.__Connection.cwd('/')
        #except ftplib.all_errors as e
        return Return

    def changeDir(self,Dir):
        #try:
        self.__Connection.cwd(Dir)
        #except ftplib.all_errors as e
        #dosmt

    def goBackToBaseDir(self):
        #try:
            self.__Connection.cwd('/')
        #except ftplib.all_errors as e
        #dosmt

    def downloadFile(self, FileName, OutputFile)
       with open(OutputFile, 'wb') as WriteInto:
           def push(Block):
                WriteInto.write(Block)
            #try:
            self.__Connection.retrbinary("RETR " + FileName, push)
            #except ftplib.all_errors as e

#Schliessen der Verbindung nicht vergessen
    def __del__(self):
        if True == self.__IsActiv:
            try:
                self.__Connection.quit()
            except:
                self.__Connection.close()
