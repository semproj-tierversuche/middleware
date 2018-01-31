#!/usr/bin/env python3
import json
import sys

from document import Document, DocumentStore

xml = sys.stdin.read()

document = Document(xml)
store = DocumentStore()
store.store(json.dumps(document.attributes))
