import os
import sqlite3
import telebot
from telebot.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ⚠️ SECURITY: এনভায়রনমেন্ট ভেরিয়েবল থেকে টোকেন লোড করুন। 
API_TOKEN = os.getenv("BOT_TOKEN", "8698806008:AAF0Oa60Mg93WdyWw5DGHSz3r1L7A1CPtJk")
ADMIN_ID = 8138758919  # এডমিন টেলিগ্রাম আইডি

# Force Subscription এর জন্য একাধিক চ্যানেল (বটকে অবশ্যই এই চ্যানেলগুলোর এডমিন হতে হবে)
TARGET_CHANNELS = ["@allproxyvpnservice24", "@allipvpnservice24"]

bot = telebot.TeleBot(API_TOKEN, parse_mode="HTML")
DB_NAME = 'shop_database.db'


# --- টেলিগ্রাম মেনু (Menu Button) সেটআপ ---
def set_bot_commands():
    commands = [
        BotCommand("start", "🚀 মূল মেনু খুলুন"),
        BotCommand("buy", "🛍️ প্রোডাক্ট কিনুন"),
        BotCommand("profile", "👤 আপনার প্রোফাইল"),
        BotCommand("deposit", "💰 ব্যালেন্স ডিপোজিট"),
        BotCommand("support", "☎️ এডমিন সাপোর্ট"),
    ]
    try:
        bot.set_my_commands(commands)
    except Exception as e:
        print(f"Failed to set bot commands: {e}")


