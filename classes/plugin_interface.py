#!/usr/bin/env python3
# requires at least python 3.4

class PlugInInterface(object):
    def __init__(self):
        pass

    def hookForSingleFile(self, FileName):
        raise Exception("NotImplementedException")
    def hookForMultibleFiles(self, PathToFolder):
        raise Exception("NotImplementedException")
