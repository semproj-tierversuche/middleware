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
    Reasons = ['The connection is not established', 'The given cookiefile was not found', 'Wrong type given. The given type was {}, a string was exspected.', 'The given cookie must have {} field.']
    ReasonCodes = [0x0, 0x1, 0x2, 0x3]
    Reason = 0x0

    NO_CONECTION = 0x0
    NO_COOKIE_FILE = 0x1
    WRONG_COOKIE_TYPE = 0x2
    MISSING_COOKIE_FIELD = 0x3

    __AdditionalInformation = None

    def __init__(self, ErrorCode, AdditionalInformation=None):
        if self.WRONG_COOKIE_TYPE == ErrorCode or self.MISSING_COOKIE_FIELD == ErrorCode:
            self.__AdditionalInformation = AdditionalInformation
        self.Reason = ErrorCode

    def __str__(self):
        if self.Reason not in self.ReasonCodes:
            return repr('Unkown error.')
        else:
            if self.WRONG_COOKIE_TYPE == self.Reason or self.MISSING_COOKIE_FIELD:
                return repr(self.Reasons[self.Reason].format(self.__AdditionalInformation))
            else:
                return repr(self.Reasons[self.Reason])

#TODO: wenn noetig SSL Certs implementieren
class HttpService(object):
    __URLBase = None
    __PersistentHeaders = None
    __VolatileHeaders = None
    __PersistentURLParameters = None
    __VolatileURLParameter = None
    __PersistentCookies = None
    __VolatileCookies = None
    __Session = None
    __Request = None
    __InputData = None
    __PreparationIsActive = None
    __UpdatePersistentRequest = None
    __Path = None

    def __init__(self, Host, UseHttps=False, PortNumber=None):
        self.__PersistentHeaders = {}
        self.__VolatileHeaders = {}
        self.__PersistentURLParameters = {}
        self.__VolatileURLParameter = {}
        self.__PersistentCookies = []
        self.__VolatileCookies = []
        self.__PreparationIsActive = False
        self.__UpdatePersistentRequest = False
        Domain = None
        Port = 80
        Protokoll = 'http'

        if not Host or not isinstance(Host, str):
            return None
        Domain = Host
        if True == UseHttps:
            Port = 443
            Potokoll = 'https'

        if PortNumber and isinstance(Port, int):
            Port = PortNumber

        self.__URLBase = Protokoll + '://' + Domain + ':' + str(Port)
        self.__Session = Requests.Session()

    def setUsernameAndPassword(self, Username, Password):
        self.__Session.auth = (Username, Password)

    def addCookieFile(self, Filename, Persistent=False):
        Cookie = []
        if not OS.path.isfile(Filename) or False == OS.access(Filename, OS.R_OK):
            raise HttpServiceException(HttpServiceException.NO_COOKIE_FILE)
        File = open(Filename, r)
        for Line in File:
            Cookie.append(Line)
        File.close()
        for x in range(0, len(Cookie)):
            self.addCookieFile(Cookie, Persistent)

    def __checkCookie(self, CookieString):
        Cookie = Cookies.SimpleCookie()
        if not isinstance(CookieString, str):
            raise HttpServiceException(HttpServiceException.WRONG_COOKIE_TYPE, type(CookieString))
        Cookie.load(CookieString)
        if 'domain' not in Cookie:
            raise HttpServiceException(HttpServiceException.MISSING_COOKIE_FIELD, 'domain')
        if 'path' not in Cookie:
            raise HttpServiceException(HttpServiceException.MISSING_COOKIE_FIELD, 'path')
        if 'expire' not in Cookie:
            raise HttpServiceException(HttpServiceException.MISSING_COOKIE_FIELD, 'expire')
        return Cookie

    def addCookie(self, CookieString, Persistent=False):
        Cookie = self.__checkCookie(CookieString)
        if True == self.__PreparationIsActive:
            if True == Persistent:
                for Key in Cookie:
                    self.__PersistentCookies[Key] = Key + '=' + Cookie[Key].value
                    for CookieKey in Cookie[Key]:
                        self.__PersistenCookie[Key] += '; ' + CookieKey + '=' + Cookie[Key][CookieKey]
            else:
                for Key in Cookie:
                    self.__VolatileCookies[Key] = Key + '=' + Cookie[Key].value
                    for CookieKey in Cookie[Key]:
                        self.__VolatileCookies[Key] += '; ' + CookieKey + '=' + Cookie[Key][CookieKey]
            self.__UpdatePersistentRequest = True
        else:
            for Key in Cookie:
                self.__PersistentCookies[Key] = Key + '=' + Cookie[Key].value
                for CookieKey in Cookie[Key]:
                    self.__PersistenCookie[Key] += '; ' + CookieKey + '=' + Cookie[Key][CookieKey]

    def startACall(self, Method, Path):
        self.__Path = Path
        if self.__PersistentCookies and self.__PersistentURLParameters and self.__PersistentHeaders:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy(), cookies=self.__PersistentCookies.copy(), headers=self.__PersistentHeaders.copy())
        elif self.__PersistentCookies and self.__PersistentURLParameters and not self.__PersistentHeaders:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy(), cookies=self.__PersistentCookies.copy())
        elif not self.__PersistentCookies and self.__PersistentURLParameters and self.__PersistentHeaders:
             self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy(), headers=self.__PersistentHeaders.copy())
        elif not self.__PersistentCookies and self.__PersistentURLParameters and not self.__PersistentHeaders:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, params=self.__PersistentURLParameters.copy())
        elif self.__PersistentCookies and not self.__PersistentURLParameters and self.__PersistentHeaders:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, cookies=self.__PersistentCookies.copy(), headers=self.__PersistentHeaders.copy())
        elif self.__PersistentCookies and not self.__PersistentURLParameters and not self.__PersistentHeaders:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, cookies=self.__PersistentCookies.copy())
        elif not self.__PersistentCookies and not self.__PersistentURLParameters and self.__PersistentHeaders:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path, headers=self.__PersistentHeaders.copy())
        else:
            self.__Request = Requests.Request(method=Method, url=self.__URLBase + Path)
        self.__PreparationIsActive = True

    def setInputData(self, InputData):
        if not InputData:
            return
        if not isinstance(InputData, str):
            InputData = str(InputData)
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
                    self.__UpdatePersistentRequest = True
                else:
                    self.__VolatileURLParameter[Name] = Value
                    self.__UpdatePersistentRequest = True
            else:
                if True == Persistent:
                    self.__PersistentURLParameters[Name] = Value
                    self.__UpdatePersistentRequest = True
                else:
                    self.__Request.params[Name] = Value
                    self.__VolatileURLParameter[Name] = Value
        else:
            self.__PersistentURLParameters[Name] = Value

    def addHeader(self, Name, Value, Persistent=False):
        if not isinstance(Name, str):
            Name = str(Name)
        if not isinstance(Value, str):
            Value = str(Value)
        if True == self.__PreparationIsActive:
            self.__Request.headers[Name] = Value
            if True == Persistent:
                self.__PersitentHeader[Name] = Value
                self.__UpdatePersistentRequest = True
        else:
            self.__VolatileHeaders[Name] = Value
            self.__Request.headers[Name] = Value

    def call(self, AdditionalParameter=None, AdditionalHeaders=None, AdditionalPath = None):
        Response = None
        ToSend = None
        SwapBody = None
        URLParameter = {}

        if (AdditionalParameter and isinstance(AdditionalParameter, dict))\
                or (AdditionalHeaders and isinstance(AdditionalHeaders, dict))\
                or (AdditionalPath and isinstance(AdditionalPath, list)):
            self.__UpdatePersistentRequest = True

        if False == self.__PreparationIsActive:
            return None
        else:
            if True == self.__UpdatePersistentRequest:
                if self.__VolatileURLParameter:
                    URLParameter = self.__PersistentURLParameters.copy()
                    self.__PersistentURLParameters = Utils.mergeDictionaries(self.__PersistentURLParameters, self.__VolatileURLParameter)
                if self.__VolatileHeaders:
                    RequestHeaders = self.__PersistentHeaders.copy()
                    self.__PersistentHeaders = Utils.mergeDictionaries(self.__PersistentHeaders, self.__VolatileHeaders)
                if self.__VolatileCookies:
                    Cookies = self.__PersistentCookies.copy()
                    self.__PersistentCookies = Utils.mergeDictionaries(self.__PersistentCookies, self.__VolatileCookies)

                self.__Request.params = self.__PersistentURLParameters.copy()
                self.__Request.headers = self.__PersistentHeaders.copy()
                self.__Request.cookies = self.__PersistentCookies.copy()

                if AdditionalParameter and isinstance(AdditionalParameter, dict):
                    for (Key, Value) in AdditionalParameter.items():
                        if not isinstance(Key, str):
                            Key = str(Key)
                        if not isinstance(Value, str):
                            Value = str(Value)
                        self.__Request.params[Key.strip()] = Value.strip()

                if AdditionalHeaders and isinstance(AdditionalHeaders, dict):
                    for (Key, Value) in AdditionalHeaders.items():
                        if not isinstance(Key, str):
                            Key = str(Key)
                        if not isinstance(Value, str):
                            Value = str(Value)
                        self.__Request.headers[Key.strip()] = Value.strip()

                if AdditionalPath and isinstance(AdditionalPath, list):
                    OrginalUrl = self.__Request.url
                    if self.__Request.url.endswith("/"):
                        self.__Request.url += "/".join(AdditionalPath)
                    else:
                        self.__Request.url += "/" + "/".join(AdditionalPath)
            try:
                ToSend = self.__Request.prepare()
                if self.__InputData:
                    ToSend.body = self.__InputData
                    self.__InputData = None
                Response = self.__Session.send(ToSend)
            except:
                raise HttpServiceException(HttpServiceException.NO_CONECTION)

            if True == self.__UpdatePersistentRequest:
                if self.__VolatileURLParameter:
                    if not URLParameter:
                        self.__PersistentURLParameters = {}
                    else:
                        self.__PersistentURLParameters = URLParameter
                if self.__VolatileHeaders:
                    if not RequestHeaders:
                        self.__PersistentHeaders = {}
                    else:
                        self.__PersistentHeaders = RequestHeaders
                if self.__VolatileCookies:
                    if not Cookies:
                        self.__PersistentCookies = []
                    else:
                        self.__PersistentCookies = Cookies

                if AdditionalPath and isinstance(AdditionalPath, list):
                    self.__Request.url = OrginalUrl

                self.__VolatileURLParameter.clear()
                self.__VolatileHeaders.clear()
                self.__VolatileCookies.clear()

            if (len(self.__PersistentURLParameters) != len(self.__Request.params))\
                or (len(self.__PersistentHeaders) != len(self.__Request.headers))\
                or ((self.__PersistentCookies and 0 != len(self.__PersistentCookies) and not self.__Request.cookies)\
                    or (self.__Request.cookies and len(self.__PersistentCookies) != len(self.__Request.cookies))):
                self.__UpdatePersistentRequest = True
            else:
                self.__UpdatePersistentRequest = False
            return Response

    def close(self):
        if self.__Session:
            self.__Session.close()
            self.__Session = None
        self.__PersistentURLParameters.clear()
        self.__InputData = ''
        self.__PersistentCookies.clear()
        self.__PersistentHeaders.clear()
        self.__Request = None
        self.__Path = None
        self.__PreparationIsActive = False
        self.__UpdatePersistentRequest = False

    def __del__(self):
        self.close()

    def reset(self):
        self.close()
        self.__Session = Requests.Session()

    def removeParameter(self, Key):
        if Key in self.__PersistentURLParameters:
            del self.__PersistentURLParameters[Key]
        if True == self.__PreparationIsActive:
            self.__UpdatePersistentRequest = True
    def removeHeader(self, Key):
        if Key in self.__PersistentHeaders:
            del self.__PersistentHeaders[Key]
        if True == self.__PreparationIsActive:
            self.__UpdatePersistentRequest = True

    def removeCookie(self, Key):
        if Key in self.__PersistentCookies:
            del self.__PersistentCookies[Key]
        if True == self.__PreparationIsActive:
            self.__UpdatePersistentRequest = True
