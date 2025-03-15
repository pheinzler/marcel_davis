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
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger("marcel-davis")

#open yaml config and get config data
with open('config.yaml', 'r') as file:
    conf = yaml.safe_load(file)

TIMEOUT = conf["timeout"]

THM_WEEK_FILENAME = conf["filename"]["thm_week"]
THM_FILENAME = conf["filename"]["thm"]
UNIMA_WEEK_FILENAME = conf["filename"]["uma_week"]
ABO_FILENAME = conf["filename"]["abo"]

CANTEEN_ID_THM = conf["canteens"]["thm"]
CANTEEN_ID_UMA = conf["canteens"]["uma"]

# get token and initialize bot
load_dotenv()
API_KEY = os.getenv("API_KEY")

#this dict is used to download the week menues. For workdays it calculates back to the start of the current week. for weekend days it forwards to the next weeks menue
days_to_sunday = {"Monday" : -1, "Tuesday" : -2, "Wednesday" : -3, "Thursday" : -4, "Friday" : -5, "Saturday" : 1, "Sunday" : 0}
weekday_dict = {"Monday" : "Montag", "Tuesday" : "Dienstag", "Wednesday" : "Mittwoch", "Thursday" : "Donnerstag", "Friday" : "Freitag", "Saturday" : "Samstag", "Sunday" : "Sonntag"}

def parse_menue(data)->dict:
    """parse the json menue of a single day"""
    menues = {}
    # loop through json data and return dict of tpye {"menue category":"{meal} - {price}"}
    for i in range(len(data)):
        menue = f"{data[i]['name']} - {data[i]['prices']['students']}€"
        menues[data[i]['category']] = menue
    return menues


def download_thm():
    """cache the mensa menue of today and write to .txt file"""
    log.info("caching mensa menue of today")
    # Get the current date and format as yyyy-mm-dd
    date:datetime = datetime.now()
    date = date.strftime('%Y-%m-%d')

    # request menue from open mensa api
    url=f"https://openmensa.org/api/v2/canteens/{CANTEEN_ID_THM}/days/{date}/meals"
    response = requests.get(url)

    menue_cache = ""
    read_menue:bool = True
    if response.status_code != 200:
        menue_cache = "Nichts gefunden"
        log.error(f"request for [mensa today] failed. status code: {response.status_code}")
        read_menue = False
    try:
        data = response.json()
        if date is None:
            menue_cache = "Hochschulmensa hat zu 💩"
            read_menue = False
    except:
            log.error("Error reading mensa today json response :(")
            menue_cache = "Hochschulmensa hat zu 💩"
            read_menue = False        
    # parse mensa menue only if valid data was sent
    if read_menue:
        today_menues = parse_menue(data)
        chache_datestr = datetime.now().strftime("%A")
        cache_date = datetime.now().strftime('%d.%m.%Y')
        menue_cache = f"{weekday_dict[chache_datestr]} {cache_date}\n\n"
        for menue in today_menues:
            menue_cache += f"{menue}\n{today_menues[menue]}\n\n"
    with open(THM_FILENAME, 'w', encoding='utf-8') as file:
        file.write(menue_cache)


def download_week(canteen_id:int, filename:str):
    """cache the menue of this week of the canteen with the given id and write to .txt file"""
    # Find start of this weeks menue date and format as yyyy-mm-dd. On weekends get next weeks menue
    date = datetime.now()
    datestr = date.strftime("%A")
    offset = days_to_sunday[datestr]
    date = datetime.now() + timedelta(offset) # sunday of weeks menue
    menue_week = {}
    # loop over week
    for i in range(1,6):
        curr_date = date + timedelta(i)
        curr_date_request_fromat = curr_date.strftime('%Y-%m-%d')
        # request menue from open mensa api
        url=f"https://openmensa.org/api/v2/canteens/{canteen_id}/days/{curr_date_request_fromat}/meals"
        response = requests.get(url)
        time.sleep(TIMEOUT)
        if response.status_code != 200:
            menue_week[curr_date.strftime("%A")] = {"ahhhh":"Nichts gefunden"}
            log.error(f"request for {curr_date}  in download_thm_week failed. status code: {response.status_code}")
            continue
        try:
            data = response.json()
            if data is None:
                menue_week[curr_date.strftime("%A")] = {"ahhh":"Hochschulmensa hat zu 💩"}
                continue
        except:
                log.error("Error reading mensa week json response :(")
                menue_week[curr_date.strftime("%A")] = {"ahhh":"Hochschulmensa hat zu 💩"}
                continue
        #parse over the menue of the current day
        menue_week[curr_date.strftime("%A")] = parse_menue(data)

    menue_from = (date+timedelta(1)).strftime("%d.%m.%Y")
    menue_to = (date+timedelta(5)).strftime("%d.%m.%Y")
    menue_date = f"Menue from Monday {menue_from} to Friday {menue_to}\n"
    with open(filename, 'w', encoding='utf-8') as file:
        #write the date of this weeks menue
        file.write(f"{menue_date}")
        for day in menue_week:
            file.write(f"\n{weekday_dict[day]}\n")
            # loop over all menues of this day and write them to the cache
            for menue in menue_week[day]:
                menue_cache = ""
                menue_cache += f"{menue}\n{menue_week[day][menue]}\n"
                file.write(menue_cache)


