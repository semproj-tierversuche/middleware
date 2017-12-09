from classes.ResourceDownloader import ResourceDownloader


Download = ResourceDownloader()
Download.setCredentials('anonymous', 'anonymous@hu-berlin.de')
Download.setBaseAddress('ftp.ncbi.nlm.nih.gov')
Download.filterFiles('*', Download.FILTER_FILE_EXCLUDE_PATTERN)
Download.filterFiles('.xml.gz', Download.FILTER_FILE_INCLUDE_ENDS_WITH)
Download.addSubFolder('pubmed/baseline/', True)
Download.downloadAll('./')
