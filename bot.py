import os
import asyncio
import random
import datetime
import pytz
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes
)

# Cấu hình log hệ thống
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Lấy Token từ biến môi trường
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ID Owner chính của bạn
DEFAULT_ADMINS = [8474356606]

# Đọc thêm Admin từ Render nếu có cấu hình biến ADMIN_IDS
env_admins = os.environ.get("ADMIN_IDS")
if env_admins:
    for i in env_admins.split(","):
        if i.strip().isdigit():
            DEFAULT_ADMINS.append(int(i.strip()))

ADMIN_IDS = set(DEFAULT_ADMINS)
KNOWN_CHATS = set()
running_tasks = {}

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ==========================================
# 🌐 PHẦN 1: CÁC LỆNH THƯỜNG (PUBLIC)
# ==========================================

# Lệnh /info xem thông tin chi tiết (Giao diện chuẩn Rose)
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    
    # Kiểm tra xem có phải lệnh reply người khác không
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        target_user = update.effective_user

    first_name = target_user.first_name or "N/A"
    last_name = target_user.last_name or ""
    username = f"@{target_user.username}" if target_user.username else "N/A"
    user_id = target_user.id
    user_link = f"tg://user?id={user_id}"
    status = "admin" if is_admin(user_id) else "user"

    info_text = (
        f"**User info:**\n"
        f"**ID:** `{user_id}`\n"
        f"**First Name:** {first_name}\n"
        f"**Last Name:** {last_name}\n"
        f"**Username:** {username}\n"
        f"**User link:** [link]({user_link})\n"
        f"**Status:** `{status}`"
    )
    await update.message.reply_text(info_text, parse_mode="Markdown", disable_web_page_preview=True)

