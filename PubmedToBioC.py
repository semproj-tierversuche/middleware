# coding: utf-8
import requests
import xml.dom.minidom
PMID = 29171663 #exemplary Pubmed ID
req = requests.get('https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pubmed.cgi/BioC_xml/'+str(PMID)+'/unicode') #returns the PubMed in BioC xml format
dom = xml.dom.minidom.parseString(req.text) #dom contains the BioC xml file in DOM format
