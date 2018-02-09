from gzip import open
from copy import deepcopy as Copy
from lxml import etree as DOM
from classes.plugin_interface import PlugInInterface
import time as Time
import datetime as Date

class Plugin(PlugInInterface):
    Transformer = None

    @staticmethod
    def getTimestamp(Node):
#        if not Node:
        if Node is None:
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
                Root = DOM.Element("PubmedArticleSet")
                Root.append(DOM.Element("PubmedArticle"))
                Node = Root[0]
                Node.append(Copy(Article))
                Documents.append(Root)
                #Documents.append(DOM.fromstring("<PubmedArticleSet><PubmedArticle>" +\
                #                DOM.tostring(Article).decode('utf-8') + "</PubmedArticle></PubmedArticleSet>"))

                Information = {}
                Information["PMID"] = str(int(Article.find("./PMID").text))#we have to keep it to match later with the outputting bioC

                Type = Article.find("./PublicationTypeList/PublicationType")
                if Type and Type.text.strip():
                    Information["PublicationType"] = Type.text.strip()
                else:
                    Information["PublicationType"] = ''

                Information["Authors"] = []
                for Autor in Article.findall("./AuthorList/Author"):
                    Information["Authors"].append("{}, {}".format(Author.find("LastName").text, Author.find("ForeName").text))

                if Article.find("./Journal/Title"):
                    Information["Journal"] = Article.find("./Journal/Title").text
                else:
                    Information["Journal"] = ""

                Information["Link"] = "https://www.ncbi.nlm.nih.gov/pubmed/" + Information["PMID"]
                Information["Keywords"] = []
                for Element in Article.findall("./KeywordList/Keyword"):
                    if Element.text and Element.text.rstrip().lower():
                         Information["Keywords"].append(Element.text.rstrip())
                #get Datuminfofield
                DateCompleted = Plugin.getTimestamp(Article.find("./DateCompleted"))
                DateRevised = Plugin.getTimestamp(Article.find("./DateRevised"))
                DateCreated = Plugin.getTimestamp(Article.find("./DateCreated"))

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
            del Nodes
            del XML
            return (Documents, NonBioCInformations)

    @staticmethod
    def toBioC(WhatEver, OriginalPath):
        if not Plugin.Transformer:
            XSLT = DOM.parse("./plugin/ftp.ncbi.nlm.nih.gov/transform.xlst")
            Plugin.Transformer = DOM.XSLT(XSLT)

        return Plugin.Transformer(WhatEver)

    @staticmethod
    def mergeArticles(ArticleOld, ArticleNew):
        return ArticleNew

    @staticmethod
    def modififyDataTree(DataTree, IDs):
        pass
