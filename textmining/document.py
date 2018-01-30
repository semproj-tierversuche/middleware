import datetime
import json
# TODO remove
from pprint import pprint
import subprocess
import xml.etree.ElementTree as ElementTree

from elasticsearch5 import Elasticsearch

JSON_PATH = "pubmed-tools/data/documents/"

XSL_FILE = "pubmed2bioc.xsl"
XSLTPROC_BIN = "xsltproc"
XSLTPROC_PATH = "pubmed-tools/bioc/"

TEXTMINING_BIN = ["java", "-jar", "TextMiningPipeline.jar"]

class Document:
    def __init__(self, xml):
        self.xml = xml
        # TODO some attributes are missing, e.g. Keywords
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
        # get PMID from XML
        xml_root = ElementTree.fromstring(self.xml)
        pmid = xml_root.find(".//PMID").text
        with open(JSON_PATH + str(int(pmid)) + ".json") as f:
            self.attributes = json.load(f)

    def _attributes_from_xml(self):
        # without PubmedArticleSet (root), because it is automatically
        # selected by ElementTree
        xml_prefix = "/PubmedArticle/MedlineCitation"
        xml_root = ElementTree.fromstring(self.xml)

        # attributes to be parsed from the XML
        map = {
            "PMID": "/PMID",
            "Title": "/Article/ArticleTitle",
            "Date": "/Article//PubDate",
            "PublicationType": "//PublicationType[1]"
        }
        map_list = {
            "Journal": "/Article/Journal",
            "AbstractText": "//AbstractText",
            "MeshHeadings": "//MeshHeading"
        }

        for key, path in map.items():
            self.attributes[key] = \
                xml_root.find("." + xml_prefix + path).text
        for key, path in map_list.items():
            self.attributes[key] = \
                [element.text for element in xml_root.findall("." +
                    xml_prefix + path)]
        elements = xml_root.findall("." + xml_prefix +
            "/Article/AuthorList/Author")
        self.attributes["Authors"] = []
        for element in elements:
            self.attributes["Authors"].append("{}, {}".format(
                element.find("LastName").text,
                element.find("ForeName").text))

        self.attributes["Link"] = "https://www.ncbi.nlm.nih.gov/pubmed/" + \
            self.attributes["PMID"]

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

class DocumentModel:
    es_options = {
        "index": "article_test",
        "doc_type": "article" }

    def __init__(self):
        self.es = Elasticsearch()

    def store(self, json):
        return self.es.index(**self.es_options, body=json)
