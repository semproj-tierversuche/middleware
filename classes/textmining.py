#!/usr/bin/env python3
# requires at least python 3.4

from classes.config import ConfigReader
from classes.utils import mergeDictionaries as merge
import classes.ResourceDownloader as RD
import classes.services as Services
import logging as Logger
import os as OS
import sys as Sys
import traceback as Trace
import imp as Plugins
import threading as Threads
from lxml import etree as DOM
from copy import deepcopy as Copy
from collections import OrderedDict
import json as JSON

class Textmining(object):

    __Configuration = None
    __LastUpdate = None
    __Downloader = None
    __Database = None
    __Textmining = None
    __Log = None
    __DocumentPushLock = None
    __BioCLock = None
    __Articles = None
    #__LastUpdate = None
    #the following is just a Hack, this should be removed
    #if the database do their job as agree upon
    #also the programmlogic has to ajusted
    __DataTree = None


    #step 1 -> reading config and start everything
    def __init__(self, ConfigurationFile):
        self.__DocumentPushLock = Threads.Lock()
        self.__BioCLock = Threads.Lock()
        self.__Articles = {}
        #self.__LastUpdate = {}
        self.__DataTree = {}
        self.__Configuration = ConfigReader()
        self.__Configuration.parseConfigFile(ConfigurationFile)
        #1.a -> start Logger
        self.__Log = Logger.getLogger("Alternativen zu Tierversuchen: ")
        #self.__Log.setLevel(Logger.NOTSET)
        LogFile = Logger.FileHandler(self.__Configuration._General['logfile'])
        Formatter = Logger.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        LogFile.setFormatter(Formatter)
        self.__Log.addHandler(LogFile)
        #1.b -> start Downloader
        self.__Downloader = RD.ResourceDownloader(self.__Configuration._General['tmpdir'])
        #1.c -> start Services
        self.__Database = Services.DatabaseService(self.__Configuration)
        self.__Textmining = Services.TextminingService(self.__Configuration)
        #1.d -> set Lastupdate to 0, to index right from the scratch
        self.__LastUpdate = 0
        self.__Log.info("Start Textmining")

    #def __getLastUpdate(self, Domain):
    def __getLastUpdate(self):
        if OS.path.isfile(self.__Configuration._General['tmpdir'] + '.dataTree.json'):
            self.__DataTree = JSON.load(open(self.__Configuration._General['tmpdir'] + '.dataTree.json'))
            for (Domain, Sets) in self.__DataTree.items():
                if self.__DataTree[Domain]['TextminingVersion'] != str(self.__Textmining.getVersion()):
                    self.__DataTree[Domain]['Date'] = 0
                    self.__DataTree[Domain]['Articles'] = {}
                else:
                    self.__DataTree[Domain]['Date'] = float(self.__DataTree[Domain]['Date'])
        else:
            self.__DataTree = {}
        #That's way it should be....but thanks to SM...so do not delete it it could be useful in the (far) future
        #Query = OrderedDict()
        #Query['type'] = 'utils'
        #Query['Resourcename'] = Domain
        #StatusCode , ResourceInformation, Error = self.__Database.queryDatabase(Query, ParameterAsPath=True)
        #if 200 == StatusCode:
        #    ResourceInformation = JSON.load(ResourceInformation)
        #    if str(ResourceInformation['TMVersion']) != self.__Textmining.version():
        #        self.__LastUpdate[Domain] = 0
        #    else:
        #        self.__LastUpdate[Domain] = float(ResourceInformation['lastupdate'])
        #else:
        #    self.__LastUpdate[Domain] = 0

    @staticmethod
    def sortInit(Entry):
        if Entry[0]['init']:
            return 0
        else:
            return 1

    #set 2 -> download the files and begin the
    def downloadFiles(self):
        for Domain in self.__Configuration._Resources:
            self.__Log.info("Start to download form " + Domain['domain'])
            #self.__getLastUpdate(Domain['domain'])
            self.__getLastUpdate()
            i = 0
            Flag = [True]
            FileContainer = []
            for Resource in Domain['folders']:
                j = 0
                self.__Downloader.setBaseAddress(Domain['domain'])
                Subdir = self.__Configuration._General['tmpdir'] + str(i)
