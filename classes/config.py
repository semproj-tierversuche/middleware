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
        Return = {}
        Return['host'] = {}
        Node = Root.find('cmd')
        #we going on to check if we need to use something else then commandline
        if None is not Node:
            Return['cmd'] = Node.text.strip()
            del Return['host']
        else:
        #alternativ: We can say host[@protokoll@port], but we cannot exact error report
            Node = Root.find('host')
            if None is Node:
                #raise a exception
                pass
            else:
                if 'protokoll' not in Node.attrib:
                    #raise a exception
                    pass
                elif 'port' not in Node.attrib:
                    #raise a exception
                    pass
                else:
                    Return['host']['name'] = Node.text.strip()
                    Return['host']['protokoll'] = Node.attrib['protokoll'].strip()
                    Return['host']['port'] = Node.attrib['port'].strip()

        return Return

    def readSubNode(self, Node, TagName):
        Node = Node.find(TagName)
        if None is Node:
        #throw exception if not in tagsoup
            pass
        else:
            return Node.text.strip()


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
                Return['address'] = allzweckWegwerfVariable


        if 'plugin' in Node.attrib:
            if os.path.isfile('./plugin/' + Return['address'] + '/plugin.py'):
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
