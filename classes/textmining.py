#!/usr/bin/env python3
# requires at least python 3.4

from classes.config import ConfigReader
from classes.utils import mergeDictionaries as merge
import classes.ResourceDownloader as RD
import classes.services as Services
from classes.ptrie import PatricaTrieNode, PatricaTrie
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
import shutil as DirDelete
import time as Time

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
    #also the programmlogic has to be ajusted
    __DataTree = None
    __ToTurnicate = None
    Verbose = None
    __Start = None


    #step 1 -> reading config and start everything
    def __init__(self, ConfigurationFile):
        self.__DocumentPushLock = Threads.Lock()
        self.__BioCLock = Threads.Lock()
        self.__Articles = {}
        #self.__LastUpdate = {}
        self.__DataTree = {}
        self.__ToTurnicate = {}
        self.Verbose = False
        self.__Configuration = ConfigReader()
        self.__Configuration.parseConfigFile(ConfigurationFile)
        #1.a -> start Logging
        self.__Log = Logger.getLogger("Alternativen zu Tierversuchen: ")
        LogFile = Logger.FileHandler(self.__Configuration._General['logfile'])
        Formatter = Logger.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        LogFile.setFormatter(Formatter)
        self.__Log.addHandler(LogFile)
        self.__Log.setLevel(Logger.INFO)
        #1.b -> start Downloader
        self.__Downloader = RD.ResourceDownloader(self.__Configuration._General['tmpdir'])
        #1.c -> start Services
        self.__Database = Services.DatabaseService(self.__Configuration)
        self.__Textmining = Services.TextminingService(self.__Configuration)
        #1.d -> set Lastupdate to 0, to index right from the scratch
        self.__LastUpdate = 0
        self.__Log.info("Start Textmining")
        if self.__Configuration._Textmining['verbose']:
            self.Verbose = True
        else:
            self.Verbose = False

    #def __getLastUpdate(self, Domain):
    def __getLastUpdate(self):
        if OS.path.isfile(self.__Configuration._General['tmpdir'] + '.dataTree.json'):
            self.__DataTree = JSON.load(open(self.__Configuration._General['tmpdir'] + '.dataTree.json'))
            for (Domain, Sets) in self.__DataTree.items():
                if self.__DataTree[Domain]['TextminingVersion'] != str(self.__Textmining.getVersion()):
                    self.__DataTree[Domain]['TextminingVersion'] = str(self.__Textmining.getVersion())
                    self.__DataTree[Domain]['Date'] = 0.0
                    self.__ToTurnicate[Domain] = PatricaTrie().load(self.__DataTree[Domain]['ids'])
                    self.__DataTree[Domain]['ids'] = PatricaTrie()
                else:
                    self.__DataTree[Domain]['Date'] = float(self.__DataTree[Domain]['Date'])
                    self.__DataTree[Domain]['ids'] = PatricaTrie().load(self.__DataTree[Domain]['ids'])
        else:
            self.__DataTree = {}
        #That's way it should be....but thanks to SM...so do not delete it it could be useful in the (far) future
        #and with some extensions like above
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

    #set 2 -> download the files and begin the
    def execute(self):
        for Domain in self.__Configuration._Resources:
            self.__Start = Time.clock()
            self.__Log.info("Start to download form " + Domain['domain'])
            #self.__getLastUpdate(Domain['domain'])
            self.__getLastUpdate()
            Sub = 0
            Flag = [True]
            FileContainer = []
            for Resource in Domain['folders']:
                j = 0
                self.__Downloader.setBaseAddress(Domain['domain'])
                Subdir = self.__Configuration._General['tmpdir'] + str(Sub)
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
                    #TODO: Just to test
                    if 1 <= j:
                        break
                    j = j+1

                    try:
                        self.__Downloader.downloadFile(str(Sub))
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

                Files = []
                for File in self.__Downloader._DownloadedFiles:
                    if True == self.Verbose:
                        self.__Log.info('File {} downloaded.'.format(File.Name))
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
                Sub = Sub+1

            #the bad work
            self.__worker(Domain['prefix'], Domain['domain'], Domain['plugin'], FileContainer)
            #do not forget to cleanup
            if True == self.Verbose:
                self.__Log.info('Clear tmp dir')
            self.__cleanTmp()
        #And save that what the db should keep
        if True == self.Verbose:
            self.__Log.info('Saving domaininfo')
        self.__saveDataTree()
        #time in sec
        EndTime = ((Time.clock()-self.__Start)*1000)*1000
        self.__Log.info('The programm took {} seconds to execute.'.format(str(EndTime)))


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

    def __worker(self, Prefix, Domain, DomainPluginDescriptor, FileContainer):
        self.__BioCLock.acquire()
        DomainIds = PatricaTrie()
        DomainDescriptor = []
        DBStorage = {}
        if True == self.Verbose:
            self.__Log.info("Installing plugin for domain {}".format(Domain))
        SearchPath, IgnoreMe = OS.path.split(DomainPluginDescriptor)
        if not SearchPath in Sys.path:
            Sys.path.append(SearchPath)
            Sys.path.append(OS.path.normpath(SearchPath+"/../"))
        FP, PathName, Description = Plugins.find_module("plugin", [SearchPath,])
        DomainPlugin = Plugins.load_module("plugin", FP, PathName, Description)
        for Container in FileContainer:
            for File in Container:
                if DomainPluginDescriptor != File['plugin']:
                    if True == self.Verbose:
                        self.__Log.info("Installing plugin for file {}".format(File['File']))
                    SearchPath, IgnoreMe = OS.path.split(File['plugin'])
                    if not SearchPath in Sys.path:
                        Sys.path.append(SearchPath)
                        Sys.path.append(OS.path.normpath(SearchPath+"/../"))
                    FP, PathName, Description = Plugins.find_module("plugin", [SearchPath,])
                    Module = Plugins.load_module("plugin", FP, PathName, Description)
                else:
                    Module = DomainPlugin

                FileDescriptor = {}
