#!/usr/bin/env python3
import sys

sys.path.insert(0, "/home/sefischer/.local/lib64/python3.5/site-packages")

from document import Document, DocumentModel

xml = sys.stdin.read()

document = Document(xml)
model = DocumentModel()
print(document.process())

model.store(document.attributes)
