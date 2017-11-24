#!/usr/bin/env python3
# requires at least python 3.4

#import http.client, urllib.parse
#from base64 import b64encode
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
    HoldBody = False

    def __init__(self, Configuration):
        Domain = None
        Port = 80
        Protokoll = 'http'

        Domain = Configuration['host']['name']
        if 'https' == Configuration['host']['protokoll']:
            Port = 443
            Potokoll = 'https'

        if Configuration['host']['port']:
            Port = Configuration['host']['port']

        self.__URLBase = Protokoll + '://' + Domain + ':' + Port
        self.__Session = Requests.Session()

    def setUsernameAndPassword(self, Username, Password):
        self.__Session.auth = (Username, Password)

    def addCookieFile(self, Filename):
        Cookie = None
        if not OS.path.isfile(Filename):
            raise HttpServiceException(HttpServiceException.NO_COOKIE_FILE)
        File = open(Filename, r)
        for Line in File:
            Cookie += Line
        File.close()
        self.addCookieFile(Cookie)

    def addCookieString(self, CookieString):
        Cookie = Cookies.SimpleCookie()
        Cookie.load(CookieString)
        CookieDirc = {}
        for Key in Cookie:
            CookieDirc[Key] = Cookie[Key]
        self.__Cookies.append(CookieDirc)

    def startACall(self, Method, Path):
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
            self.__Request.body = InputData

       # self.__Request = self.__Session.prepare_request(Req)
        self.__PrepartionIsActive = True

    def setInputData(self, InputData):
        if True == self.__PrepartionIsActive:
            self.__Request.body = InputData
        else:
            self.__InputData = InputData

    def addParameter(self, Name, Value):
        self.__Parameters[Name] = Value
        if True == self.__PrepartionIsActive:
            #if not self.__Request.parameters[Key]:
            #    for Key in self.__Parameters:
            #    self.__Request.parameters[Key] = self.__Parameters[Key]
            #else
                self.__Request.params[Name] = Value

    def addHeader(self, Name, Value):
        self.__Headers[Name] = Value
        if True == self.__PrepartionIsActive:
            #if not self.__Request.headers:
            #    for Key in self.__Headers:
            #        self.__Request.headers[Key] = self.__Headers[Key]
            #else:
                self.__Request.headers[Name] = Value

    def call(self):
        Response = None
        ToSend = None
        if False == self.__PrepartionIsActive:
            return None
        else:
            try:
                ToSend = self.__Request.prepare()
                Response = self.__Session.send(ToSend)
            except Requests.exceptions.ConnectionError:
                raise HttpServiceException(HttpServiceException.NO_CONECTION)
            if False == self.HoldBody:
                self.__Request.body = None
            return Response

    def reset(self):
        self.__Parameters = {}
        self.__InputData = None
        self.__Cookies = {}
        self.__Headers = {}

        self.__Session = Requests.Session()
        self.__PrepartionIsActive = False
        self.__Request = None

    def removeParameter(self, Key):
        if Key in self.__Parameters:
            del self.__Parameters[Key]
        if True == self.__PrepartionIsActive:
            if Key in self.__Request.params:
                del self.__Request.params[Key]
