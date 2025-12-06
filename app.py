# import sqlite3
# from datetime import datetime, time as dtime
# import pandas as pd
# import pytz
# import asyncio
# import nest_asyncio
# import requests
# from flask import Flask, render_template, request, redirect, url_for
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
# from telegram.ext import (
#     Application,
#     CommandHandler,
#     CallbackContext,
#     CallbackQueryHandler,
#     MessageHandler,
#     filters,
# )

# app = Flask(__name__)
# DB_PATH = 'crm.db'
# BOT_TOKEN = '7935396412:AAFhVBQ1NNmw-giNGacreQkS71bsFlZAmM8'
# ADMIN_CHAT_IDS = [6855997739, 266123144, 1657599027, 1725877539]

# # --- DB Init ---
# def init_db():
#     if not os.path.exists(DB_PATH):
#         con = sqlite3.connect(DB_PATH)
#         cur = con.cursor()
#         cur.execute('''
#             CREATE TABLE tolovlar (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 ismi TEXT NOT NULL,
#                 tolov INTEGER NOT NULL,
#                 kurs TEXT NOT NULL,
#                 oy TEXT NOT NULL,
#                 izoh TEXT,
#                 admin TEXT NOT NULL,
#                 oqituvchi TEXT NOT NULL,
#                 vaqt TEXT NOT NULL,
#                 tolov_turi TEXT
#             )
#         ''')
#         cur.execute('''
#             CREATE TABLE qoshimcha_summa (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 oy TEXT NOT NULL,
#                 summa INTEGER NOT NULL
#             )
#         ''')
#         con.commit()
#         con.close()
# init_db()

# # --- Flask qismi ---
# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         ismi = request.form['ismi']
#         tolov = int(request.form['tolov'])
#         if tolov < 1000:
#             tolov *= 1000
#         kurs = request.form['kurs']
#         oy = request.form['oy']
#         izoh = request.form.get('izoh', '')
#         admin = request.form['admin']
#         oqituvchi = request.form['oqituvchi']
#         tolov_turi = request.form['tolov_turi']
#         vaqt = datetime.now(pytz.timezone('Asia/Tashkent')).strftime('%Y-%m-%d %H:%M:%S')

#         con = sqlite3.connect(DB_PATH)
#         cur = con.cursor()
#         cur.execute('''
#             INSERT INTO tolovlar (ismi, tolov, kurs, oy, izoh, admin, oqituvchi, vaqt, tolov_turi)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (ismi, tolov, kurs, oy, izoh, admin, oqituvchi, vaqt, tolov_turi))
#         con.commit()
#         con.close()

#         message = (
#             f"💳 *Yangi to‘lov kiritildi!*\n\n"
#             f"👤 Ismi: {ismi}\n"
#             f"💰 To‘lov: {tolov} so‘m\n"
#             f"📚 Kurs: {kurs} ({oy} oyi)\n"
#             f"💳 To‘lov turi: {tolov_turi}\n"
#             f"👨‍🏫 O‘qituvchi: {oqituvchi}\n"
#             f"🛠 Admin: {admin}\n"
#             f"💬 Izoh: {izoh or 'Yo‘q'}\n"
#             f"🕒 Sana: {vaqt}"
#         )

#         for admin_id in ADMIN_CHAT_IDS:
#             try:
#                 requests.get(
#                     f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
#                     params={
#                         "chat_id": admin_id,
#                         "text": message,
#                         "parse_mode": "Markdown"
#                     }
#                 )
#             except Exception as e:
#                 print(f"Xabar yuborishda xatolik: {e}")

#         return redirect(url_for('index'))

#     today = datetime.now(pytz.timezone('Asia/Tashkent')).strftime('%Y-%m-%d')
#     con = sqlite3.connect(DB_PATH)
#     cur = con.cursor()
#     cur.execute('''
#         SELECT ismi, tolov, kurs, oy, izoh, admin, oqituvchi, vaqt, tolov_turi
#         FROM tolovlar
#         WHERE date(vaqt) = ?
#         ORDER BY vaqt DESC
#     ''', (today,))
#     tolovlar = cur.fetchall()
#     con.close()
#     return render_template('index.html', tolovlar=tolovlar)

