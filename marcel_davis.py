from threading import main_thread
from requests.api import get
import telebot
import requests
import bs4
import re
from bs4 import BeautifulSoup
from telebot.types import Message


from tgbot_config import API_KEY
bot = telebot.TeleBot(API_KEY)

bot.set_my_commands([
    telebot.types.BotCommand("/help","Hilfe"),
    telebot.types.BotCommand("/mensa","mensa heute"),
    telebot.types.BotCommand("/mensa_week","mensamenu woche"),
    telebot.types.BotCommand("/bp","Blockzeit"),
    telebot.types.BotCommand("/unimensa_week","unimensamenu der woche"),
]
)

@bot.message_handler(commands=["start","help"])
def start(message):
    welcome_string = """commands
/bp für blockplan
/mensa für heutiges mensamenü
/mensa_week für ganze woche
"""
    bot.send_message(message.chat.id, welcome_string)


@bot.message_handler(commands=["bp"])
def get_blockplan(message):
    data = [["Block","Start", "Ende"]]
    data += [["1", "08:00", "09:30"]]
    data += [["2", "09:45", "11:15"]]
    data += [["3", "12:00", "13:30"]]
    data += [["4", "13:40", "15:10"]]
    data += [["5", "15:20", "16:50"]]
    data += [["6", "17:00", "18:30"]]
    

    reply_string ="Wintersemester\n"

    for row in data:
        for col in row:
            reply_string += f"{col:<12}"
        reply_string += "\n"

    reply_string += "Sommersemester\n"
    data_sose = [["Block","Start", "Ende"]]
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
    words = [stri[pair[0]-1:pair[1]+1] for pair in para]
    for word in words:
        stri = stri.replace(word, " ")
    return stri

@bot.message_handler(commands=['mensa'])
def mensa(message):

    URL="https://www.stw-ma.de/Essen+_+Trinken/Speisepl%C3%A4ne/Hochschule+Mannheim.html"

    with requests.get(URL, verify=False) as url:
        soup = BeautifulSoup(url.content, features="lxml")
    match = soup.find(class_='speiseplan-table')

    result_message=""
    for row in match:
        if type(row) is not bs4.element.NavigableString:
            cells = row.find_all("td")
            del cells[-2]
            for cell in cells:
                # print(cell)
                stri = cell.get_text()
                result = re.sub(r'[\t\n]+', '', stri)
                result = re.sub(r'\€Stück|€Portion|€pro100g','€', result)
                result_message+=result+"\n"
            result_message+="\n"
    if not result_message:
        result_message="Hochschulmensa hat zu 💩"
    
    bot.send_message(message.chat.id, result_message)

@bot.message_handler(commands=['mensa_week'])
def mensa(message):

    with requests.get("https://www.stw-ma.de/Essen+_+Trinken/Speisepl%C3%A4ne/Hochschule+Mannheim-view-week.html", verify=False) as url:
        soup = BeautifulSoup(url.content)
    match = soup.find_all(class_='active1')
    data = [ele.text for ele in match]
    data = [ele.replace("\t",'').replace("\n\n\n", "\n\n") for ele in data]
    data = [ele.replace("Montag", "*Montag*") for ele in data]
    data = [ele.replace("Dienstag", "*Dienstag*") for ele in data]
    data = [ele.replace("Mittwoch", "*Mittwoch*") for ele in data]
    data = [ele.replace("Donnerstag", "*Donnerstag*") for ele in data]
    data = [ele.replace("Freitag", "*Freitag*") for ele in data]
    data = [ele.replace("`", "'") for ele in data]
    
    menu = "".join(data)
 #   menu = replace_paranthesis(menu)

    if not match:
        menu="Hochschulmensa hat zu 💩"
    bot.send_message(message.chat.id, menu, parse_mode='Markdown')

@bot.message_handler(commands=['unimensa_week'])
def mensa(message):
    with requests.get("https://www.stw-ma.de/men%C3%BCplan_schlossmensa-view-week.html", verify=False) as url:
        soup = BeautifulSoup(url.content)
    match = soup.find_all(class_='active1')
    data = [ele.text for ele in match]
    data = [ele.replace("\t",'').replace("\n\n\n", "\n\n") for ele in data]
    data = [ele.replace("Montag", "*Montag*") for ele in data]
    data = [ele.replace("Dienstag", "*Dienstag*") for ele in data]
    data = [ele.replace("Mittwoch", "*Mittwoch*") for ele in data]
    data = [ele.replace("Donnerstag", "*Donnerstag*") for ele in data]
    data = [ele.replace("Freitag", "*Freitag*") for ele in data]
    
    menu = "".join(data)
  #  menu = replace_paranthesis(menu)

    if not match:
        menu="Unimensa hat zu 💩"
    bot.send_message(message.chat.id, menu, parse_mode='Markdown')


bot.polling()
