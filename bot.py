import os
import asyncio
import random
import datetime
import pytz
import logging
import threading
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

# --- 1. FLASK WEB SERVER GIỮ RENDER LIVE ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot Telegram 24/7 đang hoạt động bình thường!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. CẤU HÌNH PHÂN QUYỀN ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")

OWNER_ID = 8474356606
ADMIN_IDS = {8474356606}
DEV_IDS = {8919454709}

# Đọc thêm từ biến môi trường nếu có
env_admins = os.environ.get("ADMIN_IDS")
if env_admins:
    for i in env_admins.split(","):
        if i.strip().isdigit():
            ADMIN_IDS.add(int(i.strip()))

KNOWN_CHATS = set()
MUTED_USERS = set()
AFK_USERS = {}
CUSTOM_TRIGGERS = {}
running_tasks = {}

def get_role(user_id: int) -> str:
    if user_id == OWNER_ID: return "Owner"
    if user_id in ADMIN_IDS: return "Admin"
    if user_id in DEV_IDS: return "Developer"
    return "Member"

def is_dev(user_id: int) -> bool:
    return user_id in DEV_IDS or user_id in ADMIN_IDS or user_id == OWNER_ID

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id == OWNER_ID

# --- 3. BỘ 20+ LỆNH THÀNH VIÊN (PUBLIC COMMANDS) ---

async def user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    role = get_role(update.effective_user.id)
    await update.message.reply_text(
        f"👋 Xin chào **{update.effective_user.first_name}**!\n"
        f"🎭 Quyền hạn của bạn: **{role}**\n"
        f"Gõ `/help` để xem danh sách 50+ lệnh tiện ích và quản trị!",
        parse_mode="Markdown"
    )

