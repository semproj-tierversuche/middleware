#!/usr/bin/env python3
# requires at least python 3.4

from threading import Lock
from classes.http_service import HttpService
from classes.cmd_service import CmdService
import classes.utils as Utils
from classes.http_service import HttpServiceException

class ServiceAsCmd(object):
    _Configuration = None
    _Encoding = None

    def __init__(self, Configuration, Encoding='utf-8'):
        self._Configuration = Configuration
        self._Encoding = Encoding

    def _prepareForCmdService(self, Type, Execution=CmdService.FORK_PTY_PROCESS):
        Cmd = None
        if 'timeout' in self._Configuration:
            Cmd  = CmdService(self._Configuration[Type]['name'], self._Configuration[Type]['timeout'])
        else:
            Cmd  = CmdService(self._Configuration[Type]['name'])
        #fetch Version
#        if True == GetVersion and -1 == self._Version:
#            for x in range(0,len(self._Configuration[Type]['version'])-1):
#                Cmd.addParameter(self._Configuration[Type]['version'][x]['key'], self._Configuration[Type]['version'][x]['value'])
#            Returncode, Stdout, Stderr = Cmd.do(self._Configuration[Type]['version'][len(self._Configuration[Type]['version'])-1]['key'], self._Configuration[Type]['version'][len(self._Configuration[Type]['version'])-1]['value'], CmdService.FORK_NORMAL_PROCESS, False)
#            if Stderr:
#                pass#Error und so
#            self._Version = Stdout.strip()
#            for x in range(0, len(self._Configuration[Type]['version'])-1):
#                Cmd.removeParameter(self._Configuration[Type]['version'][x]['key'])
        #add all params we need for execution
        for x in range(0, len(self._Configuration[Type]['parameter'])):
            if not self._Configuration[Type]['parameter'][x]['value']:
                Cmd.addParameter(self._Configuration[Type]['parameter'][x]['key'], '')
            else:
                Cmd.addParameter(self._Configuration[Type]['parameter'][x]['key'], self._Configuration[Type]['parameter'][x]['value'])
        if True == self._Configuration[Type]['keepalive'] and self._Configuration[Type]['delimiter']:
            if True == self._Configuration['stdin']:
                Cmd.startPermanentProcess(self._Configuration[Type]['delimiter'], Execution, True)
            else:
                Cmd.startPermanentProcess(self._Configuration[Type]['delimiter'], Execution, False)
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
        if 'name' not in self._Configuration['host']:
            pass#raise Error
        if 'port' in self._Configuration['host']:
            Return = self.__startTransaction(self._Configuration[Type], HttpService(self._Configuration['host']['name'], self._Configuration['host']['useHttps'], self._Configuration['host']['port']))
        else:
            Return = self.__startTransaction(self._Configuration[Type], HttpService(self._Configuration['host']['name'], self._Configuration['host']['useHttps']))
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
        Input = Input.encode(self._Encoding).decode('latin-1')
        if AdditionalParameter:
            for (Key, Value) in AdditionalParameter.items():
                HttpObject.addParameter(Key, Value, False)
        HttpObject.setInputData(Input)
        return HttpObject.call()

    def _withOrWithoutBody(self, Method, ToDo, HTTPObject, AdditionalParameter):
        Method = Method.upper()
        if AdditionalParameter and AdditionalParameter is isinstance(AdditionalParameter, dict):
            for Key in AdditionalParameter:
                if not isinstance(AdditionalParameter[Key], basestring):
                    AdditionalParameter[Key] = str(AdditionalParameter[Key])
        else:
            pass#throw error

        if 'POST' == Method:
            HTTPObject.addHeader("Content-Type", "application/x-www-form-urlencoded; multipart/form-data; charset=" + self._Encoding)
            HTTPObject.addHeader("Content-Length", str(len(ToDo)))
            Response = self.__withBody(ToDo, HTTPObject, AdditionalParameter)
        elif 'PUT' == Method:
            HTTPObject.addHeader("Content-Type", "text/plain; application/json; charset=" + self._Encoding)
            HTTPObject.addHeader("Content-Length", str(len(ToDo)))
            Response = self.__withBody(ToDo, HTTPObject, AdditionalParameter)
        else:
            Response = self.__bodyless(ToDo, HTTPObject, AdditionalParameter)
        return Response

    def _responseFormatter(self, Response):
        Response.close()# Should not normally need to be called explicitly....
        if 200 != Response.status_code:
            return (Response.status_code, '', Response.content.decode(self._Encoding))
        else:
            return (Response.status_code, Response.content.decode(self._Encoding), '')

