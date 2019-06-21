import requests
import sqlite3 as lite
import json
from newsapi import NewsApiClient
from flask import Flask, request, Response, render_template, jsonify, redirect, g
from flask_httpauth import HTTPBasicAuth
from werkzeug.http import HTTP_STATUS_CODES

app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
basic_auth = HTTPBasicAuth()

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField
from wtforms.validators import DataRequired

def access_decode(access):
    if access == 1:
        return('Публичная')
    elif access == 2:
        return ('Общего доступа')
    else:
        return ('Приватная')

class LinkForm(FlaskForm):
    full_link = StringField('Full link', validators=[DataRequired()])
    short_link = StringField('Short_link', validators=[DataRequired()])
    access = RadioField('Access', choices=[(1,access_decode(1)),
                                           (2, access_decode(2)),
                                           (3, access_decode(3))
                                            ])
    submit = SubmitField('Sign In')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

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
    return r

@app.route('/<short_link>')
@basic_auth.login_required
def index(short_link):
    r = requests.get('http://localhost:8080/'+short_link, params={'user': g.user, 'password': g.password})
    return r.text

@app.route('/all_links/', methods=['GET', 'POST'])
@basic_auth.login_required
def all_link():
    r = requests.get('http://localhost:8080/links/', headers={'Authorization': "Bearer %s" % g.token})
    links = r.json()
    print(links)
    return render_template("links.html",
        title = 'Link list:',
        name = g.user,
        links = links)

@app.route('/add_links/', methods=['GET', 'POST'])
@basic_auth.login_required
def edit_link():
    form = LinkForm()
    print(form.validate_on_submit())
    if form.full_link.data and form.short_link.data and form.access.data:
        r = requests.post('http://localhost:8080/links/',
                         headers={'Authorization': "Bearer %s" % g.token},
                         params ={
                             'full_link': form.full_link.data,
                             'short_link': form.short_link.data,
                             'access_type': form.access.data
                                })
        return redirect('/all_links/')
    return render_template('edit_link.html', title='Sign In', form=form)

@app.route('/delete_link/<link_id>', methods=['GET', 'POST'])
@basic_auth.login_required
def delete_link(link_id):
    r = requests.delete('http://localhost:8080/links/',
                     headers={'Authorization': "Bearer %s" % g.token},
                     params ={
                         'link_id': link_id})
    return redirect('/all_links/')

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