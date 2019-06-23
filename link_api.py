import requests
import sqlite3 as lite
import json
from newsapi import NewsApiClient
from flask import Flask, request, Response, render_template, jsonify, redirect, session, g
from flask_httpauth import HTTPBasicAuth
from werkzeug.http import HTTP_STATUS_CODES
from flask_login import logout_user, current_user, login_user, UserMixin, LoginManager
from random import randint, choice
import string

app = Flask(__name__)
login = LoginManager(app)
app.config['SECRET_KEY'] = 'you-will-never-guess'
basic_auth = HTTPBasicAuth()
server_path = 'http://localhost:8080/'

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash

def access_decode(access):
    if access == 1:
        return('Публичная')
    elif access == 2:
        return ('Общего доступа')
    else:
        return ('Приватная')

class User_login(UserMixin):
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

l_user = User_login

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
    r = requests.get(server_path+'login/', params = {'user' : name, 'password' : password})
    if r.json():
        r_token = requests.get(server_path+'tokens/', params = {'user' : name, 'password' : password})
    else: r_token = False
    g.user = name
    g.password = password
    if name and r_token:
        g.token = r_token.json()['token'][0]
    return r.json()

@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)

@app.route('/')
def base_index():
    if session.get('logged_in'):
        return redirect('/all_links/')
    else:
        return redirect('/login/')

@app.route('/logout/')
def logout():
    verify_password(g.user, '0')
    return redirect('/all_links/')

@app.route('/<short_link>')
@basic_auth.login_required
def index(short_link):
    r = requests.get(server_path+short_link, params={'user': g.user, 'password': g.password})
    return r.text

@app.route('/add_user/<user>')
def add_user(user):
    password = request.args.get('password')
    r = requests.post(server_path+'users/',
                      params={
                          'name': user,
                          'password': password
                      })
    return r.text

@app.route('/ua/<short_link>')
def index_ua(short_link):
    r = requests.get(server_path+short_link)
    return r.text

@app.route('/all_links/', methods=['GET', 'POST'])
@basic_auth.login_required
def all_link():
    r = requests.get(server_path+'links/', headers={'Authorization': "Bearer %s" % g.token})
    links = r.json()
    print(links)
    return render_template("links.html",
        title = 'Link list:',
        name = g.user,
        links = links)

def random_string_generator(str_size):
    return ''.join(choice(string.ascii_letters) for x in range(str_size))

@app.route('/add_links/', methods=['GET', 'POST'])
@basic_auth.login_required
def add_new_link():
    form = LinkForm()
    form.short_link.data = random_string_generator(10)
    form.access.data = '1'
    if form.full_link.data and form.short_link.data and form.access.data:
        r = requests.post(server_path+'links/',
                         headers={'Authorization': "Bearer %s" % g.token},
                         params ={
                             'full_link': form.full_link.data,
                             'short_link': form.short_link.data,
                             'access_type': form.access.data
                                })
        return redirect('/all_links/')
    return render_template('edit_link.html', title='Sign In', form=form)

@app.route('/edit_link/<id>', methods=['GET', 'POST'])
@basic_auth.login_required
def edit_link(id):

    form = LinkForm()
    r = requests.get(server_path + 'link/'+str(id),
                      headers={'Authorization': "Bearer %s" % g.token})
    select = r.json()
    form.full_link.data = select['full_link']
    form.short_link.data = select['short_link']
    form.access.data = str(select['access'])

    if form.full_link.data and form.short_link.data and form.access.data and form.submit.data:
        r = requests.patch(server_path+'links/',
                         headers={'Authorization': "Bearer %s" % g.token},
                         params ={
                             'link_id': id,
                             'full_link': form.full_link.data,
                             'short_link': form.short_link.data,
                             'access_type': form.access.data
                                })
        return redirect('/all_links/')
    return render_template('edit_link.html', title='Sign In', form=form)

@app.route('/delete_link/<link_id>', methods=['GET', 'POST'])
@basic_auth.login_required
def delete_link(link_id):
    r = requests.delete(server_path+'links/',
                     headers={'Authorization': "Bearer %s" % g.token},
                     params ={
                         'link_id': link_id})
    return redirect('/all_links/')

@app.route('/links/<short_link>')
@basic_auth.login_required
def index_links(short_link):
    r = requests.get(server_path+'links/', headers={'Authorization': "Bearer %s" % g.token})
    return r.text

@app.route('/tokens/')
@basic_auth.login_required
def index_tokens():
    r = requests.get(server_path+'tokens/',  params = {'user' : g.user, 'password' : g.password})
    return r.text

if __name__ == '__main__':
   app.run (host = '127.0.0.1', port = 5000)