#!/usr/bin/env python3
# requires at least python 3.4

import requests as Requests
from http import cookies as Cookies
import os as OS

class HttpServiceException(Exception):
    Reasons = ['The connection is not established', 'The given cookiefile was not found']
    ReasonCodes = [0x0, 0x1]
    Reason = 0x0

    NO_CONECTION = 0x0
    NO_COOKIE_FILE = 0x1

    def __init__(self, ErrorCode):
        self.Reason = ErrorCode

    def __str__(self):
        if self.Reason not in self.ReasonCodes:
            return repr('Unkown error.')
        else:
            return repr(self.Reasons[self.Reason])

#TODO: wenn noetig SSL Certs implementieren
class HttpService(object):
    __URLBase = None
    __Headers = {}
    __Session = None
    __Request = None
    __Parameters = {}
    __InputData = None
    __Cookies = []
    __PrepartionIsActive = False
    __BuildNew = False
    __Path = None

    def __init__(self, Host, UseHttps=False, PortNumber=None):
        Domain = None
        Port = 80
        Protokoll = 'http'

        if not Host:
            return None
        Domain = Host
        if True == UseHttps:
            Port = 443
            Potokoll = 'https'

        if PortNumber:
            Port = PortNumber

        self.__URLBase = Protokoll + '://' + Domain + ':' + str(Port)
        self.__Session = Requests.Session()

    def setUsernameAndPassword(self, Username, Password):
        self.__Session.auth = (Username, Password)

    def addCookieFile(self, Filename, Persistent=False):
        Cookie = None
        if not OS.path.isfile(Filename):
            raise HttpServiceException(HttpServiceException.NO_COOKIE_FILE)
        File = open(Filename, r)
        for Line in File:
            Cookie += Line
        File.close()
        self.addCookieFile(Cookie, Persistent)

    def addCookieString(self, CookieString, Persistent=False):
        Cookie = Cookies.SimpleCookie()
        Cookie.load(CookieString)
        CookieDirc = {}
        for Key in Cookie:
            CookieDirc[Key] = Cookie[Key]
        if False == self.__PrepartionIsActive:
            self.__Cookies.append(CookieDirc)
            return
        if True == Persistent:
            self.__Cookies.append(CookieDirc)
            self.__BuildNew = True

    def startACall(self, Method, Path):
        self.__Path = Path
        if self.__PrepartionIsActive:
            return
        if self.__Cookies and self.__Parameters:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__Parameters, cookies=self.__Cookies)
        elif not self.__Cookies and self.__Parameters:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__Parameters)
        elif self.__Cookies and not self.__Parameters:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, cookies=self.__Cookies)
        else:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path)

        if self.__InputData:
            self.__Request.body = self.__InputData
            self.__InputData = None
        self.__PrepartionIsActive = True

    def setInputData(self, InputData):
        if True == self.__PrepartionIsActive:
            self.__Request.body = InputData
        else:
            self.__InputData = InputData

    def addParameter(self, Name, Value, Persistent=False):
        if True == self.__PrepartionIsActive:
            self.__Request.params[Name] = Value
            if True == Persistent:
                self.__Parameters[Name] = Value
                self.__BuildNew = True
        else:
            self.__Parameters[Name] = Value

    def addHeader(self, Name, Value, Persistent=False):
        if True == self.__PrepartionIsActive:
            self.__Request.headers[Name] = Value
            if True == Persistent:
                self.__Header[Name] = Value
                self.__BuildNew = True
        else:
            self.__Headers[Name] = Value
            self.__Request.headers[Name] = Value

    def call(self):
        Response = None
        ToSend = None
        SwapBody = None
        if False == self.__PrepartionIsActive:
            return None
        else:
            if True == self.__BuildNew and ('POST' == self.__Request.method.upper() or 'PUT' == self.__Request.method.upper()):
                SwapBody = self.__Request.body
                self.startACall(self.__Request.method, self.__Path)
                if SwapBody:
                    self.setInputData(SwapBody)
            try:
                ToSend = self.__Request.prepare()
                Response = self.__Session.send(ToSend)
            except Requests.exceptions.ConnectionError:
                raise HttpServiceException(HttpServiceException.NO_CONECTION)
            return Response

    def close(self):
        self.__Session.close()
        __URLBase = None
        __Headers = {}
        __Session = None
        __Request = None
        __Parameters = {}
        __InputData = None
        __Cookies = []
        __PrepartionIsActive = False
        __BuildNew = False
        __Path = None


    def __del__(self):
        self.close()

    def reset(self):
        self.__Parameters = {}
        self.__InputData = None
        self.__Cookies = {}
        self.__Headers = {}
        self.__Request = None
        self.__Path = None
        self.__PrepartionIsActive = False
        self.__BuildNew = False

        self.__Session.close()
        self.__Session = Requests.Session()
        self.__PrepartionIsActive = False

    def removeParameter(self, Key):
        if Key in self.__Parameters:
            del self.__Parameters[Key]
        if True == self.__PrepartionIsActive:
            self.__BuildNew = True
