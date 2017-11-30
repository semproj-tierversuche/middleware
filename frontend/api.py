import json
from pathlib import Path

from flask import Flask
from flask_restful import abort, Api, Resource

def document_for_pmid(pmid):
    pmid = int(pmid)
    file_path = Path("data/documents", str(pmid) + ".json")
    if not file_path.is_file():
        return False
    with file_path.open() as f:
        return json.load(f)

# load (example) results from file
def results_for_pmid(pmid):
    # make sure that we only use ints when constructing the file name
    pmid = int(pmid)
    file_path = Path("data/results", str(pmid) + ".json")
    if not file_path.is_file():
        return False
    with file_path.open() as f:
        return json.load(f)

# Flask and flask_restful setup

app = Flask(__name__)
app.config["ERROR_404_HELP"] = False
api = Api(app)

# API definition

class ResultsAPI(Resource):
    def get(self, id):
        results = results_for_pmid(id)
        if not results:
            abort(404, message="No results available for this id.")
        return results

class DocumentAPI(Resource):
    def get(self, id):
        document = document_for_pmid(id)
        if not document:
            abort(404, message="No such document.")
        return document

api.add_resource(ResultsAPI, '/results/<int:id>')
api.add_resource(DocumentAPI, '/document/<int:id>')

# Run the flask app

if __name__ == '__main__':
    app.run(debug=True)
