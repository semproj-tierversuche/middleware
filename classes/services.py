#!/usr/bin/env python3
# requires at least python 3.4

from threading import Lock
from classes.http_service import HttpService
from classes.cmd_service import CmdService
import classes.utils as Utils
from classes.http_service import HttpServiceException

class Textmining(object):
    def do(self, Input, ParameterKey=None, ReadFromStdin=False):
        pass
    def getVersion():
        pass
    def close():
        pass
class Database(object):
    def query(self, Query):
        pass

    def delete(self, Delete):
        pass

    def insert(self, Insert):
        pass

    def update(self, Update):
        pass

class CmdAsDatabase(Database):
    def query(self, Query):
        pass
    def delete(self, Delete):
        pass
    def insert(self, Insert):
        pass
    def update(self, Update):
        pass

class CmdAsTextmining(Textmining):
    __Worker = None
    __Version = None
    __UseStdin = False

    def __init__(self, Configuration):
        Keys = []
        if 'timeout' in Configuration:
            self.__Worker = CmdService(Configuration['name'], Configuration['timeout'])
        else:
            self.__Worker = CmdService(Configuration['name'])
        if 'stdin' in Configuration:
            self.__UseStdin = Configuration['stdin']
        #fetch Version
        for x in range(0,len(Configuration['version'])-1):
            self.__Worker.addParameter(Configuration['version'][x]['key'], Configuration['version'][x]['value'])
        Stdout, Stderr = self.__Worker.do(Configuration['version'][len(Configuration['version'])-1]['key'], Configuration['version'][len(Configuration['version'])-1]['value'], CmdService.FORK_NORMAL_PROCESS, False)
        if Stderr:
            pass#Error und so
        self.__Version = Stdout.strip()
        for x in range(0, len(Configuration['version'])-1):
            self.__Worker.removeParameter(Configuration['version'][x]['key'])
        #add all params we need for execution
        for x in range(0, len(Configuration['parameter'])):
            self.__Worker.addParameter(Configuration['parameter'][x]['key'], Configuration['parameter'][x]['value'])

    def getVersion(self):
        if self.__Version:
            return self.__Version

    def do(self, Input, ParameterKey=None, ReadFromStdin=False):
        #self.__Worker.printParam()
        if not ParameterKey:
            return self.__Worker.do('', Input, CmdService.FORK_PTY_PROCESS, ReadFromStdin)
        else:
            return self.__Worker.do(ParameterKey, Input, CmdService.FORK_PTY_PROCESS, ReadFromStdin)

