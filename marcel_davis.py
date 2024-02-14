#!/usr/bin/env python3
import logging
import requests
import bs4
import re
from bs4 import BeautifulSoup
from tgbot_config import API_KEY
from telebot import TeleBot, types
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from systemd.journal import JournalHandler

TIMEOUT = 5
HSMA_WEEK_FILENAME = "hsma_week_menu.txt"
HSMA_FILENAME = "hsma_menu.txt"
UNIMA_WEEK_FILENAME = "unima_week_menu.txt"
ABO_FILENAME = "abos.txt"

bot = TeleBot(API_KEY)


def parse_week(match):
    data = [ele.text for ele in match]
    data = [ele.replace("\t", '').replace("\n\n\n", "\n\n") for ele in data]
    data = [ele.replace("Montag", "*Montag*") for ele in data]
    data = [ele.replace("Dienstag", "*Dienstag*") for ele in data]
    data = [ele.replace("Mittwoch", "*Mittwoch*") for ele in data]
    data = [ele.replace("Donnerstag", "*Donnerstag*") for ele in data]
    data = [ele.replace("Freitag", "*Freitag*") for ele in data]
    data = [ele.replace("`", "'") for ele in data]
    return data


def download_hsma():
    URL = "https://www.stw-ma.de/Essen+_+Trinken/Speisepl%C3%A4ne/Hochschule+Mannheim.html"

    with requests.get(URL, timeout=5) as url:
        soup = BeautifulSoup(url.content, features="lxml")
    match = soup.find(class_='speiseplan-table')

    menu = ""
    for row in match:
        if not isinstance(row, bs4.element.NavigableString):
            cells = row.find_all("td")
            del cells[-2]
            for cell in cells:
                # log.info(cell)
                stri = cell.get_text()
                result = re.sub(r'[\t\n]+', '', stri)
                result = re.sub(r'\€Stück|€Portion|€pro100g', '€', result)
                menu += result + "\n"
            menu += "\n"
    if not menu:
        menu = "Hochschulmensa hat zu 💩"

    with open(HSMA_FILENAME, 'w', encoding='utf-8') as file:
        file.write(menu)


def download_hsma_week():
    with requests.get("https://www.stw-ma.de/Essen+_+Trinken/Speisepl%C3%A4ne/Hochschule+Mannheim-view-week.html", timeout=5) as url:
        soup = BeautifulSoup(url.content)
    match = soup.find_all(class_='active1')
    data = parse_week(match)
    menu = "".join(data)
 #   menu = replace_paranthesis(menu)

    if not match:
        menu = "Hochschulmensa hat zu 💩"

    with open(HSMA_WEEK_FILENAME, 'w', encoding='utf-8') as file:
        file.write(menu)


def download_unima_week():
    with requests.get("https://www.stw-ma.de/men%C3%BCplan_schlossmensa-view-week.html", timeout=5) as url:
        soup = BeautifulSoup(url.content)
    match = soup.find_all(class_='active1')
    data = parse_week(match)

    menu = "".join(data)
  #  menu = replace_paranthesis(menu)

    if not match:
        menu = "Unimensa hat zu 💩"

    with open(UNIMA_WEEK_FILENAME, 'w', encoding='utf-8') as file:
        file.write(menu)


def create_abos():
    abos = Path(ABO_FILENAME)
    abos.touch(exist_ok=True)


def cache_all_menus():
    "caches all menus as files"
    log.info("caching menus")
    download_hsma_week()
    download_hsma()
    download_unima_week()
    # download_test()


@bot.message_handler(commands=["start", "help"])
def start(message):
    welcome_string = """commands
/bp für blockplan
/mensa für heutiges mensamenü
/mensa_week für ganze woche
"""
    bot.reply_to(message, welcome_string)


@bot.message_handler(commands=["bp"])
def get_blockplan(message):
    data = [["Block", "Start", "Ende"]]
    data += [["1", "08:00", "09:30"]]
    data += [["2", "09:45", "11:15"]]
    data += [["3", "12:00", "13:30"]]
    data += [["4", "13:40", "15:10"]]
    data += [["5", "15:20", "16:50"]]
    data += [["6", "17:00", "18:30"]]

    reply_string = "Wintersemester\n"

    for row in data:
        for col in row:
            reply_string += f"{col:<12}"
        reply_string += "\n"

    reply_string += "Sommersemester\n"
    data_sose = [["Block", "Start", "Ende"]]
    data_sose += [["1", "08:00", "09:30"]]
    data_sose += [["2", "09:45", "11:15"]]
    data_sose += [["3", "11:30", "13:00"]]
    data_sose += [["4", "13:40", "15:10"]]
    data_sose += [["5", "15:20", "16:50"]]
    data_sose += [["6", "17:00", "18:30"]]

    for row in data_sose:
        for col in row:
            reply_string += f"{col:<12}"
        reply_string += "\n"

    bot.reply_to(message, reply_string)