#                FileDescriptor['name'] = File
#                FileDescriptor['prefix'] = Prefix
#                FileDescriptor['plugin'] = Module
                FileDescriptor['Articles'] = []
                FileDescriptor['isInit'] = File['init']
                FileDescriptor['ArticlesBioC'] = DOM.Element("Collection")
                if True == self.Verbose:
                    self.__Log.info('Call plugin for preprocessing of file {}'.format(File['File']))

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
                    Information['MeshHeadings'] = []

                    DomainIds.insert(Information['PMID'])

                    if not self.__DataTree\
                       or Domain not in self.__DataTree\
                       or 0 == self.__DataTree[Domain]['LastUpdate']:
                        Result = None
                    else:
                        self.__Log.debug('Prepare query for article with id {}.'.format(str(Information['PMID'])))
                        if not Prefix:
                            Query = {'PMID': str(Information['PMID'])}
                        else:
                            Query = {'PMID': Prefix + str(Information['PMID'])}
                        ReturnCode, Result, Ignore = self.__Database.queryDatabase(Query)
                        self.__Log.debug('Query done for article with id {}.'.format(str(Information['PMID'])))

                    if True == self.Verbose:
                        self.__Log.info('Start conversion for article with id {}.'.format(str(Information['PMID'])))
                    if not Result:
                        ReturnCode = 400
                    if 200 == ReturnCode:
                        Result = JSON.load(Result)
                        DBStorage[Information['PMID']] = Result
                        DBStorage[Information['PMID']]['PMID'] = int(Information['PMID'])
                        Date = float(Result['Date'])
                        FileDate = float(Information['Date'])
                        if 0 == Date or 0 == FileDate:# or 0 == self.__DataTree[Domain]['LastUpdate']:
                            BioC = Module.Plugin.toBioC(Article, File['path'])
                            Information['update'] = True
                            FileDescriptor['Articles'].append(Information)
                            #perhaps there is a better way then this, but actually I does not know
                            #and the copy-append is slower then that
                            FileDescriptor['ArticlesBioC'].append(Copy(BioC.find("./document")))
                            del BioC

                        else:
                            if Date < FileDate:
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

#            FileDescriptor['Articles'] = sorted(FileDescriptor['Articles'], key=Textmining.sortEntries)
            FileDescriptor['Articles'].sort(key=Textmining.sortEntries)
            FileDescriptor['ArticlesBioC'] = '<?xml version="1.0" encoding="utf-8"?>\
                                        <!DOCTYPE collection SYSTEM "./BioC.dtd">' +\
                                        DOM.tostring(FileDescriptor['ArticlesBioC']).decode('utf-8')
            self.__Log.info('Start textmining service for file {}.'.format(File['File']))
