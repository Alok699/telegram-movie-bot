import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time
import asyncio

# ============================================
# YOUR CONFIGURATION
# ============================================

BOT_TOKEN = "8321735522:AAGEp4CycEo8KNhjgkJY9i1E_VMlAE3mMbU"
ADMIN_ID = 7687968365
CHANNEL_USERNAME = "@xvideos_op"

MOVIES_FILE = "movies.json"
BATCHES_FILE = "batches.json"
DELETE_TIME_MINUTES = 20

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# ============================================
# DATA MANAGEMENT
# ============================================

def load_movies():
    try:
        with open(MOVIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_movies(movies):
    try:
        with open(MOVIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(movies, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error: {e}")

def load_batches():
    try:
        with open(BATCHES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_batches(batches):
    try:
        with open(BATCHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(batches, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error: {e}")

MOVIES = load_movies()
BATCHES = load_batches()

# ============================================
# AUTO DELETE
# ============================================

async def auto_delete_message(context, chat_id, message_id, delay_minutes):
    await asyncio.sleep(delay_minutes * 60)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logging.info(f"✅ Deleted msg {message_id}")
    except Exception as e:
        logging.error(f"Delete error: {e}")

# ============================================
# USER COMMANDS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if context.args and len(context.args) > 0:
        code = context.args[0].lower()
        
        # BATCH CHECK
        if code in BATCHES:
            batch = BATCHES[code]
            
            await update.message.reply_text(
                f"📦 **{batch['title']}**\n\n"
                f"📹 Total Videos: {len(batch['videos'])}\n"
                f"⏰ Each video auto-deletes in {DELETE_TIME_MINUTES} min\n"
                f"💾 Save all to Saved Messages!\n\n"
                f"⬇️ Sending all videos...",
                parse_mode='Markdown'
            )
            
            for video_code in batch['videos']:
                if video_code in MOVIES:
                    movie = MOVIES[video_code]
                    
                    caption = (
                        f"🎬 **{movie['title']}**\n"
                        f"📦 Part of: {batch['title']}\n\n"
                        f"⚠️ Auto-delete in {DELETE_TIME_MINUTES} min\n"
                        f"💾 Save Now!\n\n"
                        f"📢 {CHANNEL_USERNAME}"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("💾 Save to Saved Messages", url="https://t.me/+42777")],
                        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    try:
                        sent = await context.bot.send_video(
                            chat_id=chat_id,
                            video=movie['file_id'],
                            caption=caption,
                            parse_mode='Markdown',
                            reply_markup=reply_markup
                        )
                        
                        asyncio.create_task(
                            auto_delete_message(context, chat_id, sent.message_id, DELETE_TIME_MINUTES)
                        )
                        
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logging.error(f"Error sending {video_code}: {e}")
            
            await update.message.reply_text(
                f"✅ All {len(batch['videos'])} videos sent!\n"
                f"💾 Save them quickly - deleting in {DELETE_TIME_MINUTES} min!"
            )
            
            logging.info(f"✅ Batch '{code}' sent to user {user.id}")
        
        # SINGLE VIDEO CHECK
        elif code in MOVIES:
            movie = MOVIES[code]
            
            caption = f"🎬 **{movie['title']}**\n\n"
            
            if movie.get('description'):
                caption += f"📝 {movie['description']}\n\n"
            
            caption += (
                f"⚠️ **IMPORTANT:**\n"
                f"⏰ Auto-DELETE in **{DELETE_TIME_MINUTES} min**\n"
                f"💾 Forward to Saved Messages NOW!\n\n"
                f"📢 {CHANNEL_USERNAME}"
            )
            
            keyboard = [
                [InlineKeyboardButton("💾 Save to Saved Messages", url="https://t.me/+42777")],
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                sent = await context.bot.send_video(
                    chat_id=chat_id,
                    video=movie['file_id'],
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
                asyncio.create_task(
                    auto_delete_message(context, chat_id, sent.message_id, DELETE_TIME_MINUTES)
                )
                
                logging.info(f"✅ Single video '{code}' sent to user {user.id}")
                
            except Exception as e:
                await update.message.reply_text("❌ Error sending video!")
                logging.error(f"Error: {e}")
        
        else:
            await update.message.reply_text(
                "❌ **Invalid Link!**\n\n"
                f"Get valid links from: {CHANNEL_USERNAME}",
                parse_mode='Markdown'
            )
    
    else:
        await update.message.reply_text(
            f"👋 **Welcome {user.first_name}!**\n\n"
            f"🎬 Movie/Video Delivery Bot\n\n"
            f"📌 **Features:**\n"
            f"• Single video links\n"
            f"• Batch links (multiple videos)\n"
            f"• Auto-delete in {DELETE_TIME_MINUTES} min\n\n"
            f"📢 **Channel:** {CHANNEL_USERNAME}",
            parse_mode='Markdown'
        )

# ============================================
# ADMIN - SINGLE VIDEO
# ============================================

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        "📤 **Add Single Video**\n\n"
        "Send video file now...",
        parse_mode='Markdown'
    )
    context.user_data['adding_movie'] = True

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if context.user_data.get('adding_movie'):
        video = update.message.video
        context.user_data['temp_file_id'] = video.file_id
        context.user_data['adding_movie'] = False
        context.user_data['awaiting_code'] = True
        
        await update.message.reply_text(
            "✅ Video received!\n\n"
            "Send movie code:\n"
            "(Example: movie001)"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    text = update.message.text.strip()
    
    # SINGLE VIDEO WORKFLOW
    if context.user_data.get('awaiting_code'):
        if not text.replace('_', '').isalnum():
            await update.message.reply_text("❌ Invalid code! Use: A-Z, 0-9, underscore")
            return
        
        if text.lower() in MOVIES:
            await update.message.reply_text(f"❌ Code '{text}' already exists!")
            return
        
        context.user_data['movie_code'] = text.lower()
        context.user_data['awaiting_code'] = False
        context.user_data['awaiting_title'] = True
        
        await update.message.reply_text(f"✅ Code: {text}\n\nSend title:")
    
    elif context.user_data.get('awaiting_title'):
        context.user_data['movie_title'] = text
        context.user_data['awaiting_title'] = False
        context.user_data['awaiting_description'] = True
        
        await update.message.reply_text("✅ Title saved!\n\nSend description (or type 'skip'):")
    
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
        
        save_movies(MOVIES)
        
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={movie_code}"
        
        await update.message.reply_text(
            "✅ **Video Added!**\n\n"
            f"🎬 {title}\n"
            f"🔑 `{movie_code}`\n\n"
            f"🔗 **Share Link:**\n`{link}`\n\n"
            f"Copy and share in channel!",
            parse_mode='Markdown'
        )
        
        logging.info(f"✅ Added: {movie_code}")
        context.user_data.clear()
    
    # BATCH WORKFLOW
    elif context.user_data.get('batch_awaiting_codes'):
        codes = [c.strip().lower() for c in text.split(',')]
        
        valid_codes = [c for c in codes if c in MOVIES]
        invalid_codes = [c for c in codes if c not in MOVIES]
        
        if invalid_codes:
            await update.message.reply_text(
                f"❌ Invalid codes:\n{', '.join(invalid_codes)}\n\n"
                f"Use /list to see available codes"
            )
            return
        
        context.user_data['batch_codes'] = valid_codes
        context.user_data['batch_awaiting_codes'] = False
        context.user_data['batch_awaiting_title'] = True
        
        await update.message.reply_text(f"✅ {len(valid_codes)} videos selected!\n\nSend batch title:")
    
    elif context.user_data.get('batch_awaiting_title'):
        context.user_data['batch_title'] = text
        context.user_data['batch_awaiting_title'] = False
        context.user_data['batch_awaiting_code'] = True
        
        await update.message.reply_text("✅ Title saved!\n\nSend batch code:")
    
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
        
        save_batches(BATCHES)
        
        bot_username = (await context.bot.get_me()).username
        batch_link = f"https://t.me/{bot_username}?start={batch_code}"
        
        await update.message.reply_text(
            "✅ **Batch Created!**\n\n"
            f"📦 {context.user_data['batch_title']}\n"
            f"🔑 `{batch_code}`\n"
            f"📹 Videos: {len(context.user_data['batch_codes'])}\n\n"
            f"🔗 **Batch Link:**\n`{batch_link}`\n\n"
            f"Share this to send all videos at once!",
            parse_mode='Markdown'
        )
        
        logging.info(f"✅ Batch created: {batch_code}")
        context.user_data.clear()

# ============================================
# ADMIN - BATCH
# ============================================

async def addbatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not MOVIES:
        await update.message.reply_text("❌ First add videos using /add")
        return
    
    await update.message.reply_text(
        "📦 **Create Batch**\n\n"
        "Send video codes (comma separated):\n\n"
        "Example: `movie001, movie002, movie003`\n\n"
        "Use /list to see all codes",
        parse_mode='Markdown'
    )
    
    context.user_data['batch_awaiting_codes'] = True

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    message = "📋 **All Videos:**\n\n"
    
    if MOVIES:
        for i, (code, data) in enumerate(MOVIES.items(), 1):
            message += f"{i}. `{code}` - {data['title']}\n"
        message += f"\n**Total:** {len(MOVIES)}"
    else:
        message += "No videos yet!"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def listbatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    message = "📦 **All Batches:**\n\n"
    
    if BATCHES:
        for i, (code, data) in enumerate(BATCHES.items(), 1):
            message += f"{i}. `{code}` - {data['title']} ({len(data['videos'])} videos)\n"
        message += f"\n**Total:** {len(BATCHES)}"
    else:
        message += "No batches yet!"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /delete video_code")
        return
    
    code = context.args[0].lower()
    
    if code in MOVIES:
        title = MOVIES[code]['title']
        del MOVIES[code]
        save_movies(MOVIES)
        await update.message.reply_text(f"✅ Deleted: {title}")
        logging.info(f"Deleted: {code}")
    else:
        await update.message.reply_text("❌ Not found!")

async def deletebatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /deletebatch batch_code")
        return
    
    code = context.args[0].lower()
    
    if code in BATCHES:
        title = BATCHES[code]['title']
        del BATCHES[code]
        save_batches(BATCHES)
        await update.message.reply_text(f"✅ Deleted batch: {title}")
        logging.info(f"Deleted batch: {code}")
    else:
        await update.message.reply_text("❌ Batch not found!")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    await update.message.reply_text(
        f"📊 **Bot Statistics**\n\n"
        f"🎬 Single Videos: {len(MOVIES)}\n"
        f"📦 Batches: {len(BATCHES)}\n"
        f"⏰ Auto-delete: {DELETE_TIME_MINUTES} min\n"
        f"🤖 Status: Online\n"
        f"📢 Channel: {CHANNEL_USERNAME}"
    )

# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error occurred: {context.error}")

# ============================================
# MAIN
# ============================================

def main():
    logging.info("="*50)
    logging.info("🚀 Bot Starting...")
    logging.info(f"🎬 Loaded Videos: {len(MOVIES)}")
    logging.info(f"📦 Loaded Batches: {len(BATCHES)}")
    logging.info(f"⏰ Delete Time: {DELETE_TIME_MINUTES} min")
    logging.info(f"📢 Channel: {CHANNEL_USERNAME}")
    logging.info("="*50)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # USER
    app.add_handler(CommandHandler("start", start_command))
    
    # ADMIN - SINGLE
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("delete", delete_command))
    
    # ADMIN - BATCH
    app.add_handler(CommandHandler("addbatch", addbatch_command))
    app.add_handler(CommandHandler("listbatch", listbatch_command))
    app.add_handler(CommandHandler("deletebatch", deletebatch_command))
    
    # ADMIN - GENERAL
    app.add_handler(CommandHandler("stats", stats_command))
    
    # MESSAGE HANDLERS
    app.add_handler(MessageHandler(filters.VIDEO & filters.User(ADMIN_ID), handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID), handle_text))
    
    # ERROR
    app.add_error_handler(error_handler)
    
    logging.info("✅ Bot is Online and Running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            logging.info("❌ Bot stopped by user")
            break
        except Exception as e:
            logging.error(f"💥 Bot crashed: {e}")
            logging.info("🔄 Restarting in 10 seconds...")
            time.sleep(10)
