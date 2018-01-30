#!/bin/bash
set -eu
shopt -s extglob

ls pubmed-tools/data/documents/+([0-9]).xml \
	| xargs  -P 16 -n 1 -I % sh -c './process.py < "%"'
