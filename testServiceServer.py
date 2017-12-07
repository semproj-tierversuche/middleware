#!/usr/bin/env python3
# requires at least python 3.4

from classes.services import DatabaseService
from classes.config import ConfigReader

Config = ConfigReader()
Config.parseConfigFile('../config.xml')

Test = DatabaseService(Config)
print(Test.insertIntoDatabase({ "Abstract" : [ "Test "], "Annotations" : [  ],  "Authors" : ["Lavalley, Nicholas J","Slone, Sunny R","Ding" ], "Date" : "2016", "Identifier": [  ], "Journal" : [ "Human molecular genetics" ], "Keywords" : [  ], "Link" : "https://www.ncbi.nlm.nih.gov/pubmed/26546614","MeshHeadings" : ["14-3-3 Proteins", "Animals"], "PMID" : 26546614,"PublicationType" : "Journal Article", "Substances" : [  ], "Suggest" : "", "TextminingVersion" : "0", "Title" : "14-3-3 Proteins regulate mutant LRRK2 kinase activity and neurite shortening."}))
