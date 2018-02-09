import os
import re
import hashlib
import ftplib
from threading import Lock
from time import sleep
from datetime import datetime
from fnmatch import fnmatch
from classes.ftp_downloader import FTPBasicDownloader, FTPBasicDownloaderException
from classes.resource_downloader_base import AbstractResourceDownloader

class ResourceDownloaderException(Exception):
    Reasons = ['There is no coressponding md5 File for {}.', 'The given File {} is invalid to the corresponding md5-hash.', 'The given file {} allready exists in the downloadfolder.', 'Lost connection with {} - try to reconnect.']
    ReasonCodes = [0x0, 0x1, 0x2, 0x3]
    Reason = 0x0
    NO_MD5 = 0x0
    INVALID_MD5 = 0x1
    FILE_EXISTS = 0x2
    RECONNECT = 0x3
    __Info = None

    def __init__(self, ErrorCode, Filename):
        self.Reason = ErrorCode
        self.__Info = Filename

    def __str__(self):
        if self.Reason not in self.ReasonCodes:
            return repr('Unkown error.')
        else:
            return repr(self.Reasons[self.Reason].format(self.__Info))

class File:
    Folder = None
    Access = None
    Type = None
    Size = None
    LastModification = None
    Name = None
    CheckMD5 = None
    localPath = None

def __eq__(self, other):
        return self.__dict__ == other.__dict__

class FileFilter:
    Condition = None
    Flag = None

