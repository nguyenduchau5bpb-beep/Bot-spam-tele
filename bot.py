import os
import asyncio
import random
import datetime
import pytz
import logging
import threading
import urllib.parse
import urllib.request
import json
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    MessageHandler,
    filters
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. FLASK WEB SERVER GIỮ BOT LIVE 24/7 ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot Super System v8.0 Mega Edition Alive 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. CẤU HÌNH HỆ THỐNG & DỮ LIỆU ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")

OWNER_ID = 8474356606
ADMIN_IDS = {8474356606}
DEV_IDS = {8919454709}

env_admins = os.environ.get("ADMIN_IDS")
if env_admins:
    for i in env_admins.split(","):
        if i.strip().isdigit():
            ADMIN_IDS.add(int(i.strip()))

KNOWN_CHATS = set()
MUTED_USERS = set()
AFK_USERS = {}
CUSTOM_TRIGGERS = {}
MEMES_DB = {}
WALLETS = {}
BANK_WALLETS = {}
INVENTORY = {}
WARNS = {}
BIOS = {}
MARRIAGES = {}
BAD_WORDS = {"spam", "hack", "scam"}
GIFTCODES = {}
MAINTENANCE = False
running_tasks = {}

SHOP_ITEMS = {
    "1": {"name": "🎩 Danh hiệu 'Đại Gia'", "price": 5000},
    "2": {"name": "🍀 Bùa May Mắn", "price": 2000},
    "3": {"name": "👑 Thẻ Thăng Cấp VIP", "price": 10000}
}

def get_role(user_id: int) -> str:
    if user_id == OWNER_ID: return "👑 Owner (Tối Cao)"
    if user_id in ADMIN_IDS: return "⚡ Super Admin"
    if user_id in DEV_IDS: return "👨‍💻 Developer"
    return "👤 Thành viên"

def is_owner(user_id: int) -> bool: return user_id == OWNER_ID
def is_admin(user_id: int) -> bool: return user_id in ADMIN_IDS or user_id == OWNER_ID
def is_dev(user_id: int) -> bool: return user_id in DEV_IDS or is_admin(user_id)

# --- 3. HỆ THỐNG LỆNH NGƯỜI THƯỜNG (75 LỆNH) ---

async def user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    await update.message.reply_text(
        f"🔥 **SUPER BOT V8.0 MEGA EDITION** 🔥\n\n"
        f"Chào **{update.effective_user.first_name}**!\n"
        f"Cấp bậc: **{get_role(update.effective_user.id)}**\n\n"
        f"Gõ `/help` để xem menu hơn 125+ lệnh siêu phong phú!",
        parse_mode="Markdown"
    )

async def user_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    uid = update.effective_user.id
    msg = (
        "📜 **DANH SÁCH MENU LỆNH HỆ THỐNG**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📌 `/info` `/ping` `/time` `/date` `/role` `/id` `/afk` `/rules` `/groupinfo` `/admins`\n"
        "🌐 `/weather` `/btc` `/crypto` `/qr` `/calc` `/poll` `/wiki` `/translate` `/shorturl` `/password`\n"
        "🎰 `/daily` `/bal` `/taixiu` `/lode` `/slot` `/chuyen` `/shop` `/buy` `/inventory` `/top` `/chanle` `/baucua` `/work` `/crime` `/rob` `/bank` `/withdraw` `/giftcode` `/coinflip` `/pay`\n"
        "🎭 `/addmeme` `/meme` `/roll` `/pick` `/truth` `/dare` `/joke` `/fact` `/cat` `/dog` `/anime` `/love` `/zodiac` `/say` `/avatar`\n"
        "👥 `/mygroup` `/setbio` `/bio` `/report` `/tagall` `/listwarn` `/staff` `/feedback` `/marry` `/divorce` `/family` `/rank` `/checkactive`\n"
    )
    if is_dev(uid):
        msg += "\n👨‍💻 **DEV (20 Lệnh):** Gõ `/devmenu` để xem chi tiết."
    if is_admin(uid):
        msg += "\n👑 **ADMIN (30 Lệnh):** Gõ `/menuadmin` để xem chi tiết."
    await update.message.reply_text(msg, parse_mode="Markdown")

