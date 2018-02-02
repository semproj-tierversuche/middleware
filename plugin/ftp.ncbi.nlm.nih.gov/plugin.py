from gzip import open
from lxml import etree as DOM
from classes.plugin_interface import PlugInInterface

class Plugin(PlugInInterface):

    @staticmethod
    def preTextminingHook(File, OriginalPath):
        with open(File, 'rb') as File:
            XML = DOM.parse(File)
            BioCs = []
            Root = XML.getroot()
            XSLT = DOM.parse("./plugin/ftp.ncbi.nlm.nih.gov/transform.xlst")
            Transformer = DOM.XSLT(XSLT)
            for Element in Root.findall("./PubmedArticle"):
                New = DOM.fromstring("<PubmedArticleSet><PubmedArticle>" + DOM.tostring(Element).decode('utf-8') + "</PubmedArticle></PubmedArticleSet>")
                BioCs.append(Transformer(New))


            #taken from https://github.com/semproj-tierversuche/middleware/blob/dev/textmining/document.py
            Root = XML.getroot()
            Nodes = Root.findall("./PubmedArticle/MedlineCitation")
            print(Nodes)
            NonBioCInformations = []
            for Article in Nodes:
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
                NonBioCInformations.append(Information)
            return (BioCs, NonBioCInformations)


    @staticmethod
    def preDatabaseHook(BioC):
        return BioC