async def user_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    help_text = (
        "🤖 **DANH SÁCH BỘ LỆNH CỦA BOT**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "👥 **THÀNH VIÊN (20 Lệnh):**\n"
        "• `/start` | `/help` | `/info [-id]` | `/ping` | `/time` | `/date` | `/uptime` | `/role`\n"
        "• `/roll [mốc]` | `/flip` | `/choice <a|b>` | `/rate <tên>` | `/8ball <câu hỏi>`\n"
        "• `/say <chữ>` | `/echo <chữ>` | `/reverse <chữ>` | `/length <chữ>` | `/capital <chữ>`\n"
        "• `/afk [lý do]` | `/id` | `/myid` | `/chatid` | `/avatar` | `/rules` | `/about`\n\n"
        "👨‍💻 **DEVELOPER (15 Lệnh Dev):**\n"
        "• `/devmenu` | `/sysinfo` | `/botstatus` | `/test` | `/debug` | `/pingdev`\n"
        "• `/logs` | `/cleartasks` | `/simerror` | `/eval <code_test>` | `/echojson` | `/getip`\n"
        "• `/settrigger <từ> <đáp>` | `/deltrigger <từ>` | `/listtrigger`\n\n"
        "👑 **ADMIN & OWNER (20+ Lệnh Admin):**\n"
        "• `/menuadmin` | `/send [-anon]` | `/burst [-delay=X]` | `/schedule` | `/broadcast`\n"
        "• `/mute` | `/unmute` | `/kick` | `/ban` | `/unban` | `/pin` | `/unpin` | `/title`\n"
        "• `/clear <số>` | `/slowmode <giây>` | `/addadmin` | `/deladmin` | `/adddev` | `/deldev`"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    if "-id" in context.args:
        return await update.message.reply_text(f"🆔 ID: `{target.id}`", parse_mode="Markdown")
    
    text = (
        f"📋 **INFO USER**\n"
        f"• ID: `{target.id}`\n"
        f"• Name: {target.full_name}\n"
        f"• Username: @{target.username if target.username else 'N/A'}\n"
        f"• Chức vụ Bot: `{get_role(target.id)}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = datetime.datetime.now()
    msg = await update.message.reply_text("🏓 Ping...")
    lat = (datetime.datetime.now() - start).microseconds / 1000
    await msg.edit_text(f"🏓 **Pong!** Độ trễ: `{lat:.2f}ms`", parse_mode="Markdown")

async def cmd_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    await update.message.reply_text(f"🕒 **Giờ VN:** `{datetime.datetime.now(tz).strftime('%H:%M:%S')}`", parse_mode="Markdown")

async def cmd_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    await update.message.reply_text(f"📅 **Ngày VN:** `{datetime.datetime.now(tz).strftime('%d/%m/%Y')}`", parse_mode="Markdown")

async def cmd_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = int(context.args[0]) if context.args and context.args[0].isdigit() else 100
    await update.message.reply_text(f"🎲 Số ngẫu nhiên: `{random.randint(1, m)}`", parse_mode="Markdown")

async def cmd_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🪙 Kết quả: {random.choice(['MẶT SẤP', 'MẶT NGỬA'])}")

async def cmd_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("❌ Nhập các lựa chọn cách nhau bởi khoảng trắng!")
    await update.message.reply_text(f"🎯 Bot chọn: **{random.choice(context.args)}**", parse_mode="Markdown")

async def cmd_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = " ".join(context.args) if context.args else "Bạn"
    await update.message.reply_text(f"📊 Đánh giá **{name}**: `{random.randint(0, 100)}/100` điểm!", parse_mode="Markdown")

async def cmd_8ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = ["Chắc chắn rồi", "Có vẻ đúng", "Không thể biết được", "Chắc chắn không", "Thử hỏi lại sau đi"]
    await update.message.reply_text(f"🔮 **8-Ball:** {random.choice(ans)}")

async def cmd_say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: await update.message.reply_text(" ".join(context.args))

async def cmd_reverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: await update.message.reply_text(" ".join(context.args)[::-1])

async def cmd_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: 
        t = " ".join(context.args)
        await update.message.reply_text(f"📏 Độ dài văn bản: `{len(t)}` ký tự.", parse_mode="Markdown")

async def cmd_capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: await update.message.reply_text(" ".join(context.args).upper())

async def cmd_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = " ".join(context.args) if context.args else "Đang bận"
    AFK_USERS[update.effective_user.id] = reason
    await update.message.reply_text(f"💤 **{update.effective_user.first_name}** đã bật AFK: {reason}", parse_mode="Markdown")

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 User ID: `{update.effective_user.id}` | Chat ID: `{update.effective_chat.id}`", parse_mode="Markdown")

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📜 **NỘI QUY:** Không spam, tôn trọng thành viên, tuân thủ Admin!", parse_mode="Markdown")

async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 **Bot Multi-Tool Pro v3.0**\nChạy trên Render 24/7 với Python 3.11!", parse_mode="Markdown")

async def cmd_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🎭 Quyền hiện tại của bạn: **{get_role(update.effective_user.id)}**", parse_mode="Markdown")

# --- 4. BỘ 15 LỆNH DEVELOPER (DÀNH CHO DEV & ADMIN) ---

async def dev_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id): return
    await update.message.reply_text(
        "🛠️ **DEV DASHBOARD**\n"
        "• `/sysinfo` - Cấu hình hệ thống\n"
        "• `/botstatus` - Trạng thái tác vụ\n"
        "• `/cleartasks` - Xóa sạch tác vụ chạy ngầm\n"
        "• `/settrigger <từ> <đáp>` - Tạo reply tự động\n"
        "• `/deltrigger <từ>` - Xóa reply tự động\n"
        "• `/listtrigger` - Danh sách reply tự động\n"
        "• `/eval <code_python>` - Chạy thử code ngầm",
        parse_mode="Markdown"
    )

async def dev_sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id): return
    import platform
    text = f"🖥️ **HỆ THỐNG:** OS: `{platform.system()}` | Python: `{platform.python_version()}`"
    await update.message.reply_text(text, parse_mode="Markdown")

async def dev_botstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id): return
    await update.message.reply_text(f"⚙️ Tác vụ ngầm đang chạy: `{len(running_tasks)}`", parse_mode="Markdown")

async def dev_cleartasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id): return
    running_tasks.clear()
    await update.message.reply_text("🧹 Đã dọn sạch mọi tác vụ ngầm đang chạy!")

async def dev_settrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id) or len(context.args) < 2: 
        return await update.message.reply_text("❌ Cú pháp: `/settrigger <từ_khóa> <câu_trả_lời>`", parse_mode="Markdown")
    key = context.args[0].lower()
    val = " ".join(context.args[1:])
    CUSTOM_TRIGGERS[key] = val
    await update.message.reply_text(f"✅ Đã thêm auto-reply cho từ: `{key}`", parse_mode="Markdown")

async def dev_deltrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id) or not context.args: return
    key = context.args[0].lower()
    if key in CUSTOM_TRIGGERS:
        del CUSTOM_TRIGGERS[key]
        await update.message.reply_text(f"🗑️ Đã xóa trigger: `{key}`", parse_mode="Markdown")

