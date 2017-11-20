#!/usr/bin/env python3
# requires at least python 3.4

from classes.config import ConfigReader
from classes.ResourceDownloader import ResourceDownloader

LastUpdate = 0

#step 1 -> reading config
Config = ConfigReader()
Config.parseConfigFile('../config.xml')
print(Config._Resources)
#step 2 -> prepare download
Download = ResourceDownloader()
for Resource in Config._Resources:
    Download.setBaseAddress(Resource['address'])
#step 3 -> when we did the last update for this source
#TODO
#step 4 -> adding the sources
    for Subfolder in Resource['folders']:
        if not bool(Subfolder['onInitializion']) or 0 == LastUpdate:
            Download.addSubFolder(Subfolder)

#step 5(optional) -> check md5 and remove invalide files
    if bool(Resource['md5']):
        Download.checkMD5()

#step 6 -> exclude if we have to from our last update date
    if 0 != LastUpdate:
        Download.filterFiles(0, Download.FILTER_FILE_EXCLUDE_START_DATE)
        Download.filterFiles(LastUpdate, Download.FILTER_FILE_EXCLUDE_END_DATE)

#step 7 -> set exclude and include rules by the config
    for Exclusion in Resource['exclusions']:
        if Exclusion['ending']:
            for End in Exclusion['ending']:
                Download.filterFiles(End, Download.FILTER_FILE_EXCLUDE_ENDS_WITH)

        if Exclusion['contains']:
            for Contains in Exclusion['contains']:
                Download.filterFiles(Contains, Download.FILTER_FILE_EXCLUDE_CONTAINS)

        if Exclusion['pattern']:
            for Pattern in Exclusion['pattern']:
                Download.filterFiles(Pattern, Download.FILTER_FILE_EXCLUDE_PATTERN)

        if Exclusion['date']:
            for Date in Exclusion['date']:
                Download.filterFiles(Date, Download.FILTER_FILE_EXCLUDE_DATE)

        if Exclusion['start_date']:
            for StartDate in Exclusion['start_date']:
                Download.filterFiles(StartDate, Download.FILTER_FILE_EXCLUDE_START_DATE)

        if Exclusion['end_date']:
            for EndDate in Exclusion['end_date']:
                Download.filterFiles(EndDate, Download.FILTER_FILE_EXCLUDE_END_DATE)

    for Inclusion in Resource['inclusions']:
        if Inclusion['ending']:
            for End in Inclusion['ending']:
                Download.filterFiles(End, Download.FILTER_FILE_INCLUDE_ENDS_WITH)

        if Inclusion['contains']:
            for Contains in Inclusion['contains']:
                Download.filterFiles(Contains, Download.FILTER_FILE_INCLUDE_CONTAINS)

        if Inclusion['pattern']:
            for Pattern in Inclusion['pattern']:
                Download.filterFiles(Pattern, Download.FILTER_FILE_INCLUDE_PATTERN)

        if Inclusion['date']:
            for Date in Inclusion['date']:
                Download.filterFiles(Date, Download.FILTER_FILE_INCLUDE_DATE)

        if Inclusion['start_date']:
            for StartDate in Inclusion['start_date']:
                Download.filterFiles(StartDate, Download.FILTER_FILE_INCLUDE_START_DATE)

        if Inclusion['end_date']:
            for EndDate in Inclusion['end_date']:
                Download.filterFiles(EndDate, Download.FILTER_FILE_INCLUDE_END_DATE)
#step 8 -> download files: download/Thread
#step 9 -> call domain plugin: we exspect a DOM as return
#step 10(optional) -> call xslt transformation to BioC
#step 12(opional -> join for a pulk indexing
#step 11 -> call textmining
#step 12a -> collect all data in a datastruct
#step 13 -> transform the datastruct to JSON
#step 14 -> push into database
    download.flush()
