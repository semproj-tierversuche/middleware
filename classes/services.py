#!/usr/bin/env python3
# requires at least python 3.4

from threading import Lock
from classes.http_service import HttpService

class Database(object):

    def query(self, Query):
        pass

    def delete(self, Delete):
        pass

    def insert(self, Insert):
        pass

    def update(self, Update):
        pass

class CmdAsDatabase(object):
    def __init__(self, Configuration):
        pass

class CmdAsTextmining(object):
    def __init__(self, Configuration):
        pass

class HostAsDatabase(Database):
    __Query = ''
    __QueryLock = Lock()
    __Update = ''
    __UpdateLock = Lock()
    __Delete = ''
    __DeleteLock = Lock()
    __Insert = ''
    __InsertLock = Lock()
    __Version = ''

    def __init__(self, Configuration):
        #prepare Query
        self.__Query = self.__startTransaction(Configuration['query'], HttpService(Configuration))
     #   if 'update' in Configuration:
     #       self.__Update = self.__startTransaction(Configuration['update'], HttpService(Configuration))
     #   self.__Delete = self.__startTransaction(Configuration['insert'], HttpService(Configuration))
     #   if 'delete' in Configuration:
     #       self.__Insert = self.__startTransaction(Configuration['delete'], HttpService(Configuration))

    def __startTransaction(self, Configuration, HttpObject):
        if Configuration['auth']:
            HttpObject.setUsernameAndPassword(Configuration['auth']['username'], Configuration['auth']['password'])
        for Parameter in Configuration['parameters']:
            HttpObject.addParameter(Parameter['key'], Parameter['value'])
        for Cookie in Configuration['cookies']:
            print(Cookie)
            if True == bool(Cookie['type']):
                HttpObject.addCookieString(Cookie['value'])
            else:
                HttpObject.addCookieFile(Cookie['value'])
        for Header in Configuration['headers']:
            HttpObject.addHeader(Header['key'], Header['value'])

        HttpObject.startACall(Configuration['method'], Configuration['path'])
        return HttpObject

    def __bodyless(self, Input, HttpObject):
        for Key in Input:
            HttpObject.addParameter(Key, Input[Key])
        Response = HttpObject.call()
        for Key in Input:
            HttpObject.removeParameter(Key)
        return Response

    def __withBody(self, Input, HttpObject):
        HttpObject.setInputData(Input)
        return HttpObject.call()


    def query(self, Query):
        Key = ''
        Response = ''
        if not Query:
            return
        self.__QueryLock.acquire()
        Response = self.__bodyless(Query, self.__Query)
        self.__QueryLock.release()
        return Response


    def insert(self, Insert):
        Response = ''
        if not Insert:
            return
        self.__InsertLock.acquire()
        Response = self.__withBody(Insert, self.__Insert)
        self.__QueryLock.release()
        return Response

    def update(self, Update):
        pass

    def delete(self, Delete):
        pass

    def getDBVersion(self):
        pass

class HostAsTextmining(object):
    def __init__(self, Configuration):
        pass


class Service(object):

    __Database = ''
    __TextMining = ''

    def __init__(self, Configuration):

        if "host" in Configuration._Database:
            self.__Database = HostAsDatabase(Configuration._Database)


    def callTextMining(self, JSON):
        pass

    def queryDatabase(self, Dict):
        return self.__Database.query(Dict)

    def insertIntoDatabase(self, JSON):
        return self.__Database.insert(JSON)
