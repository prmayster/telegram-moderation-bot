import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    user_info = f"{user.first_name or ''} {user.last_name or ''} (@{user.username or 'без username'})"
    
    # Кнопки для модерации
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve|{text}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject|{text}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем админу на модерацию
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Новое сообщение от {user_info}:\n\n{text}",
        reply_markup=reply_markup
    )
    await update.message.reply_text("✅ Ваше сообщение отправлено на модерацию!")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, text = query.data.split("|", 1)
    
    if action == "approve":
        await context.bot.send_message(chat_id=GROUP_ID, text=f"💬 {text}")
        await query.edit_message_text("✅ Сообщение опубликовано")
    else:
        await query.edit_message_text("❌ Сообщение отклонено")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_user_message))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()
