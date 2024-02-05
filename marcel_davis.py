#!/usr/bin/env python3
import requests
import bs4
import re
import os
from bs4 import BeautifulSoup
from tgbot_config import API_KEY
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
# from systemd.journal import JournalHandler

TIMEOUT = 5
HSMA_WEEK_FILENAME = "hsma_week_menu.txt"
HSMA_FILENAME = "hsma_menu.txt"
UNIMA_WEEK_FILENAME = "unima_week_menu.txt"
TESTFILE = "test.txt"

bot = AsyncTeleBot(API_KEY)


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

    with requests.get(URL, verify=False, timeout=5) as url:
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
    with requests.get("https://www.stw-ma.de/Essen+_+Trinken/Speisepl%C3%A4ne/Hochschule+Mannheim-view-week.html", verify=False, timeout=5) as url:
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
    with requests.get("https://www.stw-ma.de/men%C3%BCplan_schlossmensa-view-week.html", verify=False, timeout=5) as url:
        soup = BeautifulSoup(url.content)
    match = soup.find_all(class_='active1')
    data = parse_week(match)

    menu = "".join(data)
  #  menu = replace_paranthesis(menu)

    if not match:
        menu = "Unimensa hat zu 💩"

    with open(UNIMA_WEEK_FILENAME, 'w', encoding='utf-8') as file:
        file.write(menu)


def download_test():
    data = requests.get("http://localhost:5000", verify=False, timeout=5).text
    with open(TESTFILE, 'w', encoding='utf-8') as file:
        file.write(data)


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
    bot.send_message(message.chat.id, welcome_string)


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
async def mensa(message):
    log.info("mensa was called")
    with open(HSMA_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()
    await bot.send_message(message.chat.id, menu, parse_mode='Markdown')


@bot.message_handler(commands=['mensa_week'])
async def mensa_week(message):
    log.info("mensaweek was called")
    with open(HSMA_WEEK_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()
    menu_days = menu.split("*")

    menu_days=menu_days[1:]
    
    menu_days = [menu_days[i] + menu_days[i+1] for i in range(0, len(menu_days)-1, 2)]

    for day in menu_days:
        await bot.send_message(message.chat.id, day, parse_mode="Markdown")
    

@bot.message_handler(commands=['unimensa_week'])
async def uni_mensa(message):
    log.info("unimensa was called")
    with open(UNIMA_WEEK_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()

    menu_days = menu.split("*")

    menu_days=menu_days[1:]
    
    menu_days = [menu_days[i] + menu_days[i+1] for i in range(0, len(menu_days)-1, 2)]

    for day in menu_days:
        await bot.send_message(message.chat.id, day, parse_mode="Markdown")



async def bot_poll():
    # pass
    while True:
        log.info("polling msgs")
        # await bot.polling()
        await asyncio.sleep(1.0)

async def run_scheduler():
    log.info("running scheduler")
    sched = AsyncIOScheduler()
    sched.configure(timezone='Europe/Rome')
    sched.add_job(
        cache_all_menus,
        'cron',
        year="*",
        month="*",
        day="*",
        hour="*",
        minute="*",
        second="*/3"
        )
    sched.start()

    while True:
        await asyncio.sleep(1)


async def set_options():
    await bot.set_my_commands([
    types.BotCommand("/help", "Hilfe"),
    types.BotCommand("/mensa", "mensa heute"),
    types.BotCommand("/mensa_week", "mensamenu woche"),
    types.BotCommand("/bp", "Blockzeit"),
    types.BotCommand("/unimensa_week", "unimensamenu der woche"),
]
)


async def main():
    log.info("running background tasks")
    await asyncio.gather(set_options(), bot_poll(), run_scheduler())


if __name__ == '__main__':
    log = logging.getLogger("marcel_davis")
    log.addHandler(JournalHandler())
    log.setLevel(logging.INFO)
    # logging.basicConfig(level=logging.INFO)
    log.info("starting bot")
    cache_all_menus()
    log.info("running mainloop")
    asyncio.run(main())
    