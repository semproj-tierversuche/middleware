#!/usr/bin/env python3
# requires at least python 3.4

import requests as Requests
from http import cookies as Cookies
import os as OS
import classes.utils as Utils
import urllib.parse as UrlHelper

class HttpHelper(object):

    @staticmethod
    def DicionaryToPostRequestString(Dic):
        Output = ''
        if not isinstance(Dic, dict):
            return None
        else:
            for Key, Value in Dic:
                Output += UrlHelper.quote(Key) + '=' + Helper.quote(Value) + "&"
        return Output[:-1]

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
    __PersistentURLParameters = {}
    __InputData = None
    __Cookies = []
    __PreparationIsActive = False
    __UpdateURLParameter = False
    __Path = None
    __VolatileURLParameter = {}

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
        if not isinstance(CookieString, str):
            CookieString = str(CookieString)
        for Key in Cookie:
            CookieDirc[Key] = Cookie[Key]
        if False == self.__PreparationIsActive:
            self.__Cookies.append(CookieDirc)
            return
        if True == Persistent:
            self.__Cookies.append(CookieDirc)
            self.__UpdateURLParameter = True

    def startACall(self, Method, Path):
        self.__Path = Path
        if self.__Cookies and self.__PersistentURLParameters and self.__Headers:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy(), cookies=self.__Cookies, headers=self.__Headers.copy())
        elif self.__Cookies and self.__PersistentURLParameters and not self.__Headers:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy(), cookies=self.__Cookies)
        elif not self.__Cookies and self.__PersistentURLParameters and self.__Headers:
             self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy(), headers=self.__Headers.copy())
        elif not self.__Cookies and self.__PersistentURLParameters and not self.__Headers:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy())
        elif self.__Cookies and not self.__PersistentURLParameters and self.__Headers:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, cookies=self.__Cookies, headers=self.__Headers.copy())
        elif self.__Cookies and not self.__PersistentURLParameters and not self.__Headers:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, cookies=self.__Cookies)
        elif not self.__Cookies and not self.__PersistentURLParameters and self.__Headers:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, headers=self.__Headers)
        else:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path)
            # BugFix: Lost body
#        if self.__InputData:
#            self.__Request.body = self.__InputData
#            self.__InputData = None
        self.__PreparationIsActive = True

    def setInputData(self, InputData):
        if not isinstance(InputData, str):
            InputData = str(InputData)
        #BugFix: lost body
    #    if True == self.__PreparationIsActive:
    #        self.__Request.body = InputData
    #    else:
        print(InputData)
        self.__InputData = InputData

    def addParameter(self, Name, Value, Persistent=False):
        if not isinstance(Name, str):
            Name = str(Name)
        if not isinstance(Value, str):
            Value = str(Value)
        if True == self.__PreparationIsActive:
            if Name in self.__PersistentURLParameters:
                if True == Persistent:
                    self.__PersistentURLParameters[Name] = Value
                    self.__UpdateURLParameter = True
                else:
                    self.__VolatileURLParameter[Name] = Value
                    self.__UpdateURLParameter = True
            else:
                if True == Persistent:
                    self.__PersistentURLParameters[Name] = Value
                    self.__UpdateURLParameter = True
                else:
                    self.__Request.params[Name] = Value
                    self.__VolatileURLParameter[Name] = Value
        else:
            self.__PersistentURLParameters[Name] = Value

    def addHeader(self, Name, Value, Persistent=False):
        if True == self.__PreparationIsActive:
            self.__Request.headers[Name] = Value
            if True == Persistent:
                self.__Header[Name] = Value
                self.__UpdateURLParameter = True
        else:
            self.__Headers[Name] = Value
            self.__Request.headers[Name] = Value

    def call(self):
        Response = None
        ToSend = None
        SwapBody = None
        URLParameter = {}
        if False == self.__PreparationIsActive:
            return None
        else:
            if self.__VolatileURLParameter and True == self.__UpdateURLParameter:
                URLParameter = self.__PersistentURLParameters.copy()
                self.__PersistentURLParameters = Utils.mergeDictionaries(self.__PersistentURLParameters, self.__VolatileURLParameter)

            #if True == self.__UpdateURLParameter and ('POST' == self.__Request.method.upper() or 'PUT' == self.__Request.method.upper()):
            #    SwapBody = self.__Request.body
            #elif True == self.__UpdateURLParameter:
            if True == self.__UpdateURLParameter:
                self.__Request.params = self.__PersistentURLParameters.copy()
                #self.startACall(self.__Request.method, self.__Path)
            #if SwapBody:
            #    self.setInputData(SwapBody)
            try:
                ToSend = self.__Request.prepare()
                if self.__InputData:
                    ToSend.body = self.__InputData
                    self.__InputData = None
                Response = self.__Session.send(ToSend)
            except Requests.exceptions.ConnectionError:
                raise HttpServiceException(HttpServiceException.NO_CONECTION)
            if self.__VolatileURLParameter and True == self.__UpdateURLParameter:
                self.__PersistentURLParameters = URLParameter.copy()
            self.__VolatileURLParameter.clear()
            if len(self.__PersistentURLParameters) != len(self.__Request.params):
                self.__UpdateURLParameter = True
            else:
                self.__UpdateURLParameter = False
            return Response

    def close(self):
        if self.__Session:
            self.__Session.close()
            self.__Session = None
        self.__PersistentURLParameters.clear()
        self.__InputData = ''
        self.__Cookies = []
        self.__Headers.clear()
        self.__Request = None
        self.__Path = None
        self.__PreparationIsActive = False
        self.__UpdateURLParameter = False

    def __del__(self):
        self.close()

    def reset(self):
        self.close()
        self.__Session = Requests.Session()

    def removeParameter(self, Key):
        if Key in self.__PersistentURLParameters:
            del self.__PersistentURLParameters[Key]
        if True == self.__PreparationIsActive:
            self.__UpdateURLParameter = True
