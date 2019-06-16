import requests
import sqlite3 as lite
import json
from newsapi import NewsApiClient
from flask import Flask, request, Response, render_template, jsonify, redirect
from flask import g, make_response
from flask_httpauth import HTTPBasicAuth
from flask_httpauth import HTTPTokenAuth
from werkzeug.http import HTTP_STATUS_CODES
import base64
from datetime import datetime, timedelta
import os
from dateutil import parser

app = Flask(__name__)
app.config.from_object('config')
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

def sql_command(sql_req):
    con = lite.connect('links.sqlite')
    curID = con.cursor()
    curID.executescript(sql_req)
    resp = curID.fetchall()
    con.close()
    return(resp)

def sql_command_lite(sql_req):
    con = lite.connect('links.sqlite')
    curID = con.cursor()
    curID.execute(sql_req)
    resp = curID.fetchone()
    con.close()
    return resp

def sql_command_get(sql_req):
    con = lite.connect('links.sqlite')
    curID = con.cursor()
    curID.execute(sql_req)
    resp = curID.fetchall()
    con.close()
    return resp

def get_from_user(name, column):
    print('GFU:')
    return sql_command_lite('SELECT %s FROM Users WHERE Name LIKE "%s"' % (column, name))

def get_token(username, expires_in=3600):
    print('Get_token')
    now = datetime.utcnow()
    token = get_from_user(username, 'token')
    print('Get token. Token:', token)
    token_expiration = parser.parse(get_from_user(username, 'token_expiration'))
    if token and token_expiration > now + timedelta(seconds=60):
        return token
    token = base64.b64encode(os.urandom(24)).decode('utf-8')
    token_expiration = now + timedelta(seconds=expires_in)
    sql_request = 'UPDATE Users SET token = "%s", token_expiration = "%s" WHERE Name LIKE "%s"' % (token, token_expiration, username)
    sql_command(sql_request)
    return token

# get_token('Michael')

def revoke_token(username):
    token_expiration = datetime.utcnow() - timedelta(seconds=1)
    sql_request = 'UPDATE Users SET token_expiration = "%s"' % token_expiration
    sql_command_get(sql_request)

# revoke_token('Michael')

def check_token(token):
    print('Chek_token')
    sql_request = 'SELECT Name FROM Users WHERE Token LIKE "%s"' % token
    user = sql_command_lite(sql_request)
    print(sql_request)
    print (user)
    if user is None:
        return None
    if parser.parse(get_from_user(user, 'token_expiration')) < datetime.utcnow():
        return None
    return user

def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response

@token_auth.verify_token
def verify_token(token):
    current_user = check_token(token) if token else None
    print('Пользователь:', current_user)
    print('Токен:', token)
    return current_user is not None

@token_auth.error_handler
def token_auth_error():
    return error_response(401)


@app.route('/tokens', methods=['GET'])
@basic_auth.login_required
def gets_token():
    token = get_from_user('Michael', 'token')
    print (token)
#    print(token)
#    res = make_response('Setting a cookie')
#    print(res.set_cookie('my_token', (token)))
#    wer = str(request.cookies.get('my_token'))
#    print(wer)
    return jsonify({'token': token})

@basic_auth.verify_password
def verify_password(name, password):
    sql_request = 'SELECT Password FROM Users WHERE Name LIKE "%s"' % name
    pwd = sql_command_lite(sql_request)
    if pwd is None:
        return False
    return pwd[0] == password

verify_password('Michael','3')

@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)

@app.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_token()
    db.session.commit()
    return jsonify({'token': token})

def full_link(short_link):
    sql_request = 'SELECT Full_link FROM Links WHERE Short_link LIKE "%s"' % short_link
    resp = sql_command_lite(sql_request)
    return resp

def short_link_exists(short_link):
    sql_request = 'SELECT ID FROM Links WHERE Short_link LIKE "%s"' % short_link
    resp = sql_command_lite(sql_request)
    return resp