def create_abos():
    abos = Path(ABO_FILENAME)
    abos.touch(exist_ok=True)


def cache_all_menus():
    "caches all menus as files"
    log.info("caching menus")
    download_week(CANTEEN_ID_THM, THM_WEEK_FILENAME)
    download_thm()
    download_week(CANTEEN_ID_UMA, UNIMA_WEEK_FILENAME)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return_message = conf["messages"]["start"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=return_message)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return_message = conf["messages"]["help"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=return_message)


async def mensa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """return todays mensa menu"""
    log.info("mensa was called")
    # Open the file and read its contents
    with open(THM_FILENAME, 'r') as file:
        menue_cache = file.read()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


async def thm_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """return this weeks thm mensa menu"""
    log.info("thm_week was called")
    # Open the file and read its contents
    with open(THM_WEEK_FILENAME, 'r') as file:
        menue_cache = file.read()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


async def uni_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """return this weeks uni mensa menu"""
    log.info("uni_week was called")
    # Open the file and read its contents
    with open(UNIMA_WEEK_FILENAME, 'r') as file:
        menue_cache = file.read()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=menue_cache)


async def abo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_abos = []
    chatid = update.effective_chat.id
    with open(ABO_FILENAME, 'r', encoding="utf-8") as abofile:
        for line in abofile:
            all_abos.append(line.replace("\n",""))
    if chatid not in all_abos:
        all_abos.append(chatid)
        message = conf["messages"]["abo"]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        log.info(f"added chat with chatid {chatid}")
    else:
        all_abos.remove(chatid)
        message = conf["messages"]["deabo"]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        log.info(f"removed chat with chatid {chatid}")

    with open(ABO_FILENAME, 'w', encoding="utf-8") as abofile:
        for abo in all_abos:
            abofile.write("%s\n" % abo)


def send_all_abos():
    bot = Bot(token=API_KEY)
    all_abos = []
    with open(ABO_FILENAME, 'r', encoding="utf-8") as abofile:
        for line in abofile:
            all_abos.append(line)
    log.info(f"sending abos. currently there are {len(all_abos)} abos")
    with open(THM_FILENAME, 'r', encoding="utf-8") as file:
        menu = file.read()
        if len(all_abos) > 0:
            for chat_id in all_abos:
                bot.send_message(chat_id=chat_id, text=menu)


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


async def set_commands(application):
    # Set the bot commands
    await application.bot.set_my_commands([
        ("start", "Start"),
        ("help", "Hilfe"),
        ("mensa", "Mensamenü des Tages"),
        ("thm_week", "Mensamenü der Woche"),
        ("uni_week", "Unimensamenu der Woche"),
        ("abo", "(De)Abboniere den Täglichen Mensareport")
    ])
    return

def main():
    log.info("starting bot")
    application = ApplicationBuilder().token(API_KEY).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    mensa_handler = CommandHandler('mensa', mensa)
    application.add_handler(mensa_handler)

    abo_handler = CommandHandler('abo', abo)
    application.add_handler(abo_handler)

    thm_week_handler = CommandHandler('thm_week', thm_week)
    application.add_handler(thm_week_handler)

    uni_week_handler = CommandHandler('uni_week', uni_week)
    application.add_handler(uni_week_handler)

    log.info("caching all menues")
    #cache_all_menus()
    log.info("creating abos")
    create_abos()
    # Set the bot commands
    log.info("set commands")
    set_commands(application)
    log.info("run scheduler")
    run_scheduler()
    log.info("start polling")
    application.run_polling(poll_interval=2) # poll every 2 sec. default is .5 secs

if __name__ == '__main__':
    main()