# --- ডাটাবেজ হেল্পার (Safe Context Management) ---
def get_db():
    return sqlite3.connect(DB_NAME, timeout=15)


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            total_buy INTEGER DEFAULT 0
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            trx_id TEXT PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            status TEXT DEFAULT 'pending'
        )
        ''')
        conn.commit()


init_db()


def get_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance, total_buy FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute('INSERT INTO users (user_id, balance, total_buy) VALUES (?, 0.0, 0)', (user_id,))
            conn.commit()
            return 0.0, 0
        return row[0], row[1]


def update_balance(user_id, amount):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()


def add_buy_count(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET total_buy = total_buy + 1 WHERE user_id = ?', (user_id,))
        conn.commit()


def is_trx_used(trx_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT trx_id FROM transactions WHERE trx_id = ?', (trx_id.strip(),))
        return cursor.fetchone() is not None


def record_trx(trx_id, user_id, amount, method):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO transactions (trx_id, user_id, amount, method) VALUES (?, ?, ?, ?)',
                       (trx_id.strip(), user_id, amount, method))
        conn.commit()


def update_trx_status(trx_id, status):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE transactions SET status = ? WHERE trx_id = ?', (status, trx_id.strip()))
        conn.commit()


user_states = {}


# --- চ্যাট মেম্বার চেক ফাংশন (Force Sub Check for Multiple Channels) ---
def check_user_subscription(user_id):
    for channel in TARGET_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Error checking channel {channel}: {e}")
            return False
    return True


# --- সাবস্ক্রাইব রিকোয়েস্ট মেসেজ পাঠানোর ফাংশন ---
def send_sub_request(chat_id):
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/allproxyvpnservice24")
    btn2 = InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/allipvpnservice24")
    btn3 = InlineKeyboardButton("✅ I Have Joined", callback_data="check_join")
    markup.add(btn1, btn2, btn3)
    
    text = (
        "📢 <b>চ্যানেলগুলোতে যোগদান আবশ্যক</b>\n\n"
        "বট ব্যবহার করতে আমাদের নিচের অফিশিয়াল চ্যানেলগুলোতে জয়েন করুন:\n\n"
        "1️⃣ @allproxyvpnservice24\n"
        "2️⃣ @allipvpnservice24\n\n"
        "উভয় চ্যানেলে জয়েন করে নিচে ✅ <b>I Have Joined</b> বাটনে চাপ দিন।"
    )
    bot.send_message(chat_id, text, reply_markup=markup)


# --- মেইন মেনু ---
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🛍️ Buy Product"), KeyboardButton("💵 Dollar Buy/Sell"))
    markup.row(KeyboardButton("👤 Profile"), KeyboardButton("💰 Deposit"))
    markup.row(KeyboardButton("🔗 Refer"), KeyboardButton("☎️ Support"))
    return markup


# --- মূল ক্যাটাগরি মেনু ---
def get_categories_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🌐 Proxy", callback_data="cat_proxy"),
        InlineKeyboardButton("🔑 VPN", callback_data="cat_vpn")
    )
    markup.row(
        InlineKeyboardButton("📱 Premium App", callback_data="cat_app"),
        InlineKeyboardButton("▶️ YouTube Premium", callback_data="cat_yt")
    )
    return markup


# --- কমান্ডস ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    get_user(user_id)
    user_states.pop(user_id, None)

    if not check_user_subscription(user_id):
        send_sub_request(message.chat.id)
        return

    bot.send_message(
        message.chat.id,
        f"🌸 স্বাগতম {message.from_user.first_name}!\n\nআমাদের শপে আপনাকে স্বাগতম। নিচের মেনু থেকে পছন্দ করুন:",
        reply_markup=get_main_menu(),
    )


# --- জয়েন চেক করার ইনলাইন বাটন হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def verify_join(call):
    user_id = call.from_user.id
    if check_user_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ ধন্যবাদ! আপনার ভেরিফিকেশন সফল হয়েছে।", show_alert=False)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(
            call.message.chat.id,
            f"🌸 স্বাগতম {call.from_user.first_name}!\n\nআমাদের শপে আপনাকে স্বাগতম। নিচের মেনু থেকে পছন্দ করুন:",
            reply_markup=get_main_menu(),
        )
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো সবকটি চ্যানেলে জয়েন করেননি! দয়া করে সবগুলোতে জয়েন করে আবার চেষ্টা করুন።", show_alert=True)


@bot.message_handler(commands=['buy'])
@bot.message_handler(func=lambda message: message.text == "🛍️ Buy Product")
def buy_product(message):
    if not check_user_subscription(message.from_user.id):
        send_sub_request(message.chat.id)
        return
    bot.send_message(message.chat.id, "কী কিনতে চান?", reply_markup=get_categories_menu())


@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda message: message.text == "👤 Profile")
def profile_handler(message):
    if not check_user_subscription(message.from_user.id):
        send_sub_request(message.chat.id)
        return
    balance, total_buy = get_user(message.from_user.id)
    user_info = (
        f"👤 <b>আপনার প্রোফাইল তথ্য:</b>\n\n"
        f"🆔 ইউজার আইডি: <code>{message.from_user.id}</code>\n"
        f"📛 নাম: {message.from_user.first_name}\n"
        f"💰 ব্যালেন্স: {balance:.2f} BDT\n"
        f"🛍️ মোট কেনাকাটা: {total_buy}টি"
    )
    bot.send_message(message.chat.id, user_info)


@bot.message_handler(func=lambda message: message.text == "💵 Dollar Buy/Sell")
def dollar_handler(message):
    if not check_user_subscription(message.from_user.id):
        send_sub_request(message.chat.id)
        return
    text = (
        "💵 <b>ডলার কেনা-বেচা সেবা</b>\n\n"
        "বর্তমানে আমাদের কাছে Binance USDT, LTC এবং অন্যান্য কারেন্সি উপলব্ধ আছে।\n"
        "ডিপোজিট রেট: <b>১ USDT = ১৩০ BDT</b>\n\n"
        "লেনদেন করতে সরাসরি যোগাযোগের জন্য মেসেজ দিন।"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💬 Contact Admin", url="https://t.me/proxyvpnservice17"))
    markup.add(InlineKeyboardButton("📢 Telegram Channel 1", url="https://t.me/allproxyvpnservice24"))
    markup.add(InlineKeyboardButton("📢 Telegram Channel 2", url="https://t.me/allipvpnservice24"))
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=['deposit'])
@bot.message_handler(func=lambda message: message.text == "💰 Deposit")
def deposit_handler(message):
    if not check_user_subscription(message.from_user.id):
        send_sub_request(message.chat.id)
        return
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("bKash (Personal)", callback_data="dep_bkash"),
        InlineKeyboardButton("Nagad (Personal)", callback_data="dep_nagad"),
    )
    markup.add(InlineKeyboardButton("Binance Pay / USDT (Rate: 130 Tk)", callback_data="dep_binance"))
    bot.send_message(message.chat.id, "💎 ডিপোজিট মেথড সিলেক্ট করুন:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "🔗 Refer")
def refer_handler(message):
    if not check_user_subscription(message.from_user.id):
        send_sub_request(message.chat.id)
        return
    bot_username = bot.get_me().username
    bot_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    text = f"🔗 আপনার রেফারেল লিংক:\n<code>{bot_link}</code>\n\nবন্ধু ডেকে নিয়ে আসুন এবং বোনাস জিতুন!"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['support'])
@bot.message_handler(func=lambda message: message.text == "☎️ Support")
def support_handler(message):
    if not check_user_subscription(message.from_user.id):
        send_sub_request(message.chat.id)
        return
    text = (
        "☎️ <b>কাস্টমার সাপোর্ট ও অফিশিয়াল চ্যানেল</b>\n\n"
        "যেকোনো সমস্যা, প্রোডাক্ট কেনা বা পেমেন্ট সংক্রান্ত সহায়তার জন্য সরাসরি আমাদের সাপোর্ট অ্যাকাউন্টে যোগাযোগ করুন।\n\n"
        "💬 Admin Support: <a href='https://t.me/proxyvpnservice17'>@proxyvpnservice17</a>\n"
        "📢 Channel 1: @allproxyvpnservice24\n"
        "📢 Channel 2: @allipvpnservice24\n"
        "⏰ সার্ভিস টাইম: ২৪/৭ ঘন্টা"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🟢 Contact Admin", url="https://t.me/proxyvpnservice17"))
    markup.add(InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/allproxyvpnservice24"))
    markup.add(InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/allipvpnservice24"))
    bot.send_message(message.chat.id, text, reply_markup=markup)


# --- Proxy মূল ফোল্ডার (Sub-categories) ---

@bot.callback_query_handler(func=lambda call: call.data == "cat_proxy")
def show_proxy_subcategories(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📶 GB Proxy", callback_data="sub_gb_proxy"),
        InlineKeyboardButton("🌐 ISP Proxy", callback_data="sub_isp_proxy")
    )
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_cat"))
    bot.edit_message_text("Proxy-র ধরণ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- GB Proxy ফোল্ডারের সাব-ফোল্ডার তালিকা ---

@bot.callback_query_handler(func=lambda call: call.data == "sub_gb_proxy")
def show_gb_proxy_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🛡️ Datampuls Proxy", callback_data="sub_datamplus_folder"),
        InlineKeyboardButton("🛡️ 9 Proxy", callback_data="sub_9proxy_folder")
    )
    markup.row(
        InlineKeyboardButton("🛡️ 711 Proxy", callback_data="sub_711gb_folder"),
        InlineKeyboardButton("🛡️ NovProxy", callback_data="sub_novgb_folder")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Thordata Proxy", callback_data="sub_thordata_folder"),
        InlineKeyboardButton("🛡️ Repaid Proxy", callback_data="sub_repaid_folder")
    )
    markup.row(
        InlineKeyboardButton("🛡️ IP Rocket Proxy", callback_data="sub_iprocket_folder")
    )
    markup.add(InlineKeyboardButton("🔙 Back to Proxy Menu", callback_data="cat_proxy"))
    bot.edit_message_text("📶 GB Proxy ফোল্ডার নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- GB Proxy Sub-Folders handlers ---

@bot.callback_query_handler(func=lambda call: call.data == "sub_datamplus_folder")
def show_datamplus_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Datampuls 1 GB | 140TK", callback_data="px|Datampuls 1GB|140|GB"))
    markup.add(InlineKeyboardButton("🔙 Back to GB Proxy Menu", callback_data="sub_gb_proxy"))
    bot.edit_message_text("🛡️ Datampuls Proxy প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_9proxy_folder")
def show_9proxy_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ 9 Proxy 200 MB | 50Tk", callback_data="px|9 Proxy 200MB|50|MB"))
    markup.row(InlineKeyboardButton("🛡️ 9 Proxy 500 MB | 100Tk", callback_data="px|9 Proxy 500MB|100|MB"))
    markup.row(InlineKeyboardButton("🛡️ 9 Proxy 1 GB | 130Tk", callback_data="px|9 Proxy 1GB|130|GB"))
    markup.add(InlineKeyboardButton("🔙 Back to GB Proxy Menu", callback_data="sub_gb_proxy"))
    bot.edit_message_text("🛡️ 9 Proxy প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_711gb_folder")
def show_711_gb_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ 711 Proxy 1 GB | 130 TK", callback_data="px|711 Proxy 1GB|130|GB"))
    markup.add(InlineKeyboardButton("🔙 Back to GB Proxy Menu", callback_data="sub_gb_proxy"))
    bot.edit_message_text("🛡️ 711 Proxy প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_novgb_folder")
def show_nov_gb_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ NovProxy 1 GB | 160 TK", callback_data="px|NovProxy 1GB|160|GB"))
    markup.add(InlineKeyboardButton("🔙 Back to GB Proxy Menu", callback_data="sub_gb_proxy"))
    bot.edit_message_text("🛡️ NovProxy প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_thordata_folder")
def show_thordata_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Thordata 1 GB | 140 TK", callback_data="px|Thordata 1GB|140|GB"))
    markup.add(InlineKeyboardButton("🔙 Back to GB Proxy Menu", callback_data="sub_gb_proxy"))
    bot.edit_message_text("🛡️ Thordata Proxy প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_repaid_folder")
def show_repaid_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Repaid Proxy 1 GB | 160 TK", callback_data="px|Repaid Proxy 1GB|160|GB"))
    markup.add(InlineKeyboardButton("🔙 Back to GB Proxy Menu", callback_data="sub_gb_proxy"))
    bot.edit_message_text("🛡️ Repaid Proxy প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_iprocket_folder")
def show_iprocket_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ IP Rocket 1 GB | 160 TK", callback_data="px|IP Rocket 1GB|160|GB"))
    markup.add(InlineKeyboardButton("🔙 Back to GB Proxy Menu", callback_data="sub_gb_proxy"))
    bot.edit_message_text("🛡️ IP Rocket Proxy প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- ISP Proxy برندের ফোল্ডারসমূহ ---

@bot.callback_query_handler(func=lambda call: call.data == "sub_isp_proxy")
def show_isp_proxy_brands(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🛡️ 711 Proxy ISP", callback_data="isp_brand_711"),
        InlineKeyboardButton("🛡️ 9 Proxy ISP", callback_data="isp_brand_9p")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Loki Proxy ISP", callback_data="isp_brand_loki"),
        InlineKeyboardButton("🛡️ Nov Proxy ISP", callback_data="isp_brand_nov")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Cli Proxy ISP", callback_data="isp_brand_cli")
    )
    markup.add(InlineKeyboardButton("🔙 Back to Proxy Menu", callback_data="cat_proxy"))
    bot.edit_message_text("🌐 ISP Proxy ব্র্যান্ড নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- ISP Proxy ব্র্যান্ড কোডসমূহ ---

@bot.callback_query_handler(func=lambda call: call.data == "isp_brand_711")
def show_711_isp_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("50 ISP | 400 Tk", callback_data="px|711 Proxy 50 ISP|400|Pc"), InlineKeyboardButton("100 ISP | 800 Tk", callback_data="px|711 Proxy 100 ISP|800|Pc"))
    markup.row(InlineKeyboardButton("200 ISP | 1600 Tk", callback_data="px|711 Proxy 200 ISP|1600|Pc"), InlineKeyboardButton("500 ISP | 4000 Tk", callback_data="px|711 Proxy 500 ISP|4000|Pc"))
    markup.row(InlineKeyboardButton("1000 ISP | 8000 Tk", callback_data="px|711 Proxy 1000 ISP|8000|Pc"))
    markup.add(InlineKeyboardButton("🔙 Back to ISP Menu", callback_data="sub_isp_proxy"))
    bot.edit_message_text("🛡️ 711 Proxy ISP প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "isp_brand_9p")
def show_9p_isp_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("50 ISP | 170 Tk", callback_data="px|9 Proxy 50 ISP|170|Pc"), InlineKeyboardButton("100 ISP | 340 Tk", callback_data="px|9 Proxy 100 ISP|340|Pc"))
    markup.row(InlineKeyboardButton("200 ISP | 680 Tk", callback_data="px|9 Proxy 200 ISP|680|Pc"), InlineKeyboardButton("500 ISP | 1500 Tk", callback_data="px|9 Proxy 500 ISP|1500|Pc"))
    markup.row(InlineKeyboardButton("1000 ISP | 3000 Tk", callback_data="px|9 Proxy 1000 ISP|3000|Pc"))
    markup.add(InlineKeyboardButton("🔙 Back to ISP Menu", callback_data="sub_isp_proxy"))
    bot.edit_message_text("🛡️ 9 Proxy ISP প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "isp_brand_loki")
def show_loki_isp_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("50 ISP | 400 Tk", callback_data="px|Loki Proxy 50 ISP|400|Pc"), InlineKeyboardButton("100 ISP | 800 Tk", callback_data="px|Loki Proxy 100 ISP|800|Pc"))
    markup.row(InlineKeyboardButton("200 ISP | 1600 Tk", callback_data="px|Loki Proxy 200 ISP|1600|Pc"), InlineKeyboardButton("500 ISP | 3500 Tk", callback_data="px|Loki Proxy 500 ISP|3500|Pc"))
    markup.row(InlineKeyboardButton("1000 ISP | 7000 Tk", callback_data="px|Loki Proxy 1000 ISP|7000|Pc"))
    markup.add(InlineKeyboardButton("🔙 Back to ISP Menu", callback_data="sub_isp_proxy"))
    bot.edit_message_text("🛡️ Loki Proxy ISP প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "isp_brand_nov")
def show_nov_isp_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("50 ISP | 400 Tk", callback_data="px|Nov Proxy 50 ISP|400|Pc"), InlineKeyboardButton("100 ISP | 800 Tk", callback_data="px|Nov Proxy 100 ISP|800|Pc"))
    markup.row(InlineKeyboardButton("200 ISP | 1600 Tk", callback_data="px|Nov Proxy 200 ISP|1600|Pc"), InlineKeyboardButton("500 ISP | 3500 Tk", callback_data="px|Nov Proxy 500 ISP|3500|Pc"))
    markup.row(InlineKeyboardButton("1000 ISP | 7000 Tk", callback_data="px|Nov Proxy 1000 ISP|7000|Pc"))
    markup.add(InlineKeyboardButton("🔙 Back to ISP Menu", callback_data="sub_isp_proxy"))
    bot.edit_message_text("🛡️ Nov Proxy ISP প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "isp_brand_cli")
def show_cli_isp_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("50 ISP | 400 Tk", callback_data="px|Cli Proxy 50 ISP|400|Pc"), InlineKeyboardButton("100 ISP | 800 Tk", callback_data="px|Cli Proxy 100 ISP|800|Pc"))
    markup.row(InlineKeyboardButton("200 ISP | 1600 Tk", callback_data="px|Cli Proxy 200 ISP|1600|Pc"), InlineKeyboardButton("500 ISP | 3500 Tk", callback_data="px|Cli Proxy 500 ISP|3500|Pc"))
    markup.row(InlineKeyboardButton("1000 ISP | 7000 Tk", callback_data="px|Cli Proxy 1000 ISP|7000|Pc"))
    markup.add(InlineKeyboardButton("🔙 Back to ISP Menu", callback_data="sub_isp_proxy"))
    bot.edit_message_text("🛡️ Cli Proxy ISP প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- Proxy ইনপুট হ্যান্ডলার ---

@bot.callback_query_handler(func=lambda call: call.data.startswith("px|"))
def ask_proxy_quantity(call):
    _, proxy_name, rate_str, unit = call.data.split("|")
    rate = float(rate_str)

    user_states[call.from_user.id] = {
        'action': 'enter_qty',
        'product': proxy_name,
        'rate': rate,
        'unit': unit,
    }

    if unit in ["GB", "MB"]:
        msg = (
            f"Minimum: 1 {unit}\n"
            f"Price : 1 {unit} = {rate:.0f} Tk (Bdt)\n\n"
            f"🌐 English: How many {unit} of IP do you want to buy?\n"
            f"🇧🇩 Bangla: আপনি কত {unit} আইপি কিনতে চান? (শুধুমাত্র সংখ্যা লিখুন)"
        )
    else:
        msg = (
            f"🌐 Product: {proxy_name}\n\n"
            f"Minimum: 1 Pc\n"
            f"Price : {rate:.0f} Tk\n\n"
            f"🌐 English: How many Proxy do you want to buy?\n"
            f"🇧🇩 Bangla: আপনি কত পিছ Proxy আইপি কিনতে চান? (শুধুমাত্র সংখ্যা লিখুন)"
        )
    bot.send_message(call.message.chat.id, msg)


# --- VPN ক্যাটাগরি ফোল্ডারসমূহ ---

@bot.callback_query_handler(func=lambda call: call.data == "cat_vpn")
def show_vpn_items(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🛡️ Avast VPN", callback_data="vpn_folder_avast"),
        InlineKeyboardButton("🛡️ HMA VPN", callback_data="vpn_folder_hma")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Atlas VPN", callback_data="vpn_folder_atlas"),
        InlineKeyboardButton("🛡️ Hotspot Shield", callback_data="vpn_folder_hotspot")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Bitdefender", callback_data="vpn_folder_bitdefender"),
        InlineKeyboardButton("🛡️ IPVanish", callback_data="vpn_folder_ipvanish")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Nord VPN", callback_data="vpn_folder_nord"),
        InlineKeyboardButton("🛡️ BetterNet", callback_data="vpn_folder_betternet")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Browsec", callback_data="vpn_folder_browsec"),
        InlineKeyboardButton("🛡️ Norton", callback_data="vpn_folder_norton")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Cheap VPN", callback_data="vpn_folder_cheap"),
        InlineKeyboardButton("🛡️ Panda VPN", callback_data="vpn_folder_panda")
    )
    markup.row(
        InlineKeyboardButton("🛡️ CyberGhost", callback_data="vpn_folder_cyberghost"),
        InlineKeyboardButton("🛡️ PIA VPN", callback_data="vpn_folder_pia")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Surfshark", callback_data="vpn_folder_surfshark"),
        InlineKeyboardButton("🛡️ Proton VPN", callback_data="vpn_folder_proton")
    )
    markup.row(
        InlineKeyboardButton("🛡️ Express VPN", callback_data="vpn_folder_express"),
        InlineKeyboardButton("🛡️ Turbo VPN", callback_data="vpn_folder_turbo")
    )
    markup.row(
        InlineKeyboardButton("🛡️ X-VPN", callback_data="vpn_folder_xvpn")
    )
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_cat"))
    bot.edit_message_text("🔑 VPN এর ব্র্যান্ড সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- VPN Sub-Folders Handlers ---

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_avast")
def vpn_avast(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Avast 7D | 30Tk", callback_data="vpn|Avast Vpn (7D)|30"))
    markup.row(InlineKeyboardButton("🛡️ Avast 30D | 100Tk", callback_data="vpn|Avast Vpn (30D)|100"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Avast VPN প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_hma")
def vpn_hma(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ HMA 7D | 30Tk", callback_data="vpn|Hma Vpn (7D)|30"))
    markup.row(InlineKeyboardButton("🛡️ HMA 30D | 100Tk", callback_data="vpn|Hma Vpn (30D)|100"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ HMA VPN প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_atlas")
def vpn_atlas(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Atlas 7D | 30Tk", callback_data="vpn|Atlast Vpn (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Atlas VPN প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_hotspot")
def vpn_hotspot(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Hotspot 7D | 30Tk", callback_data="vpn|Hotspot Shield (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Hotspot Shield packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_bitdefender")
def vpn_bitdefender(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Bitdefender 7D | 30Tk", callback_data="vpn|Bitdefender (7D)|30"))
    markup.row(InlineKeyboardButton("🛡️ Bitdefender 30D | 100Tk", callback_data="vpn|Bitdefender (30D)|100"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Bitdefender packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_ipvanish")
def vpn_ipvanish(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ IPVanish 7D | 30Tk", callback_data="vpn|Ip Vanish (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ IPVanish packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_nord")
def vpn_nord(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Nord 7D | 30Tk", callback_data="vpn|Nord Vpn (7D)|30"))
    markup.row(InlineKeyboardButton("🛡️ Nord 30D | 220Tk", callback_data="vpn|Nord Vpn (30D)|220"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Nord VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_betternet")
def vpn_betternet(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ BetterNet 7D | 40Tk", callback_data="vpn|BetterNet (7D)|40"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ BetterNet packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_browsec")
def vpn_browsec(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Browsec 7D | 40Tk", callback_data="vpn|Browsec (7D)|40"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Browsec packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_norton")
def vpn_norton(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Norton 7D | 40Tk", callback_data="vpn|Norton Vpn (7D)|40"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Norton packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_cheap")
def vpn_cheap(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Cheap 30D | 650Tk", callback_data="vpn|Cheap Vpn (30D)|650"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Cheap VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_panda")
def vpn_panda(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Panda 7D | 30Tk", callback_data="vpn|Panda Vpn (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Panda VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_cyberghost")
def vpn_cyberghost(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ CyberGhost 7D | 30Tk", callback_data="vpn|CyberGhost (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ CyberGhost packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_pia")
def vpn_pia(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ PIA 7D | 30Tk", callback_data="vpn|Pia Vpn (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ PIA VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_surfshark")
def vpn_surfshark(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Surfshark 7D | 30Tk", callback_data="vpn|Surfshark (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Surfshark packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_proton")
def vpn_proton(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Proton 14D | 70Tk", callback_data="vpn|Proton Vpn (14D)|70"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Proton VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_express")
def vpn_express(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Express 3-4D | 20Tk", callback_data="vpn|Express (3,4D)|20"))
    markup.row(InlineKeyboardButton("🛡️ Express 30D | 170Tk", callback_data="vpn|Express (30D 1Dev)|170"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Express VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_turbo")
def vpn_turbo(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ Turbo 7D | 30Tk", callback_data="vpn|Turbo Vpn (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ Turbo VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "vpn_folder_xvpn")
def vpn_xvpn(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛡️ XVpn 7D | 30Tk", callback_data="vpn|X Vpn (7D)|30"))
    markup.add(InlineKeyboardButton("🔙 Back to VPN Menu", callback_data="cat_vpn"))
    bot.edit_message_text("🛡️ X-VPN packages:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- VPN ইনপুট হ্যান্ডলার ---

@bot.callback_query_handler(func=lambda call: call.data.startswith("vpn|"))
def ask_vpn_quantity(call):
    _, vpn_name, rate_str = call.data.split("|")
    rate = float(rate_str)

    user_states[call.from_user.id] = {
        'action': 'enter_qty',
        'product': vpn_name,
        'rate': rate,
        'unit': 'Pc',
    }

    msg = (
        f"🔑 Product: {vpn_name}\n\n"
        f"Minimum: 1 Pc\n"
        f"Price of {vpn_name}: 1 Pc = {rate:.0f} Tk (Bdt)\n\n"
        f"🌐 English: How many Vpn want to buy?\n"
        f"🇧🇩 Bangla: আপনি কত পিছ Vpn আইপি কিনতে চান? (শুধুমাত্র সংখ্যা লিখুন)"
    )
    bot.send_message(call.message.chat.id, msg)


# --- Premium Apps ক্যাটাগরি (Updated Sub-folders) ---

@bot.callback_query_handler(func=lambda call: call.data == "cat_app")
def show_app_categories(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎬 Video & Editing", callback_data="app_cat_video"),
        InlineKeyboardButton("📸 Photo & Enhancement", callback_data="app_cat_photo")
    )
    markup.row(
        InlineKeyboardButton("📺 Media & Streaming", callback_data="app_cat_media")
    )
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_cat"))
    bot.edit_message_text("📱 Premium Apps এর ক্যাটাগরি সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- 🎬 Video & Editing Sub-Folders ---

@bot.callback_query_handler(func=lambda call: call.data == "app_cat_video")
def show_video_editing_apps(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎬 CapCut Pro", callback_data="app_folder_capcut"),
        InlineKeyboardButton("🎬 InShot Pro", callback_data="app_folder_inshot")
    )
    markup.add(InlineKeyboardButton("🔙 Back to Apps Menu", callback_data="cat_app"))
    bot.edit_message_text("🎬 Video & Editing অ্যাপ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "app_folder_capcut")
def app_capcut_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 CapCut Pro | 50 Tk", callback_data="app|CapCut Pro|50"))
    markup.add(InlineKeyboardButton("🔙 Back to Video Apps", callback_data="app_cat_video"))
    bot.edit_message_text("🎬 CapCut Pro প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "app_folder_inshot")
def app_inshot_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 InShot Pro | 20 Tk", callback_data="app|InShot Pro|20"))
    markup.add(InlineKeyboardButton("🔙 Back to Video Apps", callback_data="app_cat_video"))
    bot.edit_message_text("🎬 InShot Pro প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- 📸 Photo & Enhancement Sub-Folders ---

@bot.callback_query_handler(func=lambda call: call.data == "app_cat_photo")
def show_photo_editing_apps(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📸 PicsArt Pro", callback_data="app_folder_picsart"),
        InlineKeyboardButton("📸 Remini Pro", callback_data="app_folder_remini")
    )
    markup.add(InlineKeyboardButton("🔙 Back to Apps Menu", callback_data="cat_app"))
    bot.edit_message_text("📸 Photo & Enhancement অ্যাপ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "app_folder_picsart")
def app_picsart_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 PicsArt Pro | 20 Tk", callback_data="app|PicsArt Pro|20"))
    markup.add(InlineKeyboardButton("🔙 Back to Photo Apps", callback_data="app_cat_photo"))
    bot.edit_message_text("📸 PicsArt Pro প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "app_folder_remini")
def app_remini_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 Remini Pro | 20 Tk", callback_data="app|Remini Pro|20"))
    markup.add(InlineKeyboardButton("🔙 Back to Photo Apps", callback_data="app_cat_photo"))
    bot.edit_message_text("📸 Remini Pro প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- 📺 Media & Streaming Sub-Folders ---

@bot.callback_query_handler(func=lambda call: call.data == "app_cat_media")
def show_media_apps(call):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📺 YouTube Pro", callback_data="app_folder_ytpro"),
        InlineKeyboardButton("📺 Playz TV", callback_data="app_folder_playztv")
    )
    markup.add(InlineKeyboardButton("🔙 Back to Apps Menu", callback_data="cat_app"))
    bot.edit_message_text("📺 Media & Streaming অ্যাপ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "app_folder_ytpro")
def app_ytpro_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 YouTube Pro | 20 Tk", callback_data="app|YouTube Pro|20"))
    markup.add(InlineKeyboardButton("🔙 Back to Media Apps", callback_data="app_cat_media"))
    bot.edit_message_text("📺 YouTube Pro প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "app_folder_playztv")
def app_playztv_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 Playz TV | 50 Tk", callback_data="app|Playz TV|50"))
    markup.add(InlineKeyboardButton("🔙 Back to Media Apps", callback_data="app_cat_media"))
    bot.edit_message_text("📺 Playz TV প্যাকেজ সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


# --- Premium Apps ইনপুট হ্যান্ডলার ---

@bot.callback_query_handler(func=lambda call: call.data.startswith("app|"))
def ask_app_quantity(call):
    _, app_name, rate_str = call.data.split("|")
    rate = float(rate_str)

    user_states[call.from_user.id] = {
        'action': 'enter_qty',
        'product': app_name,
        'rate': rate,
        'unit': 'Pc',
    }

    msg = (
        f"📱 Product: {app_name}\n\n"
        f"Minimum: 1 Pc\n"
        f"Price : {rate:.0f} Tk\n\n"
        f"🌐 English: How many Android Apk want to buy?\n"
        f"🇧🇩 Bangla: আপনি কত পিছ Premium Android Apk আইপি কিনতে চান? (শুধুমাত্র সংখ্যা লিখুন)"
    )
    bot.send_message(call.message.chat.id, msg)


# --- YouTube Premium ক্যাটাগরি ও ফোল্ডার ---

@bot.callback_query_handler(func=lambda call: call.data == "cat_yt")
def show_yt_items(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("▶️ YouTube Premium 30 Days", callback_data="yt_folder_30d"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_to_cat"))
    bot.edit_message_text("YouTube Premium অপশন সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "yt_folder_30d")
def show_yt_30d_options(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("▶️ YouTube Premium 30 Day | 50 Tk", callback_data="yt|YT Premium 30D|50"))
    markup.add(InlineKeyboardButton("🔙 Back to YouTube Menu", callback_data="cat_yt"))
    bot.edit_message_text("▶️ YouTube Premium প্যাকেজ নির্বাচন করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("yt|"))
def ask_yt_quantity(call):
    _, yt_name, rate_str = call.data.split("|")
    rate = float(rate_str)

    user_states[call.from_user.id] = {
        'action': 'enter_qty',
        'product': yt_name,
        'rate': rate,
        'unit': 'Pc',
    }

    msg = (
        f"▶️ Product: {yt_name}\n\n"
        f"Minimum: 1 Pc\n"
        f"Price: {rate:.0f} Tk\n\n"
        f"🌐 English: How many Youtube Premium want to buy?\n"
        f"🇧🇩 Bangla: আপনি কত পিছ Youtube Premium কিনতে চান? (শুধুমাত্র সংখ্যা লিখুন)"
    )
    bot.send_message(call.message.chat.id, msg)


# --- প্রোডাক্ট ইনপুট ও পেমেন্ট ইনফো হ্যান্ডলার ---

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('action') == 'enter_qty')
def calculate_and_show_payment(message):
    try:
        qty = float(message.text)
        if qty <= 0:
            bot.send_message(message.chat.id, "❌ সর্বনিম্ন ১ টি বা তার বেশি লিখুন।")
            return

        state = user_states.pop(message.from_user.id)
        product_name = state['product']
        rate = state['rate']
        unit_type = state.get('unit', 'Pc')
        total_price = qty * rate

        balance, _ = get_user(message.from_user.id)

        payment_info = (
            f"💳 <b>পেমেন্ট ইনফো (Send Money)</b>\n\n"
            f"📦 প্রোডাক্ট: {product_name} ({qty:.0f} {unit_type})\n"
            f"💰 মোট টাকা: {total_price:.2f} BDT\n\n"
            f"📱 Personal BKash/Nagad Number:\n<code>01935164417</code>\n\n"
            f"পেমেন্ট করে থাকলে নিচে ব্যবহৃত মেথডটি সিলেক্ট করে TrxID জমা দিন।"
        )

        markup = InlineKeyboardMarkup()
        if balance >= total_price:
            cb_data = f"paybal|{product_name}|{qty:.0f}|{unit_type}|{total_price:.2f}"
            markup.add(InlineKeyboardButton(f"✅ ব্যালেন্স থেকে কাটুন ({total_price:.2f} BDT)", callback_data=cb_data))
        else:
            markup.row(
                InlineKeyboardButton("📥 Submit bKash TrxID", callback_data="submit_bKash"),
                InlineKeyboardButton("📥 Submit Nagad TrxID", callback_data="submit_Nagad")
            )
            markup.add(InlineKeyboardButton("Contact Admin", url="https://t.me/proxyvpnservice17"))

        bot.send_message(message.chat.id, payment_info, reply_markup=markup)

    except ValueError:
        bot.send_message(message.chat.id, "❌ অনুগ্রহ করে সঠিক সংখ্যা লিখুন (যেমন: 1, 2, 5)।")


# --- ব্যালেন্স পেমেন্ট প্রসেস ও এডমিন নোটিফিকেশন ---

@bot.callback_query_handler(func=lambda call: call.data.startswith("paybal|"))
def process_balance_payment(call):
    try:
        _, item_name, qty, unit, price_str = call.data.split("|")
        price = float(price_str)

        balance, _ = get_user(call.from_user.id)

        if balance >= price:
            update_balance(call.from_user.id, -price)
            add_buy_count(call.from_user.id)

            user_wait_msg = (
                "🤗 Your order has been received.\n"
                "We will take a maximum of 30 minutes.\n\n"
                "If 30 minutes have passed, please leave a message.\n"
                "<a href='https://t.me/proxyvpnservice17'>@proxyvpnservice17</a>\n\n"
                "🤗 আপনার অর্ডারটি গ্রহণ করা হয়েছে।\n"
                "সর্বোচ্চ ৩০ মিনিট সময় নিব আমরা।\n\n"
                "৩০ মিনিটের মধ্যে সেবা না পেলে মেসেজ দিন।"
            )

            bot.edit_message_text(user_wait_msg, call.message.chat.id, call.message.message_id)

            admin_markup = InlineKeyboardMarkup()
            admin_markup.add(InlineKeyboardButton("📦 Deliver Order", callback_data=f"sendproduct|{call.from_user.id}|{item_name}"))

            admin_msg = (
                f"🛒 নতুন অর্ডার কনফার্মড!\n\n"
                f"👤 ইউজার: {call.from_user.first_name} (<code>{call.from_user.id}</code>)\n"
                f"📦 প্রোডাক্ট: {item_name} ({qty} {unit})\n"
                f"💰 মূল্য: {price:.2f} BDT\n\n"
                f"প্রোডাক্ট কোড বা ডাটা পাঠাতে নিচের Deliver Order বাটনে চাপ দিন:"
            )

            bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup)
            bot.answer_callback_query(call.id, "✅ আপনার পেমেন্ট সফল হয়েছে!")
        else:
            bot.answer_callback_query(call.id, "❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই!", show_alert=True)

    except Exception as e:
        print(f"Error in process_balance_payment: {e}")
        bot.answer_callback_query(call.id, "❌ অর্ডার প্রসেস করতে একটি সমস্যা হয়েছে!", show_alert=True)


# --- এডমিন প্রোডাক্ট ডেলিভারি প্রসেস ---

@bot.callback_query_handler(func=lambda call: call.data.startswith("sendproduct|"))
def admin_ask_delivery_code(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "আপনি এডমিন নন!", show_alert=True)
        return

    _, target_user_id, product_name = call.data.split("|", 2)

    user_states[ADMIN_ID] = {
        'action': 'delivering_code',
        'target_user': int(target_user_id),
        'product': product_name,
    }

    bot.send_message(
        ADMIN_ID,
        f"📝 Product: {product_name}\n"
        f"User ID: <code>{target_user_id}</code>\n\n"
        f"ইউজারের জন্য CDKey/Code বা প্রোডাক্টের বিস্তারিত তথ্য লিখে মেসেজ দিন:\n"
        f"(উদাহরণ: SUP-6413-C0BE-D9BE-F9F5-AAF6)",
    )


@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and user_states.get(ADMIN_ID, {}).get('action') == 'delivering_code')
def send_product_to_user(message):
    delivery_data = user_states.pop(ADMIN_ID, {})
    target_user_id = delivery_data.get('target_user')
    product_name = delivery_data.get('product')
    code_text = message.text

    formatted_msg = (
        f"💬 Admin message #msg\n"
        f"-------------------\n"
        f"{product_name} 🖤\n\n"
        f"<code>{code_text}</code>"
    )

    try:
        reply_markup = InlineKeyboardMarkup()
        reply_markup.add(InlineKeyboardButton("Reply to Admin", url="https://t.me/proxyvpnservice17"))
        bot.send_message(target_user_id, formatted_msg, reply_markup=reply_markup)
        bot.send_message(ADMIN_ID, f"✅ ইউজার <code>{target_user_id}</code> এর কাছে সফলভাবে প্রোডাক্ট পাঠানো হয়েছে!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ প্রোডাক্ট পাঠাতে সমস্যা হয়েছে: {e}")


# --- ডিপোজিট ও মেথড সিলেকশন প্রসেস ---

@bot.callback_query_handler(func=lambda call: call.data in ["dep_bkash", "dep_nagad", "dep_binance"])
def deposit_methods(call):
    if call.data == "dep_binance":
        method = "Binance USDT"
        num_info = (
            "💵 Rate: <b>1 USDT = 130 BDT</b>\n\n"
            "🆔 Binance UID: <code>751363394</code>\n"
            "🆔 ByBit UID: <code>555598333</code>"
        )
    elif call.data == "dep_bkash":
        method = "bKash"
        num_info = "📱 Personal bKash Number: <code>01935164417</code>"
    else:
        method = "Nagad"
        num_info = "📱 Personal Nagad Number: <code>01935164417</code>"

    text = (
        f"💖 <b>{method} Deposit</b>\n\n"
        f"১. টাকা/ডলার পাঠান:\n{num_info}\n\n"
        f"২. টাকা/ডলার পাঠানোর পর নিচের '📥 Submit TrxID' বাটনে চাপ দিয়ে তথ্য জমা দিন।"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📥 Submit TrxID", callback_data=f"submit_{method}"))
    markup.add(InlineKeyboardButton("❌ Close", callback_data="close"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("submit_"))
def start_submit(call):
    method = call.data.split("_", 1)[1]
    user_states[call.from_user.id] = {'action': 'deposit_amount', 'method': method}

    if "Binance" in method:
        bot.send_message(
            call.message.chat.id,
            "Send Money, then submit your Transaction ID\n\n"
            "Send the amount you deposited in <b>USDT</b> (numbers only):"
        )
    else:
        bot.send_message(
            call.message.chat.id,
            f"Send Money via <b>{method}</b>, then submit your Transaction ID\n\n"
            "Send the amount you deposited in <b>BDT</b> (numbers only):"
        )


@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('action') == 'deposit_amount')
def get_amount(message):
    try:
        input_val = float(message.text)
        if input_val <= 0:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা লিখুন।")
            return

        user_states[message.from_user.id]['amount_val'] = input_val
        user_states[message.from_user.id]['action'] = 'deposit_trx'

        bot.send_message(
            message.chat.id,
            "🧾 Now send your Transaction ID (TrxID):"
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা লিখুন (যেমন: 100, 500)।")


@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get('action') == 'deposit_trx')
def get_trx_id(message):
    trx = message.text.strip()

    if is_trx_used(trx):
        bot.send_message(
            message.chat.id,
            f"⚠️ Transaction ID '{trx}' has already been used or is pending review"
        )
        return

    data = user_states.pop(message.from_user.id, {})
    method = data.get('method', 'bKash')
    input_val = data.get('amount_val', 0.0)

    if "Binance" in method:
        usd_amount = input_val
        bdt_amount = usd_amount * 130
        amount_str = f"${usd_amount:.2f} ({bdt_amount:.2f} BDT)"
        final_bdt = bdt_amount
    else:
        final_bdt = input_val
        amount_str = f"{final_bdt:.2f} BDT"

    record_trx(trx, message.from_user.id, final_bdt, method)

    bot.send_message(
        message.chat.id,
        "⏳ আপনার পেমেন্ট/ডিপোজিট রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে!",
    )

    admin_markup = InlineKeyboardMarkup()
    admin_markup.row(
        InlineKeyboardButton("✅ Approve Deposit", callback_data=f"depapprove|{message.from_user.id}|{final_bdt:.2f}|{trx}"),
        InlineKeyboardButton("❌ Reject Deposit", callback_data=f"depreject|{message.from_user.id}|{trx}"),
    )

    bot.send_message(
        ADMIN_ID,
        f"🔔 <b>নতুন ডিপোজিট/পেমেন্ট রিকোয়েস্ট!</b>\n\n"
        f"👤 ইউজার: {message.from_user.first_name} (<code>{message.from_user.id}</code>)\n"
        f"💳 মেথড: {method}\n"
        f"🔢 TrxID: <code>{trx}</code>\n"
        f"💰 পরিমাণ: {amount_str}",
        reply_markup=admin_markup,
    )


# --- এডমিন অ্যাকশন (Approve / Reject Deposit) ---

@bot.callback_query_handler(func=lambda call: call.data.startswith("depapprove|") or call.data.startswith("depreject|"))
def admin_deposit_action(call):
    bot.answer_callback_query(call.id, text="প্রসেসড!")

    parts = call.data.split("|")
    action = parts[0]
    target_id = int(parts[1])

    if action == "depapprove":
        amount = float(parts[2])
        trx_id = parts[3]

        update_balance(target_id, amount)
        update_trx_status(trx_id, "approved")
        new_balance, _ = get_user(target_id)

        bot.edit_message_text(
            f"✅ ডিপোজিট সফলভাবে অনুমোদিত হয়েছে!\n\n"
            f"🆔 ইউজার ID: <code>{target_id}</code>\n"
            f"🔢 TrxID: <code>{trx_id}</code>\n"
            f"💰 যোগ হওয়া ব্যালেন্স: {amount:.2f} BDT",
            call.message.chat.id,
            call.message.message_id,
        )

        try:
            bot.send_message(target_id, f"🎉 আপনার {amount:.2f} BDT ডিপোজিট সফল হয়েছে!\n💰 বর্তমান ব্যালেন্স: {new_balance:.2f}৳")
        except Exception as e:
            print(f"User message error: {e}")

    elif action == "depreject":
        trx_id = parts[2]
        update_trx_status(trx_id, "rejected")

        bot.edit_message_text(
            f"❌ ডিপোজিট বাতিল করা হয়েছে।\n🆔 ইউজার ID: <code>{target_id}</code>\n🔢 TrxID: <code>{trx_id}</code>",
            call.message.chat.id,
            call.message.message_id,
        )
        try:
            bot.send_message(target_id, "❌ আপনার ডিপোজিট রিকোয়েস্টটি বাতিল করা হয়েছে।")
        except Exception as e:
            print(f"User message error: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "back_to_cat")
def back_cat(call):
    bot.edit_message_text("কী কিনতে চান?", call.message.chat.id, call.message.message_id, reply_markup=get_categories_menu())


@bot.callback_query_handler(func=lambda call: call.data == "close")
def close_msg(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)


if __name__ == '__main__':
    print("Setting bot commands...")
    set_bot_commands()
    print("Bot is running successfully...")
    bot.infinity_polling()
