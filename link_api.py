import requests
import sqlite3 as lite
import json
from newsapi import NewsApiClient
from flask import Flask, request, Response, render_template, jsonify, redirect, g
from flask_httpauth import HTTPBasicAuth
from werkzeug.http import HTTP_STATUS_CODES

app = Flask(__name__)
basic_auth = HTTPBasicAuth()

def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response

@basic_auth.verify_password
def verify_password(name, password):
    r = requests.get('http://localhost:8080/login/', params = {'user' : name, 'password' : password})
    print(r.text)
    if r.text == 'dis':
        return False
    if r:
        r_token = requests.get('http://localhost:8080/tokens/', params = {'user' : name, 'password' : password})
    g.user = name
    g.password = password
    if name:
        g.token = r_token.json()['token'][0]
    return r.text == 'ok'

@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)

@app.route('/')
@basic_auth.login_required
def index2():
    r = requests.get('http://localhost:8080/')
    return r.text

@app.route('/<short_link>')
@basic_auth.login_required
def index(short_link):
    r = requests.get('http://localhost:8080/'+short_link, params = {'user' : g.user, 'password' : g.password})
    return r.text

@app.route('/links/')
@basic_auth.login_required
def all_links():
    r = requests.get('http://localhost:8080/links/', headers={'Authorization': "Bearer %s" % g.token})
    return r.text

@app.route('/links/<short_link>')
@basic_auth.login_required
def index_links(short_link):
    r = requests.get('http://localhost:8080/links/', headers={'Authorization': "Bearer %s" % g.token})
    return r.text

@app.route('/tokens/')
@basic_auth.login_required
def index_tokens():
    r = requests.get('http://localhost:8080/tokens/',  params = {'user' : g.user, 'password' : g.password})
    return r.text

if __name__ == '__main__':
   app.run (host = '127.0.0.1', port = 5000)