#!/usr/bin/env python3
# requires at least python 3.4

#import http.client, urllib.parse
from base64 import b64encode
import requests
from http import cookies

class HttpServiceException(Exception):
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

#TODO: wenn noetig SSL Certs implementieren
class HttpService(object):
    __URLBase = ''
    __Headers = {}
    __Session = ''
    __Request = ''
    __Parameter = {}
    __Data = ''
    __Cookies = []
    __PrepartionIsActive = False

    def __init__(self, Configuration):
        Domain = ''
        Port = 80
        Protokoll = 'http'

        Domain = Configuration['host']['name']
        if 'https' == Configuration['host']['protokoll']:
            Port = 443
            protokoll = 'https'

        if Configuration['host']['port']:
            Port = Configuration['host']['port']

        self.__URLBase = Protokoll + '://' + domain + ':' + Port
        self.__Session = requests.Session()

    def setUsernameAndPassword(self, Username, Password):
        self.__Session.auth(Username, Password)

    def addCookieFile(self, Filename):
        Cookie = ''
        File = open(Filename, r)
        for Line in File:
            Cookie += Line
        File.close()
        self.addCookieFile(Cookie)

    def addCookieStr(self, CookieString):
        Cookie = cookies.SimpleCookie()
        Cookie.load(CookieString)
        CookieDirc = {}
        for Key in Cookie:
            CookieDirc[Key] = Cookie[Key]
        self.__Cookies.append(CookieDirc)

    def startACall(self, Method):
        if self.__Cookies:
            Request = Request(method=Method, url=self.__URLBase, params=self.__Parameter, cookies=self.__Cookies)
        else:
            Request = Request(method=Method, url=self.__URLBase, params=self.__Parameter)
        self.__Request = self.__Session.prepare_request(Request)

    def setData(self, Data):
        if True == self.__PrepartionIsActive:
            if self.__Data:
                self.__Data = ''
            self.__Request.body = Data
        else:
            self.__Data = Data

    def addParameter(self, Name, Value):
            self.__Parameter[Name] = Value

    def addHeader(self, Name, Value):
        if True == self.__PrepartionIsActive:
            if self.__Headers:
                for Key in self.__Headers:
                    self.__Request.headers[Key] = self.__Headers[Key]
                self.__Headers = []
            self.__Request.headers[Name] = Value
        else:
            self.__Headers[Name] = Value

    def call(self):
        Response = ''
        if False == self.__PrepartionIsActive:
            return None
        else:
            if self.__Data:
                self.__Request.body = Data
            if self.__Headers:
                for Key in self.__Headers:
                    self.__Request.headers[Key] = self.__Headers[Key]
            try:
                response = self.__Session.send(self.__Request)
            except requests.exceptions.ConnectionError:
                raise HttpServiceException(HttpServiceException.NO_CONECTION)
            return response

    def flush(self):
        self.__Parameter = {}
        self.__Data = ''
        self.__Cookies = {}
        self.__Headers = {}

        self.__Session = requests.Session()
