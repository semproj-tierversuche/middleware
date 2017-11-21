#!/usr/bin/env python3
# requires at least python 3.4

import xml.etree.ElementTree as DOM
import os

#Konstanten
PLUGIN_STREAM = 0x0
PLUGIN_PULK = 0x1

class ConfigReader(object):
    __Root = ''
    _Textmining = {}
    _Database = {}
    _Resources = []
    _Threads = 1

    def parseConfigFile(self, ConfigFile):

        Document = DOM.parse(ConfigFile)
        self.__Root = Document.getroot()
        self.readTextmining()
        self.readDatabase()
        self.readResources()
        self.readMaxThreads()

    def readService(self, Root):
        Node =''
        Nodes = []
        Return = {}
        Return['cmd'] = {}
        Return['cmd']['param'] = []
        Return['host'] = {}

        Node = Root.find('cmd')
        #we going on to check if we need to use something else then commandline
        if None is not Node:
            Return['cmd']['name'] = Node.text.strip()
            del Return['host']
            Nodes = Node.findall('param')
            if Nodes:
                for Node in Nodes:
                    if Node.text.strip():
                        Return['cmd']['param'].append(Node.text.strip())
        else:
        #alternativ: We can say host[@protokoll@port], but we cannot exact error report
            Node = Root.find('host')
            if None is Node:
                #raise a exception
                pass
            else:
                del Return['cmd']
                if 'protokoll' not in Node.attrib:
                    #raise a exception
                    pass
                elif 'port' not in Node.attrib:
                    #raise a exception
                    pass
                else:
                    Return['host']['name'] = Node.text.strip()
                    Return['host']['protokoll'] = Node.attrib['protokoll'].strip().lower()
                    Return['host']['port'] = Node.attrib['port'].strip()

        return Return

    def readSubNode(self, Node, TagName):
        NodeStrich = ''
        Nodes = []
        Return = {}
        Return['parameters'] = []
        Return['cookies'] = []
        Return['path'] = {}

        NodeStrich = Node.find(TagName)
        Node = NodeStrich
        if None is Node:
        #throw exception if not in tagsoup
            pass
        elif 'method' not in Node.attrib or not Node.attrib['method'].strip():
            #throw exception
            pass
        else:
            Return['method'] = Node.attrib['method'].strip().upper()
            Node = NodeStrich.find('path')
            if None is Node or not Node.text.strip():
                #throw exception if not in tagsoup
                pass
            else:
                Return['path']['url'] = Node.text.strip()
                if 'username' in Node.attrib and 'password' in Node.attrib and Node.attrib['username'].strip() and Node.attrib['password']:
                    Retrun['path']['username'] = Node.attrib['username'].strip()
                    Return['path']['password'] = Node.attrib['password']
                Nodes = NodeStrich.findall('param')
                if Nodes:
                    for Node in Nodes:
                        if Node.text.strip():
                            Return['parameters'].append(Node.text.strip())

                Nodes = NodeStrich.findall('cookie')
                if Nodes:
                    for Node in Nodes:
                        if Node.text.strip() and 'type' in Node.attrib:
                            if 'storage' == Node.attrib['type']:
                                Return['cookies'].append({'type': 0, 'value:':Node.text.strip()})
                            elif 'string' == Node.attrib['type']:
                                Return['cookies'].append({'type': 1, 'value:':Node.text.strip()})
        return Return


    def readTextmining(self):
        Node = ''

        Node = self.__Root.find('./services/textmining')
        if None is Node:
            #throw exception if not in tagsoup
            pass
        else:
            self._Textmining = self.readService(Node)

    def readDatabase(self):
        Node = ''

        Node = self.__Root.find('./services/database')
        if None is Node:
            #throw exception if not in tagsoup
            pass
        else:
            self._Database = self.readService(Node)
            self._Database['query'] = self.readSubNode(Node, 'query')
            self._Database['store'] = self.readSubNode(Node, 'store')

    def readMaxThreads(self):
        Node = ''
        Threads = 0

        Node = self.__Root.find('./limitations/threads')
        if None is Node:
            #throw exception if not in tagsoup -> warning
                pass
        else:
            Threads = Node.text.strip()
            if True is not isinstance(Threads, int) and 0>= int(Threads):
                #throw exception if it is not a integer
                pass
            self._Threads = int(Threads)

    def readRules(self, Nodes):
        Node = ''

        Return = {}
        Return['contains'] = []
        Return['date'] = []
        Return['ending'] = []
        Return['end_date'] = []
        Return['pattern'] = []
        Return['start_date'] = []
        for Node in Nodes:
            if 'flag' not in Node.attrib:
                continue
            Flag = Node.attrib['flag'].strip()
            #Why the hack has python no switch and case...narf
            if 'contains' == Flag:
                Return['contains'].append(Node.text.strip())
            elif 'start_date' == Flag:
                Return['start_date'].append(Node.text.strip())
            elif 'end_date' == Flag:
                Return['end_date'].append(Node.text.strip())
            elif 'endswith' == Flag:
                Return['ending'].append(Node.text.strip())
            elif 'pattern' == Flag:
                Return['pattern'].append(Node.text.strip())
            elif 'date' == Flag:
                Return['date'].append(Node.text.strip())
            else:
            #wir könnten ne Warunung ausgeben
                pass
        return Return

    def readExcludeRules(self, Node):
        Nodes = []

        Nodes = Node.findall('excludeFiles')
        return self.readRules(Nodes)

    def readIncludeRules(self, Node):
        Nodes = []

        Nodes = Node.findall('includeFiles')
        return self.readRules(Nodes)

    def readResourceRules(self, Node):
        Return = {}
        Return['exclusions'] = self.readExcludeRules(Node)
        Return['inclusions'] = self.readIncludeRules(Node)
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
                Return['onInitializion'] = 1
            else:
                Return['onInitializion'] = 0

        return Return

    def readSubFolders(self, Node):
        Return = []
        Nodes = []
        Nodes = Node.findall('./subFolder')
        if not Node:
            #Exception
            pass
        else:
            for Node in Nodes:
                Return.append(self.readSubFolder(Node))
        return Return


    def readResource(self, Node):
        Return = {}
        Return['folders'] = []
        Return['rules'] = {}
        Nodes = ''
        allzweckWegwerfVariable = ''

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
            if os.path.isfile('./plugin/' + Return['domain'] + '/plugin.py'):
                if 'pulk' == Node.attrib['plugin'].text.strip():
                    Return['plugin'] = PLUGIN_PULK
                else:
                    Return['plugin'] = PLUGIN_STREAM
            else:
            #raise a excption as warning
                pass
        else:
            Return['plugin'] = 0

        if 'xlstTransformation' in Node.attrib:
            allzweckWegwerfVariable = Node.attrib['xlstTransformation'].strip()
            if os.path.isfile(allzweckWegwerfVariable):
                Return['xslt'] = allzweckWegwerfVariable
            else:
            #raise a exception
                pass

        if 'md5Check' in Node.attrib:
            Return['md5'] = 1
        else:
            Return['md5'] = 0


        Return['folders'] = self.readSubFolders(Node)
        if not Return['folders']:
            #Exceptio
            pass
        Return['rules'] = self.readResourceRules(Node)
        return Return


    def readResources(self):
        Nodes = ''

        Nodes = self.__Root.findall('./resourceCollection/resource')
        if not Nodes:
        #raise Exception
            pass
        else:
            for Node in Nodes:
                self._Resources.append(self.readResource(Node))
