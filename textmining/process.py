#!/usr/bin/env python3
import sys

from document import Document, DocumentModel

xml = sys.stdin.read()

document = Document(xml)
model = DocumentModel()
print(document.process())

model.store(document.attributes)
