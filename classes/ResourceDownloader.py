import os
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


class FileFilter:
    Condition = None
    Flag = None


class ResourceDownloader(AbstractResourceDownloader):
    # TODO: Exception handling for whole class
    # TODO: filter files with no read access
    # TODO: exclude subfolders when adding files to queue

    _Downloader = None
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
        self._Downloader.initializeConnection()
        self._DownloadableFiles = []
        self._DownloadedFiles = []

    def addSubFolder(self, Folder):
        try:
            self._Downloader.checkConnection()
        except FTPBasicDownloaderException:
            self._Downloader.reconnect()
        FileList = self._Downloader.getFileList(Folder)
        for FileAttributes in FileList:
            File = self._buildFileObject(Folder, FileAttributes)
            if self._filterFile(File):
                self._DownloadableFiles.append(File)

    def reset(self, Folder):
        # TODO: this keeps downloaded files ???
        self.resetFilter()
        self.resetDownloadQueue()

    def filterFiles(self, FilterCondition, Flag):
        # TODO: so far this only works with EXCLUDING files
        FileFilter_ = FileFilter()
        FileFilter_.Condition = FilterCondition
        FileFilter_.Flag = Flag
        self._Filters.append(FileFilter_)
        NewDownloadableFiles = []
        for File in self._DownloadableFiles:
            if self._filterFile(File):
                NewDownloadableFiles.append(File)
        self._DownloadableFiles = NewDownloadableFiles

    def resetFilter(self):
        self._Filters = []

    def checkMD5(self):
        pass
        # TODO: md5 von patrick

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
        self._Downloader.changeDir(File.Folder)
        self._Downloader.downloadFile(File.Name, 'tmp/' + PathInTmp + File.Name)
        self._DownloadedFiles.append(File)

    def downloadAll(self, PathInTmp):
        while len(self._DownloadableFiles) > 0:
            self.downloadFile(PathInTmp)

    def resetDownloadQueue(self):
        self._DownloadableFiles = []

    def clearDownloadedFiles(self):
        self._DownloadedFiles = []
        # TODO: delete them in path

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
        for Filter in self._Filters:
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_ENDS_WITH and File.Name.endswith(Filter.Condition):
                return False
            if Filter.Flag == self.FILTER_FILE_EXCLUDE_CONTAINS and Filter.Condition in File.Name:
                return False
            # TODO: FILTER_FILE_EXCLUDE_PATTERN
            # TODO: FILTER_FILE_INCLUDE_ENDS_WITH
            # TODO: FILTER_FILE_INCLUDE_CONTAINS
            # TODO: FILTER_FILE_INCLUDE_PATTERN
            # TODO: FILTER_FILE_START_DATE
            # TODO: FILTER_FILE_END_DATE
        # TODO: default true?
        return True
