import datetime
import json
import subprocess
import xml.etree.ElementTree as ElementTree

from elasticsearch5 import Elasticsearch

JSON_PATH = "pubmed-tools/data/documents/"

XSL_FILE = "pubmed2bioc.xsl"
XSLTPROC_BIN = "xsltproc"
XSLTPROC_PATH = "pubmed-tools/bioc/"

TEXTMINING_BIN = ["java", "-jar", "TextMiningPipelinev0.jar"]

class Document:
    def __init__(self, xml):
        self.xml = xml
        self.attributes = {
                "Suggest": "",
                "Annotations": [],
                "Keywords": [],
                "Identifier": [],
                "Substances": [],
                "TextminingVersion": "0"}
        self.attributes_from_xml()

    def convert_to_bioc(self):
        date = datetime.date.today()
        date = date.strftime("%Y%m%d")
        proc_args = [
            "--nonet",
            "--path", XSLTPROC_PATH,
            "--stringparam", "article-date", date,
            XSLTPROC_PATH + XSL_FILE,
            "-" # read from stdin
        ]
        kwargs = {
            "encoding": "utf-8",
            "input": self.xml,
            "check": True, # raise on non-zero exit status
            "stdout": subprocess.PIPE,
            "stderr": subprocess.DEVNULL
        }
        proc = subprocess.run([XSLTPROC_BIN, *proc_args], **kwargs)
        return proc.stdout

    def attributes_from_xml(self):
        xml_root = ElementTree.fromstring(self.xml)
        xml_citation = xml_root.find("./PubmedArticle/MedlineCitation")
        xml_article = xml_citation.find("Article")

        # double cast to ensure that the value is an integer
        self.attributes["PMID"] = str(int(xml_citation.find("PMID").text))
        self.attributes["Title"] = xml_article.find("ArticleTitle").text

        self.attributes["Authors"] = []
        # I'd be glad to learn how to do this in a nice, readable list
        # comprehension.
        authors = xml_article.findall("AuthorList/Author")
        for author in authors:
            self.attributes["Authors"].append(
                "{}, {}".format(author.find("LastName").text,
                                author.find("ForeName").text
                )
            )

        self.attributes["Journal"] = xml_article.find("Journal/Title").text
        self.attributes["Link"] = \
            "https://www.ncbi.nlm.nih.gov/pubmed/" + self.attributes["PMID"]
        self.attributes["Keywords"] = [
            elem.text for elem in xml_citation.findall("KeywordList/Keyword")
        ]
        self.attributes["PublicationType"] = xml_article.find(
            "PublicationTypeList/PublicationType"
        ).text

        self.attributes["Abstract"] = ""
        abstract_parts = xml_article.findall("Abstract/AbstractText")
        for part in abstract_parts:
            if "Label" in part.keys():
                # this is a part of a structured abstract.
                if not self.attributes["Abstract"] == "":
                    # and this is not the first part, so we add a space
                    self.attributes["Abstract"] += " "
                self.attributes["Abstract"] += "{}: {}".format(
                    part.attrib["Label"], part.text
                )
            else:
                self.attributes["Abstract"] += part.text

        substances = xml_citation.findall(
            "ChemicalList/Chemical/NameOfSubstance"
        )
        self.attributes["Substances"] = [elem.text for elem in substances]

        self.attributes["MeshHeadings"] = []
        mesh_headings = xml_citation.findall("MeshHeadingList/MeshHeading")
        for mesh_heading in mesh_headings:
            descriptor = mesh_heading.find("DescriptorName").text
            qualifiers = [ elem.text for elem in
                           mesh_heading.findall("QualifierName") ]
            if qualifiers:
                # format: " (qual1, qual2, qual3)"
                qualifiers = " (" + ", ".join(qualifiers) + ")"
            else:
                qualifiers = ""
            self.attributes["MeshHeadings"].append(
                descriptor + qualifiers
            )

    def run_textmining(self):
        kwargs = {
            "encoding": "utf-8",
            "input": self.bioc,
            "check": True,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.DEVNULL
        }
        proc = subprocess.run(TEXTMINING_BIN, **kwargs)

        return proc.stdout

    def process(self):
        # 1. process xml to bioc
        self.bioc = self.convert_to_bioc()
        # 2. open textmining binary, pipe bioc in stdin
        return self.run_textmining()

class DocumentStore:
    es_options = {
        "index": "article_test",
        "doc_type": "article" }

    def __init__(self):
        self.es = Elasticsearch()

    def store(self, json):
        return self.es.index(**self.es_options, body=json)