# # --- Telegram qismi ---
# user_state = {}

# async def start(update: Update, context: CallbackContext):
#     user_id = update.effective_chat.id
#     if user_id not in ADMIN_CHAT_IDS:
#         await update.message.reply_text("Siz admin emassiz.")
#         return
#     keyboard = [
#         [InlineKeyboardButton("📅 Bugungi to‘lovlar", callback_data="today_report")],
#         [InlineKeyboardButton("📊 Oylik to‘lovlar", callback_data="oylik_menyu")],
#         [InlineKeyboardButton("➕ Qo‘shimcha summa", callback_data="add_extra")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text("Xush kelibsiz, admin! Tanlang:", reply_markup=reply_markup)

# # ✅ Faqat shu funksiya yangilangan:
# async def create_excel(rows, filename):
#     df = pd.DataFrame(
#         rows,
#         columns=[
#             'ID', 'Ismi', 'To‘lov', 'Kurs', 'Oy',
#             'Izoh', 'Admin', 'O‘qituvchi', 'Vaqt', 'Tolov turi'
#         ]
#     )
#     os.makedirs("reports", exist_ok=True)

#     # --- Hisoblash ---
#     jami_sum = df['To‘lov'].sum()
#     klik_sum = df.loc[
#         df['Tolov turi'].str.lower().isin(['klik', 'click', 'karta', 'card']),
#         'To‘lov'
#     ].sum()
#     naqd_sum = df.loc[
#         df['Tolov turi'].str.lower().isin(['naqd']),
#         'To‘lov'
#     ].sum()

#     # --- Bo‘sh qator ---
#     df.loc[len(df.index)] = ['', '', '', '', '', '', '', '', '', '']

#     # --- Yakuniy qatorlar ---
#     df.loc[len(df.index)] = ['', '📊 Jami', f"{jami_sum:,} so‘m", '', '', '', '', '', '', '']
#     df.loc[len(df.index)] = ['', '💳 Klik', f"{klik_sum:,} so‘m", '', '', '', '', '', '', '']
#     df.loc[len(df.index)] = ['', '💵 Naqd', f"{naqd_sum:,} so‘m", '', '', '', '', '', '', '']

#     # --- Faylni saqlash ---
#     df.to_excel(os.path.join("reports", filename), index=False)

# async def handle_callback(update: Update, context: CallbackContext):
#     query = update.callback_query
#     await query.answer()
#     user_id = query.message.chat.id

#     if user_id not in ADMIN_CHAT_IDS:
#         await query.edit_message_text("Siz admin emassiz.")
#         return

#     con = sqlite3.connect(DB_PATH)
#     cur = con.cursor()

#     if query.data == "today_report":
#         today = datetime.now(pytz.timezone('Asia/Tashkent')).date().isoformat()
#         cur.execute("SELECT * FROM tolovlar WHERE DATE(vaqt) = ?", (today,))
#         rows = cur.fetchall()

#         if not rows:
#             await query.edit_message_text(f"📅 *{today}* kuni hech qanday to‘lov yo‘q.", parse_mode="Markdown")
#             return

#         oy_dict = {}
#         for row in rows:
#             oy = row[4].capitalize()
#             if oy not in oy_dict:
#                 oy_dict[oy] = []
#             oy_dict[oy].append(row)
        
#         for oy, oy_rows in oy_dict.items():
#             filename = f"{oy}_{today}.xlsx"
#             await create_excel(oy_rows, filename)
#             with open(os.path.join("reports", filename), "rb") as f:
#                 await context.bot.send_document(chat_id=user_id, document=InputFile(f, filename))
        
#         await query.edit_message_text(f"📅 Bugungi to‘lovlar Excel fayl tarzida yuborildi.")

#     elif query.data == "oylik_menyu":
#         oylar = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentyabr","Oktyabr","Noyabr","Dekabr"]
#         keyboard = [[InlineKeyboardButton(f"🗓 {oy}", callback_data=f"month_{oy.lower()}")] for oy in oylar]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await query.edit_message_text("Oy bo‘yicha hisobotni tanlang:", reply_markup=reply_markup)

