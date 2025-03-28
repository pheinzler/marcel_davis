#!/usr/bin/env python3
import logging
import requests
import os
import yaml
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.error import TelegramError
from pathlib import Path
import re
import json
from menue import Menue
import shutil
import os
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger("marcel-davis")

#open yaml config and get config data
with open('./../conf/config.yaml', 'r') as file:
    conf = yaml.safe_load(file)

TIMEOUT = conf["timeout"]

THM_WEEK_CACHE_KEY = conf["filename"]["thm_week_cache_key"]
UNIMA_WEEK_CACHE_KEY = conf["filename"]["uma_week_cache_key"]
ABO_FILENAME = conf["filename"]["abo"]
CACHE_FILENAME = conf["filename"]["cache"]
CACHE_TEMPLATE = conf["filename"]["cache_template"]

CANTEEN_ID_THM = conf["canteens"]["thm"]
CANTEEN_ID_UMA = conf["canteens"]["uma"]

STATISTICS = conf["statistics"]
# get token and initialize bot
load_dotenv()
API_KEY = os.getenv("API_KEY")

#this dict is used to download the week menues. For workdays it calculates back to the start of the current week. for weekend days it forwards to the next weeks menue
days_to_sunday = {"Monday" : -1, "Tuesday" : -2, "Wednesday" : -3, "Thursday" : -4, "Friday" : -5, "Saturday" : 1, "Sunday" : 0}
weekday_dict = {"Monday" : "Montag", "Tuesday" : "Dienstag", "Wednesday" : "Mittwoch", "Thursday" : "Donnerstag", "Friday" : "Freitag", "Saturday" : "Samstag", "Sunday" : "Sonntag"}

def set_up_cache():
    # Check if cache.json exists
    if not os.path.exists(CACHE_FILENAME):
        # If it does not exist, copy template.json to cache.json
        shutil.copy(CACHE_TEMPLATE, CACHE_FILENAME)
        log.info(f"{CACHE_FILENAME} has been created by copying {CACHE_TEMPLATE}.")
    else:
        log.info(f"{CACHE_FILENAME} already exists, skipping creation")


def get_week_menue(cache_week:dict)->str:
    menue_cache = f"Menue von Montag {cache_week['von']} bis Freitag {cache_week['bis']}\n\n"
    try:
        for day in weekday_dict.values():
            menue_cache += f"{day} - {cache_week[day]['date']}\n"
            for menue in cache_week[day]['day']:
                menue_cache += f"- {menue}\n\t\t{cache_week[day]['day'][menue]} - {cache_week[day]['day'][menue]['price']}{cache_week[day]['day'][menue]['price_unit']}\n\n"
            menue_cache += "\n"
    except:
        None
    return menue_cache


def parse_menue(data)->dict:
    """parse the json menue of a single day"""
    menues = {}
    # loop through json data and return dict of tpye {"menue category":"{meal} - {price}"}
    for i in range(len(data)):
        menue = f"{data[i]['name']} - {data[i]['prices']['students']}€"
        menues[data[i]['category']] = menue
    return menues


def download_thm():
    log.info(f"caching todays menue for mensa @thm.")
    with open(CACHE_FILENAME, 'r') as file:
        cache = json.load(file)  # Load the JSON data
    # Get the current date and time
    current_datetime = datetime.now()
    request_date = current_datetime.strftime('%Y-%m-%d')
    # Format the date and time as YYYY-MM-DD HH:MM:SS
    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    url=f"https://openmensa.org/api/v2/canteens/{CANTEEN_ID_THM}/days/{request_date}/meals"
    response = requests.get(url)
    # reset cache menue
    cache["today"]["day"]= {}
    if response.status_code == 200:
        try:
            for ele in response.json():
                menue = Menue(ele)
                cache["today"]["day"][menue.categorie] = menue.get()
                cache["today"]["day"]["price"] = float(menue.price)
                cache["today"]["day"]["price_unit"] = menue.price_unit
        except:
                cache["today"]["day"]["No Menu"] = "Hochschulmensa hat zu 💩"
                cache["today"]["day"]["price"] = 0.0
                cache["today"]["day"]["price_unit"] = "€"
    else:
        log.error(f"request for mensa at date {request_date} failed. status code: {response.status_code}")
        cache["today"]["day"]["No Menu"] = "Hochschulmensa hat zu 💩"
        cache["today"]["day"]["price"] = 0.0
        cache["today"]["day"]["price_unit"] = "€"
    
    cache["today"]["status"] = response.status_code
    cache["today"]["last_update"] = formatted_datetime
    log.info("write to cache")
    with open(CACHE_FILENAME, 'w') as file:
        json.dump(cache, file, indent=4)


