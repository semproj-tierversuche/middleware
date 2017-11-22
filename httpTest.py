#!/usr/bin/env python3
# requires at least python 3.4

from classes.config import ConfigReader
from classes.http_service import HttpService

Config = ConfigReader()
Config.parseConfigFile('../config.xml')
print(Config._Database)
Test = HttpService(Config._Database)
Test.addParameter('q','test')
Test.addParameter('oq','test')
Test.addParameter('aqs', 'chrome..69i57j69i61j69i65j69i61j69i65l21352j0j7')
Test.addParameter('sourceid', 'chrome')
Test.addParameter('ie', 'UTF-8')
Test.startACall('GET')
print(Test.call().content)
