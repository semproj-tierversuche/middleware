from gzip import open
from lxml import etree
from classes.plugin_interface import PlugInInterface


class PubmedPlugin(PlugInInterface):

    def hookForSingleFile(self, FileName):
        with open('tmp/'+FileName, 'rb') as File:
            return etree.parse(File)