def download_week(canteen_id:int, mensa_key:str):
    """cache the menue of this week of the canteen with the given id and write to .txt file"""
    # Find start of this weeks menue date and format as yyyy-mm-dd. On weekends get next weeks menue
    log.info(f"caching this weeks menue for mensa with id {canteen_id}.")
    with open(CACHE_FILENAME, 'r') as file:
        cache = json.load(file)
    date = datetime.now()
    curr_date_time = date.strftime('%Y-%m-%d %H:%M:%S')
    datestr = date.strftime("%A")
    offset = days_to_sunday[datestr]
    date = datetime.now() + timedelta(offset) # sunday of weeks menue
    # loop over week
    for i in range(1,6):
        log.info(f"caching menue {i}/5.")
        curr_date = date + timedelta(i)
        curr_date_request_fromat = curr_date.strftime('%Y-%m-%d')
        # request menue from open mensa api
        url=f"https://openmensa.org/api/v2/canteens/{canteen_id}/days/{curr_date_request_fromat}/meals"
        response = requests.get(url)
        time.sleep(TIMEOUT)
        weekday = weekday_dict[curr_date.strftime("%A")]
        cache[mensa_key][weekday]["day"]= {}
        if response.status_code == 200:
            try:
                for ele in response.json():
                    menue = Menue(ele)
                    cache[mensa_key][weekday]["day"][menue.categorie] = menue.get()
                    cache[mensa_key][weekday]["day"]["price"] = float(menue.price)
                    cache[mensa_key][weekday]["day"]["price_unit"] = menue.price_unit
                    cache[mensa_key][weekday]["status"] = response.status_code
                    cache[mensa_key][weekday]["date"] = curr_date_request_fromat
            except:
                    cache[mensa_key][weekday]["day"]["No Menu"] = "Hochschulmensa hat zu 💩"
                    cache[mensa_key][weekday]["day"]["price"] = 0.0
                    cache[mensa_key][weekday]["day"]["price_unit"] = "€"
                    cache[mensa_key][weekday]["status"] = response.status_code
                    cache[mensa_key][weekday]["date"] = curr_date_request_fromat
        else:
            log.error(f"request for mensa at date {curr_date_request_fromat} failed. status code: {response.status_code}")
            cache[mensa_key][weekday]["day"]["No Menu"] = "Hochschulmensa hat zu 💩"
            cache[mensa_key][weekday]["day"]["price"] = 0.0
            cache[mensa_key][weekday]["day"]["price_unit"] = "€"
            cache[mensa_key][weekday]["status"] = response.status_code
            cache[mensa_key][weekday]["date"] = curr_date_request_fromat
        cache[mensa_key][weekday]["last_update"] = curr_date_time
        cache[mensa_key]["von"] = (date+timedelta(1)).strftime("%d.%m.%Y")
        cache[mensa_key]["bis"] = (date+timedelta(5)).strftime("%d.%m.%Y")
        with open(CACHE_FILENAME, 'w') as file:
            json.dump(cache, file, indent=4)


