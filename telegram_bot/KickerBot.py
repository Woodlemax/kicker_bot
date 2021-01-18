#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Телеграм кикер бот.
Поведение:
пинг, ping - проверка состояния датчика кикербота
?, чекни, го? - проверка занятости кикера
го, go - поддержка игроков
"""

import logging
import re
import requests
import random
import configparser
import os
import time

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# constant
url_influxdb = 'http://wks-alep:8086'
url_query = url_influxdb + '/query?q='
loginpass = '&db=kicker&u=kicker&p=4kicker_send'
query_ping = 'SELECT COUNT(*) FROM "ping" WHERE time > now() - 20s AND value > 0'
query_kick = 'SELECT COUNT(*) FROM "kick" WHERE time > now() - 5m AND value > 0'
path_conf = "conf.ini"
wait_player = 300

# Global vars
chat_activity = {}


def create_config(chat_id):
    """
    Create a config file
    """
    config = configparser.ConfigParser()
    config.add_section(f"Settings chat: {chat_id}")
    config.set(f"Settings chat: {chat_id}", "replay_mode", "normal")

    with open(path_conf, "w") as config_file:
        config.write(config_file)


def get_config():
    """
    Returns the config object
    """
    if not os.path.exists(path_conf):
        create_config(path_conf)

    config = configparser.ConfigParser()
    config.read(path_conf)
    return config


def get_setting(chat_id, setting):
    """
    Print out a setting
    """
    config = get_config()
    value = config.get(f"Settings chat: {chat_id}", setting, fallback=None)

    return value


def update_setting(chat_id, setting, value):
    """
    Update a setting
    """
    config = get_config()
    if not config.has_section(f"Settings chat: {chat_id}"):
        config.add_section(f"Settings chat: {chat_id}")
    config.set(f"Settings chat: {chat_id}", setting, value)
    with open(path_conf, "w") as config_file:
        config.write(config_file)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Send me "?"')


def hardmode(update, context):
    """Переключение бота в хард режим"""
    update.message.reply_text('Хард режим включен!')
    update_setting(update.effective_chat.id, 'replay_mode', 'hard')


def normalmode(update, context):
    """Переключение бота в стандартный режим"""
    update.message.reply_text('Обычный режим включен!')
    update_setting(update.effective_chat.id, 'replay_mode', 'normal')


def get_ok_busy_kicker(chat_id):
    """Получение сообщения Кикер свободен"""

    if get_setting(chat_id, 'replay_mode') == 'hard':
        ok_msg = {
            1: 'Вали, свободно!',
            2: 'Го го го, пока не заняли!',
            3: 'Чисто - уисто.',
            4: 'Никого нет там, вали уже...',
            5: 'Кикер чист, в отличии от тебя.',
            6: 'Как же вы задолбали... Свободно',
            7: 'Так то чисто, но может поработаем чутка?!',
            8: 'Сам иди проверяй, мне надоело'
        }
        m = random.randint(1, len(ok_msg))
        return ok_msg.get(m)
    else:
        return 'Свободно.'


def get_ok_ping_kicker(chat_id):
    """Получение сообщения Датчик в сети"""

    if get_setting(chat_id, 'replay_mode') == 'hard':
        ok_msg = {
            1: 'Я тут, все ровно.',
            2: 'Жив, жив, отвали уже!',
            3: 'Все еще на месте.',
            4: 'Че надо?!',
            5: 'Себе пингани!',
            6: 'Как же вы задолбали...',
            7: 'Спустись ногами и проверь, жирная скотина!',
            8: 'Понг - уенг'
        }
        m = random.randint(1, len(ok_msg))
        return ok_msg.get(m)
    else:
        return 'Понг.'


def get_msg_count_kick(chat_id, count):
    """Получение сообщения Количество ударов в кикере"""
    if get_setting(chat_id, 'replay_mode') == 'hard':
        if count % 100 in [11, 12, 13, 14] or count % 10 in [0, 5, 6, 7, 8, 9]:
            return f'Последние 5 минут кто-то пошатывал кикер: {count} шакальных ударов'
        if count % 10 == 1:
            return f'Последние 5 минут кто-то пошатывал кикер: {count} шакальных удар'
        return f'Последние 5 минут кто-то пошатывал кикер: {count} шакальных удара'
    else:
        if count % 100 in [11, 12, 13, 14] or count % 10 in [0, 5, 6, 7, 8, 9]:
            return f'Последние 5 минут активность кикера: {count} ударов'
        if count % 10 == 1:
            return f'Последние 5 минут активность кикера: {count} удар'
        return f'Последние 5 минут активность кикера: {count} удара'


def get_msg_timeout_kicker(chat_id):
    """Получение сообщения Слишком много запросов"""

    if get_setting(chat_id, 'replay_mode') == 'hard':
        ok_msg = {
            1: 'Скорострел.',
            2: 'Воу! Воу! Полегче, амиго!',
            3: 'Себе подергай.',
            4: 'Че надо?!',
            5: 'Иди нафиг',
            6: 'Выдохни уже!',
            7: 'Врача, скорее! Тут приступ!',
            8: 'Эпилептик'
        }
        m = random.randint(1, len(ok_msg))
        return ok_msg.get(m)
    else:
        return 'Ожидайте.'


def roll(update, context):
    """Проверка занятости кикера"""

    # Задержка при активном опросе
    count_kick = get_setting(update.effective_chat.id, f'user_{update.effective_user.id}_kick')
    if count_kick is not None:
        count_kick = int(count_kick) + 1
        update_setting(update.effective_chat.id, f'user_{update.effective_user.id}_kick', str(count_kick))
    else:
        count_kick = 1
        update_setting(update.effective_chat.id, f'user_{update.effective_user.id}_kick', '1')

    if count_kick == 1:
        update_setting(update.effective_chat.id, f'user_{update.effective_user.id}_time', str(time.time()))
    else:
        if count_kick > 5:
            user_time = get_setting(update.effective_chat.id, f'user_{update.effective_user.id}_time')
            if user_time is not None:
                user_time = float(user_time)
            if user_time + 60 > time.time():
                update.message.reply_text(get_msg_timeout_kicker(update.effective_chat.id))
                return
            else:
                update_setting(update.effective_chat.id, f'user_{update.effective_user.id}_time', str(time.time()))
                update_setting(update.effective_chat.id, f'user_{update.effective_user.id}_kick', '1')

    status, count = check_status(query_ping)

    # Установка начала отсчета сбора команды
    dict_chat = chat_activity.setdefault(f'{update.effective_chat.id}', {'count_play': 0})
    start_chat_play = dict_chat.setdefault('start_time', 0)

    if start_chat_play != 0:
        if start_chat_play + wait_player < time.time():
            dict_chat.clear()

    dict_chat = chat_activity.setdefault(f'{update.effective_chat.id}', {'count_play': 0})
    count_chat_play = dict_chat.setdefault('count_play', 0)

    if count_chat_play == 0:
        dict_chat.update({'start_time': time.time()})
        dict_chat.update({'count_play': 1})
        dict_chat.update({'players': {f'{update.effective_user.id}': f'{update.effective_user.first_name} {update.effective_user.last_name}'}})

    # status = 200

    if status != 200:
        update.message.reply_text(f'Не пингуется. Code: {status}')
    else:
        status, count = check_status(query_kick)
        if status != 200 and status != 404:
            update.message.reply_text(f'Ошибка получения статуса занятости. Code: {status}')
        else:
            if count > 0:
                update.message.reply_text(get_msg_count_kick(update.effective_chat.id, count))
            else:
                update.message.reply_text(get_ok_busy_kicker(update.effective_chat.id))


def check_status(query):
    """Получение статуса кикербота из influxdb, занятость/статус датчика"""
    url = f'{url_query}{query}{loginpass}'
    r = requests.get(url)
    if r.status_code != 200:
        return r.status_code, 0
    else:
        r.encoding = 'utf-8'
        result = re.search(r'(values.*,)(\d+)', r.text)
        if result is not None:
            result_count = int(result.group(2))
            if result_count > 0:
                return 200, result_count
        else:
            return 404, 0


def ping(update, context):
    """Получение состояния датчика кикер бота"""
    status, count = check_status(query_ping)
    if status != 200:
        update.message.reply_text(f'Ошибка получения статуса. Code: {status}')
    else:
        update.message.reply_text(get_ok_ping_kicker(update.effective_chat.id))


def minus(update, context):
    dict_chat = chat_activity.setdefault(f'{update.effective_chat.id}', {'count_play': 0})
    start_chat_play = dict_chat.setdefault('start_time', 0)
    if start_chat_play == 0:
        if get_setting(update.effective_chat.id, 'replay_mode') == 'hard':
            update.message.reply_text(f'Че минус?! Все равно команды нет')
        return
    else:
        if start_chat_play + wait_player < time.time():
            dict_chat.clear()
            if get_setting(update.effective_chat.id, 'replay_mode') == 'hard':
                update.message.reply_text(f'Че минус?! Все равно команды нет')
            return
        else:
            count_chat_play = dict_chat.setdefault('count_play', 0)
            if count_chat_play >= 4:
                if get_setting(update.effective_chat.id, 'replay_mode') == 'hard':
                    update.message.reply_text(f'Профукал момент')
                else:
                    update.message.reply_text(f'Опоздал')
                return
            else:
                players = dict_chat.setdefault(f'players', {f'{update.effective_user.id}': None})
                user_play = players.setdefault(f'{update.effective_user.id}', None)
                if user_play is None:
                    players.pop(f'{update.effective_user.id}', None)
                    if get_setting(update.effective_chat.id, 'replay_mode') == 'hard':
                        update.message.reply_text(f'Пофиг, ты все равно не собирался')
                    return
                else:
                    players.pop(f'{update.effective_user.id}', None)
                    count_chat_play -= 1
                    dict_chat.update({'count_play': count_chat_play})
                    update.message.reply_text(f'Ссыкло!')
                if count_chat_play == 0:
                    update.message.reply_text('Отмена сбора команды', quote=False)
                    dict_chat.clear()
                else:
                    string = 'Состав команды:'
                    i = 0
                    for value in players.values():
                        string = f'{string}\n{value}'
                        i += 1
                    if i < 4:
                        string = f'{string}\nЕще нужно {4 - i}'
                    update.message.reply_text(string, quote=False)


def plus(update, context):

    # Установка начала отсчета сбора команды
    dict_chat = chat_activity.setdefault(f'{update.effective_chat.id}', {'count_play': 0})
    start_chat_play = dict_chat.setdefault('start_time', 0)
    if start_chat_play == 0:
        return
    else:
        if start_chat_play + wait_player < time.time():
            dict_chat.clear()
            return
        dict_chat.update({'start_time': time.time()})
        count_chat_play = dict_chat.setdefault('count_play', 0)
        if count_chat_play >= 4:
            if get_setting(update.effective_chat.id, 'replay_mode') == 'hard':
                update.message.reply_text(f'Профукал момент')
            else:
                update.message.reply_text(f'Опоздал')
            return
        else:
            players = dict_chat.setdefault(f'players', {f'{update.effective_user.id}': None})
            user_play = players.setdefault(f'{update.effective_user.id}', None)
            if user_play is not None:
                return
            else:
                players.update({f'{update.effective_user.id}': f'{update.effective_user.first_name} {update.effective_user.last_name}'})
                count_chat_play += 1
                dict_chat.update({'count_play': count_chat_play})
            if count_chat_play == 4:
                string = 'Команда набрана:'
                for value in players.values():
                    string = f'{string}\n{value}'
                update.message.reply_text(string, quote=False)
                dict_chat.clear()
            else:
                string = 'Состав команды:'
                i = 0
                for value in players.values():
                    string = f'{string}\n{value}'
                    i += 1
                if i < 4:
                    string = f'{string}\nЕще нужно {4-i}'
                update.message.reply_text(string, quote=False)


def go(update, context):
    """Go the user message."""
    if random.randint(1, 100) >= 90:
        update.message.reply_text('Go Go Go!!!')


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    token = '987813746:AAGAT6yN0MLMTkMyYLWt8mHy7qI6mgHkftI'
    request_kwargs = {
        'proxy_url': 'socks5://195.201.24.119:993'
    }
    updater = Updater(token, use_context=True, request_kwargs=request_kwargs)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("hardmode", hardmode))
    dp.add_handler(CommandHandler("normalmode", normalmode))

    # Сообщения проверки занятости кикера
    dp.add_handler(MessageHandler(Filters.regex(r'^\?$')
                                  | Filters.regex(r'^\s*\?')
                                  | Filters.regex(r'[чЧ][еЕ][кК][нН][иИ]')
                                  | Filters.regex(r'[аА]\s[тТ][еЕ][пП][еЕ][рР][ьЬ]\?*')
                                  | Filters.regex(r'^[гГgG][оОoO]\s+.*\?')
                                  | Filters.regex(r'^[гГgG][оОoO]\?')
                                  | Filters.regex(r'\s+[гГgG][оОoO]\s*.*\?'), roll))

    # Сообщения поддержки игроков
    dp.add_handler(MessageHandler(Filters.regex(r'^[гГgG][оОoO]\s+')
                                  | Filters.regex(r'^[гГgG][оОoO]$')
                                  | Filters.regex(r'\s+[гГgG][оОoO]$'), go))

    # Сообщения проверки состояния датчика кикер бота
    dp.add_handler(MessageHandler(Filters.regex(r'[pPпП][iIиИ][nNнН][gGгГ]'), ping))

    # Сообщения участия в игре
    dp.add_handler(MessageHandler(Filters.regex(r'^\-$'), minus))
    dp.add_handler(MessageHandler(Filters.regex(r'^\+$'), plus))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
