#!/usr/bin/env python3
# requires at least python 3.4

from threading import Lock
from classes.http_service import HttpService
from classes.cmd_service import CmdService
import classes.utils as Utils
from classes.http_service import HttpServiceException
import os as OS

class ServiceAsCmd(object):
    _Configuration = None
    _Encoding = None

    def __init__(self, Configuration, Encoding='utf-8'):
        self._Configuration = Configuration
        self._Encoding = Encoding

    def _prepareForCmdService(self, Type, Execution=CmdService.FORK_NORMAL_PROCESS, IgnoreFly=False):
        Cmd = None
        if 'timeout' in self._Configuration:
            Cmd  = CmdService(self._Configuration[Type]['name'], self._Configuration[Type]['timeout'])
        else:
            Cmd  = CmdService(self._Configuration[Type]['name'])
        #add all params we need for execution
        for x in range(0, len(self._Configuration[Type]['parameter'])):
            Cmd.addParameter(self._Configuration[Type]['parameter'][x])

        if True == self._Configuration[Type]['keepalive'] and self._Configuration[Type]['delimiter'] and False == IgnoreFly:
            Mode = Execution+CmdService.PERMANENT_PROCESS
            Cmd.startPermanentProcess(Delimiter=self._Configuration[Type]['delimiter'].encode(self._Encoding),\
                                      Mode=Mode, Debug=self._Configuration[Type]['debug'])
        return Cmd

class ServiceAsHttp(object):
    _Configuration = None
    _Encoding = 'utf-8'
    def __init__(self, Configuration, Encoding='utf-8'):
        self._Configuration = Configuration
        self._Encoding = Encoding

    def _prepareForHttpService(self, Type):
        Return = None
        if Type not in  self._Configuration:
            return Return
        if 'name' not in self._Configuration['host'] and 'host' not in self._Configuration[Type]:
            pass#raise Error
        if 'host' not in self._Configuration[Type]:
            if 'port' in self._Configuration['host']:
                Return = self.__startTransaction(self._Configuration[Type],\
                                                 HttpService(self._Configuration['host']['name'],\
                                                             self._Configuration['host']['useHttps'],\
                                                             self._Configuration['host']['port']))
            else:
                Return = self.__startTransaction(self._Configuration[Type],\
                                                 HttpService(self._Configuration['host']['name'],\
                                                             self._Configuration['host']['useHttps']))
        else:
            if 'port' in self._Configuration[Type]['host']:
                Return = self.__startTransaction(self._Configuration[Type],\
                                                 HttpService(self._Configuration[Type]['host']['name'],\
                                                             self._Configuration[Type]['host']['useHttps'],\
                                                             self._Configuration[Type]['host']['port']))
            else:
                Return = self.__startTransaction(self._Configuration[Type],\
                                                 HttpService(self._Configuration[Type]['host']['name'],\
                                                             self._Configuration[Type]['host']['useHttps']))

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

    def __bodyless(self, Input, HttpObject, AdditionalParameter=None, AdditionalPath=None):
        if not isinstance(Input, dict):
            return None

        if AdditionalParameter:
            if isinstance(AdditionalParameter, dict):
                Input = Utils.mergeDictionaries(AdditionalParameter, Input)
            else:
                return None

        if AdditionalPath:
            if not isinstance(AdditionalPath, list):
                return None

        return HttpObject.call(AdditionalParameter=Input, AdditionalPath=AdditionalPath)

    def __withBody(self, Input, HttpObject, AdditionalParameter=None,\
                   AdditionalHeaders=None, AdditionalPath=None):
        if AdditionalParameter:
            if not isinstance(AdditionalParameter, dict):
                return None

        if AdditionalPath:
            if not isinstance(AdditionalPath, list):
                return None
        #we have to do this cause: https://github.com/python/cpython/blob/master/Lib/http/client.py#151
        Input = Input.encode(self._Encoding).decode('latin-1')
        HttpObject.setInputData(Input)
        return HttpObject.call(AdditionalParameter=AdditionalParameter,\
                               AdditionalHeaders=AdditionalHeaders,\
                               AdditionalPath=AdditionalPath)

    def _withOrWithoutBody(self, Method, ToDo, HTTPObject,\
                           AdditionalParameter=None, AdditionalPath=None):
        Method = Method.upper()

        if 'POST' == Method:
            Response = self.__withBody(ToDo, HTTPObject, AdditionalParameter=AdditionalParameter,\
                                       AdditionalPath=AdditionalPath,\
                                       AdditionalHeaders = {'Content-Type':'application/x-www-form-urlencoded;\
                                        multipart/form-data; charset=' + self._Encoding,\
                                        'Content-Length': str(len(ToDo))})
        elif 'PUT' == Method:
            Response = self.__withBody(ToDo, HTTPObject, AdditionalParameter=AdditionalParameter,\
                                       AdditionalPath=AdditionalPath,\
                                       AdditionalHeaders={'Content-Type':'text/plain; application/json;\
                                        charset=' + self._Encoding,\
                                        'Content-Length':str(len(ToDo))})
        else:
            Response = self.__bodyless(ToDo, HTTPObject,\
                                       AdditionalParameter=AdditionalParameter,\
                                       AdditionalPath=AdditionalPath)
        return Response

    def _responseFormatter(self, Response):
        if Response is None:#do not change this into not Response...python will allway consider a response object as negated
            raise TypeError("Invalid value given to http service.")
        Response.close()# Should not normally need to be called explicitly....
        if 200 != Response.status_code:
            return (Response.status_code, '', Response.content.decode(self._Encoding))
        else:
            return (Response.status_code, Response.content.decode(self._Encoding), '')

