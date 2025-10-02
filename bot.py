import json
import logging
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# ========== CONFIGURATION ==========
BOT_TOKEN = "8321735522:AAGEp4CycEo8KNhjgkJY9i1E_VMlAE3mMbU"
ADMIN_ID = 7687968365
CHANNEL_USERNAME = "@xvideos_op"
MOVIES_FILE = "movies.json"
BATCHES_FILE = "batches.json"
DELETE_TIME_MINUTES = 20

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Save error: {e}")

MOVIES = load_json(MOVIES_FILE)
BATCHES = load_json(BATCHES_FILE)

# ========== AUTO DELETE FUNCTION ==========
async def auto_delete(context, chat_id, message_id):
    await asyncio.sleep(DELETE_TIME_MINUTES * 60)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception as e:
        logging.error(f"Delete message error: {e}")

# ========== START COMMAND ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    args = context.args

    if args:
        code = args[0].lower()
        if code in BATCHES:
            batch = BATCHES[code]
            await update.message.reply_text(
                f"📦 {batch['title']}\nTotal Videos: {len(batch['videos'])}\n⏰ Auto-delete: {DELETE_TIME_MINUTES} min"
            )
            # Send all videos in batch
            for video_code in batch['videos']:
                if video_code in MOVIES:
                    movie = MOVIES[video_code]
                    caption = (
                        f"🎬 {movie['title']}\n"
                        f"📦 {batch['title']}\n"
                        f"⚠️ Auto-delete: {DELETE_TIME_MINUTES} min\n"
                        f"Save quickly!\n"
                        f"{CHANNEL_USERNAME}"
                    )
                    buttons = [
                        [InlineKeyboardButton("💾 Save", url="https://t.me/+42777")],
                        [InlineKeyboardButton("📢 Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
                    ]
                    sent = await context.bot.send_video(
                        chat_id=chat_id,
                        video=movie['file_id'],
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    asyncio.create_task(auto_delete(context, chat_id, sent.message_id))
                    await asyncio.sleep(2)
            await update.message.reply_text(f"✅ All videos sent! Auto-delete in {DELETE_TIME_MINUTES} min.")
            return
        elif code in MOVIES:
            movie = MOVIES[code]
            caption = (
                f"🎬 {movie['title']}\n"
                f"⚠️ Auto-delete: {DELETE_TIME_MINUTES} min\n"
                f"Save now!\n"
                f"{CHANNEL_USERNAME}"
            )
            buttons = [
                [InlineKeyboardButton("💾 Save", url="https://t.me/+42777")],
                [InlineKeyboardButton("📢 Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
            ]
            sent = await context.bot.send_video(
                chat_id=chat_id,
                video=movie['file_id'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            asyncio.create_task(auto_delete(context, chat_id, sent.message_id))
            return
        else:
            await update.message.reply_text("❌ Invalid code!")
            return

    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n"
        f"🎬 Movie/Video Bot\n"
        f"• Single/batch links\n"
        f"• Auto-delete: {DELETE_TIME_MINUTES} min\n"
        f"📢 {CHANNEL_USERNAME}"
    )

# ========== ADMIN HANDLERS ==========

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("📤 Add Video\nSend video file now...")
    context.user_data['adding_movie'] = True

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if context.user_data.get('adding_movie'):
        video = update.message.video
        context.user_data['temp_file_id'] = video.file_id
        context.user_data['adding_movie'] = False
        context.user_data['awaiting_code'] = True
        await update.message.reply_text("✅ Video received!\nSend code (movie001, movie002):")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = update.message.text.strip()
    if context.user_data.get('awaiting_code'):
        if not text.replace('_', '').isalnum():
            await update.message.reply_text("❌ Invalid code! A-Z 0-9 _ allowed.")
            return
        if text.lower() in MOVIES:
            await update.message.reply_text("❌ Code already exists!")
            return
        context.user_data['movie_code'] = text.lower()
        context.user_data['awaiting_code'] = False
        context.user_data['awaiting_title'] = True
        await update.message.reply_text("✅ Code saved!\nSend title:")
    elif context.user_data.get('awaiting_title'):
        context.user_data['movie_title'] = text
        context.user_data['awaiting_title'] = False
        context.user_data['awaiting_description'] = True
        await update.message.reply_text("✅ Title saved!\nSend description (or type 'skip'):")
    elif context.user_data.get('awaiting_description'):
        description = "" if text.lower() == 'skip' else text
        movie_code = context.user_data['movie_code']
        file_id = context.user_data['temp_file_id']
        title = context.user_data['movie_title']
        MOVIES[movie_code] = {
            'file_id': file_id,
            'title': title,
            'description': description,
            'added_time': int(time.time())
        }
        save_json(MOVIES_FILE, MOVIES)
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={movie_code}"
        await update.message.reply_text(
            f"✅ Added!\n🎬 {title}\nCode: `{movie_code}`\nShare Link: `{link}`"
        )
        context.user_data.clear()
    elif context.user_data.get('batch_awaiting_codes'):
        codes = [c.strip().lower() for c in text.split(',')]
        valid_codes = [c for c in codes if c in MOVIES]
        invalid_codes = [c for c in codes if c not in MOVIES]
        if invalid_codes:
            await update.message.reply_text(f"❌ Invalid codes: {', '.join(invalid_codes)}")
            return
        context.user_data['batch_codes'] = valid_codes
        context.user_data['batch_awaiting_codes'] = False
        context.user_data['batch_awaiting_title'] = True
        await update.message.reply_text(f"✅ Codes selected!\nSend batch title:")
    elif context.user_data.get('batch_awaiting_title'):
        context.user_data['batch_title'] = text
        context.user_data['batch_awaiting_title'] = False
        context.user_data['batch_awaiting_code'] = True
        await update.message.reply_text("✅ Title saved!\nSend batch code:")
    elif context.user_data.get('batch_awaiting_code'):
        batch_code = text.lower().replace(' ', '_')
        if not batch_code.replace('_', '').isalnum():
            await update.message.reply_text("❌ Invalid batch code!")
            return
        if batch_code in BATCHES:
            await update.message.reply_text("❌ Batch code already exists!")
            return
        BATCHES[batch_code] = {
            'title': context.user_data['batch_title'],
            'videos': context.user_data['batch_codes'],
            'created_time': int(time.time())
        }
        save_json(BATCHES_FILE, BATCHES)
        bot_username = (await context.bot.get_me()).username
        batch_link = f"https://t.me/{bot_username}?start={batch_code}"
        await update.message.reply_text(
            f"✅ Batch Created!\n📦 {context.user_data['batch_title']}\nCode: `{batch_code}`\nVideos: {len(context.user_data['batch_codes'])}\nBatch Link: `{batch_link}`"
        )
        context.user_data.clear()

async def addbatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not MOVIES:
        await update.message.reply_text("❌ First add videos with /add")
        return
    await update.message.reply_text("📦 Create Batch\nSend video codes (comma separated):\nExample: movie001, movie002\nUse /list for codes")
    context.user_data['batch_awaiting_codes'] = True

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    message = "📋 All Videos:\n\n"
    if MOVIES:
        for i, (code, data) in enumerate(MOVIES.items(), 1):
            message += f"{i}. `{code}` - {data['title']}\n"
        message += f"\nTotal: {len(MOVIES)} videos"
    else:
        message += "No videos yet!"
    await update.message.reply_text(message)

async def listbatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    message = "📦 All Batches:\n\n"
    if BATCHES:
        for i, (code, data) in enumerate(BATCHES.items(), 1):
            message += f"{i}. `{code}` - {data['title']} ({len(data['videos'])} videos)\n"
        message += f"\nTotal: {len(BATCHES)} batches"
    else:
        message += "No batches yet!"
    await update.message.reply_text(message)

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /delete video_code")
        return
    code = context.args[0].lower()
    if code in MOVIES:
        title = MOVIES[code]['title']
        del MOVIES[code]
        save_json(MOVIES_FILE, MOVIES)
        await update.message.reply_text(f"✅ Deleted: {title}")
    else:
        await update.message.reply_text("❌ Not found!")

async def deletebatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /deletebatch batch_code")
        return
    code = context.args[0].lower()
    if code in BATCHES:
        title = BATCHES[code]['title']
        del BATCHES[code]
        save_json(BATCHES_FILE, BATCHES)
        await update.message.reply_text(f"✅ Deleted batch: {title}")
    else:
        await update.message.reply_text("❌ Batch not found!")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(
        f"📊 Stats\nVideos: {len(MOVIES)}\nBatches: {len(BATCHES)}\nAuto-delete: {DELETE_TIME_MINUTES} min\nStatus: Online\nChannel: {CHANNEL_USERNAME}"
    )

# ========== APP & HANDLERS ==========

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("add", add_command))
app.add_handler(CommandHandler("addbatch", addbatch_command))
app.add_handler(CommandHandler("list", list_command))
app.add_handler(CommandHandler("listbatch", listbatch_command))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(CommandHandler("deletebatch", deletebatch_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(MessageHandler(filters.VIDEO & filters.User(ADMIN_ID), handle_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID), handle_text))

logging.info("Bot started! 🚀")
app.run_polling()
