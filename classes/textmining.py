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

class Textmining(object):

    __Configuration = None
    __LastUpdate = None
    __Downloader = None
    __Database = None
    __Textmining = None
    __Log = None
    __BioC = None
    __Plugins = None
    __ToDel = None
    __Lock = None
    __NonBioCInformation = None


    #step 1 -> reading config and start everything
    def __init__(self, ConfigurationFile):
        self.__Lock = Threads.Lock()
        self.__BioC = []
        self.__Plugins = []
        self.__NonBioCInformation =[]
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

    #TODO
    def getLastUpdate(self, Domain):
        #TODO
        pass

    #set 2 -> download the files and begin the
    def downloadFiles(self):

        for Domain in self.__Configuration._Resources:
            self.__Log.info("Start to download form " + Domain['domain'])
            i = 0
            Flag = [True]
            for Resource in Domain['folders']:
                j = 0
                self.__Downloader.setBaseAddress(Domain['domain'])
                Subdir = self.__Configuration._General['tmpdir'] + str(i)
                if 0 != self.__LastUpdate and True == Resource['onInitializion']:
                    continue
                Inclusions = merge(Resource['ruleset']['inclusions'], Domain['ruleset']['inclusions'])
                Exclusions = merge(Resource['ruleset']['exclusions'], Domain['ruleset']['exclusions'])
                #2a -> apply the given Filters
                self.__setFilters(Exclusions, Inclusions)
                #2b -> add Download Folder
                self.__Downloader.addSubFolder(Resource['name'], Domain['md5'])
                #2b -> apply the given Filters
#                self.__setFilters(Exclusions, Inclusions)
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
                                self.__Log.warning(str(e) + "\n" + "Skipping...")
                                continue
                        else:
                            Traceroute = Trace.format_exc()
                            self.__Log.error(str(e) + "\n" + Traceroute)
                            OS._exit(0)
                    if 9 < j:
                        break
                    else:
                        j = j+1
                Files = []
                for File in self.__Downloader._DownloadedFiles:
                    Files.append(Subdir + "/" + File.Name)
                #TODO Thread this
                self.__getBioC(Domain['plugin'], Files, Domain['domain'] + "/" + Resource['name'].lstrip(".").lstrip("/"))
                self.__Downloader.reset()
                self.__Log.info("Downloaded " + Resource['name'].lstrip(".").lstrip("/"))
                i = i+1

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

    def __getBioC(self, Plug, Files, OriginalPath):
        Collection = []
        SearchPath, File = OS.path.split(Plug)
        if not SearchPath in Sys.path:
            Sys.path.append(SearchPath)
            Sys.path.append(OS.path.normpath(SearchPath+"/../"))
        FP, PathName, Description = Plugins.find_module("plugin", [SearchPath,])
        Module = Plugins.load_module("plugin", FP, PathName, Description)
        for File in Files:
            Articles, NonBioCInformations = Module.Plugin.preTextminingHook(File, OriginalPath)
            self.__Lock.acquire()
            for Article in Articles:
                self.__BioC.append(Article)
                print(DOM.tostring(self.__BioC[len(self.__BioC)-1], pretty_print=True).decode('utf-8'))
                self.__Plugins.append(Module)
            self.__NonBioCInformation += NonBioCInformations
            OS._exit(0)
            self.__Lock.release()

    def throwAgainstTextMining(self):
        preMined = list(self.__BioC)
        while 0 != len(self.__BioC):
            self.__BioC.pop()
        for BioC in preMined:
            try:
                (ReturnCode, Stdout, Stderr) = self.__Textmining.do(BioC, ReadFromStdin=True, RetryOnFail=True)
            except Exception as e:
                Traceroute = Trace.format_exc()
                self.__Log.error(str(e) + "\n" + Traceroute)
                OS._exit(0)
            if Stderr:
                self.__Log.warning(Stderr)
            self.__BioC.append(Stdout)

    def __toJSON(self, BioC):
        pass

    def save(self):
        while 0 != len(self.__BioC):
            BioC = self.__BioC.pop()
            Module = self.__Plugins.pop()
            ToDelete = self.__ToDel.pop()
            BioC = Mudule.Plugin.preDatabaseHook(BioC)
            JSON = self.__toJSON(BioC)
            (ReturnCode, Stdout, Stderr) = self.__Database.insertIntoDatabase(JSON)
            if 200 == ReturnCode:
                OS.remove(ToDelete)
            else:
                self.__Log.error(Stderr)
                OS._exit(0)