class HostAsDatabase(Database):
    __Query = None
    __QueryLock = Lock()
    __Update = None
    __UpdateLock = Lock()
    __Delete = None
    __DeleteLock = Lock()
    __Insert = None
    __InsertLock = Lock()
    __Version = None
    __Configuration = None

    def __init__(self, Configuration, StartQuery=True, StartInsert=False, StartUpdate=False, StartDelete=False, GetVersion=False):
        self.__Configuration = Configuration
        if True == GetVersion:
            self.getDBVersion()
        self.openDatabase(True,False)

    def openDatabase(self, Query=True, Insert=True, Update=False, Delete=False):
        if True == Query and not self.__Query:
            self.__Query = self.__prepareForHttpService('query')
        if True == Insert and not self.__Insert:
            self.__Insert = self.__prepareForHttpService('insert')
        if True == Update and not self__Update and 'update' in self.__Configuration:
             self.__Update = self.__prepareForHttpService('update')
        if True == Delete and not self.__Delete and 'delete' in self.__Configuration:
             self.__Delete = self.__prepareForHttpService('delete')

    #just for error handling...later
    def __prepareForHttpService(self, Type):
        Return = None
        if Type not in self.__Configuration:
            return Return
        if 'name' not in self.__Configuration['host']:
            pass#raise Error
        if 'port' in self.__Configuration['host']:
            Return = self.__startTransaction(self.__Configuration[Type], HttpService(self.__Configuration['host']['name'], self.__Configuration['host']['useHttps'], self.__Configuration['host']['port']))
        else:
            Return = self.__startTransaction(self.__Configuration[Type], HttpService(self.__Configuration['host']['name'], self.__Configuration['host']['useHttps']))
        return Return

    def __startTransaction(self, Configuration, HttpObject):
        if Configuration['auth']:
            HttpObject.setUsernameAndPassword(Configuration['auth']['username'], Configuration['auth']['password'])
        for Parameter in Configuration['parameter']:
            HttpObject.addParameter(Parameter, Configuration['parameter'][Parameter])
        for Cookie in Configuration['cookies']:
            if True == bool(Cookie['type']):
                HttpObject.addCookieString(Cookie['value'])
            else:
                HttpObject.addCookieFile(Cookie['value'])
        for Header in Configuration['headers']:
            HttpObject.addHeader(Header['key'], Header['value'])

        HttpObject.startACall(Configuration['method'], Configuration['path'])
        return HttpObject

    def __bodyless(self, Input, HttpObject, AdditionalParameter):
        if AdditionalParameter:
           Input = Utils.mergeDictionaries(AdditionalParameter, Input)
        for (Key, Value) in Input.items():
            HttpObject.addParameter(Key, Value, False)
        Response = HttpObject.call()
        return Response

    def __withBody(self, Input, HttpObject, AdditionalParameter):
        #we have to do this cause: https://github.com/python/cpython/blob/master/Lib/http/client.py#151
        Input = Input.encode('utf-8').decode('latin-1')
        if AdditionalParameter:
            for (Key, Value) in AdditionalParameter.items():
                HttpObject.addParameter(Key, Value, False)
        HttpObject.setInputData(Input)
        return HttpObject.call()

    def __withOrWithoutBody(self, Method, ToDo, HTTPObject, AdditionalParameter):
        Method = Method.upper()
        if AdditionalParameter and AdditionalParameter is isinstance(AdditionalParameter, dict):
            for Key in AdditionalParameter:
                if not isinstance(AdditionalParameter[Key], basestring):
                    AdditionalParameter[Key] = str(AdditionalParameter[Key])
        else:
            pass#throw error

        if 'POST' == Method:
            HTTPObject.addHeader("Content-Type", "application/x-www-form-urlencoded; multipart/form-data; charset=utf-8")
            HTTPObject.addHeader("Content-Length", str(len(ToDo)))
            Response = self.__withBody(ToDo, HTTPObject, AdditionalParameter)
        elif 'PUT' == Method:
            HTTPObject.addHeader("Content-Type", "text/plain; application/json; charset=utf-8")
            HTTPObject.addHeader("Content-Length", str(len(ToDo)))
            Response = self.__withBody(ToDo, HTTPObject, AdditionalParameter)
        else:
            Response = self.__bodyless(ToDo, HTTPObject, AdditionalParameter)
        return Response

    def query(self, Query, AdditionalParameter=None):
        Response = None
        if not self.__Query:
            self.__Query = self.__prepareForHttpService('query')
        self.__QueryLock.acquire()
        try:
            Response = self.__withOrWithoutBody(self.__Configuration['query']['method'],Query, self.__Query, AdditionalParameter)
        except HttpServiceException as e:
            self.__QueryLock.release()
            raise e
        self.__QueryLock.release()
        return Response

    def insert(self, Insert, AdditionalParameter=None):
        Response = None
        if not self.__Insert:
            self.__Insert = self.__prepareForHttpService('insert')
        self.__InsertLock.acquire()
        try:
            Response = self.__withOrWithoutBody(self.__Configuration['insert']['method'], Insert, self.__Insert, AdditionalParameter)
        except HttpServiceException as e:
            self.__InsertLock.release()
            raise e
        self.__InsertLock.release()
        return Response

    def update(self, Update, AdditionalParameter=None):
        Response = None
        if not self.__Update:
            self.__Update = self.__prepareForHttpService('update')
            if None == self.__Update:
                return None#throw error
        self.__UpdateLock.acquire()
        try:
            Response = self.__withOrWithoutBody(self.__Configuration['update']['method'],Query, self.__Update, AdditionalParameter)
        except HttpServiceException as e:
            self.__UpdateLock.release()
            raise e
        self.__UpdateLock.release()
        return Response

    def delete(self, Delete, AdditionalParameter=None):
       Response = None
       if not self.__Delete:
           self.__Delete = self.__prepareForHttpService('delete')
           if None == self.__Delete:
               return None#throw error
       self.__DeleteLock.acquire()
       try:
           Response = self.__withOrWithoutBody(self.__Configuration['delete']['method'],Query, self.__Delete, AdditionalParameter)
       except HttpServiceException as e:
           self.__DeleteLock.release()
           raise e
       self.__DeleteLock.release()
       return Response

    def getVersion(self):
        return self.__Version

    def closeUpdate(self):
        if self.__Update:
           self.__Update.close()
           self.__Update = None

    def closeDelete(self):
        if self.__Delete:
            self.__Delete.close()
            self.__Delete = None

    def closeInsert(self):
        if self.__Insert:
            self.__Insert.close()
            self.__Insert = None

    def closeQuery(self):
        if self.__Query:
            self.__Query.close()
            self.__Query = None

    def close(self):
        self.closeDelete()
        self.closeInsert()
        self.closeQuery()
        self.closeUpdate()

