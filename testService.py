#!/usr/bin/env python3
# requires at least python 3.4

from classes.services import Service
from classes.config import ConfigReader

Config = ConfigReader()
Config.parseConfigFile('../config.xml')
#print(Config._Resources)
#print(Config._Textmining)
#print(Config._Database)

Test = Service(Config)
Test.queryDatabase({'q':'test'})
print(Test.queryDatabase({'p':'test'}).content)
