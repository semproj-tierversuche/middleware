import json
from pathlib import Path
import time

from elasticsearch5 import Elasticsearch

from flask import Flask
from flask_restplus import abort, Api, Resource

def document_for_pmid(pmid):
    query = {"query": {"match": {"PMID": pmid}}}
    res = es.search(**es_options, body=query)
    if res["hits"]["total"] == 0:
        return False
    return res["hits"]["hits"][0]["_source"]

# load (example) results from file, but retrieve individual records from DB
def results_for_pmid(pmid):
    # make sure that we only use ints when constructing the file name
    pmid = int(pmid)
    file_path = Path("data/results", str(pmid) + ".json")
    if not file_path.is_file():
        return False
    with file_path.open() as f:
        results_json =  json.load(f)["Results"]

    response = {}
    response["Origin"] = document_for_pmid(pmid)
    results = []
    for result in results_json:
        row = {}
        row["Record"] = document_for_pmid(result["Record"]["PMID"])
        row["Matching"] = result["Matching"]
        results.append(row)
    response["Results"] = results
    return response

# Elasticsearch setup
es = Elasticsearch()
es_options = {
        "index": "article_test",
        "doc_type": "article" }

# Flask and flask_restful setup

app = Flask(__name__)
app.config["ERROR_404_HELP"] = False
api = Api(app)

# API definition

doc_responses = { 200: 'Success',
                  404: 'Resource not found' }

@api.doc(responses=doc_responses)
class ResultsAPI(Resource):
    def get(self, id):
        results = results_for_pmid(id)
        if not results:
            abort(404, message="No results available for this id.")
        time.sleep(3)
        return results

@api.doc(responses=doc_responses)
class DocumentAPI(Resource):
    def get(self, id):
        document = document_for_pmid(id)
        if not document:
            abort(404, message="No such document.")
        time.sleep(3)
        return document

api.add_resource(ResultsAPI, '/results/<int:id>')
api.add_resource(DocumentAPI, '/document/<int:id>')

# Run the flask app

if __name__ == '__main__':
    app.run(debug=True)