class Textmining(object):
    def do(self, Input=None, AdditionalParameter=None):
        pass
    def getVersion():
        pass
    def reconnect():
        pass
    def close():
        pass
class Database(object):
    def query(self, Query, AdditionalParameter=None, AdditionalPath=None):
        pass

    def delete(self, Delete, AdditionalParameter=None, AdditionalPath=None):
        pass

    def insert(self, Insert, AdditionalParameter=None, AdditionalPath=None):
        pass

    def update(self, Update, AdditionalParameter=None, AdditionalPath=None):
        pass

class CmdAsDatabase(Database):
    def openDatabase(self, Query=True, Insert=True, Update=False, Delete=False):
        pass
    def query(self, Query):
        pass
    def delete(self, Delete):
        pass
    def insert(self, Insert):
        pass
    def update(self, Update):
        pass
    def closeQuery(self):
        pass
    def closeInsert(self):
        pass
    def closeUpdate(self):
        pass
    def closeDelete(self):
        pass
    def close(self):
        self.closeQuery()
        self.closeInsert()
        self.closeUpdate()
        self.closeDelete()
    def __del__(self):
        self.close()
class CmdAsTextmining(ServiceAsCmd, Textmining):
    _Worker = None
    __Version = None
    __Lock = None

    def __init__(self, Configuration):
        ServiceAsCmd.__init__(self, Configuration)
        self._Worker = ServiceAsCmd._prepareForCmdService(self, 'cmd',CmdService.FORK_NORMAL_PROCESS)
        self.__Lock = Lock()

    def do(self, Input=None, AdditionalParameter=None, IgnoreMe=None):
        Keys = []
        if AdditionalParameter:
            if not isinstance(AdditionalParameter, list):
                return None

        if Input:
            Input = Input.encode(self._Encoding)
        ReturnCode,Stdout, Stderr = self._Worker.do(StdinData=Input, Mode=CmdService.FORK_NORMAL_PROCESS,\
                                                          AdditionalParameter=AdditionalParameter)
        Stdout = Stdout.decode(self._Encoding)
        Stderr = Stderr.decode(self._Encoding)
        return (ReturnCode, Stdout, Stderr)

    def reconnect(self):
        if True == self._Configuration[Type]['keepalive']:
            self._Worker.close()
            self._Worker = ServiceAsCmd._prepareForCmdService(self, 'cmd',\
                                                              CmdService.FORK_NORMAL_PROCESS)

    def getVersion(self):
        if not self.__Version:
            Version = ServiceAsCmd._prepareForCmdService(self, 'cmd',\
                                                         CmdService.FORK_NORMAL_PROCESS, True)
            for x in range(0,len(self._Configuration['cmd']['version'])):
                Version.addParameter(self._Configuration['cmd']['version'][x])
            Returncode, Stdout, Stderr = Version.do()
            if Stderr:
                pass#Error und so

            Stdout = Stdout.decode(self._Encoding)
            Stderr = Stderr.decode(self._Encoding)
            self.__Version = Stdout.strip()
            Version.close()
        return self.__Version

    def close(self):
        if self._Worker:
            self._Worker.close()
            self._Worker = None
            return

    def __del__(self):
        self.close()

