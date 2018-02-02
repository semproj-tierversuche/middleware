#!/usr/bin/env python3
# requires at least python 3.4

class PlugInInterface(object):

    @staticmethod
    #must return a list of DOM (in BioC) of the corresponding file and
    #all not by BioC supported Information (PMID, Authors, Journal, Link, Keywords)
    def preTextminingHook(File, OrginalPath):
        raise Exception("NotImplementedException")

    @staticmethod
    #must return a DOM object in BioC
    def preDatabaseHook(BioC):
        raise Exception("NotImplementedException")