#                if 0 != self.__LastUpdate[Domain['domain']] and True == Resource['onInitializion']:
                if self.__DataTree\
                    and Domain in self.__DataTree\
                    and 0 != self.__DataTree[Domain]['Date'] and True == Resource['onInitializion']:
                    continue
                Inclusions = merge(Resource['ruleset']['inclusions'], Domain['ruleset']['inclusions'])
                Exclusions = merge(Resource['ruleset']['exclusions'], Domain['ruleset']['exclusions'])
                #2a -> apply the given Filters
                self.__setFilters(Exclusions, Inclusions)
                #2b -> add Download Folder
                self.__Downloader.addSubFolder(Resource['name'], Domain['md5'])
                #2d create a subfolder
                if not OS.path.isdir(Subdir):
                    OS.mkdir(Subdir)
                #2c -> download the Files
                while 0 != len(self.__Downloader._DownloadableFiles):
                    try:
                        self.__Downloader.downloadFile(str(i))
                    except (RD.ResourceDownloaderException, Exception) as e:
                        if isinstance(e, RD.ResourceDownloaderException):
                            if RD.ResourceDownloaderException.FILE_EXISTS == e.Reason:
                                continue
                            else:
                                self.__Log.warning(str(e) + "\n" + " Skipping...")
                                continue
                        else:
                            Traceroute = Trace.format_exc()
                            self.__Log.error(str(e) + "\n" + Traceroute)
                            OS._exit(0)
                    if 1 == j:
                        break
                    j = j+1
                Files = []
                for File in self.__Downloader._DownloadedFiles:
                    if not Resource['plugin']:
                       Files.append({'init': Resource['onInitializion'],'File':Subdir + "/" + File.Name,\
                                    'path': Domain['domain'] + "/" + Resource['name'].lstrip(".").lstrip("/"),\
                                    'plugin' : Domain['plugin']})
                    else:
                        Files.append({'init': Resource['onInitializion'],'File':Subdir + "/" + File.Name,\
                                      'path': Domain['domain'] + "/" + Resource['name'].lstrip(".").lstrip("/"),\
                                      'plugin': Resource['plugin']})
                FileContainer.append(Files)
                self.__Downloader.reset()
                self.__Log.info("Downloaded " + Resource['name'].lstrip(".").lstrip("/"))
                i = i+1

            self.__getBioC(Domain['prefix'], Domain['domain'], FileContainer)


    def __setFilter(self, Values, Flag):
        for Value in Values:
            self.__Downloader.filterFiles(Value, Flag)

    def __setFilters(self, Exlcusions, Inclusions):
        #first of all we have set our Update Filter
        if 0 != self.__LastUpdate:
            self.__Downloader.filterFiles(self.__LastUpdate, self.__Downloader.FILTER_FILE_EXCLUDE_END_DATE)
        if Exlcusions['start_date']:
            self.__Downloader.filterFiles(Exlcusions['start_date'], self.__Downloader.FILTER_FILE_EXCLUDE_START_DATE)
        if Exlcusions['end_date']:
            self.__Downloader.filterFiles(Exlcusions['end_date'], self.__Downloader.FILTER_FILE_EXCLUDE_START_DATE)
        if Exlcusions['date']:
            self.__Downloader.filterFiles(Exlcusions['date'], self.__Downloader.FILTER_FILE_EXCLUDE_DATE)
        if Exlcusions['ends']:
            self.__setFilter(Exlcusions['ends'], self.__Downloader.FILTER_FILE_EXCLUDE_ENDS_WITH)
        if Exlcusions['starts']:
            self.__setFilter(Exlcusions['starts'], self.__Downloader.FILTER_FILE_EXCLUDE_STARTS_WITH)
        if Exlcusions['contains']:
            self.__setFilter(Exlcusions['contains'], self.__Downloader.FILTER_FILE_EXCLUDE_CONTAINS)
        if Exlcusions['pattern']:
            self.__setFilter(Exlcusions['pattern'], self.__Downloader.FILTER_FILE_EXCLUDE_PATTERN)

        if Inclusions['start_date']:
            self.__Downloader.filterFiles(Inclusions['start_date'], self.__Downloader.FILTER_FILE_INCLUDE_START_DATE)
        if Inclusions['end_date']:
            self.__Downloader.filterFiles(Inclusions['end_date'], self.__Downloader.FILTER_FILE_INCLUDE_START_DATE)
        if Inclusions['date']:
            self.__Downloader.filterFiles(Inclusions['date'], self.__Downloader.FILTER_FILE_INCLUDE_DATE)
        if Inclusions['ends']:
            self.__setFilter(Inclusions['ends'], self.__Downloader.FILTER_FILE_INCLUDE_ENDS_WITH)
        if Inclusions['starts']:
            self.__setFilter(Inclusions['starts'], self.__Downloader.FILTER_FILE_INCLUDE_STARTS_WITH)
        if Inclusions['contains']:
            self.__setFilter(Inclusions['contains'], self.__Downloader.FILTER_FILE_INCLUDE_CONTAINS)
        if Inclusions['pattern']:
            self.__setFilter(Inclusions['pattern'], self.__Downloader.FILTER_FILE_INCLUDE_PATTERN)

    def __findEntry(self, Where, ToFind):
        if not Where:
            return -1
        else:
            Start = 0
            End = len(Where)-1

            while Start <= End:
                Mid = Start+((End-Start)>>1)
                Entry = int(Where[Mid]['PMID'])
                if ToFind == Entry:
                    return Mid
                else:
                    if Entry > ToFind:
                        End = Mid-1
                    else:
                        Start = Start+1
            return -1

    @staticmethod
    def sortEntries(Entry):
        return Entry['PMID']

    def __getBioC(self, Prefix, Domain, FileContainer):
        self.__BioCLock.acquire()
        for Container in FileContainer:

