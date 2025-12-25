from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, ADMINS

FILES = []  # Stores uploaded files


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FILES:
        await update.message.reply_text("⚠️ No content uploaded yet.")
        return
    context.user_data["index"] = 0
    await show_menu(update, context)


async def show_menu(update, context, edit=False):
    idx = context.user_data["index"]
    total = len(FILES)

    text = f"🎬 Episode {idx+1} / {total}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back"),
            InlineKeyboardButton("▶️ Play", callback_data="play"),
            InlineKeyboardButton("Next ➡️", callback_data="next")
        ]
    ])

    if edit:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = context.user_data.get("index", 0)

    if query.data == "next" and idx < len(FILES) - 1:
        context.user_data["index"] += 1

    elif query.data == "back" and idx > 0:
        context.user_data["index"] -= 1

    elif query.data == "play":
        await query.message.reply_document(FILES[idx])

    await show_menu(update, context, edit=True)


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    await update.message.reply_text("📤 Send files now. Type /done when finished.")


async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    file = update.message.document or update.message.video or update.message.photo[-1]
    FILES.append(file.file_id)

    await update.message.reply_text(f"✅ Added ({len(FILES)} files total)")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    await update.message.reply_text("🎉 Upload finished!")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("upload", upload))
app.add_handler(CommandHandler("done", done))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(
    MessageHandler(
        filters.Document.ALL | filters.VIDEO | filters.PHOTO,
        receive_file
    )
)

app.run_polling()
