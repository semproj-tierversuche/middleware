#!/usr/bin/env python3
# requires at least python 3.4

class AbstractResourceDownloader(object):
    #Preferenz Include >= Date_any > Exclude
    FILTER_FILE_EXCLUDE_ENDS_WITH = 0x0
    FILTER_FILE_EXCLUDE_CONTAINS = 0x1
    FILTER_FILE_EXCLUDE_PATTERN = 0x2
    FILTER_FILE_EXCLUDE_BEFORE_DATE = 0x3
    FILTER_FILE_EXCLUDE_AFTER_DATE = 0x4
    FILTER_FILE_EXCLUDE_DATE = 0x5
    FILTER_FILE_INCLUDE_ENDS_WITH = 0x6
    FILTER_FILE_INCLUDE_CONTAINS = 0x7
    FILTER_FILE_INCLUDE_PATTERN = 0x8
    FILTER_FILE_INCLUDE_BEFORE_DATE = 0x9
    FILTER_FILE_INCLUDE_AFTER_DATE = 0xa
    FILTER_FILE_INCLUDE_DATE = 0xb

    def setCredentials(self, Username, Password):
        raise Exception("NotImplementedException")

    def setBaseAddress(self, Address, UseTLS = False):
        raise Exception("NotImplementedException")

    def addSubFolder(self, Folder, CheckMD5 = False):
        raise Exception("NotImplementedException")

    #reset all
    def reset(self, Folder):
        raise Exception("NotImplementedException")

    def filterFiles(self, FilterCondition, Flag):
        raise Exception("NotImplementedException")

    def resetFilter(self):
        raise Exception("NotImplementedException")

    #Die Funktion läd das erste File der Downloadqueue her runter, entfernt den Eintrag aus dieser und fügt es der Gedownloades Liste hinzu
    def downloadFile(self, PathInTmp):
        raise Exception("NotImplementedException")

    #Die Funktion soll immer alles downloaden, was die Filer erlauben
    def downloadAll(self, PathInTmp):
        raise Exception("NotImplementedException")

    #De Funktion setzt die Downloadqueue zurueck
    def resetDownloadQueue(self):
        raise Exception("NotImplementedException")
    #putzt das tmp verzeichnis
    def clearDownloadedFiles(self):
        raise Exception("NotImplementedException")