async def dev_listtrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id): return
    if not CUSTOM_TRIGGERS: return await update.message.reply_text("ℹ️ Chưa có trigger tự động nào.")
    txt = "📝 **LIST TRIGGERS:**\n" + "\n".join([f"• `{k}` ➔ {v}" for k, v in CUSTOM_TRIGGERS.items()])
    await update.message.reply_text(txt, parse_mode="Markdown")

async def dev_eval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_dev(update.effective_user.id) or not context.args: return
    try:
        res = eval(" ".join(context.args))
        await update.message.reply_text(f"💻 **Kết quả Eval:** `{res}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ **Lỗi Eval:** `{e}`", parse_mode="Markdown")

# --- 5. BỘ 20+ LỆNH ADMIN & OWNER ---

async def menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return await update.message.reply_text("⛔ Quyền Admin bị từ chối!")
    
    keyboard = [
        [InlineKeyboardButton("🚀 Gửi tin", callback_data="g_send"), InlineKeyboardButton("💥 Burst", callback_data="g_burst")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="g_bc"), InlineKeyboardButton("📊 Thống kê", callback_data="g_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    txt = (
        f"👑 **BẢNG ĐIỀU KHIỂN QUẢN TRỊ VIÊN**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Admin: **{update.effective_user.first_name}** | Quyền: **{get_role(update.effective_user.id)}**\n\n"
        f"⚙️ **CÁC LỆNH ADMIN CHÍNH:**\n"
        f"• `/send [-anon] <nội dung>`\n"
        f"• `/burst [-delay=X] <số lần> <nội dung>`\n"
        f"• `/broadcast <nội dung>`\n"
        f"• `/mute` | `/unmute` | `/kick` | `/ban` | `/unban`\n"
        f"• `/pin` | `/unpin` | `/clear <số_tin>`\n"
        f"• `/adddev <ID>` | `/deldev <ID>` | `/addadmin <ID>` | `/deladmin <ID>`"
    )
    await update.message.reply_text(txt, reply_markup=reply_markup, parse_mode="Markdown")

async def admin_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not context.args: return
    args = list(context.args)
    if "-anon" in args:
        args.remove("-anon")
        try: await update.message.delete()
        except: pass
    await context.bot.send_message(chat_id=update.effective_chat.id, text=" ".join(args))

async def admin_burst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or len(context.args) < 2: return
    chat_id = update.effective_chat.id
    args = list(context.args)
    delay = 3
    for a in list(args):
        if a.startswith("-delay="):
            try:
                delay = float(a.split("=")[1])
                args.remove(a)
            except: pass

    try:
        count = int(args[0])
        text = " ".join(args[1:])
        msg = await update.message.reply_text(f"⏳ Đang gửi {count} tin nhắn...")
        
        async def run():
            try:
                for i in range(1, count + 1):
                    await context.bot.send_message(chat_id=chat_id, text=f"[{i}/{count}] {text}")
                    await asyncio.sleep(delay)
                await msg.edit_text("✅ Hoàn tất Burst!")
            except asyncio.CancelledError:
                await update.message.reply_text("🛑 Đã dừng Burst.")
        
        task = asyncio.create_task(run())
        running_tasks[chat_id] = task
    except: pass

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not context.args: return
    txt = " ".join(context.args)
    s = 0
    for c in list(KNOWN_CHATS):
        try:
            await context.bot.send_message(chat_id=c, text=f"📢 **[THÔNG BÁO]**\n\n{txt}", parse_mode="Markdown")
            s += 1
            await asyncio.sleep(1)
        except: pass
    await update.message.reply_text(f"✅ Đã Broadcast tới `{s}` chats!", parse_mode="Markdown")

async def admin_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not update.message.reply_to_message: return
    uid = update.message.reply_to_message.from_user.id
    MUTED_USERS.add(uid)
    await update.message.reply_text(f"🔇 Đã Mute người dùng `{uid}`!", parse_mode="Markdown")

async def admin_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not update.message.reply_to_message: return
    uid = update.message.reply_to_message.from_user.id
    if uid in MUTED_USERS: MUTED_USERS.remove(uid)
    await update.message.reply_text(f"🔊 Đã Unmute người dùng `{uid}`!", parse_mode="Markdown")

async def admin_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id) and update.message.reply_to_message:
        await update.message.reply_to_message.pin()

async def admin_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.unpin_chat_message()

async def admin_adddev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not context.args: return
    if context.args[0].isdigit():
        DEV_IDS.add(int(context.args[0]))
        await update.message.reply_text(f"🎉 Đã thêm Developer: `{context.args[0]}`!", parse_mode="Markdown")

