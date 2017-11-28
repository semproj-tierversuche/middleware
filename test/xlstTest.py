import lxml.etree as ET
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("xlst_file",
                           help="vollständinger Pfad der XLST Datei")
parser.add_argument("xml_file",
                            help="vollständiger Pfad der XML Datei, bei welcher die Transformation gemacht werden soll.")
args = parser.parse_args()

print(args.xlst_file)
XMLfile = open(args.xml_file)
ToTransform = ''
Xlst = ''
for line in XMLfile:
        ToTransform += line.rstrip()
XMLfile.close()
XLSTfile = open(args.xlst_file)
for line in XLSTfile:
        Xlst += line.rstrip()
XLSTfile.close()
DOM = ET.parse(ToTransform)
XSLT = ET.parse(Xlst)
Transformers = ET.XSLT(Xslt)
TDom = Transformers(DOM)
print(ET.tostring(TDom, pretty_print=True))




