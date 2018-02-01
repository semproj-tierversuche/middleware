#!/usr/bin/env python3
import json
import sys

from document import Document, DocumentStore

xml = sys.stdin.read()

document = Document(xml)
document.process()
document._annotations_from_bioc(document.textmining_result)

print(json.dumps(document.attributes))
#store = DocumentStore()
#store.store(json.dumps(document.attributes))
