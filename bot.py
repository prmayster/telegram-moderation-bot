import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
GROUP_ID = int(os.getenv("GROUP_ID", "-100123456789"))

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running on Render!"


# --- Telegram bot handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Отправь мне сообщение, и я передам его на модерацию администратору.")


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    keyboard = [
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user.id}"),
         InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")]
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
        await query.edit_message_text(f"✅ Сообщение опубликовано:\n\n{message_text}")
    elif action == "reject":
        await query.edit_message_text("❌ Сообщение отклонено.")


### >>> ИЗМЕНЕНИЕ ДЛЯ МОДЕРАЦИИ: обработка сообщений из группы
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    text = message.text or "<пустое сообщение>"

    # Удаляем оригинальное сообщение из группы
    try:
        await message.delete()
    except Exception as e:
        print("⚠️ Не удалось удалить сообщение из группы:", e)

    # Отправляем админу на модерацию
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"group_approve_{user.id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"group_reject_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📢 Сообщение из группы от @{user.username or user.first_name}:\n\n{text}",
        reply_markup=reply_markup
    )
    print(f"🕓 Сообщение от {user.username} отправлено на модерацию.")
### <<<


### >>> ИЗМЕНЕНИЕ ДЛЯ МОДЕРАЦИИ: обработка одобрения/отклонения сообщений из группы
async def handle_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_", 2)
    action = data[1]

    if action == "approve":
        text = query.message.text.split("\n\n", 1)[1]
        await context.bot.send_message(chat_id=GROUP_ID, text=text)
        await query.edit_message_text(f"✅ Одобрено и опубликовано:\n\n{text}")
    elif action == "reject":
        await query.edit_message_text("❌ Сообщение из группы отклонено.")
### <<<


def run_bot():
    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Chat(GROUP_ID), handle_user_message))
    tg_app.add_handler(CallbackQueryHandler(handle_callback, pattern="^(approve|reject)_"))

    ### >>> ИЗМЕНЕНИЕ ДЛЯ МОДЕРАЦИИ: добавляем новые хендлеры для сообщений из группы
    tg_app.add_handler(MessageHandler(filters.Chat(GROUP_ID) & filters.TEXT & ~filters.COMMAND, handle_group_message))
    tg_app.add_handler(CallbackQueryHandler(handle_group_callback, pattern="^group_"))
    ### <<<

    print("🚀 Bot started successfully!")
    tg_app.run_polling()


# --- Запуск Flask и Telegram одновременно ---
if __name__ == "__main__":
    Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
