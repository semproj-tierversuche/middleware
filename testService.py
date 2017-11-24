#!/usr/bin/env python3
# requires at least python 3.4

from classes.services import Service
from classes.config import ConfigReader

Config = ConfigReader()
Config.parseConfigFile('../config.xml')

Test = Service(Config)
print(Test.queryDatabase({'anyQueryKey':'dynamicValue'}))
