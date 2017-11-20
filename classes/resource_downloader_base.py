#!/usr/bin/env python3
# requires at least python 3.4

class AbstractResourceDownloader(object):
    #Preferenz Include >= Date_any > Exclude
    FILTER_FILE_EXCLUDE_ENDS_WITH = 0x0
    FILTER_FILE_EXCLUDE_CONTAINS = 0x1
    FILTER_FILE_EXCLUDE_PATTERN = 0x2
    FILTER_FILE_INCLUDE_ENDS_WITH = 0x3
    FILTER_FILE_INCLUDE_CONTAINS = 0x4
    FILTER_FILE_INCLUDE_PATTERN = 0x5
    FILTER_FILE_START_DATE = 0x6
    FILTER_FILE_END_DATE = 0x7

    #beides bitte nach dem jeweiligen Dir
    _DownloadableFiles = {}
    _DownloadedFiles = {}
<<<<<<< HEAD

    __Username = 'anonymous'
    __Password = 'anonymous@hu-berlin.de'
=======
>>>>>>> 7da28fea5037343017a1e4c8cde229c7c5361080

    def __init__(self):
        pass

<<<<<<< HEAD
    def setUsernameAndPassword(self, Username, Password):
        self.__Username = Username
        self.__Password = Password

    def setBaseAddress(self, Address)
=======
    def setBaseAddress(self, Address):
>>>>>>> 7da28fea5037343017a1e4c8cde229c7c5361080
        raise Exception("NotImplementedException")

    def addSubFolder(self, Folder):
        raise Exception("NotImplementedException")

    #flush all
    def flush(self, Folder):
        raise Exception("NotImplementedException")

    def filterFiles(self, FilterCondition, Flag):
        raise Exception("NotImplementedException")

    def flushFilter(self):
        raise Exception("NotImplementedException")

    #check die md5 hashes der files -> sollten die nicht stimmen werden die aus Downloadable komplett genommen
    def checkMD5(self):
        raise Exception("NotImplementedException")

    #Die Funktion läd das erste File der Downloadqueue her runter, entfernt den Eintrag aus dieser und fügt es der Gedownloades Liste hinzu
    def downloadFile(self, PathToDownloadFolder):
        raise Exception("NotImplementedException")

    #Die Funktion soll immer alles downloaden, was die Filer erlauben
    def downloadAll(self, PathToDownloadFolder):
        raise Exception("NotImplementedException")

    #De Funktion setzt die Downloadqueue zurueck
    def flushDownloadQueue(self):
        raise Exception("NotImplementedException")