class Textmining(object):
    def do(self, Input, ParameterKey=None, AdditionalParameter=None):
        pass
    def getVersion():
        pass
    def reconnect():
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

    def reconnect(What):
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

class CmdAsTextmining(ServiceAsCmd, Textmining):
    __Worker = None
    __Version = None

    def __init__(self, Configuration):
        ServiceAsCmd.__init__(self, Configuration)
        self.__Worker = ServiceAsCmd._prepareForCmdService(self, 'cmd',CmdService.FORK_PTY_PROCESS)

    def do(self, Input, ParameterKey=None, AdditionalParameter=None, ReadFromStdin=False):
        Keys = []
        if AdditionalParameter:
            for Key in AdditionalParameter:
                self.__Worker.addParameter(Key, AdditionalParameter[Key])
        if not ParameterKey:
            ReturnCode, Stdout, Stderr = self.__Worker.do('', Input, CmdService.FORK_PTY_PROCESS, ReadFromStdin)
        else:
            ReturnCode, Stdout, Stderr = self.__Worker.do(ParameterKey, Input, CmdService.FORK_PTY_PROCESS, ReadFromStdin)
        if AdditionalParameter:
            for Key in AdditionalParameter:
                self.__Worker.removeParameter(Key)
        return (ReturnCode, Stdout, Stderr)

    def reconnect(self):
        if True == self.__Worker._FlyingProcess:
            self.__Worker.close()
            self.__Worker = ServiceAsCmd.__prepareForCmdService(self, 'cmd',CmdService.FORK_PTY_PROCESS)

    def getVersion(self):
        if not self.__Version:
            Version = ServiceAsCmd._prepareForCmdService(self, 'cmd', CmdService.FORK_NORMAL_PROCESS)
            for x in range(0,len(self._Configuration['cmd']['version'])-1):
                Version.addParameter(self._Configuration['cmd']['version'][x]['key'], self._Configuration['cmd']['version'][x]['value'])
            Returncode, Stdout, Stderr = Version.do(self._Configuration['cmd']['version'][len(self._Configuration['cmd']['version'])-1]['key'], self._Configuration['cmd']['version'][len(self._Configuration['cmd']['version'])-1]['value'], CmdService.FORK_NORMAL_PROCESS)
            if Stderr:
                pass#Error und so
            self.__Version = Stdout.strip()
            Version.close()
            return self.__Version
        else:
            return self.__Version

    def close(self):
        if self.__Worker:
            self.__Worker.close()

class HostAsDatabase(Database, ServiceAsHttp):
    __Query = None
    __QueryLock = Lock()
    __Update = None
    __UpdateLock = Lock()
    __Delete = None
    __DeleteLock = Lock()
    __Insert = None
    __InsertLock = Lock()
    __Version = None

    def __init__(self, Configuration, StartQuery=True, StartInsert=False, StartUpdate=False, StartDelete=False):
        ServiceAsHttp.__init__(self,  Configuration)
        self.openDatabase(StartQuery, StartInsert, StartUpdate, StartDelete)

    def openDatabase(self, Query=True, Insert=True, Update=False, Delete=False):
        if True == Query and not self.__Query:
            self.__Query = ServiceAsHttp._prepareForHttpService(self, 'query')
        if True == Insert and not self.__Insert:
            self.__Insert = ServiceAsHttp._prepareForHttpService(self, 'insert')
        if True == Update and not self.__Update and 'update' in self._Configuration:
             self.__Update = ServiceAsHttp._prepareForHttpService(self, 'update')
        if True == Delete and not self.__Delete and 'delete' in self._Configuration:
             self.__Delete = ServiceAsHttp._prepareForHttpService(self, 'delete')

    #just for error handling...later
    def query(self, Query, AdditionalParameter=None):
        Response = None
        if not self.__Query:
            self.__Query = ServiceAsHttp._prepareForHttpService(self, 'query')
        self.__QueryLock.acquire()
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['query']['method'],Query, self.__Query, AdditionalParameter)
        except HttpServiceException as e:
            raise e
        finally:
            self.__QueryLock.release()
        return ServiceAsHttp._responseFormatter(self, Response)

    def insert(self, Insert, AdditionalParameter=None):
        Response = None
        if not self.__Insert:
            self.__Insert = ServiceAsHttp._prepareForHttpService(self, 'insert')
        self.__InsertLock.acquire()
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['insert']['method'], Insert, self.__Insert, AdditionalParameter)
        except HttpServiceException as e:
            raise e
        finally:
            self.__InsertLock.release()
        return ServiceAsHttp._responseFormatter(self, Response)

    def update(self, Update, AdditionalParameter=None):
        Response = None
        if not self.__Update:
            self.__Update = ServiceAsHttp._prepareForHttpService(self, 'update')
            if None == self.__Update:
                return None#throw error
        self.__UpdateLock.acquire()
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['update']['method'],Query, self.__Update, AdditionalParameter)
        except HttpServiceException as e:
            raise e
        finally:
            self.__UpdateLock.release()
        return ServiceAsHttp._responseFormatter(self, esponse)

    def delete(self, Delete, AdditionalParameter=None):
       Response = None
       if not self.__Delete:
           self.__Delete = ServiceAsHttp._prepareForHttpService(self, 'delete')
           if None == self.__Delete:
               return None#throw error
       self.__DeleteLock.acquire()
       try:
           Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['delete']['method'],Query, self.__Delete, AdditionalParameter)
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