#            print(FileDescriptor['ArticlesBioC'])
            self.__throwAgainstTextMining(Domain, FileDescriptor)
            DomainDescriptor.append(FileDescriptor)
        del FileContainer
        DomainDescriptor = self.__DomainDataTree(Domain, DomainPlugin, DomainIds,\
                                                 Prefix, DomainDescriptor, DBStorage)

        if DBStorage:
            del DBStorage

        self.__save(Domain, Prefix, DomainIds, DomainDescriptor)
        self.__BioCLock.release()

    def __throwAgainstTextMining(self, Domain, FileDescriptor):
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
                             Exiting".format(ReturnCode))
            OS._exit(0)
        FileDescriptor['ArticlesBioC'] = DOM.fromstring(Stdout)
        #we need memory
        del Stdout
        self.__parseResult(FileDescriptor)

    def __parseResult(self, FileDescriptor):
        #first we catch all articles of a file
        self.__Log.info('Start parsing textmining results.')
        Articles = FileDescriptor['ArticlesBioC'].findeAll("./document")
        for Article in Articles:
            ID = int(Article.find("./ID").text.strip())
            #we match the ID to a our FD
            Index = self.__findEntry(FileDescriptor['Articles'], ID)
            if -1 == Index:
                Traceroute = Trace.format_stack()
                self.__Log.fatal("The given id {} does not match with anyone in the \
                                 strorage".format(ID) + "\n" + Tracerout)
                OS._exit(0)
            else:
                #we have our Article pointer...
                Passages = Article.findAll("./passage")
                for Passage in Passages:
                    Type = Passage.find("./infon[@key='type']").text.strip().lower()
                    #we look for the abstract
                    if 'abstract' == Type:
                        Abstract = Passage.findAll("./sentence/text")
                        #no abstract no annotations no fun
                        if 0 == len(Abstract):
                            self.__Log.warning("Article with id {} has no abstract. \
                                               Skipping article...".format(str(ID)))
                            FileDescriptor['Articles'].pop(Index)
                            break
                        else:
                            for Line in Abstract:
                                if Line.text.strip():
                                    FileDescriptor['Articles'][Index]['Abstract'] +=\
                                    ' ' + Line.text.strip()
                            FileDescriptor['Articles'][Index]['Abstract'] =\
                            FileDescriptor['Articles'][Index]['Abstract'].lstrip()

                            #go for annotation form the abstract
                            Annotations = Passage.findAll("./annotation")
                            AnnotationCounter = 0
                            for Annotation in Annotations:
                                AnnotationCounter = AnnotationCounter+1
                                PName =  Annotation.find("infon[@key='preferred_name']").text.strip()
                                CId = Annotation.find("infon[@key='concept_id']").text.strip()
                                if not PName or not CId:
                                    self.__Log.warning("Invalid annotation format \
                                                       in article with id {} \
                                                       at annotation {}. \
                                                       Skipping annotation...".format(str(ID), str(AnnotationCounter)))
                                    continue
                                else:
                                    FileDescriptor['Articles'][Index]['Annotations'].extend([PName, CId])

                    #we look for the title
                    elif 'title' == Type:
                        #same like in the abstract -> no fun
                        if not Passage.find('text').text.strip():
                            self.__Log.warning("Article with ID {} has no title. \
                                               Skipping article...".format(str(ID)))
                            FileDescriptor['Articles'].pop(Index)
                            break
                        else:
                            FileDescriptor['Articles'][Index]['Title'] =\
                            Passage.find('text').text.strip()
                    elif 'metadata' == Type:#we get Substances or Qualifiers
                        Sentences = Passage.findAll('./sentence')
                        if not Sentences:
                            continue
                        for Sentence in Sentences:
                            Type = Sentence.find("./infon[@key='type']").text.strip().lower()
                            #Quilifiers
                            # format: " (qual1, qual2, qual3)"
                            if 'meshheading' == Type:
                                Qulifiers = []
                                Descriptor = ''
                                Annotations = Sentence.findAll("./annotation")
                                for Annotation in Annotations:
                                    SubType = Annotation.find("./infon[@key='type']")
                                    if not SubType\
                                    or (SubType and not SubType.text.strip()):
                                        self.__Log.warning("Invalid Identifier in \
                                                           article with id {}.".format(str(ID)))
                                    else:
                                        SubType = SubType.text.strip().lower()
                                        if 'descriptor' == SubType:
                                            DescriptorNode = Annotation.find("./text")
                                            if not DescriptorNode\
                                               or (DescriptorNode and not DescriptorNode.text.strip()):
                                                continue
                                            else:
                                                if Descriptor:
                                                    self.__Log.warning("Rewriting descriptor in article \
                                                                       with id {}.".format(str(ID)))
                                                Descriptor = DescriptorNode.text.strip().lower()
                                        elif 'qualifier' == SubType:
                                            QualifierNode = Annotation.find("./text")
                                            if not QualifierNode\
                                               or (QualifierNode and not QualifierNode.text.strip()):
                                                continue
                                            else:#
                                                Qualifiers.append(QualifierNode.text.strip().lower())
                                        else:
                                            self.__Log.warning("Unknown meshheader {} \
                                                               in article with id {}.".format(SubType, str(ID)))
                                            continue

                                if not Descriptor:
                                    self.__Log.warning("There was no descriptor given \
                                                       in article with id {}.".format(str(ID)))
                                    continue
                                if Qualifiers:
                                    Qualifiers.sort()
                                    FileDescriptor['Articles']\
                                    [Index]['MeshHeadings'].append(Descriptor + '('\
                                                               ", ".join(Qualifiers) + ')')
                                else:
                                    FileDescriptor['Articles']\
                                    [Index]['MeshHeadings'].append(Descriptor)
                            #Substances
                            elif 'chemical' == Type:
                                Chemical = Sentence.find("./annotation/text").text.strip().lower()
                                if Chemical:
                                    FileDescriptor['Articles'][Index]['Substances'].append(Chemical)
                            else:
                                self.__Log("Got unkown metadata type {} in article \
                                           with id {}.".format(Type, str(ID)))
                    else:
                        self.__Log.warning('Got unknown type {} in article with \
                                           id {}.'.format(Type, str(ID)))
                if True == self.Verbose:
                    self.__Log.info('Parsing finished for article with id {}.'.format(str(ID)))
            #here is a classical example why I like braces!
            if not FileDescriptor['Articles'][Index]['Title']:
                self.__Log.waring("The article with ID {} has no abstract \
                                  Skipping the article...".format(str(ID)))
                FileDescriptor['Articles'].pop(Index)

            if not FileDescriptor['Articles'][Index]['Abstract']:
                self.__Log.waring("The article with ID {} has no abstract \
                                  Skipping the article...".format(str(ID)))
                FileDescriptor['Articles'].pop(Index)

            if not FileDescriptor['Articles'][Index]['Annotations']:
                self.__Log.warning("The article with id {} \
                                   has no annotations.".format(str(ID)))
        #DB wanted things sorted
            FileDescriptor['Articles'][Index]['MeshHeadings'].sort()
            FileDescriptor['Articles'][Index]['Substances'].sort()
        #we need memoryy
        del FileDescriptor['ArticlesBioC']

    @staticmethod
    def sortInit(Entry):
        if Entry['isInit']:
            return 0
        else:
            return 1

    def __DomainDataTree(self, Domain, DomainPlugin, DomainIds,\
                         Prefix, DomainFileDescriptor, DBStorage):
        self.__Log.info('Start computig datastructure for {}.'.format(Domain))
        Inits = []
        Updates = []
        #we will not check if a id is twice...that would be a error
        for Documents in DomainFileDescriptor:
            if True == Documents['isInit']:
                Inits.extend(Documents['Articles'])
            else:
                Updates.extend(Documents['Articles'])

        #sort and merge sort ^^
        Inits.sort(key=Textmining.sortEntries)
        Updates.sort(key=Textmining.sortEntries)
        Merge = []

        #merge initialisation with Updates (if we have to)
        while 0 != len(Inits) and 0 != len(Updates):
            if Updates[0]['PMID']<Init[0]['PMID']:
                Merge.append(Updates.pop(0))
            elif Updates[0]['PMID']>Init[0]['PMID']:
                Merge.append(Inits.pop(0))
            #das folgende ist eindeutig Domainlogik
            else:
                DomainPlugin.Plugin.mergeArticles(Inits.pop(0), Updates.pop(0))

        if 0 != len(Inits):
            Merge.extend(Inits)
        if 0 != len(Updates):
            Merge.extend(Updates)

        if self.__DataTree and self.__DataTree[Domain]['ids']:
            if DBStorage:
                ToUpdate = list(DBStorage.values())
                del DBStorage
            Difference = DomainIds.symetricDifferenz(self.__DataTree[Domain]['ids'])
            #let's burn the database
            for PmId in Difference:
                if not Prefix:
                    Query = {'PMID': str(PmId)}
                else:
                    Query = {'PMID': Prefix + str(PmId)}
                ReturnCode, Result, Err = self.__Database.queryDatabase(Query)
                if 200 != ReturnCode:
                    self.__Log.warning('Exspected a article for id {} \
                                       and got no result. Database \
                                       says:\n{}'.format(str(PmId), Err))
                    continue
                if not Result:
                    self.__Log.warning('Exspected a article for id {} \
                                       and got no result.'.format(str(PmId)))
                    continue

                DomainIds.insert(PmId)
                Result = JSON.load(Result)
                Result['PMID'] = PmId
                ToUpdate.append(Result)

            Merge2 = []
            while 0 != len(ToUpdate) and 0 != len(Merge):
                if Merge[0]['PMID']<ToUpdate[0]['PMID']:
                    Merge2.append(Merge.pop(0))
                elif Merge[0]['PMID']>ToUpdate[0]['PMID']:
                    Merge2.append(ToUpdate.pop(0))
                else:
                    DomainPlugin.Plugin.mergeArticles(ToUpdate.pop(0), Merge.pop(0))

            if 0 != len(ToUpdate):
                Merge2.extend(ToUpdate)
            if 0 != len(Merge):
                Merge2.extend(Merge)

            Merge = Merge2

        self.__Log.info('Calling plug in to finalize the dataset of {}'.format(Domain))
        DomainPlugin.Plugin.modififyDataTree(Merge, DomainIds.getValues())

    def __save(self, Domain, Prefix, DomainIds, DomainDescriptor):

        if 0 != len(self.__ToTurnicate[Domain]):
            self.__Log.info('Clear database of {}.'.format(Domain))
            Turnicate = self.__ToTurnicate[Domain].getValues()
            while 0 != len(Turnicate):
                Query = {}
                if Prefix:
                    Query['PMID'] = Prefix + str(Turnicate.pop(0))
                else:
                    Query['PMID'] = str(Turnicate.pop(0))

                self.__Database.deleteInDatabase(Query)
            del self.__ToTurnicate[Domain]

        self.__Log.info('Updating database for {}.'.format(Domain))
        while 0 != len(DomainDescriptor):
            Article = DomainDescriptor.pop(0)
            Update = Article['update']
            del Article['update']

            Query = {}
            if Prefix:
                Query['PMID'] = Prefix + str(Article['PMID'])
                Article['PMID'] = Prefix + str(Article['PMID'])
            else:
                Query['PMID'] = str(Article['PMID'])

            if True == Update:
                self.__Database.updateInDatabase(JSON.dump(Article), Query, True)
            else:
                self.__Database.insertIntoDatabase(JSON.dump(Article), Query, True)

        if True == self.__Verbose:
            self.__Log.info('Saving ids for autocompletion of {}'.format(Domain))
        if Prefix:
            DomainIds.save(self.__Configuration._General['tmpdir'] + '.' + Prefix + ".pt")
            self.__DataTree[Domain]['ids'] = self.__Configuration._General['tmpdir'] + '.' + Prefix + ".pt"
        else:
            DomainIds.save(self.__Configuration._General['tmpdir'] + ".ids.pt")
            self.__DataTree[Domain]['ids'] = self.__Configuration._General['tmpdir'] + ".ids.pt"

        self.__DataTree[Domain]['TextminingVersion'] = str(self.__Textmining.getVersion())
        self.__DataTree[Domain]['Date'] = Time.time()

    def __cleanTmp(self):
        Sub = 0
        while True:
            if not OS.path.isdir(self.__Configuration._General['tmpdir'] + str(Sub)):
                break
            DirDelete.rmtree(self.__Configuration._General['tmpdir'] + str(Sub), ignore_errors=True)
            Sub = Sub+1

    def __saveDataTree(self):
        with open(self.__Configuration._General['tmpdir'] + ".dataTree.json", 'w') as File:
            File.write(JSON.dump(self.__DataTree))

    def __del__(self):
        self.__cleanTmp()