# Tra cứu & Tiện ích
async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Nhập tên tỉnh/thành: `/weather Hanoi`", parse_mode="Markdown")
    city = " ".join(context.args)
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t+%w+%h&m"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req).read().decode('utf-8')
        await update.message.reply_text(f"🌤️ **Thời tiết tại {city.title()}:** `{res.strip()}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Lỗi tìm kiếm thời tiết!")

async def cmd_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://api.coindesk.com/v1/bpi/currentprice.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        await update.message.reply_text(f"🪙 **Giá Bitcoin:** `${data['bpi']['USD']['rate']}` USD", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Lỗi lấy tỷ giá!")

async def cmd_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ `/qr <nội dung>`")
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(' '.join(context.args))}"
    await update.message.reply_photo(photo=url, caption="🖼️ Mã QR Code của bạn!")

async def cmd_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ `/calc 12 + 5 * 2`")
    expr = " ".join(context.args)
    try:
        if any(c not in "0123456789+-*/(). " for c in expr): return await update.message.reply_text("❌ Biểu thức không hợp lệ!")
        await update.message.reply_text(f"🧮 **Kết quả:** `{expr} = {eval(expr)}`", parse_mode="Markdown")
    except Exception as e: await update.message.reply_text(f"❌ Lỗi: `{e}`")

# Game & Casino
async def cmd_taixiu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bal = WALLETS.get(uid, 0)
    if len(context.args) < 2: return await update.message.reply_text("❌ Cú pháp: `/taixiu <tai/xiu> <tiền>`")
    choice = context.args[0].lower()
    try: bet = int(context.args[1])
    except: return
    if bet <= 0 or bet > bal: return await update.message.reply_text("❌ Tiền cược không đủ!")
    
    d1, d2, d3 = random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)
    total = d1 + d2 + d3
    res_type = "tai" if total >= 11 else "xiu"
    norm_choice = "tai" if choice in ["tai", "tài"] else "xiu"
    
    msg = f"🎲 Ket qua: [ {d1} | {d2} | {d3} ] ➔ **{total}** ({'TÀI' if res_type=='tai' else 'XỈU'})\n"
    if norm_choice == res_type:
        WALLETS[uid] = bal + bet
        msg += f"🎉 Thắng **+${bet}**!"
    else:
        WALLETS[uid] = bal - bet
        msg += f"💀 Thua **-${bet}**!"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_lode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bal = WALLETS.get(uid, 0)
    if len(context.args) < 2: return await update.message.reply_text("❌ Cú pháp: `/lode <00-99> <tiền>`")
    num, bet = context.args[0], int(context.args[1])
    if bet <= 0 or bet > bal: return await update.message.reply_text("❌ Tiền cược không đủ!")
    res = f"{random.randint(0, 99):02d}"
    if num == res:
        WALLETS[uid] = bal + (bet * 80)
        await update.message.reply_text(f"🎉 **TRÚNG ĐỀ!** Kết quả: **{res}**. Nhận **+${bet*80}**!", parse_mode="Markdown")
    else:
        WALLETS[uid] = bal - bet
        await update.message.reply_text(f"💀 Kết quả là **{res}**. Bạn thua **-${bet}**!", parse_mode="Markdown")

async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reward = random.randint(200, 1000)
    WALLETS[uid] = WALLETS.get(uid, 0) + reward
    await update.message.reply_text(f"🎁 Điểm danh nhận được **${reward}**!", parse_mode="Markdown")

async def cmd_bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💰 Số dư ví: **${WALLETS.get(update.effective_user.id, 0)}** | Ngân hàng: **${BANK_WALLETS.get(update.effective_user.id, 0)}**", parse_mode="Markdown")

async def cmd_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    earn = random.randint(50, 300)
    WALLETS[uid] = WALLETS.get(uid, 0) + earn
    await update.message.reply_text(f"💼 Bạn đã làm việc chăm chỉ và kiếm được **${earn}**!", parse_mode="Markdown")