class HostAsDatabase(Database, ServiceAsHttp):
    _Query = None
    __QueryLock = Lock()
    _Update = None
    __UpdateLock = Lock()
    _Delete = None
    __DeleteLock = Lock()
    _Insert = None
    __InsertLock = Lock()
    __Version = None

    def __init__(self, Configuration, StartQuery=True, StartInsert=False, StartUpdate=False, StartDelete=False):
        ServiceAsHttp.__init__(self,  Configuration)
        self.openDatabase(StartQuery, StartInsert, StartUpdate, StartDelete)

    def openDatabase(self, Query=True, Insert=True, Update=False, Delete=False):
        if True == Query and not self._Query:
            self._Query = ServiceAsHttp._prepareForHttpService(self, 'query')
        if True == Insert and not self._Insert:
            self._Insert = ServiceAsHttp._prepareForHttpService(self, 'insert')
        if True == Update and not self._Update and 'update' in self._Configuration:
             self._Update = ServiceAsHttp._prepareForHttpService(self, 'update')
        if True == Delete and not self._Delete and 'delete' in self._Configuration:
             self._Delete = ServiceAsHttp._prepareForHttpService(self, 'delete')

    #just for error handling...later
    def query(self, Query, AdditionalParameter=None, AdditionalPath=None):
        Response = None
        if not self._Query:
            self._Query = ServiceAsHttp._prepareForHttpService(self, 'query')
        self.__QueryLock.acquire()
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['query']['method'],\
                                                        Query, self._Query,\
                                                        AdditionalParameter,\
                                                        AdditionalPath)
        except HttpServiceException as e:
            raise e
        finally:
            self.__QueryLock.release()
        return ServiceAsHttp._responseFormatter(self, Response)

    def insert(self, Insert, AdditionalParameter=None, AdditionalPath=None):
        Response = None
        if not self._Insert:
            self._Insert = ServiceAsHttp._prepareForHttpService(self, 'insert')
        self.__InsertLock.acquire()
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['insert']['method'],\
                                                        Insert, self._Insert,\
                                                        AdditionalParameter,\
                                                        AdditionalPath)
        except HttpServiceException as e:
            raise e
        finally:
            self.__InsertLock.release()
        return ServiceAsHttp._responseFormatter(self, Response)

    def update(self, Update, AdditionalParameter=None, AdditionalPath=None):
        Response = None
        if not self._Update:
            self._Update = ServiceAsHttp._prepareForHttpService(self, 'update')
            if None == self._Update:
                return None#throw error
        self.__UpdateLock.acquire()
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['update']['method'],\
                                                        Update, self._Update,\
                                                        AdditionalParameter,\
                                                        AdditionalPath)
        except HttpServiceException as e:
            raise e
        finally:
            self.__UpdateLock.release()
        return ServiceAsHttp._responseFormatter(self, esponse)

    def delete(self, Delete, AdditionalParameter=None, AdditionalPath=None):
       Response = None
       if not self._Delete:
           self._Delete = ServiceAsHttp._prepareForHttpService(self, 'delete')
           if None == self._Delete:
               return None#throw error
       self.__DeleteLock.acquire()
       try:
           Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['delete']['method'],\
                                                       Delete, self._Delete,\
                                                       AdditionalParameter,\
                                                       AdditionalPath)
       except HttpServiceException as e:
           raise e
       finally:
           self.__DeleteLock.release()
       return ServiceAsHttp._responseFormatter(self, Response)

    def getVersion(self):
        if -1 == Version:
            Version = ServiceAsHttp._prepareForHttpService(self, 'version')
            self.__QueryLock.acquire()
            try:
                Response = self._withOrWithoutBody(self, self._Configuration['version']['method'], Input, Version, {})
            except HttpServiceException as e:
                self.__QueryLock.release()
                Version.close()
                raise e
            else:
                self.__Version = Response.content.decode(self._Encoding)
            finally:
                Version.close()
                Response.close()
                self.__QueryLock.release()

    def reconnect(self, Query=False, Insert=False, Update=False, Delete=False):
        if True == Query:
            self.closeQuery()
        if True == Insert:
            self.closeInsert()
        if True == Update:
            self.closeUpdate()
        if True == Delete:
            self.closeDelete()

        self.open(Query, Insert, Update, Delete)
    def closeUpdate(self):
        if self._Update:
           self._Update.close()
           self._Update = None

    def closeDelete(self):
        if self._Delete:
            self._Delete.close()
            self._Delete = None

    def closeInsert(self):
        if self._Insert:
            self._Insert.close()
            self._Insert = None

    def closeQuery(self):
        if self._Query:
            self._Query.close()
            self._Query = None

    def close(self):
        self.closeDelete()
        self.closeInsert()
        self.closeQuery()
        self.closeUpdate()

    def __del__(self):
        self.close()
