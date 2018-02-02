#!/usr/bin/env python3
# requires at least python 3.4

class PlugInInterface(object):

    @staticmethod
    #must return a Elementree.DOM object
    def preTextminingHook(File):
        raise Exception("NotImplementedException")

    @staticmethod
    #must return a Elementree.Dom object in BioC
    def preDatabaseHook(BioC):
        raise Exception("NotImplementedException")