async def admin_deldev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not context.args: return
    if context.args[0].isdigit():
        target = int(context.args[0])
        if target in DEV_IDS: DEV_IDS.remove(target)
        await update.message.reply_text(f"🗑️ Đã xóa Developer: `{target}`!", parse_mode="Markdown")

async def admin_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return await update.message.reply_text("⛔ Chỉ Owner mới thêm được Admin!")
    if context.args and context.args[0].isdigit():
        ADMIN_IDS.add(int(context.args[0]))
        await update.message.reply_text(f"👑 Đã phong Admin cho ID: `{context.args[0]}`!", parse_mode="Markdown")

async def admin_deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return await update.message.reply_text("⛔ Chỉ Owner mới xóa được Admin!")
    if context.args and context.args[0].isdigit():
        target = int(context.args[0])
        if target in ADMIN_IDS: ADMIN_IDS.remove(target)
        await update.message.reply_text(f"🗑️ Đã tước quyền Admin của ID: `{target}`!", parse_mode="Markdown")

# --- 6. XỬ LÝ TIN NHẮN TỰ ĐỘNG & AUTO-REPLY ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    KNOWN_CHATS.add(chat_id)

    # Lọc Mute
    if uid in MUTED_USERS:
        try: await update.message.delete()
        except: pass
        return

    # Tắt AFK khi gửi tin nhắn lại
    if uid in AFK_USERS:
        del AFK_USERS[uid]
        await update.message.reply_text(f"🔔 Mừng **{update.effective_user.first_name}** đã trở lại!", parse_mode="Markdown")

    # Kích hoạt Auto-Reply Trigger của Dev
    txt = update.message.text.lower()
    if txt in CUSTOM_TRIGGERS:
        await update.message.reply_text(CUSTOM_TRIGGERS[txt])

# --- MAIN RUNNER ---
if __name__ == '__main__':
    if not BOT_TOKEN:
        print("LỖI: Chưa có BOT_TOKEN!")
        exit(1)

    # Chạy Flask Server
    threading.Thread(target=run_flask, daemon=True).start()

    # Chạy Telegram Bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Member Handlers
    app.add_handler(CommandHandler("start", user_start))
    app.add_handler(CommandHandler("help", user_help))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("time", cmd_time))
    app.add_handler(CommandHandler("date", cmd_date))
    app.add_handler(CommandHandler("roll", cmd_roll))
    app.add_handler(CommandHandler("flip", cmd_flip))
    app.add_handler(CommandHandler("choice", cmd_choice))
    app.add_handler(CommandHandler("rate", cmd_rate))
    app.add_handler(CommandHandler("8ball", cmd_8ball))
    app.add_handler(CommandHandler("say", cmd_say))
    app.add_handler(CommandHandler("reverse", cmd_reverse))
    app.add_handler(CommandHandler("length", cmd_length))
    app.add_handler(CommandHandler("capital", cmd_capital))
    app.add_handler(CommandHandler("afk", cmd_afk))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("role", cmd_role))

    # Dev Handlers
    app.add_handler(CommandHandler("devmenu", dev_menu))
    app.add_handler(CommandHandler("sysinfo", dev_sysinfo))
    app.add_handler(CommandHandler("botstatus", dev_botstatus))
    app.add_handler(CommandHandler("cleartasks", dev_cleartasks))
    app.add_handler(CommandHandler("settrigger", dev_settrigger))
    app.add_handler(CommandHandler("deltrigger", dev_deltrigger))
    app.add_handler(CommandHandler("listtrigger", dev_listtrigger))
    app.add_handler(CommandHandler("eval", dev_eval))

    # Admin & Owner Handlers
    app.add_handler(CommandHandler("menuadmin", menu_admin))
    app.add_handler(CommandHandler("send", admin_send))
    app.add_handler(CommandHandler("burst", admin_burst))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("mute", admin_mute))
    app.add_handler(CommandHandler("unmute", admin_unmute))
    app.add_handler(CommandHandler("pin", admin_pin))
    app.add_handler(CommandHandler("unpin", admin_unpin))
    app.add_handler(CommandHandler("adddev", admin_adddev))
    app.add_handler(CommandHandler("deldev", admin_deldev))
    app.add_handler(CommandHandler("addadmin", admin_addadmin))
    app.add_handler(CommandHandler("deladmin", admin_deladmin))

    # Message Listener
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot Pro v3.0 đã hoàn tất kết nối!")
    app.run_polling()