class HostAsTextmining(Textmining, ServiceAsHttp):
    _Worker = None
    __Version = None
    __Lock = Lock()

    def __init__(self, Configuration, Encoding='utf-8'):
        ServiceAsHttp.__init__(self, Configuration, Encoding)
        self._Worker = ServiceAsHttp._prepareForHttpService(self, 'cmd')

    def do(self, Input, AdditionalParameter=None, AdditionalPath=None):
        Response = None

        if AdditionalPath:
            if not isinstance(AdditionalParameter, list):
                return None

        if AdditionalParameter:
            if not isinstance(AdditionalParameter, list):
                return None
        self.__Lock.acquire()
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['cmd']['method'],\
                                                        Input, self._Worker,\
                                                        AdditionalParameter=AdditionalParameter,\
                                                        AdditionalPath=AdditionalPath)
        except HttpServiceException as e:
            raise e
        finally:
            self.__Lock.release()
        return ServiceAsHttp._responseFormatter(self, Response)


    def getVersion(self):
        if not self.__Version:
            Version = self._prepareForHttpService(self, 'version')
            try:
                Response = self._withOrWithoutBody(self, self._Configuration['version']['method'], '', Version, {})
            except HttpServiceException as e:
                raise e
            else:
                self.__Version = Response.content.decode(self._Encoding)
                Response.close()
            finally:
                Version.close()
        return self.__Version

    def reconnect(self):
        self.close()
        self.__Worker = ServiceAsHttp._prepareForHttpService(self, 'cmd')

    def close(self):
        if self.__Worker:
            self.__Worker.close()
            self.__Worker = None
            return ('', '')

    def __del__(self):
        self.close()