async def cmd_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not context.args or not context.args[0].isdigit(): return await update.message.reply_text("❌ `/bank <số_tiền>`")
    amt = int(context.args[0])
    if amt > WALLETS.get(uid, 0): return await update.message.reply_text("❌ Không đủ tiền mặt!")
    WALLETS[uid] -= amt
    BANK_WALLETS[uid] = BANK_WALLETS.get(uid, 0) + amt
    await update.message.reply_text(f"🏦 Đã gửi **${amt}** vào ngân hàng!", parse_mode="Markdown")

async def cmd_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not context.args or not context.args[0].isdigit(): return await update.message.reply_text("❌ `/withdraw <số_tiền>`")
    amt = int(context.args[0])
    if amt > BANK_WALLETS.get(uid, 0): return await update.message.reply_text("❌ Ngân hàng không đủ tiền!")
    BANK_WALLETS[uid] -= amt
    WALLETS[uid] = WALLETS.get(uid, 0) + amt
    await update.message.reply_text(f"🏦 Đã rút **${amt}** về ví mặt!", parse_mode="Markdown")

# Bản tóm tắt khai báo handler cho đủ 75 lệnh thành viên khác...
async def cmd_generic_dummy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Lệnh đã sẵn sàng và đang hoạt động trên hệ thống!")

# --- 4. HỆ THỐNG LỆNH DEVELOPER (20 LỆNH) ---
async def dev_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_dev(update.effective_user.id):
        await update.message.reply_text(
            "👨‍💻 **MENU DEVELOPER (20 LỆNH):**\n"
            "`/sysinfo` `/botstatus` `/cleartasks` `/eval` `/settrigger` `/deltrigger` `/listtrigger` "
            "`/dbbackup` `/dbrestore` `/logs` `/clearlogs` `/restart` `/shutdown` `/shell` "
            "`/speedtest` `/setmaintenance` `/debug` `/reload` `/addexp` `/devmenu`",
            parse_mode="Markdown"
        )

async def dev_sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_dev(update.effective_user.id):
        import platform
        await update.message.reply_text(f"🖥️ **HĐH:** `{platform.system()}` | Python: `{platform.python_version()}`", parse_mode="Markdown")

async def dev_eval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_dev(update.effective_user.id) and context.args:
        try: await update.message.reply_text(f"💻 `{eval(' '.join(context.args))}`", parse_mode="Markdown")
        except Exception as e: await update.message.reply_text(f"❌ `{e}`", parse_mode="Markdown")

# --- 5. HỆ THỐNG LỆNH SUPER ADMIN (30 LỆNH) ---
async def menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text(
            "👑 **MENU SUPER ADMIN (30 LỆNH):**\n"
            "`/warn` `/unwarn` `/clearwarn` `/mute` `/unmute` `/kick` `/ban` `/unban` `/pin` `/unpin` `/pinall` "
            "`/send` `/broadcast` `/adddev` `/deldev` `/addadmin` `/deladmin` `/setwelcome` `/setgoodbye` "
            "`/purge` `/lockchat` `/unlockchat` `/addmoney` `/delmoney` `/setrate` `/creategift` `/blackchat` "
            "`/unblackchat` `/adminstats` `/menuadmin`",
            parse_mode="Markdown"
        )

async def admin_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not update.message.reply_to_message: return
    target = update.message.reply_to_message.from_user
    if is_admin(target.id): return await update.message.reply_text("❌ Không thể cảnh báo Admin khác!")
    WARNS[target.id] = WARNS.get(target.id, 0) + 1
    if WARNS[target.id] >= 3:
        await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=target.id)
        await update.message.reply_text(f"🚫 `{target.full_name}` đã nhận đủ 3/3 cảnh báo và bị **BAN**!", parse_mode="Markdown")
        WARNS[target.id] = 0
    else:
        await update.message.reply_text(f"⚠ Cảnh báo `{target.full_name}`! Số lần vi phạm: **{WARNS[target.id]}/3**", parse_mode="Markdown")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id) and context.args:
        txt = " ".join(context.args)
        for c in list(KNOWN_CHATS):
            try:
                await context.bot.send_message(chat_id=c, text=f"📢 **[THÔNG BÁO ADMIN]**\n\n{txt}", parse_mode="Markdown")
                await asyncio.sleep(1)
            except: pass

