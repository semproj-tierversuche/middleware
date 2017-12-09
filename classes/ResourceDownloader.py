import os
import re
import hashlib
import ftplib
from time import sleep
from datetime import datetime
from fnmatch import fnmatch
from classes.ftp_downloader import FTPBasicDownloader, FTPBasicDownloaderException
from classes.resource_downloader_base import AbstractResourceDownloader


class NotExistentMD5Exception(Exception):
    pass


class MD5ValidationException(Exception):
    pass


class FileAlreadyExistsException(Exception):
    pass


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
    _unfilteredFiles = []
    _DownloadableFiles = []
    _DownloadedFiles = []
    _Username = ''
    _Password = ''
    _UseTLS = False
    _Filters = []

    def setCredentials(self, Username, Password):
        self._Username = Username
        self._Password = Password

    def setBaseAddress(self, Address, UseTLS = False):
        self._UseTLS = UseTLS
        self._Downloader = FTPBasicDownloader(Address)
        self._Downloader.UseTLS = self._UseTLS
        self._Downloader.Username = self._Username
        self._Downloader.Password = self._Password
        self._unfilteredFiles = []
        self._DownloadableFiles = []
        self._DownloadedFiles = []
        self._Downloader.initializeConnection()

    def addSubFolder(self, Folder, CheckMD5 = False):
        try:
            self._Downloader.checkConnection()
        except FTPBasicDownloaderException:
            self._Downloader.reconnect()
        print('retrieving file list of ' + Folder)
        FileList = self._Downloader.getFileList(Folder)
        for FileAttributes in FileList:
            File = self._buildFileObject(Folder, FileAttributes)
            File.CheckMD5 = CheckMD5
            self._unfilteredFiles.append(File)
            if self._filterFile(File):
                self._DownloadableFiles.insert(0, File)
        # print file list
        print('filtered filelist:')
        for File in self._DownloadableFiles:
            print(File.Name)

    # reset löscht keine files!
    def reset(self, Folder):
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
        for File in self._unfilteredFiles:
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
        self._goBackToBaseDir()
        # add trailing slash and remove leadingFile.localPath
        if not(PathInTmp[-1:] == '/'):
            PathInTmp += '/'
        PathInTmp.lstrip('/')
        File = self._DownloadableFiles.pop()
        self._unfilteredFiles.remove(File)
        self._Downloader.changeDir(File.Folder)
        # dir exists?
        if not os.path.exists('tmp/' + PathInTmp):
            os.makedirs('tmp/' + PathInTmp)
        File.localPath = 'tmp/' + PathInTmp + File.Name
        print('downloading ' + File.Name)
        # TODO: remove if
        if not os.path.isfile(File.localPath):
            self._downloadFile(File.Name, File.localPath)
            self._DownloadedFiles.append(File)
        else:
            raise FileAlreadyExistsException('File ' + File.localPath + ' already exists.')
        if File.CheckMD5:
            print('checking md5 of ' + File.Name)
            self._checkMD5(File)

    def downloadAll(self, PathInTmp):
        while len(self._DownloadableFiles) > 0:
            self.downloadFile(PathInTmp)

    def resetDownloadQueue(self):
        self._unfilteredFiles = []
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
                File_.Size = Value
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
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_ENDS_WITH and File.Name.endswith(Filter.Condition):
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_CONTAINS and Filter.Condition in File.Name:
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_PATTERN and fnmatch(File.Name, Filter.Condition):
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_END_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) < 0:
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_START_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) > 0:
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) == 0:
                Return = False
            if Filter.Flag == self.FILTER_FILE_INCLUDE_ENDS_WITH and File.Name.endswith(Filter.Condition):
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_CONTAINS and Filter.Condition in File.Name:
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_PATTERN and fnmatch(File.Name, Filter.Condition):
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_END_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) < 0:
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_START_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) > 0:
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) == 0:
                Return = True
        return Return

    def _checkMD5(self, File):
        MD5File = self._findMatchingMD5FileToFile(File)
        # TODO: downloadFile to-path should be build relative to PathInTmp
        md5FileLocalPath = 'tmp/' + MD5File.Name
        self._downloadFile(MD5File.Name, md5FileLocalPath)
        f = open(md5FileLocalPath, 'r')
        try:
            serverMD5 = re.search(r"([a-fA-F\d]{32})", f.read()).group(1)
        except AttributeError:
            serverMD5 = ''
        localMD5 = self._md5sum(File.localPath)
        if not serverMD5 == localMD5:
            raise MD5ValidationException('MD5 checksums of ' + File.localPath + ' do not match.')

    def _md5sum(self, Filename, Blocksize=65536):
        Hash = hashlib.md5()
        with open(Filename, "rb") as f:
            for Block in iter(lambda: f.read(Blocksize), b""):
                Hash.update(Block)
        return Hash.hexdigest()

    def _findMatchingMD5FileToFile(self, File):
        for possibleMD5File in self._unfilteredFiles:
            if File.Name + '.md5' == possibleMD5File.Name and File.Folder == possibleMD5File.Folder:
                return possibleMD5File
        raise NotExistentMD5Exception(File.Name + '.md5 not found in ' + File.Folder + '.')

    def _downloadFile(self, Filename, Destination):
        try:
            self._Downloader.downloadFile(Filename, Destination)
        except ftplib.all_errors as e:
            StatusCode = int(e.args[0][:3])
            # if statuscode 42x retry with reconnect
            if StatusCode % 420 < 10 and StatusCode / 420 == 1:
                print('connection lost. reconnecting..')
                self._Downloader.reconnect()
                self._Downloader.downloadFile(Filename, Destination)
            else:
                raise e

    def _goBackToBaseDir(self):
        try:
            self._Downloader.goBackToBaseDir()
        except ftplib.all_errors as e:
            StatusCode = int(e.args[0][:3])
            # if statuscode 42x retry with reconnect
            if StatusCode - 420 in range(0, 9):
                print('connection lost. reconnecting..')
                self._Downloader.reconnect()
                self._Downloader.goBackToBaseDir()
            else:
                raise e
