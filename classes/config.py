#!/usr/bin/env python3
# requires at least python 3.4

from xml.etree import ElementTree as DOM
import os as OS
import codecs as Codex
import json as JSON
from pathlib import Path
import time as Time

class ConfigException(Exception):
    Reasons = ['The given Element was not found.']
    ReasonCodes = [0x0]
    Reason = 0x0
    NOT_FOUND = 0x0
    def __init__(self, ErrorCode):
        self.Reason = ErrorCode
        def __str__(self):
            if self.Reason not in self.ReasonCodes:
                return repr('Unkown error.')
            else:
                return repr(self.Reasons[self.Reason])

#Konstanten
PLUGIN_STREAM = 0x0
PLUGIN_PULK = 0x1

class ConfigReader(object):
    __Root = None
    _Textmining = {}
    _Database = {}
    _Resources = []
    _General = {}

    def parseConfigFile(self, ConfigFile):
        Go = False
        CacheFile = OS.path.dirname(OS.path.abspath(ConfigFile)) + '/.configCache'
        if OS.path.isfile(CacheFile) and OS.stat(ConfigFile).st_mtime < OS.stat(CacheFile).st_mtime:
            Cache = JSON.load(open(CacheFile))
            if str(Cache['check']) != str(int(OS.stat(CacheFile).st_mtime)):
                Go = False
            else:
                self._Textmining = Cache['textmining']
                self._Database = Cache['database']
                self._Resources = Cache['resources']
                self._General = Cache['general']
                return

        if False == Go:
            Document = DOM.parse(ConfigFile)
            self.__Root = Document.getroot()
            self.readTextmining()
            self.readDatabase()
            self.readResources()
            self.readGeneral()
            if True == OS.access(OS.path.dirname(OS.path.abspath(ConfigFile)), OS.W_OK):
                ToCache = {}
                ToCache['textmining'] = self._Textmining
                ToCache['database'] = self._Database
                ToCache['resources'] = self._Resources
                ToCache['general'] = self._General
                ToCache['check'] = int(Time.time())
                with open(CacheFile, 'w') as OutFile:
                    JSON.dump(ToCache, OutFile)

    def readCmdAttributes(self, Nodes):
        Return = []
        for Node in Nodes:
            if 'key' in Node.attrib and Node.attrib['key'].strip():
                if Node.text and Node.text.strip():
                    Return.append({'key' : Node.attrib['key'].strip(), 'value': Node.text.strip()})
                else:
                    Return.append({'key' : Node.attrib['key'].strip(), 'value':''})
        return Return

    def readHostConfiguration(self, Node, Return):
        if 'useHttps' in Node.attrib:
            Return['host']['useHttps'] = True
        else:
            Return['host']['useHttps'] = False
        if 'port' in Node.attrib:
            Return['host']['port'] = str(int(Node.attrib['port'].strip()))

    def readCmdConfiguration(self, Node, Return):
        if 'keepalive' in Node.attrib and Node.attrib['keepalive']:
            Char = Codex.decode(Node.attrib['keepalive'], "hex").decode('utf-8')
            if 1 == len(Char):
                Return['cmd']['keepalive'] = True
                Return['cmd']['delimiter'] = Char
            else:
                Return['cmd']['keepalive'] = False
        else:
            Return['cmd']['keepalive'] = False
        if 'endOfStream' in Node.attrib and Node.attrib['endOfStream']:
            Char = Codex.decode(Node.attrib['endOfStream'], "hex").decode('utf-8')
            if 1 == len(Char):
                Return['cmd']['readOnlyEnd'] = True
                Return['cmd']['endDelimiter'] = Char
            else:
                Return['cmd']['readOnlyEnd'] = False
        else:
            Return['cmd']['readOnlyEnd'] = False


        if 'timeout' in Node.attrib and Node.attrib['timeout'].strip():
            Timeout = int(Node.attrib['timeout'].strip())
            if 0<Timeout:
                Return['cmd']['timeout'] = Timeout

        if 'readFromStdin' in Node.attrib:
            Return['cmd']['stdin'] = True
        else:
            Return['cmd']['stdin'] = False

    def readService(self, Root):
        Node =None
        Nodes = []
        Timeout = 0
        Return = {}
        Return['cmd'] = {}
        Return['cmd']['parameter'] = {}
        Return['cmd']['version'] = {}

        Return['host'] = {}

        Node = Root.find('cmd')
        #we going on to check if we need to use something else then commandline
        if None is not Node:
            Return['cmd']['version'] = {}
            Order = {}
            if 'name' not in Node.attrib or not Node.attrib['name'].strip():
                pass

            Return['cmd']['name'] = Node.attrib['name'].strip()
            del Return['host']

            self.readCmdConfiguration(Node, Return)

            Nodes = Node.findall('param')
            if Nodes:
                Return['cmd']['parameter'] = self.readCmdAttributes(Nodes)

            Nodes = Node.findall('version')
            if not Nodes:
                pass#error
            else:
                Return['cmd']['version'] = self.readCmdAttributes(Nodes)
        else:
            Node = Root.find('host')
            if None is Node:
                #raise a exception
                pass
            else:
                del Return['cmd']
                self.readHostConfiguration(Node, Return)
                Return['host']['name'] = Node.text.strip()

        return Return
    def readSubNode(self, Configuration, Node, TagName):
        if 'host' in Configuration:
            return self.readSubNodeHttp(Node, TagName)
        else:
            return self.readSubNodeCmd(Node, TagName)

    def readSubNodeCmd(self, Node, TagName):
        Return = {}
        if 'cmd' in Node.attrib and Node.attrib['cmd']:
            Return['cmd'] = {}
            Return['cmd']['name'] = Node.attrib['cmd']
            self.readCmdConfiguration(Node, Return)

        Return['parameter'] = {}
        Nodes = Node.findall('param')
        if Nodes:
            for Node in Nodes:
                if 'key' in Node.attrib and Node.attrib['key'].strip():
                    Return['parameter'][Node.attrib['key'].strip()] = Node.text

        return Return

    def readSubNodeHttp(self, Node, TagName):
        NodeStrich = None
        Nodes = []
        Return = {}
        Return['parameter'] = {}
        Return['cookies'] = []
        Return['headers'] = []
        Return['path'] = None
        Return['auth'] = {}

        NodeStrich = Node.find(TagName)
        Node = NodeStrich
        if None is Node:
        #throw exception if not in tagsoup
            pass
        elif 'method' not in Node.attrib or not Node.attrib['method'].strip():
            #throw exception
            pass
        else:
            if 'host' in Node.attrib and Node.attrib['host']:
                Return['host'] = {}
                self.readHostConfiguration(Node, Return)
                Return['host']['name'] = Node.attrib['host'].strip()

            if 'username' in Node.attrib and 'password' in Node.attrib and Node.attrib['username'].strip():
                Return['auth']['username'] = Node.attrib['username'].strip()
                Return['auth']['password'] = Node.attrib['password']
            Return['method'] = Node.attrib['method'].strip().upper()

            if 'path' not in Node.attrib or not Node.attrib['path'].strip():
                #throw exception if not in tagsoup
                pass
            else:
                Return['path'] = Node.attrib['path'].strip()
                Nodes = NodeStrich.findall('param')
                if Nodes:
                    for Node in Nodes:
                        if 'key' in Node.attrib and Node.attrib['key'].strip():
                            Return['parameter'][Node.attrib['key'].strip()] = Node.text

                Nodes = NodeStrich.findall('cookie')
                if Nodes:
                    for Node in Nodes:
                        if Node.text.strip() and 'type' in Node.attrib:
                            if 'storage' == Node.attrib['type']:
                                Return['cookies'].append({'type': 0, 'value':Node.text.strip()})
                            elif 'string' == Node.attrib['type']:
                                Return['cookies'].append({'type': 1, 'value':Node.text.strip()})

                Nodes = NodeStrich.findall('header')
                if Nodes:
                    for Node in Nodes:
                        if 'name' in Node.attrib and Node.attrib['name']:
                            Return['headers'].append({'name': Node.attrib['name'].strip(), 'value':Node.text.strip()})
        return Return

    def readTextmining(self):
        Node = None

        Node = self.__Root.find('./services/textmining')
        if None is Node:
            #throw exception if not in tagsoup
            pass
        else:
            self._Textmining = self.readService(Node)

    def readDatabase(self):
        Node = None

        Node = self.__Root.find('./services/database')
        if None is Node:
            #throw exception if not in tagsoup
            pass
        else:
            self._Database = self.readService(Node)
            self._Database['version'] = self.readSubNode(self._Database, Node, 'version')
            self._Database['query'] = self.readSubNode(self._Database, Node, 'query')
            self._Database['insert'] = self.readSubNode(self._Database, Node, 'insert')
            self._Database['update'] = self.readSubNode(self._Database, Node, 'update')
            self._Database['delete'] = self.readSubNode(self._Database, Node, 'delete')

    def readGeneral(self):
        Node = None
        Subnode = None
        Threads = 0

        Node = self.__Root.find('./general')
        if None is Node:
            pass

        Subnode = self.__Root.find('./general/threads')
        if None is Subnode:
            pass
        else:
            Threads = Subnode.text.strip()
            if True is not isinstance(Threads, int) and 0>= int(Threads):
                #throw exception if it is not a integer
                pass
            self._General['threads'] = int(Threads)

        Subnode = self.__Root.find('./general/logfile')
        if None is Subnode:
            pass
        else:
            Logfile = Subnode.text.strip()
            Logfile = Logfile.rstrip("/")
            if not Logfile:
                pass
            elif not OS.path.isdir(Logfile) or True == OS.path.islink(Logfile):
                pass
            Head, Tail = OS.path.split(Logfile)
            Logfile = OS.path.dirname(OS.path.abspath(Logfile))
            if not("/" == Logfile[-1:]):
                Logfile += "/"
            Logfile += Tail
            if not OS.access(Logfile, OS.W_OK):
                pass
            else:
                if not("/" == Logfile[-1:]):
                    self._General['logfile'] = Logfile + "/"
                else:
                    self._General['logfile'] = Logfile
                self._General['logfile'] += "tierv.log"
        Subnode = self.__Root.find('./general/tmp')
        if None is Subnode:
            pass
        else:
            Tmpdir = Subnode.text.strip()
            Tmpdir = Tmpdir.rstrip("/")
            if not Tmpdir:
                pass
            elif not OS.path.isdir(Tmpdir) or True == OS.path.islink(Tmpdir):
                pass
            Head, Tail = OS.path.split(Tmpdir)
            Tmpdir = OS.path.dirname(OS.path.abspath(Tmpdir))
            if not("/" == Tmpdir[-1:]):
                Tmpdir += "/"
            Tmpdir += Tail
            if not OS.access(Tmpdir, OS.W_OK) or not OS.access(Tmpdir, OS.R_OK):
                pass
            else:
                if not("/" == Tmpdir[-1:]):
                    self._General['tmpdir'] = Tmpdir + "/"
                else:
                    self._General['tmpdir'] = Tmpdir

    def readRules(self, Nodes):
        Node = None

        Return = {}
        Return['contains'] = []
        Return['date'] = []
        Return['starts'] = []
        Return['ends'] = []
        Return['end_date'] = ''
        Return['pattern'] = []
        Return['start_date'] = ''
        for Node in Nodes:
            if 'flag' not in Node.attrib:
                continue
            Flag = Node.attrib['flag'].strip()
            #Why the hack has python no switch and case...narf
            if 'contains' == Flag:
                Return['contains'].append(Node.text.strip())
            elif 'startdate' == Flag:
                Return['start_date'] = Node.text.strip()
            elif 'end_date' == Flag:
                Return['enddate'] = Node.text.strip()
            elif 'endswith' == Flag:
                Return['ends'].append(Node.text.strip())
            elif 'startswith' == Flag:
                Return['starts'].append(Node.text.strip())
            elif 'pattern' == Flag:
                Return['pattern'].append(Node.text.strip())
            elif 'date' == Flag:
                Return['date'].append(Node.text.strip())
            else:
            #wir könnten ne Warunung ausgeben
                pass
        return Return

    def readRuleSet(self, Node, Which):
        Nodes = []
        Nodes = Node.findall(Which)
        return self.readRules(Nodes)

    def readResourceRules(self, Node):
        Return = {}
        Return['exclusions'] = self.readRuleSet(Node, "./excludeFiles")
        Return['inclusions'] = self.readRuleSet(Node, "./includeFiles")
        return Return

    def readSubFolder(self, Node):
        Return = {}
        allzweckWegwerfVariable = Node.text.strip()
        if not allzweckWegwerfVariable:
        #Exception
            pass
        else:
            Return['name'] = allzweckWegwerfVariable
            if 'onInitializion' in Node.attrib:
                Return['onInitializion'] = True
            else:
                Return['onInitializion'] = False
            Return['ruleset'] = self.readResourceRules(Node)

        return Return

    def readSubFolders(self, Node):
        Return = []
        Nodes = []
        Element = None
        Nodes = Node.findall('./subFolder')
        if not Node:
            #Exception
            pass
        else:
            for Node in Nodes:
                Element = self.readSubFolder(Node)
                if True == Element['onInitializion']:
                    Return.insert(0, Element)
                else:
                    Return.append(Element)

        return Return

    def readResource(self, Node):
        Return = {}
        Return['folders'] = []
        Nodes = None
        allzweckWegwerfVariable = None

        if 'domain' not in Node.attrib:
        #raise a exception
            pass
        else:
            allzweckWegwerfVariable = Node.attrib['domain'].strip()
            if not allzweckWegwerfVariable:
                #Exception
                pass
            else:
                Return['domain'] = allzweckWegwerfVariable

        if 'plugin' in Node.attrib:
            if OS.path.isfile('./plugin/' + Node.attrib['plugin'].strip() + '/plugin.py'):
              Return['plugin'] = './plugin/' + Node.attrib['plugin'].strip() + '/plugin.py'
            #raise a excption as warning
        else:
            if OS.path.isfile('./plugin/' + Return['domain'] + '/plugin.py'):
                Return['plugin'] = './plugin/' + Return['domain'] + '/plugin.py'
            else:
                Return['plugin'] = None
                #error

        if 'md5Check' in Node.attrib:
            Return['md5'] = True
        else:
            Return['md5'] = False


        Return['folders'] = self.readSubFolders(Node)
        if not Return['folders']:
            #Exceptio
            pass
        Return['ruleset'] = self.readResourceRules(Node)
        return Return

    def readResources(self):
        Nodes = None

        Nodes = self.__Root.findall('./resourceCollection/resource')
        if not Nodes:
        #raise Exception
            pass
        else:
            for Node in Nodes:
                self._Resources.append(self.readResource(Node))
