#!/usr/bin/env python3
# requires at least python 3.4
from ftplib import all_errors as FTPErrors
from ftplib import FTP
from ftplib import FTP_TLS
import threading as Threads
import os as OS

class FTPBasicDownloaderException(Exception):
    Reasons = ['The connection is not established.', 'The given socket was invalid.']
    ReasonCodes = [0x0, 0x1]
    Reason = 0x0
    NO_CONNECTION = 0x0
    NO_SOCKET = 0x1

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
    __Connection = None
    Username = ''
    Password = ''
    __IsActiv = False
    UseTLS = False
    __LastDir = None
    __Timeout = None

    def __init__(self, BaseAddress, ServerTimeout=45):
        self._Base = BaseAddress
        self.__Connection = ''
        self.__Timeout = 45

    def initializeConnection(self):
        if True == bool(self.UseTLS):
            self.__Connection = FTP_TLS(self._Base)
        else:
            self.__Connection = FTP(self._Base)
        self.__IsActiv = True

        if not self.Username:
            self.__Connection.login()
        else:
            self.__Connection.login(self.Username, self.Password)
        LastDir = '/'

    #fuer einen Reconnect reicht das erneute Login, die Sockets sind ja noch gebunden
    def reconnect(self):
        # bei 60 sekunden timeout wirft erneuter login bei mir EOFError
        # baue alles neu
        self.closeConnection()
        self.initializeConnection()
        self.__Connection.cwd(self.__LastDir)

    def getFileList(self, Dir):
        Return = []
        self.checkConnection()
        self.__Connection.cwd(Dir)
        self.__Connection.retrlines('MLSD', Return.append)
        self.__Connection.cwd('/')
        return Return

    def changeDir(self,Dir):
        self.checkConnection()
        self.__Connection.cwd(Dir)
        self.__LastDir = self.__Connection.pwd()

    def goBackToBaseDir(self):
        self.checkConnection()
        self.__Connection.cwd('/')

    def downloadFile(self, FileName, OutputFile):
        self.checkConnection()
        Socket = None
#        self.__Connection.set_debuglevel(2)
        self.__Connection.voidcmd('TYPE I')
        try:
            Socket = self.__Connection.transfercmd('RETR ' + FileName)
        except FTPErrors as e:
            StatusCode = int(e.args[0][:3])
            if 450 == StatusCode:
                pass
            elif 200 == StatusCode:
                pass
            else:
                raise e
        def writer(Socket):
            if not Socket:
                raise FTPBasicDownloaderException(FTPBasicDownloaderException.NO_SOCKET)
            WriteInto = open(OutputFile, 'wb')
            while True:
                Block = Socket.recv(1024<<10)
                if not Block:
                    break
                WriteInto.write(Block)
            Socket.close()
            WriteInto.close()

        Writer = Threads.Thread(target=writer, args=(Socket,))
        Writer.start()

        while True == Writer.is_alive:
            Writer.join(self.__Timeout)
            self.__Connection.voidcmd("NOOP")
        self.__Connection.voidresp()
 #       with open(OutputFile, 'wb') as WriteInto:
 #           self.__Connection.retrbinary('RETR %s' % FileName, WriteInto.write)
#       We had to modify that to keep the cmd channel open

    def checkConnection(self):
        if False == self.__IsActiv:
            raise FTPBasicDownloaderException(FTPBasicDownloaderException.NO_CONNECTION)
        else:
            try:
                self.__Connection.voidcmd("NOOP")
#            except ftplib.all_errors as e:
            except FTPErrors as e:
                StatusCode = int(e.args[0][:3])
                if 10 > StatusCode % 420 and 1 == StatusCode/420:
                    raise FTPBasicDownloaderException(FTPBasicDownloaderException.NO_CONNECTION)
                else:
                    raise e
    def getCurrentDir(self):
        return self.__LastDir

#Schliessen der Verbindung nicht vergessen
    def closeConnection(self):
        if True == self.__IsActiv:
            try:
                self.__Connection.quit()
            except Exception:
                pass
            self.__Connection.close()
            self.__IsActiv = False

    def __del__(self):
        self.closeConnection()
