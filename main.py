# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

# [START gae_python38_auth_verify_token]
from flask import Flask, request, jsonify, abort, make_response, url_for
from flask_cors import CORS
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token
from idna import unicode
from flask_httpauth import HTTPTokenAuth

auth = HTTPTokenAuth(scheme='Bearer')

firebase_request_adapter = requests.Request()

app = Flask(__name__)
CORS(app)

items = [
    {
        'id': 1,
        'title': u'Cat Food',
        'description': u'It\'s cat food'
    },
    {
        'id': 2,
        'title': u'Dog Food',
        'description': u'It\'s dog food'
    }
]


@auth.verify_token
def verify_token(token):
    if token:
        try:
            # Verify the token against the Firebase Auth API. This example
            # verifies the token on each page load. For improved performance,
            # some applications may wish to cache results in an encrypted
            # session store (see for instance
            # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
            result = google.oauth2.id_token.verify_firebase_token(
                token, firebase_request_adapter)

            return result
        except ValueError as exc:
            # This will be raised if the token is expired or any other
            # verification checks fail.
            str(exc)


@auth.error_handler
def unauthorized(error):
    return make_response(jsonify({'error': error}), 401)


def make_public_stock(stock):
    new_stock = {}
    for field in stock:
        if field == 'id':
            new_stock['uri'] = url_for('get_stock', stock_id=stock['id'], _external=True)
        else:
            new_stock[field] = stock[field]
    return new_stock


@app.route('/api/stock', methods=['GET'])
@auth.login_required
def get_stock():
    return jsonify({'stock': [make_public_stock(item) for item in items]})


@app.route('/api/stock/<int:stock_id>', methods=['GET'])
@auth.login_required
def get_item(stock_id):
    stock = [stock for stock in items if stock['id'] == stock_id]
    if len(stock) == 0:
        abort(404)
    return jsonify({'stock': [make_public_stock(item) for item in stock]})


@app.route('/api/stock', methods=['POST'])
@auth.login_required
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    stock = {
        'id': items[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
    }
    items.append(stock)
    return jsonify({'stock': [make_public_stock(item) for item in stock]}), 201


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/api/stock/<int:stock_id>', methods=['PUT'])
@auth.login_required
def update_stock(stock_id):
    stock = [stock for stock in items if stock['id'] == stock_id]
    if len(stock) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    stock[0]['title'] = request.json.get('title', stock[0]['title'])
    stock[0]['description'] = request.json.get('description', stock[0]['description'])
    stock[0]['done'] = request.json.get('done', stock[0]['done'])
    return jsonify({'task': [make_public_stock(item) for item in stock[0]]})


@app.route('/api/stock/<int:stock_id>', methods=['DELETE'])
@auth.login_required
def delete_task(stock_id):
    stock = [stock for stock in items if stock['id'] == stock_id]
    if len(stock) == 0:
        abort(404)
    items.remove(stock[0])
    return jsonify({'result': True})


# [END gae_python38_auth_verify_token]


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)