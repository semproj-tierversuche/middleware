#!/usr/bin/env python3
# requires at least python 3.4

import http.client, urllib.parse
from base64 import b64encode

class FTPBasicDownloaderException(Exception):
    Reasons = ['The connection is not established']
    Reason = 0x0
    NO_CONECTION = 0x0
    def __init__(self, ErrorCode):
        self.Reason = ErrorCode

    def __str__(self):
        if self.Reason not in self.Reasons:
            return repr('Unkown error.')
        else:
            return repr(self.Reasons[self.Reason])

#TODO: wenn noetig SSL Certs implementieren
class HttpService(object):
    __Use_HTTPS = False
    __Connection = ''
    __IsActive = False
    __Domain = ''
    __Port = 80
    __basicAuth = ''
    __Headers = {}

    def __init__(self, Configuration):
        self.__Domain = Configuration['host']['name']
        if 'https' == Configuration['host']['protokoll']:
            self.__Port = 443
            self.Use_HTTPS = True
        if Configuration['host']['port']:
            self.__Port = Configuration['host']['port']

    def setUsernameAndPassword(self, Username, Password):
        self.__Headers['Authorization'] = 'Basic %s' % base64.encodestring('%s:%s' % (Username, Password)).replace('\n', '')

    def connect(self):
        if self

    def closeConnection(self):
        if self.__IsActive:
            self.__Connection.close()
            self.__IsActive = False

    def __del__(self):
        self.closeConnection()

