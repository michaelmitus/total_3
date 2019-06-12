import requests
import vk_api
import bs4
import json
from newsapi import NewsApiClient
from random import randint, choice
import string
from vk_api.longpoll import VkLongPoll, VkEventType

vk_token = '9f6ef21d1fa6d22f2cbdff6eaf02dd8a52f05e3e141f0293b6f934006a26ae3d8b4780807cd39efbc07c8'
vk_session = vk_api.VkApi(token=vk_token)

longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

def write_msg(user_id, message):
    vk.messages.send(user_id=user_id,
                     message=message,
                     random_id=randint(1254353245, 2345378568347568347563453245345345))

def clean_all_tag_from_str(string_line):
    """
    Очистка строки stringLine от тэгов и их содержимых
    :param string_line: Очищаемая строка
    :return: очищенная строка
    """
    result = ""
    not_skip = True
    for i in list(string_line):
        if not_skip:
            if i == "<":
                not_skip = False
            else:
                result += i
        else:
            if i == ">":
                not_skip = True

    return result

def get_user_name_from_vk_id(user_id):
    request = requests.get("https://vk.com/id" + str(user_id))
    bs = bs4.BeautifulSoup(request.text, "html.parser")
    user_name = clean_all_tag_from_str(bs.findAll("title")[0])

    return user_name.split()[0]

def vk_print(user_id, title, menu_items):
    msg_text = title + '\n'
    for items in range(len(menu_items)):
        msg_text = msg_text + (str(items + 1) + '. ' + str(menu_items[items]) + '\n')
    write_msg(user_id=user_id,
              message=msg_text)

def vk_menu(user_id, title, menu_items):
    vk_print(user_id, title, menu_items)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.from_user or event.from_chat:
                return event.text

def add_user(user_id):
    response = requests.post('http://localhost:8080/users/',
                             params = {'vk_id': user_id, 'name': get_user_name_from_vk_id(user_id)})
    print(response)
    return response.text

def add_link(user_id, full_link, short_link, access):
    response = requests.post('http://localhost:8080/links/',
                             params = {'user_id': user_id, 'full_link': full_link ,'short_link': short_link, 'access_type': access})
    print(response)
    return response.text

def random_string_generator(str_size):
    return ''.join(choice(string.ascii_letters) for x in range(str_size))

def access_decode(access):
    if access == 1:
        return('Публичная')
    elif access == 2:
        return ('Общего доступа')
    else:
        return ('Приватная')

def get_links(user_id):
    response = requests.get('http://localhost:8080/links/',
                             params = {'user_id': user_id})
    todos = json.loads(response.text)
    select = list()
    for items in range(len(todos)):
        select_item = (todos[items])
        select.append(select_item)
    return select

def print_links(user_id):
    msg_text = 'N п/п - Полная ссылка - Сокращенная - Доступ \n'
    all_links = get_links(user_id)
    for items in range(len(all_links)):
        msg_text = msg_text + (str(items + 1) + ' - ' +
                               str(all_links[items][0]) + ' - ' +
                               str(all_links[items][1]) + ' - ' +
                               access_decode(all_links[items][2]) +'\n')
    write_msg(user_id=user_id,
              message=msg_text)

def main_menu(user_id):
    vk_print(user_id, 'Главное меню:', ('Регистрация пользователя', 'Регистрация ссылок', 'Показать все ссылки пользователя'))

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
   #Слушаем longpoll, если пришло сообщение то:
        if event.from_user or event.from_chat: #Если написали
            if event.text == '1':
                write_msg(event.user_id, add_user(event.user_id))
            elif event.text == '7':
                write_msg(event.user_id, random_string_generator(10))
            elif event.text == '3':
                print_links(event.user_id)
            elif event.text == '2':
                full_link = vk_menu(event.user_id, 'Регистрация ссылок:', ('Введите полную ссылку', 'Выход'))
                short_link = random_string_generator(10)
                access = int(vk_menu(event.user_id, 'Выберите уровень доступа',
                                 ('Публичная', 'Общего доступа', 'Приватная')))
                add_link(event.user_id, full_link, short_link, access)
                vk_print(event.user_id, 'Cоздана ссылка:',
                         ('Полая ссыслка: '+full_link, 'Короткая ссылка: '+short_link, 'Уровень доступа: '+access_decode(access)))
            else:
                main_menu(event.user_id)
