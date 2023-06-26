from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os
import json
from utils import process_results

app = Flask(__name__)
CORS(app)

def load_environment_variables():
    load_dotenv()
    return os.environ.get("GOOGLE_API_KEY"), os.environ.get("CUSTOM_SEARCH_ENGINE_ID")

API_KEY, CX = load_environment_variables()

@app.route('/.well-known/ai-plugin.json', methods=['GET'])
def get_plugin_info():
    with open('.well-known/ai-plugin.json') as f:
        data = json.load(f)
        data['api']['url'] = f"{request.scheme}://{request.host}/.well-known/openapi.yaml"
        data['logo_url'] = f"{request.scheme}://{request.host}/.well-known/icon.png"

        return jsonify(data)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    responseTooLarge_str = request.args.get('percentileofresults', '')
    responseTooLarge = 1
    try:
        # Try to convert the string to an integer
        responseTooLarge = int(responseTooLarge_str)
    except ValueError:
        # If it's not possible, then responseTooLarge remains 1
        responseTooLarge = 1
        pass

    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CX}&q={query}&num=10"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        results = data.get('items', [])
        formatted_results = process_results(results,responseTooLarge)
        return jsonify({"results": formatted_results})
    else:
        error_data = response.json()  # Get JSON data from the error response
        print(f"Error fetching search results: {error_data}")  # Print the error data
        return jsonify({"error": "Error fetching search results", "details": error_data}), response.status_code

@app.route('/.well-known/<path:filename>')
def serve_well_known_files(filename):
    return send_from_directory(os.path.join(os.getcwd(), ".well-known"), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
