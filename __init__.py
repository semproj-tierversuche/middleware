from classes.ResourceDownloader import ResourceDownloader


download = ResourceDownloader()
download.addUrl('ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/')
download.addUrl('ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/')
download.run()