def cache_all_menus():
    "caches all menus in data/cache.json"
    download_thm()
    download_week(CANTEEN_ID_THM, THM_WEEK_CACHE_KEY)
    download_week(CANTEEN_ID_UMA, UNIMA_WEEK_CACHE_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("start was called")
    return_message = conf["messages"]["start"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=return_message)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("help was called")
    return_message = conf["messages"]["help"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=return_message)


async def mensa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """return todays mensa menu"""
    log.info("Mensa was called")
    with open(CACHE_FILENAME, 'r') as file:
        cache = json.load(file)
    menues = cache["today"]["day"]
    chache_datestr = datetime.now().strftime("%A")
    cache_date = datetime.now().strftime('%d.%m.%Y')
    menue_cache = f"{weekday_dict[chache_datestr]} {cache_date}\n\n"
    for menue in menues:
        menue_cache += f"{menue}\n{menues[menue]} - {menues[menue]["price"]}{menues[menue]["price_unit"]}\n\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("/tomorrow was called")
    with open(CACHE_FILENAME, 'r') as file:
        cache = json.load(file)
    date = datetime.now() + timedelta(1)
    date_format = date.strftime('%Y-%m-%d')
    weekday = weekday_dict[date.strftime("%A")]
    if weekday == "Samstag" or weekday == "Sonntag":
        log.warning(f"Requested Menue for tomorrow was a weekend - {weekday} :)")
        message = "Hochschulmensa hat zu 💩"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return
    menues = cache[THM_WEEK_CACHE_KEY][weekday]["day"]
    menue_cache = f"{weekday} {date_format}\n\n"
    for menue in menues:
        menue_cache += f"{menue}\n{menues[menue]}\n\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


async def thm_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """return this weeks thm mensa menu"""
    log.info("thm_week was called")
    # Open the file and read its contents
    with open(CACHE_FILENAME, 'r') as file:
        cache = json.load(file)
    menue_cache:str = get_week_menue(cache[THM_WEEK_CACHE_KEY])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


async def uni_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """return this weeks uni mensa menu"""
    log.info("uni_week was called")
    # Open the file and read its contents
    # with open(CACHE_FILENAME, 'r') as file:
    #     cache = json.load(file)
    # menue_cache = get_week_menue(cache[UNIMA_WEEK_CACHE_KEY])
    menue_cache = "work in progress. Upadte coming - soon... maybe :)"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


async def abo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("/abo was called")
    requesting_id=update.effective_chat.id
    with open(ABO_FILENAME, 'r') as file:
        chat_ids:list = json.load(file)
    message = ""
    if requesting_id in chat_ids:
        log.info(f"{requesting_id} already in abos, removing file")
        chat_ids.remove((requesting_id))
        message = conf["messages"]["deabo"]
    else:
        log.info(f"{requesting_id} not in abo ids. Adding id")
        chat_ids.append(requesting_id)
        message = conf["messages"]["abo"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    log.info("storing updated abo file.")
    with open(ABO_FILENAME, 'w') as file:
        json.dump(chat_ids, file)


async def date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_date = update.message.text[6:] if update.message.text != "/date" else "No date sent"
    log.info(f"date was called. - requested for: {request_date}")
    # Define the regex pattern for YYYY-MM-DD
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    # Check if the date_string matches the pattern
    if not re.match(pattern, request_date):
        log.warning(f"wrong date format")
        response_message =conf["messages"]["wrong_date"]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response_message)
        return
    # request menue from open mensa api
    url=f"https://openmensa.org/api/v2/canteens/{CANTEEN_ID_THM}/days/{request_date}/meals"
    response = requests.get(url)

    menue_cache = ""
    read_menue:bool = True
    if response.status_code != 200:
        menue_cache = "Nichts gefunden"
        log.error(f"request to OpenMensa failed. status code: {response.status_code} - request message: {update.message.text}")
        read_menue = False
    try:
        data = response.json()
        if data is None:
            menue_cache = "Hochschulmensa hat zu 💩"
            read_menue = False
    except:
        log.error(f"error reading response json, returning default message")
        menue_cache = "Hochschulmensa hat zu 💩"
        read_menue = False
    # parse mensa menue only if valid data was sent
    if read_menue:
        today_menues = parse_menue(data)
        menue_cache = f"{request_date}\n\n"
        for menue in today_menues:
            menue_cache += f"{menue}\n{today_menues[menue]}\n\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


def send_all_abos():
    log.info("sending menu to abo chats")
    bot = Bot(token=API_KEY)
    with open(ABO_FILENAME, 'r') as file:
        chat_ids:list = json.load(file)
    log.info(f"sending abos. currently there are {len(chat_ids)} abos")
    with open(CACHE_FILENAME, 'r') as file:
        cache = json.load(file)
    menues = cache["today"]["day"]
    chache_datestr = datetime.now().strftime("%A")
    cache_date = datetime.now().strftime('%d.%m.%Y')
    menue_cache = f"{weekday_dict[chache_datestr]} {cache_date}\n\n"
    for menue in menues:
        menue_cache += f"{menue}\n{menues[menue]}\n\n"
    for cid in chat_ids:
        try:
            bot.send_message(chat_id=cid, text=menue_cache)
        except TelegramError as e:
                print(f"Failed to send message to chat ID {cid}: {e}")


def run_scheduler():
    log.info("running scheduler")
    sched = BackgroundScheduler()
    sched.configure(timezone='Europe/Rome')
    sched.add_job(
        cache_all_menus,
        'cron',
        year="*",
        month="*",
        day_of_week="0-4",
        hour="*",
        minute="*/30",
        second=0
    )
    sched.add_job(
        send_all_abos,
        'cron',
        year="*",
        month="*",
        day_of_week="0-4",
        hour=9,
        minute=0,
        second=0
    )
    sched.start()


def main():
    log.info("Starting bot...")
    application = ApplicationBuilder().token(API_KEY).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    tomorrow_handler = CommandHandler('tomorrow', tomorrow)
    application.add_handler(tomorrow_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    mensa_handler = CommandHandler('mensa', mensa)
    application.add_handler(mensa_handler)

    abo_handler = CommandHandler('abo', abo)
    application.add_handler(abo_handler)

    thm_week_handler = CommandHandler('thm_week', thm_week)
    application.add_handler(thm_week_handler)

    # uni_week_handler = CommandHandler('uni_week', uni_week)
    # application.add_handler(uni_week_handler)

    date_handler = CommandHandler('date', date)
    application.add_handler(date_handler)

    log.info("Setup cache")
    set_up_cache()
    log.info("Caching menues")
    cache_all_menus()
    log.info("Set up scheduler")
    run_scheduler()
    log.info("Start polling...")
    application.run_polling(poll_interval=2) # poll every 2 sec. default is .5 secs

if __name__ == '__main__':
    main()
