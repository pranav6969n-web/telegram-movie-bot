import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MOVIE_CHANNEL_ID = int(os.getenv("MOVIE_CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# In-memory index (Telegram = storage)
MOVIES = []  # {name, year, tags, message_id}

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Movie Search Bot\n\n"
        "🔎 Send movie name or tag to search."
    )

# ---------- INDEX MOVIES (ADMIN ONLY) ----------
async def index_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if not msg or not msg.caption:
        return

    try:
        name, year, tags = [x.strip() for x in msg.caption.split("|")]
    except:
        return

    MOVIES.append({
        "name": name.lower(),
        "year": year,
        "tags": tags.lower(),
        "message_id": msg.message_id
    })

    print(f"Indexed: {name}")

# ---------- SEARCH ----------
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower()

    results = [
        m for m in MOVIES
        if query in m["name"] or query in m["tags"]
    ][:10]

    if not results:
        await update.message.reply_text("❌ No movies found.")
        return

    buttons = [
        [InlineKeyboardButton(
            f"{m['name'].title()} ({m['year']})",
            callback_data=str(m["message_id"])
        )]
        for m in results
    ]

    await update.message.reply_text(
        "🎬 Search Results:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- SEND MOVIE ----------
async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg_id = int(query.data)

    await context.bot.copy_message(
        chat_id=query.message.chat.id,
        from_chat_id=MOVIE_CHANNEL_ID,
        message_id=msg_id
    )

# ---------- BOT ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

# Channel uploads → index
app.add_handler(MessageHandler(
    filters.ChatType.CHANNEL & (filters.VIDEO | filters.Document.ALL),
    index_movie
))

# User search
app.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    search
))

app.add_handler(CallbackQueryHandler(send_movie))

print("🤖 Telegram-only Movie Bot running...")
app.run_polling()
