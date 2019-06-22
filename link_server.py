import requests
import sqlite3 as lite
import json
from newsapi import NewsApiClient
from flask import Flask, request, Response, render_template, jsonify, redirect, make_response
from flask import g, make_response
from flask_httpauth import HTTPBasicAuth
from flask_httpauth import HTTPTokenAuth
from werkzeug.http import HTTP_STATUS_CODES
import base64
from datetime import datetime, timedelta
import os
from dateutil import parser

import jwt

from flask import Flask, render_template, request, redirect, url_for, flash, make_response

app = Flask(__name__)
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
    print(sql_req)
    return resp

def sql_command_get(sql_req):
    con = lite.connect('links.sqlite')
    curID = con.cursor()
    curID.execute(sql_req)
    resp = curID.fetchall()
    con.close()
    return resp

def get_from_user(name, column):
    result = sql_command_lite('SELECT %s FROM Users WHERE Name LIKE "%s"' % (column, name))
    return result

def get_token(username, expires_in=3600):
    now = datetime.utcnow()
    token_tuple = get_from_user(username, 'token')
    if token_tuple:
        token = token_tuple[0]
    token_expiration_tuple = get_from_user(username, 'token_expiration')
    if token_expiration_tuple:
        token_expiration_one = token_expiration_tuple[0]

    if token_expiration_one:
        token_expiration = parser.parse(token_expiration_one)
        if token and token_expiration > now + timedelta(seconds=60):
            return token

    token = jwt.encode({'name': username}, 'midis-python', algorithm='HS256').decode('utf-8')
    token_expiration = now + timedelta(seconds=expires_in)
    sql_request = 'UPDATE Users SET token = "%s", token_expiration = "%s" WHERE Name LIKE "%s"' % (token, token_expiration, username)
    sql_command(sql_request)
    return token

# get_token('Michael')

def revoke_token(username):
    token_expiration = datetime.utcnow() - timedelta(seconds=1)
    sql_request = 'UPDATE Users SET token_expiration = "%s" WHERE Name LIKE "%s"' % (token_expiration, username)
    sql_command(sql_request)
    return 'ok'

# revoke_token('Michael')

def check_token(token):
    sql_request = 'SELECT Name FROM Users WHERE Token LIKE "%s"' % token
    result = sql_command_lite(sql_request)
    if result:
        user = result[0]
    else:
        return None
    if user is None:
        return None
    token_expiration = get_from_user(user, 'token_expiration')[0]
    if token_expiration:
        if parser.parse(token_expiration) < datetime.utcnow():
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
    if current_user:
        print('Аутентификация токена пользователь: ', current_user, current_user is not None)
    return current_user is not None

@token_auth.error_handler
def token_auth_error():
    return error_response(401)

@basic_auth.verify_password
def verify_password(name, password):
    sql_request = 'SELECT Password FROM Users WHERE Name LIKE "%s"' % name
    pwd = sql_command_lite(sql_request)
    if pwd is None:
        return False
    if pwd[0] == password:
        get_token(name)
    return pwd[0] == password

# verify_password('Michael','444')

@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)

@app.route('/tokens/', methods=['GET'])
def gets_token(*args, **kwargs):
    user = request.args.get('user')
    password = request.args.get('password')
    if verify_password(user, password):
        token = get_from_user(user, 'token')
        return jsonify({'token': token})
    return HttpResponse('401 Unauthorized', status=401)

@app.route('/login/', methods=['GET'])
def check_login(*args, **kwargs):
    name = request.args.get('user')
    password = request.args.get('password')
    jsonify(verify_password(name, password))
    return jsonify(verify_password(name, password))

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

def user_ID(name):
    sql_request = 'SELECT ID FROM Users WHERE name = "%s"' % name
    resp = sql_command_lite(sql_request)
    return resp

def add_link(user_id, full_link, short_link, access_type):
#    Добавление ссылки
    if not short_link_exists(short_link):
        sql_request = "INSERT INTO Links (Full_Link, Short_Link, UserID, Access) VALUES ('%s','%s', '%s','%s')" % (full_link, short_link, user_id, access_type)
        sql_command(sql_request)
        return 'Ok'+sql_request
    else:
        return 'Ошибка. Такая короткая ссылка уже зарегистрирована'

