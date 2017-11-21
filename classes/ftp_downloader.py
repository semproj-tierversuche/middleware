#!/usr/bin/env python3
# requires at least python 3.4
from ftplib import FTP
from ftplib import FTP_TLS

class FTPBasicDownloaderException(Exception):
    Reasons = ['The connection is not established']
    ReasonCodes = [0x0]
    Reason = 0x0
    NO_CONECTION = 0x0

    def __init__(self, ErrorCode):
        self.Reason = ErrorCode

    def __str__(self):
        if self.Reason not in self.ReasonCodes:
            return repr('Unknown Error')
        else:
            return repr(self.Reasons[self.Reason])

#ToDo: ->Disclamer
#      ->Exception handlig -> gleich mit dem Logger dann verheiraten oder
#      erstmal den Fehler weiter schmeißen?
class FTPBasicDownloader(object):
#    _ReturnAsDOM = False
#    _Base = ''
#    _Dirs = ''
    __Connectionnection= ''
    Username = ''
    Password = ''
    __IsActiv = False
    UseTLS = False

    #def __init__(self, BaseAddr, Username, Password, ReturnAsDOM):
    def __init__(self, BaseAddress):
        self._Base = BaseAddress
        self.__Connection = ''

    def initializeConnection(self):
        #try:
        if True == bool(self.UseTLS):
            self.__Connection = FTP_TLS(self._Base)
        else:
            self.__Connection = FTP(self._Base)
        #except ftplib.all_errors as e:
        self._IsActiv = True

        #folgendes solltes später geloggt werden
        #try:
        if not self.Username:
            self.__Connection.login()
        else:
            self.__Connection.login(self.Username, self.Password)
        #except ftplib.all_errors as e:

    #fuer einen Reconnect reicht das erneute Login, die Sockets sind ja noch gebunden
    def reconnect(self):
#       self.initializeConnection()
        #try:
        if False == self.__IsActiv:
            self.initializeConnection()
        else:
            if not self.Username:
                self.__Connection.login()
            else:
                self.__Connection.login(self.Username, self.Password)
        #except ftplib.all_errors as e:


    def getFileList(self, Dir):
        Return = []

        self.checkConnection()
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
        self.checkConnection()
        #try:
        self.__Connection.cwd(Dir)
        #except ftplib.all_errors as e
        #dosmt

    def goBackToBaseDir(self):
        self.checkConnection()
        #try:
        self.__Connection.cwd('/')
        #except ftplib.all_errors as e
        #dosmt

    def downloadFile(self, FileName, OutputFile):
        self.checkConnection()
        with open(OutputFile, 'wb') as WriteInto:
           def push(Block):
                WriteInto.write(Block)
                #try:
                self.__Connection.retrbinary("RETR %s" % FileName, push)
                #except ftplib.all_errors as e


    def checkConnection(self):
        if False == self.__IsActiv:
            raise FTPBasicDownloaderException(FTPBasicDownloaderException.NO_CONECTION)

#Schliessen der Verbindung nicht vergessen
    def closeConnection(self):
        if True == self.__IsActiv:
            try:
                self.__Connection.quit()
            except:
                self.__Connection.close()
            self.__IsActiv = False

    def __del__(self):
        self.closeConnection()