#            SearchPath, File = OS.path.split(Container['plugin'])
#            if not SearchPath in Sys.path:
#                Sys.path.append(SearchPath)
#                Sys.path.append(OS.path.normpath(SearchPath+"/../"))
#            FP, PathName, Description = Plugins.find_module("plugin", [SearchPath,])
#            Module = Plugins.load_module("plugin", FP, PathName, Description)

#            FileDescriptor = {}
#            FileDescriptor['name'] = File
#            FileDescriptor['prefix'] = Prefix
#            FileDescriptor['plugin'] = Module
#            FileDescriptor['Articles'] = []
#            FileDescriptor['ArticlesBioC'] = []

            for File in Container:
                SearchPath, IgnoreMe = OS.path.split(File['plugin'])
                if not SearchPath in Sys.path:
                    Sys.path.append(SearchPath)
                    Sys.path.append(OS.path.normpath(SearchPath+"/../"))
                FP, PathName, Description = Plugins.find_module("plugin", [SearchPath,])
                Module = Plugins.load_module("plugin", FP, PathName, Description)

                FileDescriptor = {}
                FileDescriptor['name'] = File
                FileDescriptor['prefix'] = Prefix
                FileDescriptor['plugin'] = Module
                FileDescriptor['Articles'] = []
                FileDescriptor['ArticlesBioC'] = DOM.Element("Collection")


                Articles, NonBioCInformations = Module.Plugin.bioCPreprocessing(File['File'], File['path'])
                if len(Articles) != len(NonBioCInformations):
                    self.__Log.warning("The given Plugin {} is malfunction. Skipping all content of {}.".format(Plug, File['File']))
                    continue
                while 0 != len(Articles):
                    Article = Articles.pop(0)
                    Information = NonBioCInformations.pop(0)

                    Information['PMID'] = int(Information['PMID'])
                    Information["Authors"] = sorted(Information["Authors"])
                    if Information["Keywords"]:
                        Information["Keywords"] = sorted(Information["Keywords"])

                    Information['TextminingVersion'] = self.__Textmining.version()
                    Information['Suggest'] = ''
                    Information['Abstract'] = ''
                    Information['Title'] = ''
                    Information['Annotations'] = []
                    Information['Identifier'] = []
                    Information['Substances'] = []

                    if Domain in self.__DataTree:
                        Index = self.__findEntry(self.__DataTree[Domain]['Articles'], Information['PMID'])
                    else:
                        Index = -1
                    if -1 != Index:
                        Date = int(self.__DataTree[Domain]['Articles']['Date'])
                        if 0 == Date or 0 == int(Information['Date']) or 0 == self.__DataTree[Domain]['LastUpdate']:
                            BioC = Module.Plugin.toBioC(Article, File['path'])
                            Information['update'] = True
                            FileDescriptor['Articles'].append(Information)
                            #perhaps there is a better way then this, but actually I does not know
                            #and the copy-append is slower then that
                            FileDescriptor['ArticlesBioC'].append(Copy(BioC.find("./document")))
                            del BioC

                        else:
                            if Date < float(Information['Date']):
                                BioC = Module.Plugin.toBioC(Article, File['path'])
                                Information['update'] = True
                                FileDescriptor['Articles'].append(Information)
                                FileDescriptor['ArticlesBioC'].append(Copy(BioC.find("./document")))
                                del BioC
                            #else means we already up to date
                    else:
                         BioC = Module.Plugin.toBioC(Article, File['path'])
                         Information['update'] = False
                         FileDescriptor['Articles'].append(Information)
                         FileDescriptor['ArticlesBioC'].append(Copy(BioC.find("./document")))
                         del BioC

                #Also this has to be changed if the database works like exspected
                #Query = OrderedDict()
                #Query['type'] = 'document'
                #Query['PMID'] = Prefix + str(Information['PMID'])
                #RetrunCode, Document, Ignore = self.__Database.queryDatabase(Query, ParameterAsPath=True)
                #we only have to update the article if the last update is older then current
                #if not Document:
                #    StatusCode = 400
                #if 200 == ReturnCode:
                #    Document = JSON.load(Document)
                    #is always older if we can not determine the last update date
                #    if 0 == int(Document['Date']) or  0 == int(Information['Date'])  or 0 == self.__LastUpdate[Domain]:
                #        BioC = Module.Plugin.toBioC(Article, OriginalPath)
                #        Information['update'] = True
                #        Information['bioC'] = BioC
                #        FileDescriptor['Articles'].append(Information)
                #    else:
                #        if float(Document['Date']) < float(Information['Date']):
                #            BioC = Module.Plugin.toBioC(Article, OriginalPath)
                #            Information['update'] = True
                #            Information['bioC'] = BioC
                #            FileDescriptor['Articles'].append(Information)
                #or we insert if the article does not exist in the datebase
                #else:
                #    BioC = Modlue.Plugin.toBioC(Article, OriginalPath)
                #    Information['update'] = False
                #    Information['bioC'] = BioC
                #    FileDescriptor['Articles'].append(Information)

            FileDescriptor['Articles'] = sorted(FileDescriptor['Articles'], key=Textmining.sortEntries)
            FileDescriptor['ArticlesBioC'] = '<?xml version="1.0" encoding="utf-8"?>\
                                        <!DOCTYPE collection SYSTEM "./BioC.dtd">' +\
                                        DOM.tostring(FileDescriptor['ArticlesBioC']).decode('utf-8')
            self.__throwAgainstTextMining(Domain, FileDescriptor)
        self.__BioCLock.release()

    def __throwAgainstTextMining(self, Domain, FileDescriptor):
        OS._exit(0)
        try:
            if self.__Configuration._Textmining["terminator"]:
                RetrunCode, Stdout, Stderr = self.__Textmining.do(FileDescriptor['ArticlesBioC']\
                                                                  + "\n" + self.__Configuration._Textmining["terminator"])
            else:
                RetrunCode, Stdout, Stderr = self.__Textmining.do(FileDescriptor['ArticlesBioC'])
        except Exception as e:
            Traceroute = Trace.format_exc()
            self.__Log.error(str(e) + "\n" + Traceroute)
            OS._exit(0)
        #just free some memory
        del FileDescriptor['ArticlesBioC']
        if Stderr:
            self.__Log.warning(Stderr)
        if not Stdout:
            self.__Log.error("Got no output. The return code of the program was {}.\
                             Check cmd_service.py constants and those of the called programm.\
                             Exiting" + ReturnCode)
            OS._exit(0)
        FileDescriptor['ArticlesBioC'] = DOM.fromstring(Stdout)
        del Stdout
        self.__parseResult(FileDescriptor)

    def __parseResult(self, FileDescriptor):
        #first we catch all articles of a file
        Articles = FileDescriptor['ArticlesBioC'].findeAll("./document")
        for Article in Articles:
            ID = int(Article.find("./ID").text.strip())
            #we match the ID to a our FD
            Index = self.__findEntry(FileDescriptor['Articles'], ID)
            if -1 == Index:
                Traceroute = Trace.format_stack()
                self.__Log.fatal("The given id {} does not match with anyone in the\
                                 strorage".format(ID) + "\n" + Tracerout)
                OS._exit(0)
            else:
                #we have our Article pointer...
                Passages = Article.findAll("./passage")
                for Passage in Passages:
                    Type = Passage.find("./infon[@key='type']").text.strip().lower()
                    if 'abstract' == Type:
                        FileDescriptor['Articles'][Index]['Abstract'] =\
                            Passage.find('text').text.stip()
                    elif 'title' == Type:
                        FileDescriptor['Articles'][Index]['Title'] =\
                            Passage.find('text').text.stip()
                    else:#we get Substances or Qualifiers or other Annotations
                        pass





    def __toJSON(self, BioC):
        pass

    def save(self):
        pass
