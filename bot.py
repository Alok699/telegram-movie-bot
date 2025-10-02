import json
import logging
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8110138902:AAGWKzSEkVRaR0dbHgehQRgEBJobV8ZqA3o"
ADMIN_IDS = [7687968365, 6368862755, 6492557901]
CHANNEL_USERNAME = "@xvideos_op"
MOVIES_FILE = "movies.json"
BATCHES_FILE = "batches.json"
DELETE_TIME_MINUTES = 30

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error(f"Save error: {e}")

MOVIES = load_json(MOVIES_FILE)
BATCHES = load_json(BATCHES_FILE)

async def auto_delete(context, chat_id, message_id):
    await asyncio.sleep(DELETE_TIME_MINUTES * 60)
    try:
        await context.bot.delete_message(chat_id, message_id)
        logger.info(f"Deleted message {message_id} from chat {chat_id}")
    except Exception as e:
        logger.error(f"Delete error: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat_id = update.effective_chat.id

    # Generic warning - no explicit mentions
    DELETION_WARNING = (
        "⚠️ <b>Important Notice</b>

"
        "⏰ Files expire in <b>30 minutes</b>
"
        "💾 Save immediately to avoid loss

"
        "🔒 This is an automated delivery system"
    )

    if args:
        code = args[0].lower()
        
        if code in BATCHES:
            batch = BATCHES[code]
            await update.message.reply_text(DELETION_WARNING, parse_mode="HTML")
            
            for idx, video_code in enumerate(batch['videos'], 1):
                if video_code in MOVIES:
                    movie = MOVIES[video_code]
                    # Very generic caption - no content hints
                    caption = (
                        f"📁 <b>File {idx}/{len(batch['videos'])}</b>
"
                        f"━━━━━━━━━━━━━━━
"
                        f"⏰ Expires: {DELETE_TIME_MINUTES} min
"
                        f"💾 Save now"
                    )
                    buttons = [
                        [InlineKeyboardButton("💾 Cloud Save", url="https://t.me/+42777")],
                        [InlineKeyboardButton("📢 More Files", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
                    ]
                    sent = await context.bot.send_video(
                        chat_id=chat_id,
                        video=movie['file_id'],
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    asyncio.create_task(auto_delete(context, chat_id, sent.message_id))
                    await asyncio.sleep(3)
            return
            
        elif code in MOVIES:
            movie = MOVIES[code]
            await update.message.reply_text(DELETION_WARNING, parse_mode="HTML")
            
            # Generic single file caption
            caption = (
                f"📁 <b>File Delivery</b>
"
                f"━━━━━━━━━━━━━━━
"
                f"⏰ Expires: {DELETE_TIME_MINUTES} min
"
                f"💾 Save immediately"
            )
            buttons = [
                [InlineKeyboardButton("💾 Cloud Save", url="https://t.me/+42777")],
                [InlineKeyboardButton("📢 More Files", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
            ]
            sent = await context.bot.send_video(
                chat_id=chat_id,
                video=movie['file_id'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            asyncio.create_task(auto_delete(context, chat_id, sent.message_id))
            return
    
    return

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await update.message.reply_text(
        "📁 <b>Upload File</b>

"
        "📤 Send video now...",
        parse_mode="HTML"
    )
    context.user_data['adding_movie'] = True

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if context.user_data.get('adding_movie'):
        video = update.message.video
        context.user_data['temp_file_id'] = video.file_id
        context.user_data['adding_movie'] = False
        context.user_data['awaiting_code'] = True
        await update.message.reply_text(
            "✅ <b>File Received</b>

"
            "🔑 Enter access code:
"
            "Example: <code>file_001</code>",
            parse_mode="HTML"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    text = update.message.text.strip()
    
    if context.user_data.get('awaiting_code'):
        if not text.replace('_', '').replace('-', '').isalnum():
            await update.message.reply_text("❌ Invalid code format", parse_mode="HTML")
            return
        if text.lower() in MOVIES:
            await update.message.reply_text("❌ Code already exists", parse_mode="HTML")
            return
        context.user_data['movie_code'] = text.lower()
        context.user_data['awaiting_code'] = False
        context.user_data['awaiting_title'] = True
        await update.message.reply_text(
            "✅ <b>Code Saved</b>

"
            "📝 Enter label (internal use only):",
            parse_mode="HTML"
        )
        
    elif context.user_data.get('awaiting_title'):
        context.user_data['movie_title'] = text
        context.user_data['awaiting_title'] = False
        context.user_data['awaiting_description'] = True
        await update.message.reply_text(
            "✅ <b>Label Saved</b>

"
            "📄 Add note (or type <code>skip</code>):",
            parse_mode="HTML"
        )
        
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
            f"✅ <b>Upload Complete</b>

"
            f"📝 Label: {title}
"
            f"🔑 Code: <code>{movie_code}</code>
"
            f"🔗 Link:
<code>{link}</code>

"
            f"📊 Total: {len(MOVIES)} files",
            parse_mode="HTML"
        )
        context.user_data.clear()
        
    elif context.user_data.get('batch_awaiting_codes'):
        codes = [c.strip().lower() for c in text.split(',')]
        valid_codes = [c for c in codes if c in MOVIES]
        invalid_count = len(codes) - len(valid_codes)
        
        if invalid_count > 0:
            await update.message.reply_text(
                f"❌ {invalid_count} invalid codes
"
                f"✅ {len(valid_codes)} valid",
                parse_mode="HTML"
            )
            return
            
        context.user_data['batch_codes'] = valid_codes
        context.user_data['batch_awaiting_codes'] = False
        context.user_data['batch_awaiting_title'] = True
        await update.message.reply_text(
            f"✅ {len(valid_codes)} codes verified

"
            f"📝 Enter collection name:",
            parse_mode="HTML"
        )
        
    elif context.user_data.get('batch_awaiting_title'):
        context.user_data['batch_title'] = text
        context.user_data['batch_awaiting_title'] = False
        context.user_data['batch_awaiting_code'] = True
        await update.message.reply_text(
            "✅ <b>Name Saved</b>

"
            "🔑 Enter collection code:",
            parse_mode="HTML"
        )
        
    elif context.user_data.get('batch_awaiting_code'):
        batch_code = text.lower().replace(' ', '_')
        if not batch_code.replace('_', '').replace('-', '').isalnum():
            await update.message.reply_text("❌ Invalid code", parse_mode="HTML")
            return
        if batch_code in BATCHES:
            await update.message.reply_text("❌ Code exists", parse_mode="HTML")
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
            f"✅ <b>Collection Created</b>

"
            f"📦 Name: {context.user_data['batch_title']}
"
            f"🔑 Code: <code>{batch_code}</code>
"
            f"📁 Files: {len(context.user_data['batch_codes'])}
"
            f"🔗 Link:
<code>{batch_link}</code>

"
            f"📊 Total: {len(BATCHES)} collections",
            parse_mode="HTML"
        )
        context.user_data.clear()

async def addbatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not MOVIES:
        await update.message.reply_text("❌ No files available", parse_mode="HTML")
        return
    await update.message.reply_text(
        "📦 <b>Create Collection</b>

"
        "📝 Enter codes (comma-separated):
"
        "Example: <code>file001,file002</code>

"
        "💡 Use /list to see codes",
        parse_mode="HTML"
    )
    context.user_data['batch_awaiting_codes'] = True

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if MOVIES:
        message = "📁 <b>File List</b>
━━━━━━━━━━━━━━━

"
        for i, (code, data) in enumerate(MOVIES.items(), 1):
            message += f"{i}. <code>{code}</code>
   📝 {data['title']}

"
        message += f"━━━━━━━━━━━━━━━
📊 Total: {len(MOVIES)}"
    else:
        message = "❌ No files"
    await update.message.reply_text(message, parse_mode="HTML")

async def listbatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if BATCHES:
        message = "📦 <b>Collections</b>
━━━━━━━━━━━━━━━

"
        for i, (code, data) in enumerate(BATCHES.items(), 1):
            message += f"{i}. <code>{code}</code>
   📝 {data['title']}
   📁 {len(data['videos'])} files

"
        message += f"━━━━━━━━━━━━━━━
📊 Total: {len(BATCHES)}"
    else:
        message = "❌ No collections"
    await update.message.reply_text(message, parse_mode="HTML")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /delete <code>code</code>", parse_mode="HTML")
        return
    code = context.args[0].lower()
    if code in MOVIES:
        title = MOVIES[code]['title']
        del MOVIES[code]
        save_json(MOVIES_FILE, MOVIES)
        await update.message.reply_text(f"✅ Deleted: {title}", parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Not found", parse_mode="HTML")

async def deletebatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /deletebatch <code>code</code>", parse_mode="HTML")
        return
    code = context.args[0].lower()
    if code in BATCHES:
        title = BATCHES[code]['title']
        del BATCHES[code]
        save_json(BATCHES_FILE, BATCHES)
        await update.message.reply_text(f"✅ Deleted: {title}", parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Not found", parse_mode="HTML")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await update.message.reply_text(
        f"📊 <b>System Status</b>
"
        f"━━━━━━━━━━━━━━━

"
        f"📁 Files: {len(MOVIES)}
"
        f"📦 Collections: {len(BATCHES)}
"
        f"👥 Operators: {len(ADMIN_IDS)}
"
        f"⏰ Expire time: {DELETE_TIME_MINUTES} min
"
        f"✅ Status: Active",
        parse_mode="HTML"
    )

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("add", add_command))
app.add_handler(CommandHandler("addbatch", addbatch_command))
app.add_handler(CommandHandler("list", list_command))
app.add_handler(CommandHandler("listbatch", listbatch_command))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(CommandHandler("deletebatch", deletebatch_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(MessageHandler(filters.VIDEO & filters.User(ADMIN_IDS), handle_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), handle_text))

logger.info("🚀 System online")
logger.info(f"👤 Bot: @BDG99bot")
app.run_polling()