#     elif query.data.startswith("month_"):
#         oy_nomi = query.data.replace("month_", "")
#         cur.execute("SELECT tolov, tolov_turi FROM tolovlar WHERE lower(oy) = ?", (oy_nomi,))
#         rows = cur.fetchall()
#         cur.execute("SELECT summa FROM qoshimcha_summa WHERE lower(oy)=?", (oy_nomi,))
#         extra = cur.fetchone()
#         con.close()

#         qoshimcha = extra[0] if extra else 0

#         if not rows and qoshimcha==0:
#             await query.edit_message_text(f"{oy_nomi.capitalize()} oyi uchun to‘lovlar topilmadi.")
#             return

#         jami_sum = sum(row[0] for row in rows) + qoshimcha
#         naqd_sum = sum(row[0] for row in rows if str(row[1]).lower() == "naqd")
#         karta_sum = sum(row[0] for row in rows if str(row[1]).lower() in ["klik", "click", "karta", "card"])

#         text = (
#             f"🗓 *{oy_nomi.capitalize()}* oyi uchun to‘lovlar:\n\n"
#             f"💵 Naqd: {naqd_sum:,} so‘m\n"
#             f"💳 Karta: {karta_sum:,} so‘m\n"
#             f"➕ Qo‘shimcha summa: {qoshimcha:,} so‘m\n"
#             f"📊 Jami: {jami_sum:,} so‘m"
#         )
#         await query.edit_message_text(text, parse_mode="Markdown")

#         con = sqlite3.connect(DB_PATH)
#         cur = con.cursor()
#         cur.execute("SELECT * FROM tolovlar WHERE lower(oy)=?", (oy_nomi,))
#         oy_rows = cur.fetchall()
#         con.close()
#         if oy_rows:
#             filename = f"{oy_nomi}_tolovlar.xlsx"
#             await create_excel(oy_rows, filename)
#             with open(os.path.join("reports", filename), "rb") as f:
#                 await context.bot.send_document(chat_id=user_id, document=InputFile(f, filename))

#     elif query.data == "add_extra":
#         oylar = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentyabr","Oktyabr","Noyabr","Dekabr"]
#         keyboard = [[InlineKeyboardButton(f"🗓 {oy}", callback_data=f"extra_{oy.lower()}")] for oy in oylar]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await query.edit_message_text("Qo‘shimcha summa kiritiladigan oyni tanlang:", reply_markup=reply_markup)

#     elif query.data.startswith("extra_"):
#         oy_nomi = query.data.replace("extra_", "")
#         user_state[user_id] = {'oy': oy_nomi, 'awaiting': True}
#         await query.message.reply_text(f"{oy_nomi.capitalize()} oyi uchun qo‘shimcha summani kiriting:")

# async def handle_message(update: Update, context: CallbackContext):
#     user_id = update.message.chat.id
#     if user_id in user_state and user_state[user_id].get('awaiting'):
#         try:
#             summa = int(update.message.text.replace(',', '').strip())
#         except:
#             await update.message.reply_text("Iltimos, faqat raqam kiriting.")
#             return

#         oy = user_state[user_id]['oy']
#         con = sqlite3.connect(DB_PATH)
#         cur = con.cursor()
#         cur.execute("SELECT id FROM qoshimcha_summa WHERE lower(oy)=?", (oy,))
#         exist = cur.fetchone()
#         if exist:
#             cur.execute("UPDATE qoshimcha_summa SET summa=? WHERE id=?", (summa, exist[0]))
#         else:
#             cur.execute("INSERT INTO qoshimcha_summa (oy, summa) VALUES (?, ?)", (oy, summa))
#         con.commit()
#         con.close()
#         await update.message.reply_text(f"{oy.capitalize()} oyi uchun qo‘shimcha summa saqlandi: {summa:,} so‘m")
#         user_state[user_id]['awaiting'] = False



