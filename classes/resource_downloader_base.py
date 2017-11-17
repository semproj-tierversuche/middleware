#!/usr/bin/env python3
# requires at least python 3.4

class AbstactResourceDownloader(object):
    #Preferenz Include >= Date_any > Exclude
    FILTER_FILE_EXCLUDE_ENDS_WITH = 0x0
    FILTER_FILE_EXCLUDE_CONTAINS = 0x1
    FILTER_FILE_EXCLUDE_PATTERN = 0x2
    FILTER_FILE_INCLUDE_ENDS_WITH = 0x3
    FILTER_FILE_INCLUDE_CONTAINS = 0x4
    FILTER_FILE_INCLUDE_PATTERN = 0x5
    FILTER_FILE_START_DATE = 0x6
    FILTER_FILE_END_DATE = 0x7

   _DownloadableFiles = []
   _DownloadedFiles = []

    def __init__(self):
        pass

    def setBaseAddress(self, Address)
        raise Exception("NotImplementedException")

    def addSubFolder(self, Folder)
        raise Exception("NotImplementedException")

    def filterFiles(self, FilterCondition, Flag)
        raise Exception("NotImplementedException")

    def flushFilter(self)
        raise Exception("NotImplementedException")

    #Die Funktion läd das erste File der Downloadqueue her runter, entfernt den Eintrag aus dieser und fügt es der Gedownloades Liste hinzu
    def downloadFile(self, PathToDownloadFolder)
        raise Exception("NotImplementedException")

    #Die Funktion soll immer alles downloaden, was die Filer erlauben
    def downloadAll(self, PathToDownloadFolder)
        raise Exception("NotImplementedException")

    #De Funktion setzt die Downloadqueue zurueck
    def flushDownloadQueue(self):
        raise Exception("NotImplementedException")
