#!/usr/bin/env python3
# requires at least python 3.4

class PlugInInterface(object):

    @staticmethod
    #returns all not by BioC supported Information (PMID, Authors, Journal, Link, Keywords, PublicationType,Date) of one document
    #and very important the last modified of document, if its given by the file itself, otherwise set this field to None
    #also gives whatever (string, DOM, handle...) back which is neccesary for the transformation to BioC
    def bioCPreprocessing(File, OriginalPath):
        raise Exception("NotImplementedException")

    @staticmethod
    #must return a list of DOM (in BioC) of the corresponding file
    def toBioC(WhatEver, OrginalPath):
        raise Exception("NotImplementedException")

    @staticmethod
    #this function must diside how to handle collding articles
    #and must return a merge of both article in the given schema
    def mergeArticles(ArticleOld, ArticleNew):
        raise Exception("NotImplementedException")

    @staticmethod
    #this function can modifiy the complete DataTree before storing into the
    #database if there any additional stuff to do and store use the Field
    #suggestions
    #the returns nothing
    def modififyDataTree(DataTree, IDs):
        raise Exception("NotImplementedException")
