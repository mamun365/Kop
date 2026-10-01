import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import threading
import os
import json

# ==========================================
# ⚠️ অ্যাডমিন এবং গ্রুপ সেটিংস
# ==========================================
BOT_TOKEN = '8997878182:AAE2z0wEVYIgbrFpI-ZBrwkSX9yfiDvjYPc'
ADMIN_ID = 7777314453  
OTP_GROUP_ID = -5448372158 

bot = telebot.TeleBot(BOT_TOKEN, num_threads=100)

# 💡 API Config সেভ এবং লোড করার সিস্টেম
API_CONFIG_FILE = "api_config.json"

def load_api():
    if os.path.exists(API_CONFIG_FILE):
        with open(API_CONFIG_FILE, 'r') as f: return json.load(f)
    # ডিফল্ট TGQuantumX API (আপনার দেওয়া স্ক্রিনশট অনুযায়ী)
    return {
        'api_username': '', 
        'api_key': '',
        'tgq_username': 'user_ecec0898b7',
        'tgq_password': 'pass_3838a5d0399b40dd'
    }

def save_api(data):
    with open(API_CONFIG_FILE, 'w') as f: json.dump(data, f)

BOT_CONFIG = load_api()

BASE_URL = 'https://api.durianrcs.com/out/ext_api'
SERVICE_PIDS = {'Telegram': '0257', 'WhatsApp': '6058', 'TikTok': '0234', 'Facebook': '0013'}

user_data = {}
menu_buttons = ['🔁 Bulk Auto Mode', '🛑 Stop Bulk Mode', '⚙️ Settings', '⚙️ Set Service', '🌍 Select Country']