def replace_paranthesis(stri):
    para_auf = [i for i in range(len(stri)) if stri[i] == "("]
    para_zu = [i for i in range(len(stri)) if stri[i] == ")"]
    para = list(zip(para_auf, para_zu))
    words = [stri[pair[0] - 1:pair[1] + 1] for pair in para]
    for word in words:
        stri = stri.replace(word, " ")
    return stri


@bot.message_handler(commands=['mensa'])
def mensa(message):
    log.info("mensa was called")
    with open(HSMA_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()
    bot.reply_to(message, menu, parse_mode='Markdown')


@bot.message_handler(commands=['mensa_week'])
def mensa_week(message):
    log.info("mensaweek was called")
    with open(HSMA_WEEK_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()
    menu_days = menu.split("*")

    menu_days = menu_days[1:]

    menu_days = [menu_days[i] + menu_days[i + 1]
                 for i in range(0, len(menu_days) - 1, 2)]

    for day in menu_days:
        bot.reply_to(message, day, parse_mode="Markdown")


@bot.message_handler(commands=['unimensa_week'])
def uni_mensa(message):
    log.info("unimensa was called")
    with open(UNIMA_WEEK_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()

    menu_days = menu.split("*")

    menu_days = menu_days[1:]

    menu_days = [menu_days[i] + menu_days[i + 1]
                 for i in range(0, len(menu_days) - 1, 2)]

    for day in menu_days:
        bot.reply_to(message, day, parse_mode="Markdown")


@bot.message_handler(commands=['abo'])
def abo(message):
    chatid = str(message.chat.id)
    with open(ABO_FILENAME, 'r', encoding="utf-8") as abofile:
        all_abos = abofile.readlines()
    if chatid not in all_abos:
        all_abos.append(chatid)
        bot.reply_to(
            message,
            "du wirst jetzt täglich Infos zur mensa erhalten")
        log.info(f"added chat with chatid {chatid}")
    else:
        all_abos.remove(chatid)
        bot.reply_to(
            message,
            "du wirst jetzt täglich **keine** Infos zur mensa erhalten",
            parse_mode="markdown")
        log.info(f"removed chat with chatid {chatid}")

    with open(ABO_FILENAME, 'w', encoding="utf-8") as abofile:
        abofile.writelines(all_abos)


def send_all_abos():
    with open(ABO_FILENAME, 'r', encoding="utf-8") as abofile:
        all_abos = abofile.readlines()
    log.info(f"sending abos. currently there are {len(all_abos)} abos")
    with open(HSMA_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()
        if len(all_abos) > 0:
            for chat_id in all_abos:
                bot.send_message(chat_id, menu)


def bot_poll():
    # pass
    while True:
        log.info("polling msgs")
        bot.infinity_polling()


def run_scheduler():
    log.info("running scheduler")
    sched = BackgroundScheduler()
    sched.configure(timezone='Europe/Rome')
    sched.add_job(
        cache_all_menus,
        'cron',
        year="*",
        month="*",
        day="*",
        hour=6,
        minute=0,
        second=0
    )
    sched.add_job(
        send_all_abos,
        'cron',
        year="*",
        month="*",
        day="*",
        hour=7,
        minute=0,
        second=0
    )
    sched.start()


def set_options():
    bot.set_my_commands([
        types.BotCommand("/help", "Hilfe"),
        types.BotCommand("/mensa", "mensa heute"),
        types.BotCommand("/mensa_week", "mensamenu woche"),
        types.BotCommand("/bp", "Blockzeit"),
        types.BotCommand("/unimensa_week", "unimensamenu der woche"),
        types.BotCommand("/abo", "toggelt abbos"),
    ]
    )


def main():
    log.info("running background tasks")
    set_options()
    run_scheduler()
    bot_poll()


if __name__ == '__main__':
    log = logging.getLogger("marcel_davis")
    log.addHandler(JournalHandler())
    log.setLevel(logging.INFO)
    # logging.basicConfig(level=logging.INFO)
    log.info("starting bot")
    cache_all_menus()
    create_abos()
    log.info("running mainloop")
    main()
