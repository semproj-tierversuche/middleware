#!/usr/bin/env python3
# requires at least python 3.4

from classes.config import ConfigReader
from classes.ResourceDownloader import ResourceDownloader

LastUpdate = 0

#step 1 -> reading config
Config = ConfigReader()
Config.parseConfigFile("../config.xml")
#step 2 -> prepare download
download = ResourceDownloader()
for resource in Config._Resources:
    download.setBaseAddress(resource['address'])
#step 3 -> when we did the last update for this source
#TODO
#step 4 -> adding the sources
    for subfolder in resource["folders"]:
        if not bool(subfoldet['onInitializion']) or 0 == LastUpdate:
            download.addSubFolder(subfolder)

#step 5(optional) -> check md5 and remove invalide files
    if bool(resource["md5"]):
        download.checkMD5()

    download.flush()
