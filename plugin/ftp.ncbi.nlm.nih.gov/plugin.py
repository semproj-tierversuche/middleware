from gzip import open
from lxml import etree as DOM
from classes.plugin_interface import PlugInInterface
import time as Time
import datetime as Date

class Plugin(PlugInInterface):
    Transformer = None

    @staticmethod
    def getTimestamp(Node):
        if not Node:
            return 0
        Year = Node.find("./Year").text
        Month = Node.find("./Month").text
        Day = Node.find("./Day").text

        return Time.mktime(Date.datetime.strptime("{}-{}-{}".format(Year, Month, Day), "%Y-%m-%d").timetuple())

    @staticmethod
    def bioCPreprocessing(File, OriginalPath):
        Documents = []
        NonBioCInformations = []
        with open(File, 'rb') as File:
            XML = DOM.parse(File)
            Root = XML.getroot()
            #taken from https://github.com/semproj-tierversuche/middleware/blob/dev/textmining/document.py
            Nodes = Root.findall("./PubmedArticle/MedlineCitation")
            for Article in Nodes:
                Documents.append(DOM.fromstring("<PubmedArticleSet><PubmedArticle><MedlineCitation>" + DOM.tostring(Article).decode('utf-8') + "</MedlineCitation></PubmedArticle></PubmedArticleSet>"))

                Information = {}
                Information["PMID"] = str(int(Article.find("./PMID").text))#we have to keep it to match later with the outputting bioC

                Information["Authors"] = []
                for Autor in Article.findall("./AuthorList/Author"):
                    Information["Authors"].append("{}, {}".format(Author.find("LastName").text, Author.find("ForeName").text))

                if Article.find("./Journal/Title"):
                    Information["Journal"] = Article.find("./Journal/Title").text

                Information["Link"] = "https://www.ncbi.nlm.nih.gov/pubmed/" + Information["PMID"]
                if Article.findall("./KeywordList/Keyword"):
                    Information["Keywords"] = [Element.text  for Element in Article.findall("./KeywordList/Keyword")]

                #get Dateinfofield
                DateCompleted = Plugin.getTimestamp(Article.find("./DateCompleted"))
                DateRevised = Plugin.getTimestamp(Article.find("./DateRevised"))
                DateCreated = Plugin.getTimestamp(Artcile.find("./DateCreated"))

                if DateCompleted > DateCreated:
                    if DateCompleted > DateRevised:
                        Information["Date"] = DateCompleted
                    else:
                        Information["Date"] = DateRevised
                else:
                    if DateCreated > DateRevised:
                        Information["Date"] = DateCreated
                    else:
                        Information["Date"] = DateRevised

                NonBioCInformations.append(Information)

            return (Documents, NonBioCInformations)


    @staticmethod
    def toBioC(WhatEver, OriginalPath):
        if not Plugin.Transformer:
            XSLT = DOM.parse("./plugin/ftp.ncbi.nlm.nih.gov/transform.xlst")
            Plugin.Transformer = DOM.XSLT(Plugin.XSLT)

        return Transformer(WhatEver)

    @staticmethod
    def preDatabaseHook(BioC, Filename, OriginalPath):
        return BioC
