from gzip import open
from lxml import etree as DOM
from classes.plugin_interface import PlugInInterface

class Plugin(PlugInInterface):

    @staticmethod
    def preTextminingHook(File):
        with open(File, 'rb') as File:
 #           return DOM.parse(File)
            XML = DOM.parse(File)
            Articles = []
            Root = XML.getroot()
            for Element in Root.findall("./PubmedArticle"):
                Articles.append(Element)
            return Articles



            #taken from https://github.com/semproj-tierversuche/middleware/blob/dev/textmining/document.py
 #           Articles = []
 #           Root = XML.getroot()
 #           Nodes = Root.findall("./PubmedArticle/MedlineCitation")
 #           for Node in Nodes:
 #               continue
 #               FormattetArticle = { "Suggest": "", "Annotations": [], "Keywords": [], "Identifier": [], "Substances": [], "TextminingVersion": "0" }
 #               Article = Node.find("./Article")
 #               FormattetArticle["PMID"] = str(int(Article.find("./PMID").text))
 #               FormattetArticle["Title"] = Article.find("./ArticleTitle").text

  #              FormattetArticle["Authors"] = []
  #              for Autor in Article.findall("./AuthorList/Author"):
  #                  FormattetArticle["Authors"].append("{}, {}".format(Author.find("LastName").text, Author.find("ForeName").text))

   #             FormattedArticle["Journal"] = Article.find("./Journal/Title").text
    #            FormattedArticle["Link"] = "https://www.ncbi.nlm.nih.gov/pubmed/" + FormattetArticle["PMID"]
     #           FormattedArticle["Keywords"] = [Element.text  for Element in Node.findall("./KeywordList/Keyword")]

      #          FormattedArticle["Abstract"] = ''
       #         Parts = Article.findall("./Abstract/AbstractText")
        #        for Partion in Parts:
         #           if 'Label' in Partion.keys():
          #              if FormattedArticle["Abstract"]:
           #                 FormattedArticle["Abstract"] += " "
            #            FormattedArticle["Abstract"] += "{}: {}".format(Partion.attrib["Label"], Partion.text)
             #       else:
              #          FormattedArticle["Abstract"] += Partion.text

#                Substances = Node.findall("./ChemicalList/Chemical/NameOfSubstance")
 #               FormattedArticle["Substances"] = [Element.text for Element in Substances]

  #              FormattedArticle["MeshHeadings"] = []
   #             MeshHeadings = Node.findall("./MeshHeadingList/MeshHeading")
    #            for Heading in MeshHeadings:
     #               Descriptor = Heading.find("./DescriptorName").text
      #              Qualifiers = [ Element.text for Element in Heading.findall("./QualifierName") ]
#                    if Qualifiers:
 #                       Qualifiers = " (" + ", ".join(Qualifiers) + ")"
  #                  else:
   #                     Qualifiers = ""
#
 #                   FormattedArticle["MeshHeadings"].append(Descriptor + Qualifiers)
  #              Articles.append(FormattetArticle)
   #         return XML

    @staticmethod
    def preDatabaseHook(BioC):
        return BioC