def user_exists(name):
    sql_request = 'SELECT ID FROM Users WHERE Name LIKE "%s"' % name
    resp = sql_command_lite(sql_request)
    return resp

def user_ID(vk_ID):
    sql_request = 'SELECT ID FROM Users WHERE vk_ID = "%s"' % vk_ID
    resp = sql_command_lite(sql_request)
    return resp

def add_link(vk_id, full_link, short_link, access_type):
#    Добавление ссылки
    if not short_link_exists(short_link):
        sql_request = "INSERT INTO Links (Full_Link, Short_Link, UserID, Access) VALUES ('%s','%s', '%s','%s')" % (full_link, short_link, user_ID(vk_id), access_type)
        sql_command(sql_request)
        return 'Ok'+sql_request
    else:
        return 'Ошибка. Такая короткая ссылка уже зарегистрирована'

def get_links(vk_ID):
    sql_request = "SELECT Full_Link, Short_Link, Access FROM Links WHERE UserID=%s" % (str(user_ID(vk_ID)))
    return jsonify(sql_command_get(sql_request))

def delete_link(short_link):
    sql_request = "DELETE FROM Links WHERE Short_Link='%s'" % (str(short_link))
    sql_command(sql_request)
    return 'Delete '+sql_request

def update_link(full_link, short_link, access_type):
    sql_request = "DELETE FROM Links WHERE Short_Link='%s'" % (str(short_link))
    sql_command(sql_request)
    return 'Delete '+sql_request

def add_user(id_vk, name, password):
    if not user_exists(name):
        sql_request = "INSERT INTO Users (vk_ID, name, Password) VALUES ('%s','%s','%s')" % (str(id_vk), name, password)
        sql_command(sql_request)
        return "Добавлен пользователь :'%s'" % (name)
    else:
        return "Пользователь :'%s' уже зарегистрирован. Выберите другое имя " % (name)

def access_decode(access):
    if access == 1:
        return('Публичная')
    elif access == 2:
        return ('Общего доступа')
    else:
        return ('Приватная')


def get_links_http(user_id):
    sql_request = "SELECT Full_Link, Short_Link, Access FROM Links WHERE UserID=%s" % 4
    links = sql_command_get(sql_request)
    select = []

    for items in range(len(links)):
        select_item = (links[items])
        select.append({'Full_link': select_item[0], 'Short_link': select_item[1], 'Access': access_decode(select_item[2])})

    return render_template("index.html",
        title = 'Список ссылок:',
        user = user_id,
        links = select)


@app.route('/links/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@basic_auth.login_required
def links(*args, **kwargs):
    user_id = request.args.get('user_id')
    link_id = request.args.get('link_id')
    full_link = request.args.get('full_link')
    short_link = request.args.get('short_link')
    access_type = request.args.get('access_type')
    if request.method == 'GET':
        return get_links_http(user_id)
    elif request.method == 'POST':
        return add_link(user_id, full_link, short_link, access_type)
    elif request.method == 'PATCH':
        return update_link(full_link, short_link, access_type)
    elif request.method == 'DELETE':
        return delete_link(short_link)
    else:
        return 'None'

@app.route('/users/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@basic_auth.login_required
def users(*args, **kwargs):
    user_id = request.args.get('user_id')
    vk_id = request.args.get('vk_id')
    password = request.args.get('password')
    name = request.args.get('name')
    if request.method == 'GET':
        return get_links(user_id)
    elif request.method == 'POST':
        return add_user(vk_id, name, password)
    elif request.method == 'PATCH':
        return update_link(full_link, short_link, access_type)
    elif request.method == 'DELETE':
        return delete_link(short_link)
    else:
        return 'None'

@app.route('/<short_link>')
def index(short_link):
    f_link = full_link(short_link)
    if f_link:
        return redirect(f_link[0], code=302)
    else:
        return get_links_http(4)

if __name__ == '__main__':
   app.run (host = '127.0.0.1', port = 8080)

