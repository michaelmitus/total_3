import requests
import sqlite3 as lite
import json
from newsapi import NewsApiClient
from flask import Flask, request, Response, render_template, jsonify

app = Flask(__name__)

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

def short_link_exists(short_link):
    sql_request = 'SELECT ID FROM Links WHERE Short_link LIKE "%s"' % short_link
    resp = sql_command_lite(sql_request)
    return resp

def user_exists(name):
    sql_request = 'SELECT ID FROM Users WHERE Name LIKE "%s"' % name
    resp = sql_command_lite(sql_request)
    return resp[0]

def user_ID(vk_ID):
    sql_request = 'SELECT ID FROM Users WHERE vk_ID = "%s"' % vk_ID
    resp = sql_command_lite(sql_request)
    return resp[0]

def add_link(vk_id, full_link, short_link, access_type):
#    Добавление ссылки
    if not short_link_exists(short_link):
        sql_request = "INSERT INTO Links (Full_Link, Short_Link, UserID, Access) VALUES ('%s','%s', '%s','%s')" % (full_link, short_link, user_ID(vk_id), access_type)
        sql_command(sql_request)
        return 'Ok'+sql_request
    else:
        return 'Ошибка. Такая короткая ссылка уже зарегистрирована'

def get_links(vk_ID):
    print(user_ID(vk_ID))
    sql_request = "SELECT Full_Link, Short_Link, Access FROM Links WHERE UserID=%s" % (str(user_ID(vk_ID)))
    print(sql_request)
    print(sql_command_get(sql_request))
    print(sql_command(sql_request))
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

@app.route('/links/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def links(*args, **kwargs):
    user_id = request.args.get('user_id')
    link_id = request.args.get('link_id')
    full_link = request.args.get('full_link')
    short_link = request.args.get('short_link')
    access_type = request.args.get('access_type')
    if request.method == 'GET':
        return get_links(user_id)
    elif request.method == 'POST':
        return add_link(user_id, full_link, short_link, access_type)
    elif request.method == 'PATCH':
        return update_link(full_link, short_link, access_type)
    elif request.method == 'DELETE':
        return delete_link(short_link)
    else:
        return 'None'

@app.route('/users/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
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

if __name__ == '__main__':
   app.run (host = '127.0.0.1', port = 8080)