# Lệnh /help trợ giúp công khai
async def user_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    help_text = (
        "🤖 **DANH SÁCH LỆNH TIỆN ÍCH**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "👤 `/info` - Xem thông tin tài khoản Telegram\n"
        "🎲 `/roll` - Đổ xúc xắc ngẫu nhiên (1-100)\n"
        "🪙 `/flip` - Tung đồng xu (Sấp/Ngửa)\n"
        "⏰ `/time` - Xem giờ hệ thống Việt Nam\n"
        "🏓 `/ping` - Kiểm tra tốc độ phản hồi bot\n"
        "👑 `/menuadmin` - Bảng điều khiển Quản trị viên"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def flip_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    await update.message.reply_text(f"Kết quả: {random.choice(['🪙 **MẶT SẤP**', '🪙 **MẶT NGỬA**'])}!", parse_mode="Markdown")

async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    await update.message.reply_text(f"🎲 Số ngẫu nhiên: `{random.randint(1, 100)}`", parse_mode="Markdown")

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.datetime.now(tz)
    await update.message.reply_text(f"🕒 **Giờ VN:** `{now.strftime('%H:%M:%S - %d/%m/%Y')}`", parse_mode="Markdown")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    KNOWN_CHATS.add(update.effective_chat.id)
    start_time = datetime.datetime.now()
    msg = await update.message.reply_text("🏓 Pong...")
    latency = (datetime.datetime.now() - start_time).microseconds / 1000
    await msg.edit_text(f"🏓 **Pong!** Độ trễ: `{latency:.2f} ms`", parse_mode="Markdown")

# ==========================================
# 👑 PHẦN 2: BẢNG ĐIỀU KHIỂN & LỆNH ADMIN
# ==========================================

# Mở Menu Admin bằng lệnh /menuadmin hoặc /start
async def menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    KNOWN_CHATS.add(chat_id)

    if not is_admin(user_id):
        await update.message.reply_text("⛔ Bạn không có quyền mở Menu Admin!", parse_mode="Markdown")
        return

    keyboard = [
        [InlineKeyboardButton("🚀 Gửi tin ngay", callback_data="guide_send"), InlineKeyboardButton("⏱️ Hẹn giờ", callback_data="guide_schedule")],
        [InlineKeyboardButton("💥 Gửi chuỗi (Burst)", callback_data="guide_burst"), InlineKeyboardButton("📢 Broadcast All", callback_data="guide_broadcast")],
        [InlineKeyboardButton("📊 Thống kê Bot", callback_data="cmd_stats"), InlineKeyboardButton("🛑 Hủy tác vụ", callback_data="cancel_task")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_admin = (
        f"👑 **SUPER ADMIN CONTROL PANEL**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Admin: **{update.effective_user.first_name}**\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"📌 **DANH SÁCH LỆNH ADMIN:**\n"
        f"• `/send <nội dung>` - Gửi ngay\n"
        f"• `/schedule <phút> <nội dung>` - Hẹn giờ\n"
        f"• `/burst <số lần> <nội dung>` - Chạy chuỗi (3s/tin)\n"
        f"• `/broadcast <nội dung>` - Gửi toàn bộ chat\n"
        f"• `/addadmin <ID>` / `/deladmin <ID>` - Quản lý Admin"
    )
    await update.message.reply_text(welcome_admin, reply_markup=reply_markup, parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.message.reply_text("⛔ Thao tác này chỉ dành cho Admin!")
        return

    chat_id = query.message.chat_id

    if query.data == "guide_send":
        await query.message.reply_text("📌 `/send <nội dung>`: Gửi tin nhắn ngay lập tức.", parse_mode="Markdown")
    elif query.data == "guide_schedule":
        await query.message.reply_text("📌 `/schedule <phút> <nội dung>`: Lập lịch gửi tin nhắn.", parse_mode="Markdown")
    elif query.data == "guide_burst":
        await query.message.reply_text("📌 `/burst <số lần> <nội dung>`: Gửi chuỗi tự động (3s/tin).", parse_mode="Markdown")
    elif query.data == "guide_broadcast":
        await query.message.reply_text("📌 `/broadcast <nội dung>`: Gửi thông báo đến mọi nhóm/người dùng.", parse_mode="Markdown")
    elif query.data == "cmd_stats":
        msg = f"📊 **THỐNG KÊ BOT**\n👥 Admin: `{len(ADMIN_IDS)}` | 💬 Chat đã nhớ: `{len(KNOWN_CHATS)}`"
        await query.message.reply_text(msg, parse_mode="Markdown")
    elif query.data == "cancel_task":
        if chat_id in running_tasks and not running_tasks[chat_id].done():
            running_tasks[chat_id].cancel()
            del running_tasks[chat_id]
            await query.message.reply_text("🛑 **Đã hủy tác vụ đang chạy!**")
        else:
            await query.message.reply_text("ℹ️ Không có tác vụ nào đang chạy.")

# Lệnh Admin nâng cao
async def send_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return await update.message.reply_text("❌ Cú pháp: `/send <nội dung>`", parse_mode="Markdown")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=" ".join(context.args))

async def burst_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    chat_id = update.effective_chat.id
    if len(context.args) < 2: return await update.message.reply_text("❌ Cú pháp: `/burst <số lần> <nội dung>`", parse_mode="Markdown")

    try:
        count = int(context.args[0])
        text = " ".join(context.args[1:])
        if count > 100: return await update.message.reply_text("⚠️ Giới hạn tối đa 100 tin!")

        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Hủy tiến trình", callback_data="cancel_task")]])
        status_msg = await update.message.reply_text(f"⏳ Đang gửi {count} tin...", reply_markup=cancel_btn)

        async def run_burst():
            try:
                for i in range(1, count + 1):
                    await context.bot.send_message(chat_id=chat_id, text=f"[{i}/{count}] {text}")
                    if i % 5 == 0 or i == count:
                        await status_msg.edit_text(f"📊 Tiến độ: `{i}/{count}`...", reply_markup=cancel_btn, parse_mode="Markdown")
                    await asyncio.sleep(3)
                await update.message.reply_text("✅ Hoàn tất!")
            except asyncio.CancelledError:
                await update.message.reply_text("🛑 Đã dừng.")

        task = asyncio.create_task(run_burst())
        running_tasks[chat_id] = task
    except ValueError:
        await update.message.reply_text("❌ Số lần gửi phải là một số!")

async def schedule_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if len(context.args) < 2: return await update.message.reply_text("❌ Cú pháp: `/schedule <số phút> <nội dung>`", parse_mode="Markdown")
    try:
        minutes = float(context.args[0])
        text = " ".join(context.args[1:])
        context.job_queue.run_once(
            lambda ctx: ctx.bot.send_message(chat_id=ctx.job.chat_id, text=f"⏰ **[Lập Lịch]**\n{ctx.job.data}", parse_mode="Markdown"),
            when=minutes * 60, chat_id=update.effective_chat.id, data=text
        )
        await update.message.reply_text(f"🎯 Đã hẹn giờ sau `{minutes}` phút.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Số phút không hợp lệ!")

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return await update.message.reply_text("❌ Cú pháp: `/broadcast <nội dung>`", parse_mode="Markdown")

    text = " ".join(context.args)
    status_msg = await update.message.reply_text(f"📢 Đang Broadcast tới {len(KNOWN_CHATS)} chat...")
    success = 0
    for target_chat in list(KNOWN_CHATS):
        try:
            await context.bot.send_message(chat_id=target_chat, text=f"📢 **[THÔNG BÁO]**\n\n{text}", parse_mode="Markdown")
            success += 1
            await asyncio.sleep(2)
        except Exception:
            pass
    await status_msg.edit_text(f"✅ Đã Broadcast xong cho `{success}` chat!", parse_mode="Markdown")

# Quản lý Admin động
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("❌ Cú pháp: `/addadmin <User_ID>`", parse_mode="Markdown")
    new_id = int(context.args[0])
    ADMIN_IDS.add(new_id)
    await update.message.reply_text(f"🎉 Đã thêm Admin `{new_id}`!", parse_mode="Markdown")

async def del_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("❌ Cú pháp: `/deladmin <User_ID>`", parse_mode="Markdown")
    target_id = int(context.args[0])
    if target_id in ADMIN_IDS:
        ADMIN_IDS.remove(target_id)
        await update.message.reply_text(f"🗑️ Đã xóa Admin `{target_id}`!", parse_mode="Markdown")

# --- KHỞI CHẠY BOT ---
if __name__ == '__main__':
    if not BOT_TOKEN:
        print("LỖI: Chưa cài BOT_TOKEN!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Lệnh Thường (Public)
    app.add_handler(CommandHandler("info", user_info))
    app.add_handler(CommandHandler("help", user_help))
    app.add_handler(CommandHandler("flip", flip_coin))
    app.add_handler(CommandHandler("roll", roll_dice))
    app.add_handler(CommandHandler("time", get_time))
    app.add_handler(CommandHandler("ping", ping))

    # Lệnh Admin (Private)
    app.add_handler(CommandHandler("start", menu_admin))
    app.add_handler(CommandHandler("menuadmin", menu_admin))
    app.add_handler(CommandHandler("send", send_now))
    app.add_handler(CommandHandler("burst", burst_messages))
    app.add_handler(CommandHandler("schedule", schedule_msg))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("deladmin", del_admin))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🚀 Bot đã sẵn sàng chạy!")
    app.run_polling()