import os
import sqlite3
from datetime import datetime, time as dtime, timedelta
import pandas as pd
import pytz
import asyncio
import nest_asyncio
import requests
from flask import Flask, render_template, request, redirect, url_for
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

app = Flask(__name__)

DB_PATH = 'crm.db'
BOT_TOKEN = '8392134768:AAEY2RKIU1SfYEu5077DMHDTPeBNm1BKS1U'
ADMIN_CHAT_IDS = [6855997739, 266123144, 520801616, 6671470759]


# --- DB Init ---
def init_db():
    if not os.path.exists(DB_PATH):
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE tolovlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ismi TEXT NOT NULL,
                tolov INTEGER NOT NULL,
                kurs TEXT NOT NULL,
                oy TEXT NOT NULL,
                izoh TEXT,
                admin TEXT NOT NULL,
                oqituvchi TEXT NOT NULL,
                vaqt TEXT NOT NULL,
                tolov_turi TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE qoshimcha_summa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oy TEXT NOT NULL,
                summa INTEGER NOT NULL
            )
        ''')
        con.commit()
        con.close()
init_db()


# --- Flask qismi ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ismi = request.form['ismi']
        tolov = int(request.form['tolov'])
        if tolov < 1000:
            tolov *= 1000
        kurs = request.form['kurs']
        oy = request.form['oy']
        izoh = request.form.get('izoh', '')
        admin = request.form['admin']
        oqituvchi = request.form['oqituvchi']
        tolov_turi = request.form['tolov_turi']
        vaqt = datetime.now(pytz.timezone('Asia/Tashkent')).strftime('%Y-%m-%d %H:%M:%S')

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute('''
            INSERT INTO tolovlar (ismi, tolov, kurs, oy, izoh, admin, oqituvchi, vaqt, tolov_turi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ismi, tolov, kurs, oy, izoh, admin, oqituvchi, vaqt, tolov_turi))
        con.commit()
        con.close()

        message = (
            f"💳 *Yangi to‘lov kiritildi!*\n\n"
            f"👤 Ismi: {ismi}\n"
            f"💰 To‘lov: {tolov} so‘m\n"
            f"📚 Kurs: {kurs} ({oy} oyi)\n"
            f"💳 To‘lov turi: {tolov_turi}\n"
            f"👨‍🏫 O‘qituvchi: {oqituvchi}\n"
            f"🛠 Admin: {admin}\n"
            f"💬 Izoh: {izoh or 'Yo‘q'}\n"
            f"🕒 Sana: {vaqt}"
        )

        for admin_id in ADMIN_CHAT_IDS:
            try:
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        "chat_id": admin_id,
                        "text": message,
                        "parse_mode": "Markdown"
                    }
                )
            except Exception as e:
                print(f"Xabar yuborishda xatolik: {e}")

        return redirect(url_for('index'))

    today = datetime.now(pytz.timezone('Asia/Tashkent')).strftime('%Y-%m-%d')
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''
        SELECT ismi, tolov, kurs, oy, izoh, admin, oqituvchi, vaqt, tolov_turi
        FROM tolovlar
        WHERE date(vaqt) = ?
        ORDER BY vaqt DESC
    ''', (today,))
    tolovlar = cur.fetchall()
    con.close()
    return render_template('index.html', tolovlar=tolovlar)


# --- Telegram qismi ---
user_state = {}


async def start(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    if user_id not in ADMIN_CHAT_IDS:
        await update.message.reply_text("Siz admin emassiz.")
        return
    keyboard = [
        [InlineKeyboardButton("📅 Bugungi to‘lovlar", callback_data="today_report")],
        [InlineKeyboardButton("📊 Oylik to‘lovlar", callback_data="oylik_menyu")],
        [InlineKeyboardButton("➕ Qo‘shimcha summa", callback_data="add_extra")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Xush kelibsiz, admin! Tanlang:", reply_markup=reply_markup)


async def create_excel(rows, filename):
    df = pd.DataFrame(
        rows,
        columns=[
            'ID', 'Ismi', 'To‘lov', 'Kurs', 'Oy',
            'Izoh', 'Admin', 'O‘qituvchi', 'Vaqt', 'Tolov turi'
        ]
    )
    os.makedirs("reports", exist_ok=True)

    jami_sum = df['To‘lov'].sum()
    klik_sum = df.loc[
        df['Tolov turi'].str.lower().isin(['klik', 'click', 'karta', 'card']),
        'To‘lov'
    ].sum()
    naqd_sum = df.loc[
        df['Tolov turi'].str.lower().isin(['naqd']),
        'To‘lov'
    ].sum()

    df.loc[len(df.index)] = ['', '', '', '', '', '', '', '', '', '']
    df.loc[len(df.index)] = ['', '📊 Jami', f"{jami_sum:,} so‘m", '', '', '', '', '', '', '']
    df.loc[len(df.index)] = ['', '💳 Klik', f"{klik_sum:,} so‘m", '', '', '', '', '', '', '']
    df.loc[len(df.index)] = ['', '💵 Naqd', f"{naqd_sum:,} so‘m", '', '', '', '', '', '', '']

    df.to_excel(os.path.join("reports", filename), index=False)


async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.message.chat.id

    if user_id not in ADMIN_CHAT_IDS:
        await query.edit_message_text("Siz admin emassiz.")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    if query.data == "today_report":
        today = datetime.now(pytz.timezone('Asia/Tashkent')).date().isoformat()
        cur.execute("SELECT * FROM tolovlar WHERE DATE(vaqt) = ?", (today,))
        rows = cur.fetchall()

        if not rows:
            await query.edit_message_text(f"📅 *{today}* kuni hech qanday to‘lov yo‘q.", parse_mode="Markdown")
            return

        oy_dict = {}
        for row in rows:
            oy = row[4].capitalize()
            if oy not in oy_dict:
                oy_dict[oy] = []
            oy_dict[oy].append(row)

        for oy, oy_rows in oy_dict.items():
            filename = f"{oy}_{today}.xlsx"
            await create_excel(oy_rows, filename)
            with open(os.path.join("reports", filename), "rb") as f:
                await context.bot.send_document(chat_id=user_id, document=InputFile(f, filename))

        await query.edit_message_text(f"📅 Bugungi to‘lovlar Excel fayl tarzida yuborildi.")

    elif query.data == "oylik_menyu":
        oylar = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentyabr","Oktyabr","Noyabr","Dekabr"]
        keyboard = [[InlineKeyboardButton(f"🗓 {oy}", callback_data=f"month_{oy.lower()}")] for oy in oylar]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Oy bo‘yicha hisobotni tanlang:", reply_markup=reply_markup)

    elif query.data.startswith("month_"):
        oy_nomi = query.data.replace("month_", "")
        cur.execute("SELECT tolov, tolov_turi FROM tolovlar WHERE lower(oy) = ?", (oy_nomi,))
        rows = cur.fetchall()
        cur.execute("SELECT summa FROM qoshimcha_summa WHERE lower(oy)=?", (oy_nomi,))
        extra = cur.fetchone()
        con.close()

        qoshimcha = extra[0] if extra else 0

        if not rows and qoshimcha==0:
            await query.edit_message_text(f"{oy_nomi.capitalize()} oyi uchun to‘lovlar topilmadi.")
            return

        jami_sum = sum(row[0] for row in rows) + qoshimcha
        naqd_sum = sum(row[0] for row in rows if str(row[1]).lower() == "naqd")
        karta_sum = sum(row[0] for row in rows if str(row[1]).lower() in ["klik", "click", "karta", "card"])

        text = (
            f"🗓 *{oy_nomi.capitalize()}* oyi uchun to‘lovlar:\n\n"
            f"💵 Naqd: {naqd_sum:,} so‘m\n"
            f"💳 Karta: {karta_sum:,} so‘m\n"
            f"➕ Qo‘shimcha summa: {qoshimcha:,} so‘m\n"
            f"📊 Jami: {jami_sum:,} so‘m"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT * FROM tolovlar WHERE lower(oy)=?", (oy_nomi,))
        oy_rows = cur.fetchall()
        con.close()
        if oy_rows:
            filename = f"{oy_nomi}_tolovlar.xlsx"
            await create_excel(oy_rows, filename)
            with open(os.path.join("reports", filename), "rb") as f:
                await context.bot.send_document(chat_id=user_id, document=InputFile(f, filename))

    elif query.data == "add_extra":
        oylar = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentyabr","Oktyabr","Noyabr","Dekabr"]
        keyboard = [[InlineKeyboardButton(f"🗓 {oy}", callback_data=f"extra_{oy.lower()}")] for oy in oylar]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Qo‘shimcha summa kiritiladigan oyni tanlang:", reply_markup=reply_markup)

    elif query.data.startswith("extra_"):
        oy_nomi = query.data.replace("extra_", "")
        user_state[user_id] = {'oy': oy_nomi, 'awaiting': True}
        await query.message.reply_text(f"{oy_nomi.capitalize()} oyi uchun qo‘shimcha summani kiriting:")


async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat.id
    if user_id in user_state and user_state[user_id].get('awaiting'):
        try:
            summa = int(update.message.text.replace(',', '').strip())
        except:
            await update.message.reply_text("Iltimos, faqat raqam kiriting.")
            return

        oy = user_state[user_id]['oy']
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id FROM qoshimcha_summa WHERE lower(oy)=?", (oy,))
        exist = cur.fetchone()
        if exist:
            cur.execute("UPDATE qoshimcha_summa SET summa=? WHERE id=?", (summa, exist[0]))
        else:
            cur.execute("INSERT INTO qoshimcha_summa (oy, summa) VALUES (?, ?)", (oy, summa))
        con.commit()
        con.close()
        await update.message.reply_text(f"{oy.capitalize()} oyi uchun qo‘shimcha summa saqlandi: {summa:,} so‘m")
        user_state[user_id]['awaiting'] = False


# ✅ YANGI FUNKSIYA: Avtomatik 23:59 da bugungi to‘lovlarni yuboradi
async def auto_daily_report(context: CallbackContext):
    tz = pytz.timezone("Asia/Tashkent")
    today = datetime.now(tz).date().isoformat()

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * FROM tolovlar WHERE DATE(vaqt) = ?", (today,))
    rows = cur.fetchall()
    con.close()

    if not rows:
        print("Bugungi to‘lovlar yo‘q.")
        return

    oy_dict = {}
    for row in rows:
        oy = row[4].capitalize()
        if oy not in oy_dict:
            oy_dict[oy] = []
        oy_dict[oy].append(row)

    for oy, oy_rows in oy_dict.items():
        filename = f"{oy}_{today}.xlsx"
        await create_excel(oy_rows, filename)
        for admin_id in ADMIN_CHAT_IDS:
            with open(os.path.join("reports", filename), "rb") as f:
                await context.bot.send_document(chat_id=admin_id, document=InputFile(f, filename))
    print(f"✅ {today} uchun avtomatik hisobot yuborildi.")


async def schedule_daily_task(app_bot: Application):
    while True:
        now = datetime.now(pytz.timezone('Asia/Tashkent'))
        target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)
        sleep_time = (target - now).total_seconds()
        await asyncio.sleep(sleep_time)
        await auto_daily_report(app_bot)


async def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot ishga tushdi.")

    # 🔁 Har kech soat 23:59 da avtomatik hisobot
    asyncio.create_task(schedule_daily_task(app_bot))

    await app_bot.run_polling()


if __name__ == '__main__':
    import threading
    nest_asyncio.apply()
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()
    asyncio.run(run_bot())


# async def run_bot():
#     app_bot = Application.builder().token(BOT_TOKEN).build()
#     app_bot.add_handler(CommandHandler("start", start))
#     app_bot.add_handler(CallbackQueryHandler(handle_callback))
#     app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
#     print("✅ Bot ishga tushdi.")
#     await app_bot.run_polling()

# if __name__ == '__main__':
#     import threading
#     nest_asyncio.apply()
#     threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()
#     asyncio.run(run_bot())
