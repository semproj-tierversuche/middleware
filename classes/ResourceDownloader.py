from classes.ftp_downloader import FTPBasicDownloader
from classes.resource_downloader_base import AbstractResourceDownloader


class FileAttributes:
    Access = None
    Symlinks = None
    Owner = None
    Group = None
    Filesize = None
    LastModification = None
    Filename = None


class ResourceDownloader(AbstractResourceDownloader):
    # TODO: Exception handling for whole class
    # TODO: filter files with no read access
    # TODO: reconnect only if needed

    _Downloader = None
    _Filters = []

    def __init__(self):
        super().__init__()
        self._DownloadableFiles = []
        self._DownloadedFiles = []
        self.__Username = ''
        self.__Password = ''
        self.UseTLS = False

    def setBaseAddress(self, Address):
        #USERNAME = 'anonymous'
        #PASSWORD = 'anonymous@hu-berlin.de'
        self._Downloader = FTPBasicDownloader(Address)
        self._Downloader.UseTLS = self.UseTLS
        self._Downloader.Username = self.__Username
        self._Downloader.Password = self.__Password
        self._Downloader.initializeConnection()
        self._DownloadableFiles = []
        self._DownloadedFiles = []

    def addSubFolder(self, Folder):
        self._Downloader.reconnect()
        #self._Downloader.goBackToBaseDir()
        FileList = self._Downloader.getFileList(Folder)
        for File in FileList:
            FileAttributes = self._parseFileAttributes(File)
            # make file a tupel of path and filename
            File = (Folder, FileAttributes.Filename)
            if self._filterFile(File):
                self._DownloadableFiles.append(File)

    def flush(self, Folder):
        print('ok')
        # TODO: what should this be doing?

    def filterFiles(self, FilterCondition, Flag):
        self._Filters.append((Flag, FilterCondition))

    def flushFilter(self):
        self._Filters = []

    def checkMD5(self):
        print('ok')
        # TODO: check md5 of all files

    def downloadFile(self, PathToDownloadFolder):
        # reconnect
        self._Downloader.reconnect()
        self._Downloader.goBackToBaseDir()
        # check trailing slash
        if not(PathToDownloadFolder[-1:] == '/'):
            PathToDownloadFolder += '/'

        File = self._DownloadableFiles.pop()
        # File[0] ~> Folder; File[1] ~> FileAttributes instance
        self._Downloader.changeDir(File[0])
        self._Downloader.downloadFile(File[1], PathToDownloadFolder + File[1])
        self._DownloadedFiles.append(File)

    def downloadAll(self, PathToDownloadFolder):
        while len(self._DownloadableFiles) > 0:
            self.downloadFile(PathToDownloadFolder)

    def flushDownloadQueue(self):
        self._DownloadableFiles = []

    def _parseFileAttributes(self, AttributesString):
        Attributes = AttributesString.split(' ')
        Attributes = [a for a in Attributes if a]
        # TODO: check if mapping works in every case
        AttributesObject = FileAttributes()

        AttributesObject.Access = Attributes[0]
        AttributesObject.Symlinks = Attributes[1]
        AttributesObject.Owner = Attributes[2]
        AttributesObject.Group = Attributes[3]
        AttributesObject.Filesize = Attributes[4]
        AttributesObject.LastModification = Attributes[5] + ' ' + Attributes[6] + ' ' + Attributes[7]
        AttributesObject.Filename = Attributes[8]

        return AttributesObject

    def _filterFile(self, File):
        for Filter in self._Filters:
            if Filter[0] == self.FILTER_FILE_EXCLUDE_ENDS_WITH and File[1].endswith(Filter[1]):
                return False
            if Filter[0] == self.FILTER_FILE_EXCLUDE_CONTAINS and Filter[1] in File[1]:
                return False
            # TODO: FILTER_FILE_EXCLUDE_PATTERN
            if Filter[0] == self.FILTER_FILE_INCLUDE_ENDS_WITH and File[1].endswith(Filter[1]):
                return True
            if Filter[0] == self.FILTER_FILE_INCLUDE_CONTAINS and Filter[1] in File[1]:
                return True
            # TODO: FILTER_FILE_INCLUDE_PATTERN
            # TODO: FILTER_FILE_START_DATE = 0x6
            # TODO: FILTER_FILE_END_DATE = 0x7
        # TODO: default true?
        return True
