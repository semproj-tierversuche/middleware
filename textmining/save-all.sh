#!/bin/bash
set -eu
shopt -s extglob

for file in  pubmed-tools/data/documents/+([0-9]).xml; do
	./process.py < "$file"
done
