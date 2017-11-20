#!/usr/bin/env python3
# requires at least python 3.4

from classes.config import ConfigReader
from classes.ResourceDownloader import ResourceDownloader


class TextMining(object):

    __LastUpdate = 0
    __Configurartion = ''
    __Downloaderer = ''

    #step 1 -> reading config
    def __init__(self, ConfigurationFile):
        self.__Configuration = ConfigReader()
        self.__Configuration.parseConfigFile('../config.xml')
        print(Config._Resources)
        self.__Downloader = ResourceDownloader().


    def prepareDownload(self):
        for Resource in Config._Resources:
            self.__Downloader.setBaseAddress(Resource['domain'])
            for Subfolder in Resource['folders']:
                self.__addSubFolder(Subfolder)

            if bool(Resource['md5']):
                self.__Downloader.checkMD5()

            self.__setFilter(Resource)

    def getLastUpdate(self, Domain):
        #TODO
        pass

    def __addSubFolder(self, Subfolder):
        if not bool(Subfolder['onInitializion']) or 0 == self.__LastUpdate:
            self.__Downloader.addSubFolder(Subfolder)

    #set a singel Filter to the Downloader
    def __setFilter(self, Container, Key, Flag):
        Filter = ''

        if Container[Key]:
            for Filter in Container[Key]:
                self.__Downloader.filterFiles(Filter, Flag)

    #set the filters for Resource
    def __setFilters(self, Resource):
        #first of all we have set our Update Filter
        if 0 != self.__LastUpdate:
            self.__Downloader.filterFiles(0, self.__Downloader.FILTER_FILE_EXCLUDE_START_DATE)
            self.__Downloader.filterFiles(LastUpdate, self.__Downloader.FILTER_FILE_EXCLUDE_END_DATE)


        for Exclusion in Resource['exclusions']:
            self.addFilter(Exclusion, 'ending', self.__Downloader.FILTER_FILE_EXCLUDE_ENDS_WITH)
            self.addFilter(Exclusion, 'contains', self.__Downloader.FILTER_FILE_EXCLUDE_CONTAINS)
            self.addFilter(Exclusion, 'pattern', self.__Downloader.FILTER_FILE_EXCLUDE_PATTERN)
            self.addFilter(Exclusion, 'start_date', self.__Downloader.FILTER_FILE_EXCLUDE_START_DATE)
            self.addFilter(Exclusion, 'end_date', self.__Downloader.FILTER_FILE_EXCLUDE_END_DATE)
            self.addFilter(Exclusion, 'date', self.__Downloader.FILTER_FILE_EXCLUDE_DATE)
        for Inclusion in Resource['inclusions']:
            self.addFilter(Inclusion, 'ending', self.__Downloader.FILTER_FILE_INCLUDE_ENDS_WITH)
            self.addFilter(Inclusion, 'contains', self.__Downloader.FILTER_FILE_INCLUDE_CONTAINS)
            self.addFilter(Inclusion, 'pattern', self.__Downloader.FILTER_FILE_INCLUDE_PATTERN)
            self.addFilter(Inclusion, 'start_date', self.__Downloader.FILTER_FILE_INCLUDE_START_DATE)
            self.addFilter(Inclusion, 'end_date', self.__Downloader.FILTER_FILE_INCLUDE_END_DATE)
            self.addFilter(Inclusion, 'date', self.__Downloader.FILTER_FILE_INCLUDE_DATE)

#step 8 -> download files: download/Thread

#step 9 -> call domain plugin: we exspect a DOM as return

#step 10(optional) -> call xslt transformation to BioC

#step 11 -> call textmining

#step 12(opional -> join for a pulk indexing

#step 12a -> collect all data in a datastruct

#step 13 -> transform the datastruct to JSON

#step 14 -> push into database
    download.flush()
