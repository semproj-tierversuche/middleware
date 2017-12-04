import os
import hashlib
from datetime import datetime
from fnmatch import fnmatch
from classes.ftp_downloader import FTPBasicDownloader, FTPBasicDownloaderException
from classes.resource_downloader_base import AbstractResourceDownloader


class File:
    Folder = None
    Access = None
    Symlinks = None
    Owner = None
    Group = None
    Size = None
    LastModification = None
    Name = None
    localPath = None

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class FileFilter:
    Condition = None
    Flag = None


class ResourceDownloader(AbstractResourceDownloader):
    # TODO: Exception handling refinement -> what exceptions is ftp_downloader going to throw?
    # TODO: filter files with no read access
    # TODO: exclude subfolders when adding files to queue

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

    def addSubFolder(self, Folder):
        try:
            self._Downloader.checkConnection()
        except FTPBasicDownloaderException:
            self._Downloader.reconnect()
        FileList = self._Downloader.getFileList(Folder)
        for FileAttributes in FileList:
            File = self._buildFileObject(Folder, FileAttributes)
            self._unfilteredFiles.append(File)
            if self._filterFile(File):
                self._DownloadableFiles.append(File)

    def reset(self, Folder):
        # TODO: this keeps downloaded files ???
        self.resetFilter()
        self.resetDownloadQueue()

    def filterFiles(self, FilterCondition, Flag):
        FileFilter_ = FileFilter()
        FileFilter_.Condition = FilterCondition
        FileFilter_.Flag = Flag
        self._Filters.append(FileFilter_)
        # sort filters by flag value to achieve correct precedence
        self._Filters.sort(key=lambda Filter: Filter.Flag)
        NewDownloadableFiles = []
        for File in self._unfilteredFiles:
            if self._filterFile(File):
                NewDownloadableFiles.append(File)
        self._DownloadableFiles = NewDownloadableFiles

    def resetFilter(self):
        self._Filters = []

    def checkMD5(self):
        for File in self._DownloadedFiles:
            Md5 = self._md5sum(File.localPath)
        # TODO: download & validate md5 here

    def downloadFile(self, PathInTmp):
        try:
            self._Downloader.checkConnection()
        except FTPBasicDownloaderException:
            self._Downloader.reconnect()
        self._Downloader.goBackToBaseDir()
        # add trailing slash and remove leading
        if not(PathInTmp[-1:] == '/'):
            PathInTmp += '/'
        PathInTmp.lstrip('/')
        File = self._DownloadableFiles.pop()
        self._unfilteredFiles.remove(File)
        self._Downloader.changeDir(File.Folder)
        File.localPath = 'tmp/' + PathInTmp + File.Name
        self._Downloader.downloadFile(File.Name, File.localPath)
        self._DownloadedFiles.append(File)

    def downloadAll(self, PathInTmp):
        while len(self._DownloadableFiles) > 0:
            self.downloadFile(PathInTmp)

    def resetDownloadQueue(self):
        self._unfilteredFiles = []
        self._DownloadableFiles = []

    def clearDownloadedFiles(self):
        for File in self._DownloadedFiles:
            # TODO: try catch this
            os.remove(File.localPath)
        self._DownloadedFiles = []

    def _buildFileObject(self, Folder, AttributesString):
        Attributes = AttributesString.split(' ')
        Attributes = [a for a in Attributes if a]
        # TODO: check if mapping works in every case (windows?)
        File_ = File()
        File_.Folder = Folder
        File_.Access = Attributes[0]
        File_.Symlinks = Attributes[1]
        File_.Owner = Attributes[2]
        File_.Group = Attributes[3]
        File_.Size = Attributes[4]
        File_.LastModification = Attributes[5] + ' ' + Attributes[6] + ' ' + Attributes[7]
        File_.Name = Attributes[8]
        return File_

    def _filterFile(self, File):
        Return = True
        # TODO: timezone of ftp server
        try:
            LastModificationDatetime = datetime.strptime(File.LastModification, '%b %e %H:%M')
        except ValueError:
            LastModificationDatetime = datetime.strptime(File.LastModification, '%b %e %Y')
        for Filter in self._Filters:
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_ENDS_WITH and File.Name.endswith(Filter.Condition):
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_CONTAINS and Filter.Condition in File.Name:
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_PATTERN and fnmatch(File.Name, Filter.Condition):
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_BEFORE_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) < 0:
                Return = False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_AFTER_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) > 0:
                Return = False
            if Filter.Flag == self.FILTER_FILE_INCLUDE_ENDS_WITH and File.Name.endswith(Filter.Condition):
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_CONTAINS and Filter.Condition in File.Name:
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_PATTERN and fnmatch(File.Name, Filter.Condition):
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_BEFORE_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) < 0:
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_AFTER_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) > 0:
                Return = True
            if Filter.Flag == self.FILTER_FILE_INCLUDE_AFTER_DATE and (LastModificationDatetime.timestamp() - int(Filter.Condition)) == 0:
                Return = True
        return Return

    def _md5sum(self, Filename, Blocksize=65536):
        Hash = hashlib.md5()
        with open(Filename, "rb") as f:
            for Block in iter(lambda: f.read(Blocksize), b""):
                Hash.update(Block)
        return Hash.hexdigest()
