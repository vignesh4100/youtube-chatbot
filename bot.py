import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from telegram.helpers import escape_markdown
from pytube import Search
from googleapiclient.discovery import build
from pydub import AudioSegment

# Load API keys from environment or define directly (for testing only)
TELEGRAM_TOKEN = "8060520218:AAHJihyTe-Gt4ujjDLApGOBiAeSYNPPN1FQ"
YOUTUBE_API_KEY = "AIzaSyA2fpKWAk8zWPilI3bK9xbqNwCpyLmqwYQ"

# Setup logging
logging.basicConfig(level=logging.INFO)

# Setup YouTube API client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# ------------------- Video Selection (Free, No LLM) -------------------
def select_best_video(videos, query):
    query_lower = query.lower()
    for video in videos:
        title = video["snippet"]["title"].lower()
        if all(word in title for word in query_lower.split()):
            return video
    return videos[0] if videos else None

# ------------------- Search YouTube -------------------
def search_youtube(query, max_results=5):
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    return response.get("items", [])

# ------------------- Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send a message or voice note (Hindi/English) to find the best YouTube video!"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text("🔎 Searching YouTube...")
    videos = search_youtube(query)
    best = select_best_video(videos, query)
    if best:
        video_id = best["id"]["videoId"]
        title = best["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        escaped_title = escape_markdown(title, version=2)
        escaped_url = escape_markdown(url, version=2)

        await update.message.reply_text(
            f"✅ Best match: *{escaped_title}*\n{escaped_url}",
            parse_mode="MarkdownV2"
        )
    else:
        await update.message.reply_text("😢 Sorry, I couldn't find anything.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    ogg_path = "voice.ogg"
    wav_path = "voice.wav"

    await file.download_to_drive(ogg_path)

    try:
        sound = AudioSegment.from_ogg(ogg_path)
        sound.export(wav_path, format="wav")
        await update.message.reply_text("✅ Voice received, but speech-to-text is not enabled in free mode.")
    except Exception as e:
        await update.message.reply_text("⚠️ Could not process audio.")
        logging.error(f"Audio conversion failed: {e}")
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

# ------------------- Main Setup -------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
