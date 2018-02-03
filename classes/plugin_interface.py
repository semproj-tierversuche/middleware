#!/usr/bin/env python3
# requires at least python 3.4

class PlugInInterface(object):

    @staticmethod
    #returns all not by BioC supported Information (PMID, Authors, Journal, Link, Keywords, Date) of one document
    #and very important the last modified of document, if its given by the file itself, otherwise set this field to None
    #also gives whatever (string, DOM, handle...) back which is neccesary for the transformation to BioC
    def bioCPreprocessing(File, OriginalPath):
        raise Exception("NotImplementedException")

    @staticmethod
    #must return a list of DOM (in BioC) of the corresponding file
    def toBioC(WhatEver, OrginalPath):
        raise Exception("NotImplementedException")

    @staticmethod
    #must return a DOM object in BioC
    def modififyTextminingOutput(BioC, Filename, OrginalPath):
        raise Exception("NotImplementedException")
