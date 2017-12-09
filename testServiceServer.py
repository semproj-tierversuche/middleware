#!/usr/bin/env python3
# requires at least python 3.4

from classes.services import DatabaseService
from classes.config import ConfigReader
import os as OS
import time
from classes.http_service import HttpServiceException

Config = ConfigReader()
Config.parseConfigFile('../config.xml')

Test = DatabaseService(Config)
Dir = OS.listdir("/home/geislemx/frontend/middleware/frontend/data/documents")
for x in range(0, len(Dir)):
	fobj = open("/home/geislemx/frontend/middleware/frontend/data/documents/"+Dir[x])
	store = ''
	for line in fobj:
	    store += line
	fobj.close()

#print(Test.queryDatabase({'PMID':'12663096'}, {'type':'document'}))

	try:
		print(Test.insertIntoDatabase(store, {'type':'document'}))
	except HttpServiceException as e:
		time.sleep(3)
		print(Test.insertIntoDatabase(store, {'type':'document'}))
#print(Test.insertIntoDatabase('', {'type':'document'}))
#print(Test.insertIntoDatabase({ "Abstract" : [ "Test "], "Annotations" : [  ],  "Authors" : ["Lavalley, Nicholas J","Slone, Sunny R","Ding" ], "Date" : "2016", "Identifier": [  ], "Journal" : [ "Human molecular genetics" ], "Keywords" : [  ], "Link" : "https://www.ncbi.nlm.nih.gov/pubmed/26546614","MeshHeadings" : ["14-3-3 Proteins", "Animals"], "PMID" : 26546614,"PublicationType" : "Journal Article", "Substances" : [  ], "Suggest" : "", "TextminingVersion" : "0", "Title" : "14-3-3 Proteins regulate mutant LRRK2 kinase activity and neurite shortening."}))
