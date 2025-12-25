import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from config import BOT_TOKEN, ADMINS

# ---------- DATABASE ----------
conn = sqlite3.connect("files.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL
)
""")
conn.commit()


def get_all_files():
    cursor.execute("SELECT file_id FROM files")
    return [row[0] for row in cursor.fetchall()]


# ---------- USER ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = get_all_files()

    if not files:
        await update.message.reply_text("⚠️ No content uploaded yet.")
        return

    context.user_data["index"] = 0
    await show_menu(update, context)


async def show_menu(update, context, edit=False):
    files = get_all_files()
    idx = context.user_data["index"]
    total = len(files)

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

    files = get_all_files()
    idx = context.user_data.get("index", 0)

    if not files:
        await query.message.reply_text("⚠️ No content available.")
        return

    if query.data == "next" and idx < len(files) - 1:
        context.user_data["index"] += 1

    elif query.data == "back" and idx > 0:
        context.user_data["index"] -= 1

    elif query.data == "play":
        await query.message.reply_document(files[idx])

    await show_menu(update, context, edit=True)


# ---------- ADMIN ----------
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    await update.message.reply_text("📤 Send files now. Type /done when finished.")


async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    file = update.message.document or update.message.video or update.message.photo[-1]

    cursor.execute(
        "INSERT INTO files (file_id) VALUES (?)",
        (file.file_id,)
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM files")
    total = cursor.fetchone()[0]

    await update.message.reply_text(f"✅ Added ({total} files total)")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    await update.message.reply_text("🎉 Upload finished!")


# ---------- APP ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("upload", upload))
app.add_handler(CommandHandler("done", done))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(
    MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO, receive_file)
)

app.run_polling()