#TODO -> Fehlerbehandlung responsecodes
class DatabaseService(object):
    DATABASE_QUERY = 0x0
    DATABASE_INSERT = 0x1
    DATABASE_UPDATE = 0x2
    DATABASE_DELETE = 0x3
    DATABASE_ALL = 0x4


    __Database = None

    def __init__(self, Configuration):

        if 'host' in Configuration._Database:
            self.__Database = HostAsDatabase(Configuration._Database)
        else:
            pass

    def queryDatabase(self, Dict, AdditionalParameter=None, ParameterAsPath=False,RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.query(Dict, AdditionalParameter, ParameterAsPath)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_QUERY)
                Code, Out, Error = self.queryDatabase(Dict, AdditionalParameter, ParameterAsPath, False)
            else:
                raise e
        return (Code, Out, Error)

    def insertIntoDatabase(self, JSON, AdditionalParameter=None, ParameterAsPath=False, RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.insert(JSON, AdditionalParameter,  ParameterAsPath)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_INSERT)
                Code, Out, Error = self.insertIntoDatabase(JSON, AdditionalParameter, False)
            else:
                raise e
        return (Code, Out, Error)

    def updateInDatabase(self, JSON, AdditionalParameter=None, ParameterAsPath=False, RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.update(JSON, AdditionalParameter, ParameterAsPath)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_UPDATE)
                Code, Out, Error = self.updateInDatabase(JSON, AdditionalParameter, ParameterAsPath, False)
            else:
                raise e
            return (Code, Out, Error)

    def deleteInDatabase(self, Dict, AdditionalParameter=None, ParameterAsPath=False, RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.delete(Dict, AdditionalParameter,  ParameterAsPath)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_DELETE)
                Code, Out, Error = self.deleteInDatabase(Dict, AdditionalParameter, ParameterAsPath, False)
            else:
                raise e
            return (Code, Out, Error)

    def reconnect(self, What):
        if self.DATABASE_QUERY == What or self.DATABASE_ALL == What:
            self.__Database.closeQuery()
            self.__Database.openDatabase()
        if self.DATABASE_INSERT == What or self.DATABASE_ALL == What:
            self.__Database.closeInsert()
            self.__Database.openDatabase(Query=False, Insert=True)
        if self.DATABASE_UPDATE == What or self.DATABASE_ALL == What:
            self.__Database.closeUpdate()
            self.__Database.openDatabase(Query=False, Update=True)
        if self.DATABASE_DELETE == What  or self.DATABASE_ALL == What:
            self.__Database.closeDelete()
            self.__Database.openDatabase(Query=False, Delete=True)

    def close(self, What=DATABASE_ALL):
       if self.DATABASE_QUERY == What  or self.DATABASE_ALL == What:
           self.__Database.closeQuery()
       if self.DATABASE_INSERT == What or self.DATABASE_ALL == What:
           self.__Database.closeInsert()
       if self.DATABASE_UPDATE == What or self.DATABASE_ALL == What:
           self.__Database.closeUpdate()
       if self.DATABASE_DELETE == What or self.DATABASE_ALL == What:
           self.__Database.closeDelete()

    def __del__(self):
        if not self.__Database:
            return
        self.close()

class TextminingService(object):

    _Textmining = None
    __Lock = Lock()

    def __init__(self, Configuration):
        if 'host' in Configuration._Textmining:
            self._Textmining = HostAsTextmining(Configuration._Textmining)
        else:
            self._Textmining = CmdAsTextmining(Configuration._Textmining)
    def version(self):
        return self._Textmining.getVersion()

    def do(self, Input, AdditionalParameter=None, AdditionalPath=None,\
           RetryOnFail=False):
        self.__Lock.acquire()
        if True == RetryOnFail:
            try:
                ReturnCode, Stdout, Stderr = self._Textmining.do(Input, AdditionalParameter, AdditionalPath)
            except HttpServiceException as e:
                self.__Textmining.reconnect()
                ReturnCode, Stdout, Stderr = self._Textmining.do(Input, AdditionalParameter, AdditionalPath)
            finally:
                self.__Lock.release()

            if (ReturnCode != CmdService._OK and 0 > ReturnCode) or 1 == ReturnCode:
                self.__Textmining.reconnect()
                ReturnCode, Stdout, Stderr = self._Textmining.do(Input, AdditionalParameter, AddtionalPath)
        else:
            ReturnCode, Stdout, Stderr = self._Textmining.do(Input,\
                                                             AdditionalParameter,\
                                                             AdditionalPath)
            self.__Lock.release()
        return (ReturnCode, Stdout, Stderr)

    def close(self):
        if self._Textmining:
            return self._Textmining.close()

    def __del__(self):
        self.close()
