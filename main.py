import telebot
import pyotp
import requests
import random
import time
import datetime
import threading
from flask import Flask
from faker import Faker
from telebot import types
from concurrent.futures import ThreadPoolExecutor

# --- ⚙️ কনফিগারেশন ---
TOKEN = '8783194900:AAH__MsqIgqwKn_-Pzg2NdxQsIJ1OjvAVY8' 
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbygPBUx_yZ_iF6otutHertOraccSABCRRXI-uosllwptItMrzoqlyp1R-FImIgM09529w/exec"
ADMIN_ID = 8061525743 
BOT_NAME = "𝐓𝐚𝐧𝐣𝐢𝐦 𝐀𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐨𝐧"

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=50)
app = Flask(__name__)
fake = Faker()
executor = ThreadPoolExecutor(max_workers=30)

user_db = {} 
user_tasks = {}

@app.route('/')
def home():
    return f"🚀 {BOT_NAME} System is Online!"

def send_to_sheet(row, sheet_name):
    try:
        requests.post(WEB_APP_URL, json={"row": row, "sheet_name": sheet_name}, timeout=15)
    except: pass

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('🚀 𝐒𝐭𝐚𝐫𝐭 𝐖𝐨𝐫𝐤', '👤 𝐌𝐲 𝐏𝐫𝐨𝐟𝐢𝐥𝐞')
    markup.add('👥 𝐌𝐲 𝐑𝐞𝐟𝐞𝐫𝐫𝐚𝐥𝐬', '💸 𝐖𝐢𝐭𝐡𝐝𝐫𝐚𝐰', '📞 𝐒𝐮প্পোর্টর')
    if user_id == ADMIN_ID:
        markup.add('📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭')
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = message.chat.id
    if user_id not in user_db:
        user_db[user_id] = {'balance': 0.0, 'refer_count': 0}
    bot.send_message(user_id, f"🌟 **Welcome to {BOT_NAME}**", reply_markup=main_menu(user_id), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🚀 𝐒𝐭𝐚𝐫𝐭 𝐖𝐨𝐫𝐤")
def task_selection(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📸 Instagram + 2FA", callback_data="cat_2fa"),
        types.InlineKeyboardButton("🍪 Instagram Cookies", callback_data="cat_cookies")
    )
    bot.send_message(message.chat.id, "✨ **𝐒𝐞𝐥𝐞𝐜𝐭 𝐘𝐨𝐮𝐫 𝐂𝐚𝐭𝐞𝐠𝐨𝐫𝐲:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def method_selection(call):
    chat_id = call.message.chat.id
    category = call.data
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if category == "cat_2fa":
        markup.add(
            types.InlineKeyboardButton("📧 Instagram 2FA (Hotmail/Outlook)", callback_data="t_2fa_mail"),
            types.InlineKeyboardButton("🚫 Instagram 2FA (Not Temp Mail)", callback_data="t_2fa_no")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("📧 Instagram Cookies (Hotmail/Outlook)", callback_data="t_cook_mail"),
            types.InlineKeyboardButton("🚫 Instagram Cookies (Not Temp Mail)", callback_data="t_cook_no")
        )
    bot.edit_message_text("🛠 **𝐒𝐞𝐥𝐞𝐜𝐭 𝐌𝐞𝐭𝐡𝐨𝐝:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("t_"))
def start_task(call):
    chat_id = call.message.chat.id
    task_type = "2FA" if "2fa" in call.data else "Cookies"
    method_name = "Hotmail/Outlook" if "mail" in call.data else "Not Temp Mail"
    
    f_name = fake.user_name() + str(random.randint(10, 99))
    pwd = fake.password(length=10)
    email = f"{f_name}@hotmail.com" if "mail" in call.data else "N/A"
    
    user_tasks[chat_id] = {
        "type": task_type, "method": method_name, "name": f_name, 
        "pass": pwd, "email": email, "time": time.time()
    }
    
    msg = f"📝 **𝐍𝐞𝐰 𝐓𝐚𝐬𝐤: {task_type}**\n━━━━━━━━━━━━━\n👤 **User:** `{f_name}`\n🔑 **Pass:** `{pwd}`"
    if email != "N/A": msg += f"\n📧 **Email:** `{email}`"
    msg += f"\n━━━━━━━━━━━━━\n📥 " + ("২এফএ কী দিন" if task_type == "2FA" else "কুকিজ পেস্ট করুন")
    
    bot.send_message(chat_id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(call.message, handle_task_input)

def handle_task_input(message):
    chat_id = message.chat.id
    if chat_id not in user_tasks: return
    
    if time.time() - user_tasks[chat_id]['time'] > 600:
        bot.send_message(chat_id, "⏰ **Time Out! Task Closed.**")
        del user_tasks[chat_id]
        return

    data = user_tasks[chat_id]
    user_input = message.text.strip() if message.text else ""

    if data['type'] == "2FA":
        try:
            totp = pyotp.TOTP(user_input.replace(" ", ""))
            otp = totp.now()
            data['2fa_key'] = user_input
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📤 𝐒𝐮𝐛𝐦𝐢𝐭 𝐑𝐞𝐩𝐨𝐫𝐭", callback_data="final_submit"))
            bot.send_message(chat_id, f"🔢 **Your OTP:** `{otp}`\n\n✅ রিপোর্ট সাবমিট করুন।", reply_markup=markup, parse_mode="Markdown")
        except:
            bot.send_message(chat_id, "❌ ভুল কী! আবার সঠিক কী দিন।")
            bot.register_next_step_handler(message, handle_task_input)
    
    else: 
        formatted_report = f"{data['name']}|{data['pass']}|{user_input}"
        data['report'] = formatted_report
        bot.send_message(chat_id, f"✅ **Cookies এডিট করা হয়েছে:**\n\n`{formatted_report}`\n\n🔗 https://submitwork.org", parse_mode="Markdown")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Submitted", callback_data="final_submit"))
        bot.send_message(chat_id, "সাবমিট করে নিচের বাটনে ক্লিক করুন।", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "final_submit")
def final_submit(call):
    chat_id = call.message.chat.id
    data = user_tasks.get(chat_id)
    if not data: return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if data['type'] == "2FA":
        row = [timestamp, str(chat_id), f"{data['type']} ({data['method']})", data['name'], data['pass'], data.get('2fa_key', 'N/A'), "Pending"]
        executor.submit(send_to_sheet, row, "2FA_Data")
    else:
        row = [timestamp, str(chat_id), f"{data['type']} ({data['method']})", data['report'], "Pending"]
        executor.submit(send_to_sheet, row, "Cookies_Data")

    bot.edit_message_text("✅ **সফলভাবে জমা হয়েছে!**", chat_id, call.message.message_id)
    del user_tasks[chat_id]

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