class ResourceDownloader(AbstractResourceDownloader):
    # TODO: filter files with no read access

    _Downloader = None
    _UnfilteredFiles = None
    _DownloadableFiles = None
    _DownloadedFiles = None
    _Username = ''
    _Password = ''
    _UseTLS = None
    _Filters = None
    _CurrentDir = None
    _PathToTmp = None

    def __init__(self, PathToTmp):
         self._UnfilteredFiles = []
         self._DownloadableFiles = []
         self._DownloadedFiles = []
         self._UseTLS = False
         self._Filters = []
         if not(PathToTmp[-1:] == '/'):
             self._PathToTmp = PathToTmp + '/'
         else:
             self._PathToTmp = PathToTmp

    def setCredentials(self, Username, Password):
        self._Username = Username
        self._Password = Password

    def setBaseAddress(self, Address, UseTLS = False):
        self._UseTLS = UseTLS
        self._Downloader = FTPBasicDownloader(Address)
        self._Downloader.UseTLS = self._UseTLS
        self._Downloader.Username = self._Username
        self._Downloader.Password = self._Password
        self._UnfilteredFiles = []
        self._DownloadableFiles = []
        self._DownloadedFiles = []
        self._Downloader.initializeConnection()

    def addSubFolder(self, Folder, CheckMD5 = False):
        try:
            self._Downloader.checkConnection()
        except FTPBasicDownloaderException:
            self._Downloader.reconnect()
        FileList = self._Downloader.getFileList(Folder)
        for FileAttributes in FileList:
            File = self._buildFileObject(Folder, FileAttributes)
            File.CheckMD5 = CheckMD5
            self._UnfilteredFiles.append(File)
            if self._filterFile(File):
                self._DownloadableFiles.insert(0, File)
        # print file list

    # reset löscht keine files!
    def reset(self):
        self.clearDownloadedFiles()
        self.resetFilter()
        self.resetDownloadQueue()

    def filterFiles(self, FilterCondition, Flag):
        FileFilter_ = FileFilter()
        FileFilter_.Condition = FilterCondition
        FileFilter_.Flag = Flag
        self._Filters.append(FileFilter_)
        # sort filters by flag value to achieve correct precedence
        # self._Filters.sort(key=lambda Filter: Filter.Flag)
        NewDownloadableFiles = []
        for File in self._UnfilteredFiles:
            if self._filterFile(File):
                NewDownloadableFiles.append(File)
        self._DownloadableFiles = NewDownloadableFiles

    def resetFilter(self):
        self._Filters = []

    def downloadFile(self, PathInTmp):
        try:
            self._Downloader.checkConnection()
        except FTPBasicDownloaderException:
            self._Downloader.reconnect()
        # add trailing slash and remove leadingFile.localPath
        if not(PathInTmp[-1:] == '/'):
            PathInTmp += '/'
        PathInTmp.lstrip('/')
        PathInTmp = self._PathToTmp + PathInTmp
        File = self._DownloadableFiles.pop(0)
        self._UnfilteredFiles.remove(File)
        if self._CurrentDir != File.Folder:
            self._CurrentDir = File.Folder
            self._Downloader.goBackToBaseDir()
            self._Downloader.changeDir(File.Folder)
        # dir exists?
        File.localPath = PathInTmp + File.Name
        if not os.path.isfile(File.localPath):
            self._downloadFile(File.Name, File.localPath)
            self._DownloadedFiles.append(File)
        else:
            Stat = os.stat(File.localPath )
            if 0 != File.Size and int(File.Size) == int(Stat.st_size):
                if File.CheckMD5:
                    try:
                        self._checkMD5(File)
                    except ResourceDownloaderException:
                        os.remove(File.localPath)
                        self._downloadFile(File.Name, File.localPath)
                        self._DownloadedFiles.append(File)
                    else:
                        self._DownloadedFiles.append(File)
                        return
                else:
                    self._DownloadedFiles.append(File)
                    self._Lock.release()
                    return
            else:
                os.remove(File.localPath)
                self._downloadFile(File.Name, File.localPath)
                self._DownloadedFiles.append(File)

        if File.CheckMD5:
            self._checkMD5(File)

    def downloadAll(self, PathInTmp):
        while len(self._DownloadableFiles) > 0:
            self.downloadFile(PathInTmp)

    def resetDownloadQueue(self):
        self._UnfilteredFiles = []
        self._DownloadableFiles = []

    def clearDownloadedFiles(self):
        self._DownloadedFiles = []

    def _buildFileObject(self, Folder, AttributesString):
        File_ = File()
        Attributes = AttributesString.split(";")
        File_.Name = Attributes[-1].strip()
        for Attribute in Attributes[:-1]:
            (Field, Value) = Attribute.split("=")
            if 'modify' == Field:
                File_.LastModification = Value
            if 'perm' == Field:
                File_.Access = Value
            if 'size' == Field:
                File_.Size = int(Value)
            if 'type' == Field:
                File_.Type = Value
        File_.Folder = Folder
        return File_

    def _filterFile(self, File):
        Return = True
        # filter all dirs
        if not 'file' == File.Type:
            return False
        #parse date
        try:
            LastModificationDatetime = datetime.strptime(File.LastModification + ' UTC', '%Y%m%d%H%M%S %Z')
        except ValueError:
            # retry with fraction of seconds removed
            LastModification = File.LastModification[:-4]
            LastModificationDatetime = datetime.strptime(LastModification + ' UTC', '%Y%m%d%H%M%S %Z')
        for Filter in self._Filters:
            if ResourceDownloader.FILTER_FILE_INCLUDE_STARTS_WITH == Filter.Flag and File.Name.startswith(Filter.Condition):
                Return = True
            if Filter.Flag == ResourceDownloader.FILTER_FILE_INCLUDE_ENDS_WITH and File.Name.endswith(Filter.Condition):
                Return = True
            if Filter.Flag == ResourceDownloader.FILTER_FILE_INCLUDE_CONTAINS and Filter.Condition in File.Name:
                Return = True
            if Filter.Flag == ResourceDownloader.FILTER_FILE_INCLUDE_PATTERN and fnmatch(File.Name, Filter.Condition):
                Return = True
            if Filter.Flag == ResourceDownloader.FILTER_FILE_INCLUDE_END_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) < 0:
                Return = True
            if Filter.Flag == ResourceDownloader.FILTER_FILE_INCLUDE_START_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) > 0:
                Return = True
            if Filter.Flag == ResourceDownloader.FILTER_FILE_INCLUDE_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) == 0:
                Return = True

            if ResourceDownloader.FILTER_FILE_EXCLUDE_STARTS_WITH == Filter.Flag and File.Name.startswith(Filter.Condition):
                Return = False
            if Filter.Flag == ResourceDownloader.FILTER_FILE_EXCLUDE_ENDS_WITH and File.Name.endswith(Filter.Condition):
                Return = False
            if Filter.Flag == ResourceDownloader.FILTER_FILE_EXCLUDE_CONTAINS and Filter.Condition in File.Name:
                Return = False
            if Filter.Flag == ResourceDownloader.FILTER_FILE_EXCLUDE_PATTERN and fnmatch(File.Name, Filter.Condition):
                Return = False
            if Filter.Flag == ResourceDownloader.FILTER_FILE_EXCLUDE_END_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) < 0:
                Return = False
            if Filter.Flag == ResourceDownloader.FILTER_FILE_EXCLUDE_START_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) > 0:
                Return = False
            if Filter.Flag == ResourceDownloader.FILTER_FILE_EXCLUDE_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) == 0:
                Return = False
        return Return

    def _checkMD5(self, File):
        MD5File = self._findMatchingMD5FileToFile(File)
        # TODO: downloadFile to-path should be build relative to PathInTmp
        md5FileLocalPath = self._PathToTmp + MD5File.Name
        self._downloadFile(MD5File.Name, md5FileLocalPath)
        f = open(md5FileLocalPath, 'r')
        try:
            serverMD5 = re.search(r"([a-fA-F\d]{32})", f.read()).group(1)
        except AttributeError:
            serverMD5 = ''
        finally:
            f.close()
            #we will delete the file immediatly
            os.remove(md5FileLocalPath)

        localMD5 = self._md5sum(File.localPath)
        if not serverMD5 == localMD5:
            raise ResourceDownloaderException(ResourceDownloaderException.INVALID_MD5, File.localPath)

    def _md5sum(self, Filename, Blocksize=65536):
        Hash = hashlib.md5()
        with open(Filename, "rb") as f:
            for Block in iter(lambda: f.read(Blocksize), b""):
                Hash.update(Block)
        return Hash.hexdigest()

    def _findMatchingMD5FileToFile(self, File):
        for possibleMD5File in self._UnfilteredFiles:
            if File.Name + '.md5' == possibleMD5File.Name and File.Folder == possibleMD5File.Folder:
                return possibleMD5File
        raise ResourceDownloaderException(ResourceDownloaderException.NO_MD5, File.Name)

    def _downloadFile(self, Filename, Destination):
        try:
            self._Downloader.downloadFile(Filename, Destination)
        except FTPBasicDownloaderException:
            # if statuscode 42x retry with reconnect
             self._Downloader.reconnect()
             self._Downloader.downloadFile(Filename, Destination)

    def _goBackToBaseDir(self):
        try:
            self._Downloader.goBackToBaseDir()
        except FTPBasicDownloaderException:
             self._Downloader.reconnect()
             self._Downloader.goBackToBaseDir()