def get_user(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {
            'pid': SERVICE_PIDS['Telegram'], 
            'service_name': 'Telegram', 
            'cuy': '', 
            'bulk_running': False, 
            'checker_on': True, 
            'num_type': 'FRESH', 
            'fetch_delay': 5.0, 
            'checker_warned': False 
        }
    return user_data[chat_id]

# ==========================================
# ⚙️ সেটিংস মেনু
# ==========================================
def generate_settings_markup(chat_id):
    u = get_user(chat_id)
    markup = InlineKeyboardMarkup(row_width=1)
    
    chk_status = "ON 🟢" if u['checker_on'] else "OFF 🔴"
    n_type = u['num_type']
    type_icon = "🟢" if n_type == "FRESH" else ("🚫" if n_type == "OLD" else "🌐")
    delay = f"{u['fetch_delay']}s" if u['fetch_delay'] > 0 else "0ms (Max Speed)"
    
    tgq_status = "✅ Set" if BOT_CONFIG.get('tgq_username') else "❌ Not Set"
    durian_status = "✅ Set" if BOT_CONFIG.get('api_username') else "❌ Not Set"
    
    markup.add(
        InlineKeyboardButton(f"🛠 Checker: {chk_status}", callback_data="set_checker"),
        InlineKeyboardButton(f"📱 Type: {n_type} {type_icon}", callback_data="set_type"),
        InlineKeyboardButton(f"⏱ Delay: {delay}", callback_data="set_delay"),
        InlineKeyboardButton(f"🔑 Set TGQ API ({tgq_status})", callback_data="update_tgq_api_ui"),
        InlineKeyboardButton(f"🔑 Set Durian API ({durian_status})", callback_data="update_durian_api_ui"),
        InlineKeyboardButton("❌ Close Settings", callback_data="close_settings")
    )
    return markup

@bot.message_handler(func=lambda message: message.text == '⚙️ Settings')
def open_settings(message):
    if message.chat.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "⚙️ **Bot Control Panel:**", reply_markup=generate_settings_markup(message.chat.id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["set_checker", "set_type", "set_delay", "close_settings", "update_tgq_api_ui", "update_durian_api_ui"])
def handle_settings(call):
    chat_id = call.message.chat.id
    if chat_id != ADMIN_ID: return
    u = get_user(chat_id)
    action = call.data
    
    if action == "set_checker":
        u['checker_on'] = not u['checker_on']
    elif action == "set_type":
        types = ['FRESH', 'OLD', 'ALL']
        idx = types.index(u['num_type'])
        u['num_type'] = types[(idx + 1) % 3]
    elif action == "set_delay":
        delays = [5.0, 1.0, 0.5, 0.0]
        idx = delays.index(u['fetch_delay'])
        u['fetch_delay'] = delays[(idx + 1) % 4]
    elif action == "update_tgq_api_ui":
        msg = bot.send_message(chat_id, "✍️ **TGQuantumX API দিন:**\n(Username এবং Password মাঝে স্পেস দিয়ে লিখুন)\n\nউদাহরণ: `user_ecec0898b7 pass_3838a5d0399b40dd`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_tgq_api_update)
        return
    elif action == "update_durian_api_ui":
        msg = bot.send_message(chat_id, "✍️ **DurianRCS API দিন:**\n(Username এবং API Key মাঝে স্পেস দিয়ে লিখুন)\n\nউদাহরণ: `your_username your_apikey`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_durian_api_update)
        return
    elif action == "close_settings":
        bot.delete_message(chat_id, call.message.message_id)
        return bot.send_message(chat_id, "✅ Settings Saved.")
        
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=generate_settings_markup(chat_id))

def process_tgq_api_update(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
    if message.text in menu_buttons: return bot.send_message(chat_id, "❌ API Update Cancelled.")
        
    parts = message.text.strip().split()
    if len(parts) == 2:
        BOT_CONFIG['tgq_username'] = parts[0]
        BOT_CONFIG['tgq_password'] = parts[1]
        save_api(BOT_CONFIG)
        bot.send_message(chat_id, f"✅ **TGQ API Updated & Saved!**\nUser: `{parts[0]}`", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "⚠️ **ভুল ফরম্যাট!** স্পেস দিয়ে লিখুন।")

def process_durian_api_update(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
    if message.text in menu_buttons: return bot.send_message(chat_id, "❌ API Update Cancelled.")
        
    parts = message.text.strip().split()
    if len(parts) == 2:
        BOT_CONFIG['api_username'] = parts[0]
        BOT_CONFIG['api_key'] = parts[1]
        save_api(BOT_CONFIG)
        bot.send_message(chat_id, f"✅ **Durian API Updated & Saved!**\nUser: `{parts[0]}`", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "⚠️ **ভুল ফরম্যাট!** স্পেস দিয়ে লিখুন।")

# --- ১. মূল মেনু ---
def get_main_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton('🔁 Bulk Auto Mode'), KeyboardButton('🛑 Stop Bulk Mode'))
    markup.add(KeyboardButton('⚙️ Settings'), KeyboardButton('⚙️ Set Service'))
    markup.add(KeyboardButton('🌍 Select Country'))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
    get_user(chat_id)
    bot.send_message(chat_id, "Welcome Admin! Set up your bot:", reply_markup=get_main_menu())

# ==========================================
# ⚙️ সার্ভিস এবং কান্ট্রি
# ==========================================
@bot.message_handler(func=lambda message: message.text == '⚙️ Set Service')
def set_service(message):
    if message.chat.id != ADMIN_ID: return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton('Telegram', callback_data='srv_Telegram'), InlineKeyboardButton('WhatsApp', callback_data='srv_WhatsApp'))
    markup.add(InlineKeyboardButton('TikTok', callback_data='srv_TikTok'), InlineKeyboardButton('Facebook', callback_data='srv_Facebook'))
    bot.send_message(message.chat.id, "Select Service:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('srv_'))
def handle_service_selection(call):
    chat_id = call.message.chat.id
    if chat_id != ADMIN_ID: return
    service_name = call.data.split('_')[1]
    u = get_user(chat_id)
    u['service_name'] = service_name
    u['pid'] = SERVICE_PIDS[service_name] 
    bot.edit_message_text(f"✅ Service set to: **{service_name}**", chat_id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == '🌍 Select Country')
def ask_country(message):
    if message.chat.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "✍️ Send Country Code (e.g., US, UK, BD).\n*(Send `ALL` for random)*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_country)

def save_country(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
    if message.text in menu_buttons or message.text.startswith('/'): return
    u = get_user(chat_id)
    code = message.text.strip().lower() 
    u['cuy'] = '' if code == 'all' else code
    bot.send_message(chat_id, f"✅ Country set to: **{code.upper()}**", parse_mode="Markdown")

# ==========================================
# 🔍 TGQuantumX API Checker Logic
# ==========================================
def check_number_tgq(phone_number):
    """TGQuantumX API ব্যবহার করে নাম্বার চেক করার ফাংশন"""
    url = "http://api.tgquantumx.online:8090/check"
    clean_number = phone_number.replace("+", "")
    
    payload = {
        "username": BOT_CONFIG.get('tgq_username', ''),
        "password": BOT_CONFIG.get('tgq_password', ''),
        "phone_numbers": [clean_number]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        data = res.json()
        
        if data.get("success"):
            if clean_number in data.get("fresh", []): return "fresh"
            if clean_number in data.get("registered", []): return "registered"
            if clean_number in data.get("banned", []): return "banned"
            if clean_number in data.get("invalid", []): return "invalid"
            return "unknown"
        else:
            print(f"API Error: {data.get('error')}")
            return "error"
    except Exception as e:
        print(f"TGQ API Request Error: {e}")
        return "error"

# ==========================================
# ✨ Simple OTP Wait & Group Forward
# ==========================================
def check_otp_background(chat_id, number, pid):
    api_number = number.replace('+', '') 
    
    for _ in range(270): 
        msg_url = f"{BASE_URL}/getMsg?name={BOT_CONFIG['api_username']}&ApiKey={BOT_CONFIG['api_key']}&pid={pid}&pn={api_number}&serial=2"
        
        try:
            res = requests.get(msg_url)
            msg_res = res.json()
            
            if msg_res.get('code') == 200:
                otp_code = msg_res.get('data')
                
                simple_msg = f"🚀 **Abir Developer Bot**\n\n📱 Number: `{number}`\n📊 Status: ✅ (OTP Received)\n✉️ Code: `{otp_code}`"
                bot.send_message(chat_id, simple_msg, parse_mode="Markdown")
                
                try: 
                    group_msg = f"📱 Number: <code>{number}</code>\n✉️ Code: <code>{otp_code}</code>"
                    bot.send_message(OTP_GROUP_ID, group_msg, parse_mode="HTML")
                except Exception as group_err: 
                    print(f"Group Message Failed: {group_err}") 
                return 
                
        except ValueError:
            pass
        except Exception as e:
            print(f"OTP Fetch Error: {e}")
            
        time.sleep(1.5) 
    
    requests.get(f"{BASE_URL}/addBlack?name={BOT_CONFIG['api_username']}&ApiKey={BOT_CONFIG['api_key']}&pid={pid}&pn={api_number}")
    bot.send_message(chat_id, f"❌ `{number}` - OTP Timeout (Blacklisted)", parse_mode="Markdown")

# --- ৮. ডাইনামিক ফেচার (অটোমেটিক স্পিড লজিক) ---
def continuous_number_fetcher(chat_id):
    u = get_user(chat_id)
    bot.send_message(chat_id, f"🚀 **Bulk Mode Started!**\nService: `{u['service_name']}`\nType: `{u['num_type']}`", parse_mode="Markdown")
    
    current_delay = u['fetch_delay']
    u['checker_warned'] = False 
    
    while u['bulk_running']:
        url = f"{BASE_URL}/getMobile?name={BOT_CONFIG['api_username']}&ApiKey={BOT_CONFIG['api_key']}&pid={u['pid']}&cuy={u['cuy']}&num=1&noblack=1&serial=2"
        
        try:
            res = requests.get(url)
            response = res.json()
            
            if response.get('code') == 200:
                number = str(response.get('data'))
                api_number_format = number 
                
                if not number.startswith('+'): 
                    number = '+' + number
                
                current_delay = u['fetch_delay']
                
                # TGQuantumX API দিয়ে নাম্বার চেক করা
                status = check_number_tgq(number)
                
                proceed = False
                status_text = ""
                icon = ""
                
                if status == "fresh":
                    if u['checker_on']: 
                        proceed = True
                        status_text = "Fresh"
                        icon = "✅"
                elif status == "registered":
                    if not u['checker_on']: 
                        proceed = True
                        status_text = "Old"
                        icon = "🚫"
                elif status == "banned":
                    if not u['checker_on']: 
                        proceed = True
                        status_text = "Banned"
                        icon = "❄️" 
                elif status == "invalid":
                    proceed = True
                    status_text = "Invalid"
                    icon = "❌"
                
                if proceed:
                    msg_text = (
                        f"🚀 **Abir Developer Bot**\n"
                        f"-------------------\n"
                        f"📱 Number: `{number}`\n"
                        f"📊 Status: {status_text} {icon}\n"
                        f"⏳ OTP: Waiting for OTP..."
                    )
                    bot.send_message(chat_id, msg_text, parse_mode="Markdown")
                    threading.Thread(target=check_otp_background, args=(chat_id, number, u['pid'])).start()
                else:
                    # কন্ডিশন ম্যাচ না করলে নাম্বার ব্ল্যাকলিস্ট
                    requests.get(f"{BASE_URL}/addBlack?name={BOT_CONFIG['api_username']}&ApiKey={BOT_CONFIG['api_key']}&pid={u['pid']}&pn={api_number_format}")
            
            else:
                if current_delay >= 5.0: current_delay = 1.0
                elif current_delay >= 1.0: current_delay = 0.5
                
        except ValueError:
            pass
        except Exception as e: 
            print(f"Fetch Error: {e}")
        
        if current_delay > 0:
            time.sleep(current_delay)

@bot.message_handler(func=lambda message: message.text in ['🔁 Bulk Auto Mode', '🛑 Stop Bulk Mode'])
def toggle_bulk(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID: return
    
    if not BOT_CONFIG['api_username'] or not BOT_CONFIG['api_key']:
        bot.send_message(chat_id, "⚠️ **DurianRCS API সেট করা নেই!**\nকাজ শুরু করার আগে দয়া করে ⚙️ Settings থেকে Durian API সেট করুন।", parse_mode="Markdown")
        return

    if not BOT_CONFIG.get('tgq_username') or not BOT_CONFIG.get('tgq_password'):
        bot.send_message(chat_id, "⚠️ **TGQuantumX API সেট করা নেই!**\nকাজ শুরু করার আগে দয়া করে ⚙️ Settings থেকে TGQ API সেট করুন।", parse_mode="Markdown")
        return

    u = get_user(chat_id)
    
    if message.text == '🔁 Bulk Auto Mode':
        if u['bulk_running']: bot.send_message(chat_id, "Bulk Mode is already running!")
        else:
            u['bulk_running'] = True
            threading.Thread(target=continuous_number_fetcher, args=(chat_id,)).start()
            
    elif message.text == '🛑 Stop Bulk Mode':
        if u['bulk_running']:
            u['bulk_running'] = False
            bot.send_message(chat_id, "Stopping Bulk Mode...")

print("🔥 Bot is running! TGQuantumX Checker Enabled without Session!")
bot.infinity_polling()