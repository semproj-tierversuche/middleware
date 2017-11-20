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



#step 6 -> set exclude and include rules by the config
    for Exclusion in Resource['exclusions']:
        for End in Exclusion['ending']:
            Download.filterFiles(End, Download.FILTER_FILE_EXCLUDE_ENDS_WITH)
        for Contains in Exclusion['contains']:
            Download.filterFiles(Contains, Download.FILTER_FILE_EXCLUDE_CONTAINS)
        for Pattern in Exclusion['pattern']:
            Download.filterFiles(Pattern, Download.FILTER_FILE_EXCLUDE_PATTERN)
        for StartDate in Exclusion['start_date']:
            Download.filterFiles(StartDate, Download.FILTER_FILE_EXCLUDE_START_DATE)
        for EndDate in Exclusion['end_date']:
            Download.filterFiles(EndDate, Download.FILTER_FILE_EXCLUDE_END_DATE)

    for Inclusion in Resource['inclusions']:
        for End in Inclusion['ending']:
            Download.filterFiles(End, Download.FILTER_FILE_INCLUDE_ENDS_WITH)
        for Contains in Inclusion['contains']:
            Download.filterFiles(Contains, Download.FILTER_FILE_INCLUDE_CONTAINS)
        for Pattern in Inclusion['pattern']:
            Download.filterFiles(Pattern, Download.FILTER_FILE_INCLUDE_PATTERN)
        for StartDate in Inclusion['start_date']:
            Download.filterFiles(StartDate, Download.FILTER_FILE_INCLUDE_START_DATE)
        for EndDate in Inclusion['end_date']:
            Download.filterFiles(EndDate, Download.FILTER_FILE_INCLUDE_END_DATE)

#step 7 -> set

    download.flush()