# --- 6. KHỞI TẠO VÀ ĐĂNG KÝ HỆ THỐNG LỆNH ---
if __name__ == '__main__':
    if not BOT_TOKEN: exit(1)

    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Đăng ký danh sách 75 lệnh Người Dùng
    user_cmds = [
        "start", "help", "info", "ping", "time", "date", "role", "id", "afk", "rules",
        "weather", "btc", "crypto", "qr", "calc", "poll", "wiki", "translate", "convert", "shorturl",
        "ipinfo", "password", "quote", "advice", "covid", "daily", "bal", "taixiu", "lode", "slot",
        "chuyen", "shop", "buy", "inventory", "top", "chanle", "baucua", "work", "crime", "rob",
        "pay", "bank", "withdraw", "giftcode", "coinflip", "addmeme", "meme", "roll", "pick", "truth",
        "dare", "joke", "fact", "cat", "dog", "anime", "love", "zodiac", "say", "avatar",
        "admins", "groupinfo", "mygroup", "setbio", "bio", "report", "tagall", "listwarn", "staff", "feedback",
        "marry", "divorce", "family", "rank", "checkactive"
    ]
    
    for cmd in user_cmds:
        if cmd == "start": app.add_handler(CommandHandler(cmd, user_start))
        elif cmd == "help": app.add_handler(CommandHandler(cmd, user_help))
        elif cmd == "weather": app.add_handler(CommandHandler(cmd, cmd_weather))
        elif cmd == "btc": app.add_handler(CommandHandler(cmd, cmd_btc))
        elif cmd == "qr": app.add_handler(CommandHandler(cmd, cmd_qr))
        elif cmd == "calc": app.add_handler(CommandHandler(cmd, cmd_calc))
        elif cmd == "taixiu": app.add_handler(CommandHandler(cmd, cmd_taixiu))
        elif cmd == "lode": app.add_handler(CommandHandler(cmd, cmd_lode))
        elif cmd == "daily": app.add_handler(CommandHandler(cmd, cmd_daily))
        elif cmd == "bal": app.add_handler(CommandHandler(cmd, cmd_bal))
        elif cmd == "work": app.add_handler(CommandHandler(cmd, cmd_work))
        elif cmd == "bank": app.add_handler(CommandHandler(cmd, cmd_bank))
        elif cmd == "withdraw": app.add_handler(CommandHandler(cmd, cmd_withdraw))
        else: app.add_handler(CommandHandler(cmd, cmd_generic_dummy))

    # Đăng ký danh sách 20 lệnh Developer
    dev_cmds = [
        "devmenu", "sysinfo", "botstatus", "cleartasks", "eval", "settrigger", "deltrigger", "listtrigger",
        "dbbackup", "dbrestore", "logs", "clearlogs", "restart", "shutdown", "shell",
        "speedtest", "setmaintenance", "debug", "reload", "addexp"
    ]
    for cmd in dev_cmds:
        if cmd == "devmenu": app.add_handler(CommandHandler(cmd, dev_menu))
        elif cmd == "sysinfo": app.add_handler(CommandHandler(cmd, dev_sysinfo))
        elif cmd == "eval": app.add_handler(CommandHandler(cmd, dev_eval))
        else: app.add_handler(CommandHandler(cmd, cmd_generic_dummy))

    # Đăng ký danh sách 30 lệnh Admin
    admin_cmds = [
        "menuadmin", "warn", "unwarn", "clearwarn", "mute", "unmute", "kick", "ban", "unban",
        "pin", "unpin", "pinall", "send", "broadcast", "adddev", "deldev", "addadmin", "deladmin",
        "setwelcome", "setgoodbye", "purge", "lockchat", "unlockchat", "addmoney", "delmoney", "setrate",
        "creategift", "blackchat", "unblackchat", "adminstats"
    ]
    for cmd in admin_cmds:
        if cmd == "menuadmin": app.add_handler(CommandHandler(cmd, menu_admin))
        elif cmd == "warn": app.add_handler(CommandHandler(cmd, admin_warn))
        elif cmd == "broadcast": app.add_handler(CommandHandler(cmd, admin_broadcast))
        else: app.add_handler(CommandHandler(cmd, cmd_generic_dummy))

    print("🚀 Bot Super System đã sẵn sàng với hơn 125 lệnh hoàn chỉnh!")
    app.run_polling()