class HostAsTextmining(Textmining, ServiceAsHttp):
    __Worker = None
    __Version = None
    __Lock = Lock()

    def __init__(self, Configuration, Encoding='utf-8'):
        ServiceAsHttp.__init__(self, Configuration, Encoding)
        self.__Worker = ServiceAsHttp._prepareForHttpService(self, 'cmd')
#        Version = self._prepareForHttpService(self, 'version')
#       try:
#            Response = self._withOrWithoutBody(self, self._Configuration['version']['method'], '', Version, {})
#        except HttpServiceException as e:
#            raise e
#        else:
#            self.__Version = Response.content.decode(self._Encoding)
#            Response.close()
#        finally:
#            Version.close()

    def do(self, Input, ParameterKey=None, AddtionailParameter=None, ReadFromStdin=False):
        Response = None
        self.__Lock.acquire()
#        if not self.__Worker:
#            self.__Worker = ServiceAsHttp._prepareForHttpService(self, 'cmd')
        try:
            Response = ServiceAsHttp._withOrWithoutBody(self, self._Configuration['cmd']['method'], Input, self.__Worker, AdditionalParameter)
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
#            self.__Database = CmdAsDataBase(Configuration._Database)

    def queryDatabase(self, Dict, AdditionalParameter=None, RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.query(Dict, AdditionalParameter)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_QUERY)
                Code, Out, Error = self.queryDatabase(Dict, AdditionalParameter, False)
            else:
                raise e
        return (Code, Out, Error)

    def insertIntoDatabase(self, JSON, AdditionalParameter=None, RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.insert(JSON, AdditionalParameter)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_INSERT)
                Code, Out, Error = self.insertIntoDatabase(JSON, AdditionalParameter, False)
            else:
                raise e
        return (Code, Out, Error)

    def updateInDatabase(self, JSON, AdditionalParameter=None, RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.update(JSON)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_UPDATE)
                Code, Out, Error = self.updateInDatabase(JSON, AdditionalParameter, False)
            else:
                raise e
            return (Code, Out, Error)

    def deleteInDatabase(self, Dict, AdditionalParameter=None, RetryOnFail=False):
        try:
            Code, Out, Error = self.__Database.delete(Dict)
        except HttpServiceException as e:
            if True == RetryOnFail:
                self.reconnect(self.DATABASE_DELETE)
                Code, Out, Error = self.deleteInDatabase(Dict, AdditionalParameter, False)
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

    __Textmining = None
    __Lock = Lock()

    def __init__(self, Configuration):
        if 'host' in Configuration._Textmining:
            self.__Textmining = HostAsTextmining(Configuration._Textmining)
        else:
            self.__Textmining = CmdAsTextmining(Configuration._Textmining)
    def version(self):
        return self.__Textmining.getVersion()

    def do(self, Input, ParameterKey=None, AdditionalParameter=None, ReadFromStdin=False, RetryOnFail=False):
        self.__Lock.acquire()
        if True == RetryOnFail:
            try:
                ReturnCode, Stdout, Stderr = self.__Textmining.do(Input, ParameterKey, AdditionalParameter, ReadFromStdin)
            except HttpServiceException as e:
                self.reconnect()
                ReturnCode, Stdout, Stderr = self.__Textmining.do(Input, ParameterKey, AdditionalParameter, ReadFromStdin)

            if ReturnCode != CmdService._OK and 0 > ReturnCode:
                self.reconnect()
                ReturnCode, Stdout, Stderr = self.__Textmining.do(Input, ParameterKey, AdditionalParameter, ReadFromStdin)
        else:
            ReturnCode, Stdout, Stderr = self.__Textmining.do(Input, ParameterKey, AdditionalParameter, ReadFromStdin)
        return (ReturnCode, Stdout, Stderr)

    def close(self):
        if self.__Textmining:
            self.__Textmining.close()

    def __del__(self):
        self.close()
