import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ======================
# 🔧 Настройки
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))   # ⚠️ Укажи свой Telegram ID
GROUP_ID = int(os.getenv("GROUP_ID", "-100123456789"))  # ⚠️ Укажи ID группы

# ======================
# ⚙️ Инициализация Flask и Telegram
# ======================
app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()


# ======================
# 🤖 Команды и обработчики
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Отправь мне сообщение, и я передам его на модерацию администратору.")


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Сообщение от @{user.username or user.first_name}:\n\n{text}",
        reply_markup=reply_markup
    )

    await update.message.reply_text("✅ Сообщение отправлено на модерацию!")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_", 1)

    if action == "approve":
        message_text = query.message.text.split("\n\n", 1)[1]
        await context.bot.send_message(chat_id=GROUP_ID, text=message_text)
        await query.edit_message_text(f"✅ Сообщение одобрено и опубликовано:\n\n{message_text}")

    elif action == "reject":
        await query.edit_message_text("❌ Сообщение отклонено.")


# ======================
# 🧩 Добавляем обработчики
# ======================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
application.add_handler(CallbackQueryHandler(handle_callback))


# ======================
# 🌐 Flask маршруты
# ======================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    application.update_queue.put(update)
    return "ok", 200


@app.route("/", methods=["GET"])
def home():
    return "🤖 Telegram bot with moderation is running on Render!", 200


# ======================
# 🚀 Точка входа
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