class HostAsTextmining(Textmining):
    def __init__(self, Configuration):
        pass

#TODO -> Fehlerbehandlung responsecodes
class DatabaseService(object):
    DATABASE_QUERY = 0x0
    DATABASE_INSERT = 0x1
    DATABASE_UPDATE = 0x2
    DATABASE_DELETE = 0x3


    __Database = None

    def __init__(self, Configuration):

        if 'host' in Configuration._Database:
            self.__Database = HostAsDatabase(Configuration._Database)
        else:
            pass
#            self.__Database = CmdAsDataBase(Configuration._Database)

    def queryDatabase(self, Dict, AdditionalParameter=None, ReconnectOnFail=False):
        try:
            Response = self.__Database.query(Dict, AdditionalParameter)
        except HttpServiceException as e:
            if True == ReconnectOnFail:
                self.reconnect(self.DATABASE_QUERY)
                Response = self.queryDatabase(Dict, AdditionalParameter, False)
            else:
                raise e
        return Response.status_code, Response.content.decode('utf-8')

    def insertIntoDatabase(self, JSON, AdditionalParameter=None, ReconnectOnFail=False):
        try:
            Response = self.__Database.insert(JSON, AdditionalParameter)
        except HttpServiceException as e:
            if True == ReconnectOnFail:
                self.reconnect(self.DATABASE_INSERT)
                Response = self.insertIntoDatabase(JSON, AdditionalParameter, False)
            else:
                raise e
        return Response.status_code, Response.content.decode('utf-8')

    def updateInDatabase(self, JSON, AdditionalParameter=None, ReconnectOnFail=False):
        try:
            Response = self.__Database.update(JSON)
        except HttpServiceException as e:
            if True == ReconnectOnFail:
                self.reconnect(self.DATABASE_UPDATE)
                Response = self.updateInDatabase(JSON, AdditionalParameter, False)
            else:
                raise e
        return Response.status_code, Response.content.decode('utf-8')

    def deleteInDatabase(self, Dict, AdditionalParameter=None, ReconnectOnFail=False):
        try:
            Response = self.__Database.delete(Dict)
        except HttpServiceException as e:
            if True == ReconnectOnFail:
                self.reconnect(self.DATABASE_DELETE)
                Response = self.deleteInDatabase(Dict, AdditionalParameter, False)
            else:
                raise e
        return Response.status_code, Response.content.decode('utf-8')

    def reconnect(self, What):
        if self.DATABASE_QUERY == What:
            self.__Database.closeQuery()
            self.__Database.openDatabase()
        elif self.DATABASE_INSERT == What:
            self.__Database.closeInsert()
            self.__Database.openDatabase(Query=Fase, Insert=True)
        elif self.DATABASE_UPDATE == What:
            self.__Database.closeUpdate()
            self.__Database.openDatabase(Query=False, Update=True)
        else:
            self.__Database.closeDelete()
            self.__Database.openDatabase(Query=False, Delete=True)

 #   def close(What:

class TextminingService(object):

    __Textmining = None

    def __init__(self, Configuration):
        if 'host' in Configuration._Textmining:
            pass
            #self.__Textmining = HostAsTextmining(Configuration._Textmining['host'])
        else:
            self.__Textmining = CmdAsTextmining(Configuration._Textmining['cmd'])
    def version(self):
        return self.__Textmining.getVersion()

    def do(self, Input, ParameterKey=None, ReadFromStdin=False):
        Stdout, Stderr = self.__Textmining.do(Input, ParameterKey, ReadFromStdin)
        if Stderr:
            pass#Error und so
        return Stdout

    def close():
        self.__Textmining.close()
