import requests
import sqlite3 as lite
import json
from newsapi import NewsApiClient
from flask import Flask, request, Response, render_template, jsonify, redirect
from flask_httpauth import HTTPBasicAuth
from werkzeug.http import HTTP_STATUS_CODES

app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'

@app.route('/<short_link>')
def index(short_link):
    r = requests.get('http://localhost:8080/links/')
    return r.text

@app.route('/links/<short_link>')
def index_linkls(short_link):
    r = requests.get('http://localhost:8080/links/', headers={'Authorization': 'Bearer AbPBvhUnVFiLoOvA84vaQsj2OMpEC1va'})
    print(r)
    return r.text

@app.route('/get-cookie/')
def get_cookie():
    wer = request.cookies.get('my_token')
    print(wer)

if __name__ == '__main__':
   app.run (host = '127.0.0.1', port = 5000)