def get_links(user_id):
    sql_request = "SELECT Full_Link, Short_Link, Access FROM Links WHERE UserID=%s" % user_id
    return jsonify(sql_command_get(sql_request))

def delete_link(id):
    sql_request = "DELETE FROM Links WHERE ID='%s'" % (str(id))
    sql_command(sql_request)
    return 'Delete '+sql_request

def update_link(link_id, full_link, short_link, access_type):
    sql_request = "UPDATE Links SET Full_link = %s, Short_link = $s, Access = $s), WHERE ID=%s" % (full_link, short_link, access_type, str(link_id))
    sql_command(sql_request)
    return 'Update '+sql_request

def add_user(id_vk, name, password):
    if not user_exists(name):
        sql_request = "INSERT INTO Users (vk_ID, name, Password) VALUES ('%s','%s','%s')" % (str(id_vk), name, password)
        sql_command(sql_request)
        return "Добавлен пользователь :'%s'" % (name)
    else:
        return "Пользователь :'%s' уже зарегистрирован. Выберите другое имя " % (name)

def access_decode(access):
    if access == 1:
        return ('Публичная')
    elif access == 2:
        return ('Общего доступа')
    else:
        return ('Приватная')

def get_links_http(user):
    user_id = user_ID(user)
    if user_id:
        user_id = user_id[0]
    else:
        user_id = 0
    print(user_id)
    if user_id > 0 :
        sql_request = "SELECT Full_Link, Short_Link, Access, id FROM Links WHERE UserID=%s" % user_id
    else:
        sql_request = "SELECT Full_Link, Short_Link, Access, id FROM Links WHERE Access=%s" % 1
    links = sql_command_get(sql_request)
    select = []

    for items in range(len(links)):
        select_item = (links[items])
        select.append({'Full_link':     select_item[0],
                       'Short_link':    select_item[1],
                       'Access_ID':     select_item[2],
                       'Access':        access_decode(select_item[2]),
                       'ID':            select_item[3],
                       })
    return jsonify(select)

@app.route('/links/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@token_auth.login_required
def links(*args, **kwargs):
    full_link = request.args.get('full_link')
    short_link = request.args.get('short_link')
    access_type = request.args.get('access_type')
    link_id = request.args.get('link_id')

    auth3 = request.headers.get('Authorization').replace('Bearer ','')
    jwt_req = jwt.decode(auth3, 'midis-python', algorithms=['HS256'])
    user_name = jwt_req['name']

    user_id = user_ID(user_name)[0]

    if not user_id:
        user_id = 0

    if request.method == 'GET':
        return get_links_http(user_name)
    elif request.method == 'POST':
        print(user_id, full_link, short_link, access_type)
        return add_link(user_id, full_link, short_link, access_type)
    elif request.method == 'PATCH':
        return update_link(full_link, short_link, access_type)
    elif request.method == 'DELETE':
        return delete_link(link_id)
    else:
        return False

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
        return False

def check_link_access(short_link, user):
    sql_request = "SELECT UserID, Access FROM Links WHERE Short_Link='%s'" % (str(short_link))
    r = sql_command_get(sql_request)
    if r:
        l_user = r[0][0]
        l_access = r[0][1]
        if user_ID(user):
            l_user_ID = user_ID(user)[0]
        else:
            l_user_ID = 0
        if l_access == 1:
            return True
        elif l_access == 2:
            if l_user_ID > 0:
                return True
        else:
            return l_user_ID == l_user
    return False

def relink(short_link, user):
    print(short_link)
    print(user)
    print(check_link_access(short_link, user))
    if check_link_access(short_link, user):
        f_link = full_link(short_link)
        if f_link:
            return redirect(f_link[0], code=302)
    else:
        return make_response(jsonify({'error': 'Unauthorized access'}), 401)

@app.route('/<short_link>')
def index(short_link):
    user = request.args.get('user')
    password = request.args.get('password')
    if verify_password(user, password):
            return relink(short_link, user)
    else:
        return relink(short_link, 0)
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

if __name__ == '__main__':
   app.run (host = '127.0.0.1', port = 8080)

