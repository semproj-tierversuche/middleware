import datetime
import ftputil
from urllib.parse import urlparse


class ResourceDownloader(object):
    # TODO: default startDate 19.12.2016 only works with PubMed
    __startDate = datetime.datetime(2016, 12, 19)
    __resources = []

    def addUrl(self, url):
        resource = urlparse(url)
        # TODO: url validation
        if not(resource.scheme == 'ftp'):
            raise RuntimeError('So far, only ftp is supported')
        self.__resources.append(resource)

    def setStartDate(self, startDate):
        if not(isinstance(startDate, datetime.datetime)):
            raise TypeError("startDate should be of type datetime.datetime")
        self.__startDate = startDate

    def run(self):
        for resource in self.__resources:
            # TODO: change credentials
            with ftputil.FTPHost(resource.netloc, 'anonymous', 'anonymous@hu-berlin.de') as host:
                # TODO: add support for single file downloads
                names = host.listdir(resource.path)
                # TODO: filter by startDate
                for name in names:
                    print(name)


