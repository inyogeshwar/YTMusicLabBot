import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from database import Database
from youtube_service import YouTubeService
from lyrics_service import LyricsService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class SimpleMusicBot:
    def get_music_main_menu(self):
        """Return a music-related main menu keyboard like the screenshot, but only for music features."""
        keyboard = [
            [InlineKeyboardButton("YouTube 🎬", callback_data="music_youtube"),
             InlineKeyboardButton("YT Music 🎵", callback_data="music_ytmusic")],
            [InlineKeyboardButton("Lyrics 📝", callback_data="music_lyrics"),
             InlineKeyboardButton("Top Charts 📈", callback_data="music_top")],
            [InlineKeyboardButton("My Downloads 📂", callback_data="music_downloads")],
            [InlineKeyboardButton("⬅️ Back", callback_data="music_back"),
             InlineKeyboardButton("⬆️ Main Menu", callback_data="music_mainmenu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    async def music_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the music main menu with buttons."""
        await update.message.reply_text(
            "🎶 **Music Menu**\n\nChoose an option:",
            reply_markup=self.get_music_main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        # Music menu command
        application.add_handler(CommandHandler("musicmenu", self.music_menu_command))
    def __init__(self):
        # Configuration
        self.bot_token = os.getenv('BOT_TOKEN')
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.genius_token = os.getenv('GENIUS_API_TOKEN')
        
        # Primary admin (unchangeable)
        self.primary_admin_id = 7176592290
        
        # Support multiple admin IDs
        admin_ids_str = os.getenv('ADMIN_USER_IDS', os.getenv('ADMIN_USER_ID', ''))
        self.admin_user_ids = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
        
        # Ensure primary admin is always included
        if self.primary_admin_id not in self.admin_user_ids:
            self.admin_user_ids.append(self.primary_admin_id)
        
        self.downloads_dir = os.getenv('DOWNLOADS_DIR', 'downloads')
        self.temp_dir = os.getenv('TEMP_DIR', 'temp')
        
        # Create directories
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize services
        self.db = Database(os.getenv('DATABASE_PATH', 'bot_database.db'))
        self.youtube = YouTubeService(self.youtube_api_key)
        self.lyrics = LyricsService(self.genius_token)
        
        # User sessions for multi-step operations
        self.user_sessions: Dict[int, Dict] = {}
    
    def escape_markdown(self, text: str) -> str:
        """Escape markdown special characters"""
        escape_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def is_youtube_url(self, text: str) -> bool:
        """Check if text contains a YouTube URL"""
        youtube_patterns = [
            'youtube.com/watch',
            'youtu.be/',
            'youtube.com/v/',
            'youtube.com/embed/',
            'm.youtube.com/watch'
        ]
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in youtube_patterns)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Add user to database
        self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        welcome_text = f"""
🎵 **Welcome to Simple Music Bot!** 🎵

Hello {user.first_name}! I'm your YouTube MP3 downloader. Here's what I can do:

🎧 **Features:**
• 🔍 Search YouTube songs by name
• 🔗 Download from YouTube URLs directly  
• � Search for song lyrics
• �📥 Download MP3 audio only
• 🎵 High quality 192kbps

📱 **How to use:**
1. Send me a song name: "Despacito"
2. Send me a YouTube URL: https://youtu.be/...
3. Use /search command: /search despacito
4. Use /lyrics command: /lyrics despacito
5. Choose from results and download MP3!

🔧 **Commands:**
/help - Show all commands
/search <song> - Search for songs

Ready to download music? Send me a song name or YouTube URL! 🎶
        """
        
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        is_admin = await self.is_admin(user_id)
        
        help_text = """
🔰 **Simple Music Bot Commands**

**🎵 Music Commands:**
/search <song> - Search YouTube for songs
/lyrics <song> - Search for song lyrics

**📱 Quick Actions:**
📝 Send me a song name - I'll search automatically!
🔗 Send me a YouTube URL - I'll download it directly!

**💡 Supported URLs:**
• youtube.com/watch?v=...
• youtu.be/...
• m.youtube.com/watch?v=...

**💡 Features:**
🎵 MP3 (192kbps audio only)
🎶 High quality guaranteed
⚡ Fast downloads

Need help? Just ask! 🎶
        """
        
        if is_admin:
            help_text += """

**🛡️ Admin Commands:**
/addpromo - Admin control panel (shows all commands)
/broadcast <msg> - Send message to all users
/users - Show user statistics
/stats - Show download statistics
/admins - Show admin list
/setchannel @channel - Force users to join channel
/clearchannel - Remove forced channel
/delpromo - Remove promo banner"""
            
            if await self.is_primary_admin(user_id):
                help_text += """
/addadmin <id> - Add new admin (Primary only)
/deladmin <id> - Remove admin (Primary only)"""
            
            help_text += "\n            "
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        user_id = update.effective_user.id
        
        # Check channel membership (admins bypass)
        if not await self.is_admin(user_id):
            if not await self.check_channel_membership(user_id, context):
                await self.send_channel_join_message(update)
                return
        
        if not context.args:
            await update.message.reply_text("Please provide a song name to search.\n\nExample: `/search despacito`", parse_mode=ParseMode.MARKDOWN)
            return
        
        query = ' '.join(context.args)
        await self.handle_search(update, query)
    
    async def lyrics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lyrics command"""
        user_id = update.effective_user.id
        
        # Check channel membership (admins bypass)
        if not await self.is_admin(user_id):
            if not await self.check_channel_membership(user_id, context):
                await self.send_channel_join_message(update)
                return
        
        if not context.args:
            await update.message.reply_text("Please provide a song name to search for lyrics.\n\nExample: `/lyrics despacito`", parse_mode=ParseMode.MARKDOWN)
            return
        
        query = ' '.join(context.args)
        await self.handle_lyrics_search(update, query)
    
    async def handle_lyrics_search(self, update: Update, query: str):
        """Handle lyrics search functionality"""
        user_id = update.effective_user.id
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Send searching message
        searching_msg = await update.message.reply_text(f"🔍 Searching lyrics for: **{self.escape_markdown(query)}**...", parse_mode=ParseMode.MARKDOWN)
        
        try:
            # Search for lyrics
            lyrics_info = await self.lyrics.search_lyrics(query)
            
            if not lyrics_info:
                await searching_msg.edit_text("❌ No lyrics found. Please try a different search term or check the spelling.")
                return
            
            # Format and send lyrics info
            lyrics_text = self.lyrics.format_lyrics_info(lyrics_info)
            
            # Create keyboard with download option
            keyboard = [
                [InlineKeyboardButton("🎵 Download MP3", callback_data=f"lyrics_download:{lyrics_info['title']} {lyrics_info['artist']}")],
                [InlineKeyboardButton("🔍 Search Again", callback_data="lyrics_search_again")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await searching_msg.edit_text(lyrics_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Lyrics search error: {e}")
            await searching_msg.edit_text(f"❌ **Error searching lyrics:** {str(e)}")
    
    async def handle_search(self, update: Update, query: str):
        """Handle search functionality"""
        user_id = update.effective_user.id
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Send searching message
        searching_msg = await update.message.reply_text(f"🔍 Searching for: **{self.escape_markdown(query)}**...", parse_mode=ParseMode.MARKDOWN)
        
        # Search YouTube
        videos = await self.youtube.search_videos(query, max_results=8)
        
        if not videos:
            await searching_msg.edit_text("❌ No results found. Please try a different search term.")
            return
        
        # Create inline keyboard with results
        keyboard = []
        for i, video in enumerate(videos):
            title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
            # Remove problematic characters for button text
            clean_title = title.replace('*', '').replace('_', '').replace('[', '').replace(']', '')
            keyboard.append([InlineKeyboardButton(
                f"🎵 {clean_title}",
                callback_data=f"download_mp3:{video['id']}:{i}"
            )])
            keyboard.append([InlineKeyboardButton(
                f"📹 {clean_title} (MP4)",
                callback_data=f"download_mp4:{video['id']}:{i}"
            )])
        
        # Add lyrics and search again buttons
        keyboard.append([InlineKeyboardButton("📝 Get Lyrics", callback_data=f"get_lyrics:{query}")])
        keyboard.append([InlineKeyboardButton("🔄 Search Again", callback_data="search_again")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store search results in user session
        self.user_sessions[user_id] = {
            'search_results': videos,
            'query': query
        }
        
        result_text = f"🎵 **Search Results for:** {self.escape_markdown(query)}\n\nChoose a song to download as MP3:"
        await searching_msg.edit_text(result_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_youtube_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Handle direct YouTube URL downloads"""
        user_id = update.effective_user.id
        
        # Update user activity
        self.db.update_user_activity(user_id)
        
        # Send processing message
        processing_msg = await update.message.reply_text("🔍 **Processing YouTube URL...**", parse_mode=ParseMode.MARKDOWN)
        
        try:
            # Get video info
            video_info = await self.youtube.get_video_info(url)
            if not video_info:
                await processing_msg.edit_text("❌ **Error:** Could not get video information. Please check the URL.")
                return
            
            # Create confirmation message
            safe_title = self.escape_markdown(video_info['title'][:80])
            safe_channel = self.escape_markdown(video_info['channel'])
            duration_text = f" \\({video_info['duration']}\\)" if video_info.get('duration') else ""
            
            confirm_text = f"""
🎵 **Video Found:**
📺 **{safe_title}**
👤 **By:** {safe_channel}{duration_text}

Do you want to download this as MP3?
            """
            
            # Create confirmation keyboard
            keyboard = [
                [InlineKeyboardButton("✅ Download MP3", callback_data=f"url_download_mp3:{video_info['id']}")],
                [InlineKeyboardButton("📹 Download MP4", callback_data=f"url_download_mp4:{video_info['id']}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_download")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Store video info in user session
            self.user_sessions[user_id] = {
                'url_video': video_info,
                'original_url': url
            }
            
            await processing_msg.edit_text(confirm_text.strip(), reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error processing YouTube URL: {e}")
            await processing_msg.edit_text(f"❌ **Error:** {str(e)}")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages as search queries or YouTube URLs"""
        user_id = update.effective_user.id
        
        # Check if user is admin (admins bypass channel check)
        if not await self.is_admin(user_id):
            # Check channel membership
            if not await self.check_channel_membership(user_id, context):
                await self.send_channel_join_message(update)
                return
        
        message_text = update.message.text.strip()
        
        # Ignore if it starts with a command
        if message_text.startswith('/'):
            return
        
        # Check if it's a YouTube URL
        if self.is_youtube_url(message_text):
            await self.handle_youtube_url(update, context, message_text)
        else:
            # Treat as search query
            await self.handle_search(update, message_text)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id
        data = query.data

        # Music main menu buttons
        if data.startswith("music_"):
            if data == "music_youtube":
                await query.edit_message_text("� *YouTube Music Search*\n\nSend a song name or YouTube link.", parse_mode=ParseMode.MARKDOWN)
            elif data == "music_ytmusic":
                await query.edit_message_text("🎵 *YT Music Search*\n\nSend a song name for YT Music.", parse_mode=ParseMode.MARKDOWN)
            elif data == "music_lyrics":
                await query.edit_message_text("� *Lyrics Search*\n\nSend a song name for lyrics.", parse_mode=ParseMode.MARKDOWN)
            elif data == "music_top":
                await query.edit_message_text("� *Top Charts*\n\nFeature coming soon!", parse_mode=ParseMode.MARKDOWN)
            elif data == "music_downloads":
                await query.edit_message_text("📂 *My Downloads*\n\nFeature coming soon!", parse_mode=ParseMode.MARKDOWN)
            elif data == "music_back":
                await query.edit_message_text("⬅️ *Back*\n\nReturning to previous menu.", parse_mode=ParseMode.MARKDOWN)
            elif data == "music_mainmenu":
                await query.edit_message_text("⬆️ *Main Menu*\n\nReturning to main menu.", parse_mode=ParseMode.MARKDOWN)
            return

        # ...existing code for admin panel and other buttons...
    
    async def handle_mp3_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle MP3 download request"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        _, video_id, result_index = query.data.split(':')
        result_index = int(result_index)
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please search again.")
            return
        
        videos = self.user_sessions[user_id]['search_results']
        if result_index >= len(videos):
            await query.edit_message_text("❌ Invalid selection. Please search again.")
            return
        
        video = videos[result_index]
        video_url = video['url']
        
        # Show processing message
        safe_title = self.escape_markdown(video['title'][:50])
        processing_msg = await query.edit_message_text(
            f"⏳ **Processing your MP3 download...**\n\n"
            f"🎵 **Song:** {safe_title}...\n"
            f"📁 **Format:** MP3\n\n"
            f"Please wait, this may take a few moments...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await self.process_mp3_download(user_id, video, video_url, processing_msg, context)
        except Exception as e:
            logger.error(f"Download error: {e}")
            await processing_msg.edit_text(
                f"❌ **Download failed!**\n\n"
                f"Error: {str(e)[:100]}...\n\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def process_mp3_download(self, user_id: int, video: dict, video_url: str, processing_msg, context):
        """Process MP3 download"""
        try:
            # Download audio
            audio_file = await self.youtube.download_audio(video_url, self.temp_dir)
            if not audio_file:
                raise Exception("Failed to download audio")
            
            # Get file info
            file_size = os.path.getsize(audio_file)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            
            # Send file
            safe_title = self.escape_markdown(video['title'][:50])
            safe_channel = self.escape_markdown(video['channel'])
            caption = f"""
🎵 **{safe_title}...**
📺 **Channel:** {safe_channel}
📦 **Size:** {file_size_mb} MB
🎯 **Quality:** 192kbps MP3
            """
            
            await processing_msg.edit_text("📤 **Uploading your MP3...**", parse_mode=ParseMode.MARKDOWN)
            
            with open(audio_file, 'rb') as audio:
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=audio,
                    caption=caption.strip(),
                    parse_mode=ParseMode.MARKDOWN,
                    title=video['title'],
                    performer=video['channel']
                )
            
            # Record download
            self.db.add_download(user_id, video['title'], 'mp3')
            
            # Clean up
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
            await processing_msg.edit_text(
                "✅ **Download Complete!**\n\n"
                "Your MP3 has been sent above! 🎵",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Send promotional content after download
            await self.send_promotional_content(user_id, context)
            
            # Auto-delete processing message after 30 seconds
            asyncio.create_task(self.auto_delete_message(processing_msg, 30))
        
        except Exception as e:
            raise Exception(f"MP3 processing failed: {str(e)}")
    
    async def handle_mp4_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle MP4 download request"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        _, video_id, result_index = query.data.split(':')
        result_index = int(result_index)
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please search again.")
            return
        
        videos = self.user_sessions[user_id]['search_results']
        if result_index >= len(videos):
            await query.edit_message_text("❌ Invalid selection. Please search again.")
            return
        
        video = videos[result_index]
        video_url = video['url']
        
        # Show processing message
        safe_title = self.escape_markdown(video['title'][:50])
        processing_msg = await query.edit_message_text(
            f"⏳ **Processing your MP4 download...**\n\n"
            f"📹 **Video:** {safe_title}...\n"
            f"📁 **Format:** MP4\n\n"
            f"Please wait, this may take a few moments...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await self.process_mp4_download(user_id, video, video_url, processing_msg, context)
        except Exception as e:
            logger.error(f"Download error: {e}")
            await processing_msg.edit_text(
                f"❌ **Download failed!**\n\n"
                f"Error: {str(e)[:100]}...\n\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def process_mp4_download(self, user_id: int, video: dict, video_url: str, processing_msg, context):
        """Process MP4 download"""
        try:
            # Download video
            video_file = await self.youtube.download_video(video_url, self.temp_dir)
            if not video_file:
                raise Exception("Failed to download video")
            
            # Get file info
            file_size = os.path.getsize(video_file)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            
            # Send file
            safe_title = self.escape_markdown(video['title'][:50])
            safe_channel = self.escape_markdown(video['channel'])
            caption = f"""
📹 **{safe_title}...**
📺 **Channel:** {safe_channel}
📦 **Size:** {file_size_mb} MB
🎯 **Quality:** MP4 Video
            """
            
            await processing_msg.edit_text("📤 **Uploading your MP4...**", parse_mode=ParseMode.MARKDOWN)
            
            with open(video_file, 'rb') as video:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video,
                    caption=caption.strip(),
                    parse_mode=ParseMode.MARKDOWN,
                    supports_streaming=True
                )
            
            # Record download
            self.db.add_download(user_id, video['title'], 'mp4')
            
            # Clean up
            if os.path.exists(video_file):
                os.remove(video_file)
            
            await processing_msg.edit_text(
                "✅ **Download Complete!**\n\n"
                "Your MP4 has been sent above! 📹",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Send promotional content after download
            await self.send_promotional_content(user_id, context)
            
            # Auto-delete processing message after 30 seconds
            asyncio.create_task(self.auto_delete_message(processing_msg, 30))
        
        except Exception as e:
            raise Exception(f"MP4 processing failed: {str(e)}")
    
    async def handle_url_mp4_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle MP4 download from URL"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please send the URL again.")
            return
        
        video_info = self.user_sessions[user_id]['url_video']
        original_url = self.user_sessions[user_id]['original_url']
        
        # Show processing message
        safe_title = self.escape_markdown(video_info['title'][:50])
        processing_msg = await query.edit_message_text(
            f"⏳ **Processing your MP4 download...**\n\n"
            f"📹 **Video:** {safe_title}...\n"
            f"📁 **Format:** MP4\n\n"
            f"Please wait, this may take a few moments...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await self.process_mp4_download(user_id, video_info, original_url, processing_msg, context)
        except Exception as e:
            logger.error(f"URL Download error: {e}")
            await processing_msg.edit_text(
                f"❌ **Download failed!**\n\n"
                f"Error: {str(e)[:100]}...\n\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def auto_delete_message(self, message, delay_seconds: int):
        """Auto-delete message after specified delay"""
        try:
            await asyncio.sleep(delay_seconds)
            await message.delete()
        except Exception as e:
            logger.error(f"Error auto-deleting message: {e}")
            
        except Exception as e:
            raise Exception(f"MP3 processing failed: {str(e)}")
    
    async def handle_url_mp3_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle MP3 download from URL"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please send the URL again.")
            return
        
        video_info = self.user_sessions[user_id]['url_video']
        original_url = self.user_sessions[user_id]['original_url']
        
        # Show processing message
        safe_title = self.escape_markdown(video_info['title'][:50])
        processing_msg = await query.edit_message_text(
            f"⏳ **Processing your MP3 download...**\n\n"
            f"🎵 **Song:** {safe_title}...\n"
            f"📁 **Format:** MP3\n\n"
            f"Please wait, this may take a few moments...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await self.process_mp3_download(user_id, video_info, original_url, processing_msg, context)
        except Exception as e:
            logger.error(f"URL Download error: {e}")
            await processing_msg.edit_text(
                f"❌ **Download failed!**\n\n"
                f"Error: {str(e)[:100]}...\n\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_lyrics_search_from_button(self, update: Update, search_query: str):
        """Handle lyrics search from button click"""
        query = update.callback_query
        
        # Update message to show searching
        await query.edit_message_text(f"🔍 Searching lyrics for: **{self.escape_markdown(search_query)}**...", parse_mode=ParseMode.MARKDOWN)
        
        try:
            # Search for lyrics
            lyrics_info = await self.lyrics.search_lyrics(search_query)
            
            if not lyrics_info:
                await query.edit_message_text("❌ No lyrics found. Please try a different search term.")
                return
            
            # Format and send lyrics info
            lyrics_text = self.lyrics.format_lyrics_info(lyrics_info)
            
            # Create keyboard with download option
            keyboard = [
                [InlineKeyboardButton("🎵 Download MP3", callback_data=f"lyrics_download:{lyrics_info['title']} {lyrics_info['artist']}")],
                [InlineKeyboardButton("🔍 Search Again", callback_data="lyrics_search_again")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(lyrics_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Lyrics search error: {e}")
            await query.edit_message_text(f"❌ **Error searching lyrics:** {str(e)}")
    
    async def handle_lyrics_to_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE, song_info: str):
        """Handle download request from lyrics search"""
        query = update.callback_query
        
        # Update message to show searching
        await query.edit_message_text(f"🔍 Searching YouTube for: **{self.escape_markdown(song_info)}**...", parse_mode=ParseMode.MARKDOWN)
        
        try:
            # Search YouTube for the song
            videos = await self.youtube.search_videos(song_info, max_results=3)
            
            if not videos:
                await query.edit_message_text("❌ No YouTube results found for this song.")
                return
            
            # Create keyboard with video options
            keyboard = []
            for i, video in enumerate(videos):
                title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
                clean_title = title.replace('*', '').replace('_', '').replace('[', '').replace(']', '')
                keyboard.append([InlineKeyboardButton(
                    f"🎵 {clean_title}",
                    callback_data=f"download_mp3:{video['id']}:{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔄 Back to Lyrics", callback_data=f"get_lyrics:{song_info}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Store search results in user session
            user_id = update.effective_user.id
            self.user_sessions[user_id] = {
                'search_results': videos,
                'query': song_info
            }
            
            result_text = f"🎵 **YouTube Results for:** {self.escape_markdown(song_info)}\n\nChoose a song to download as MP3:"
            await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            await query.edit_message_text(f"❌ **Error searching YouTube:** {str(e)}")
    
    async def send_promotional_content(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Send promotional banner to user after download"""
        try:
            current_promo = self.db.get_current_promo()
            if not current_promo:
                return  # No promo to send
            
            # Simple separator
            await context.bot.send_message(
                chat_id=user_id,
                text="━━━━━━━━━━━━━━━━━━━",
                parse_mode=None
            )
            
            # Send promotional content
            await context.bot.send_photo(
                chat_id=user_id,
                photo=current_promo['file_id'],
                caption=current_promo['caption'],
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Promo send error: {e}")
            # Don't break download if promo fails
    
    # Admin Commands
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_user_ids
    
    async def is_primary_admin(self, user_id: int) -> bool:
        """Check if user is primary admin"""
        return user_id == self.primary_admin_id
    
    async def check_channel_membership(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is member of forced channel"""
        forced_channel = self.db.get_setting('forced_channel')
        if not forced_channel:
            return True  # No forced channel set
        
        try:
            member = await context.bot.get_chat_member(chat_id=forced_channel, user_id=user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            return True  # If we can't check, allow access
    
    async def send_channel_join_message(self, update: Update):
        """Send message asking user to join the channel"""
        forced_channel = self.db.get_setting('forced_channel')
        if forced_channel:
            keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{forced_channel[1:]}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🔒 **Channel Membership Required**\n\n"
                f"To use this bot, you must join our channel:\n"
                f"👉 {forced_channel}\n\n"
                f"After joining, send /start again to continue!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **Broadcast Message**\n\n"
                "Usage: `/broadcast <message>`\n\n"
                "This will send the message to all bot users.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        message = ' '.join(context.args)
        users = self.db.get_all_users()
        
        sent = 0
        failed = 0
        
        status_msg = await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")
        
        for user_id in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **Broadcast Message**\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
                sent += 1
            except Exception:
                failed += 1
            
            # Update status every 50 messages
            if (sent + failed) % 50 == 0:
                await status_msg.edit_text(
                    f"📤 Broadcasting...\n\n"
                    f"✅ Sent: {sent}\n"
                    f"❌ Failed: {failed}\n"
                    f"📊 Progress: {sent + failed}/{len(users)}"
                )
        
        await status_msg.edit_text(
            f"✅ **Broadcast Complete!**\n\n"
            f"📤 Total users: {len(users)}\n"
            f"✅ Successfully sent: {sent}\n"
            f"❌ Failed: {failed}"
        )
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        total_users, active_users = self.db.get_user_count()
        
        stats_text = f"""
👥 **User Statistics**

📊 **Total Users:** {total_users}
✅ **Active Users:** {active_users}
📈 **Growth Rate:** {active_users/max(total_users, 1)*100:.1f}%

📅 **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        download_stats = self.db.get_download_stats()
        user_stats = self.db.get_user_count()
        
        stats_text = f"""
📊 **Bot Statistics**

👥 **Users:**
• Total: {user_stats[0]}
• Active: {user_stats[1]}

💾 **Downloads:**
• Total: {download_stats['total']}
• Today: {download_stats['today']}
• MP3 Files: {download_stats['formats'].get('mp3', 0)}

📅 **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def admins_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admins command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        admin_list = "\n".join([f"• {admin_id}" for admin_id in self.admin_user_ids])
        
        admins_text = f"""
👑 **Bot Administrators**

**Admin User IDs:**
{admin_list}

**Total Admins:** {len(self.admin_user_ids)}

📅 **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(admins_text, parse_mode=ParseMode.MARKDOWN)
    
    async def setchannel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setchannel command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **Set Forced Channel**\n\n"
                "Usage: `/setchannel @channelusername`\n\n"
                "This will force all users to join the specified channel before using the bot.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        channel_username = context.args[0]
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
        
        # Save channel to database
        self.db.set_bot_setting('forced_channel', channel_username)
        
        await update.message.reply_text(
            f"✅ **Forced channel set!**\n\n"
            f"🔗 **Channel:** {channel_username}\n\n"
            f"Users must now join this channel to use the bot.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def clearchannel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clearchannel command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Remove forced channel from database
        self.db.delete_bot_setting('forced_channel')
        
        await update.message.reply_text(
            "✅ **Forced channel removed!**\n\n"
            "Users can now use the bot without joining any channel.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def addpromo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addpromo command (Admin only) - Simple promotional banner"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only command")
            return
        
        if not update.message.reply_to_message:
            # Show admin command menu with inline buttons
            keyboard = [
                [InlineKeyboardButton("📊 User Stats", callback_data="admin_users"),
                 InlineKeyboardButton("📈 Bot Stats", callback_data="admin_stats")],
                [InlineKeyboardButton("� Broadcast", callback_data="admin_broadcast"),
                 InlineKeyboardButton("👥 Admin List", callback_data="admin_list")],
                [InlineKeyboardButton("📺 Set Channel", callback_data="admin_setchannel"),
                 InlineKeyboardButton("🗑️ Clear Channel", callback_data="admin_clearchannel")],
                [InlineKeyboardButton("🎯 Add Promo", callback_data="admin_addpromo"),
                 InlineKeyboardButton("❌ Delete Promo", callback_data="admin_delpromo")]
            ]
            
            # Add primary admin only buttons
            if await self.is_primary_admin(update.effective_user.id):
                keyboard.append([
                    InlineKeyboardButton("➕ Add Admin", callback_data="admin_addadmin"),
                    InlineKeyboardButton("➖ Remove Admin", callback_data="admin_deladmin")
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🛡️ **Admin Control Panel**\n\n"
                "Choose an action below:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        replied_msg = update.message.reply_to_message
        if not replied_msg.photo:
            await update.message.reply_text("❌ Reply to a photo only")
            return
        
        # Get photo and caption
        photo = replied_msg.photo[-1]
        caption = ' '.join(context.args) if context.args else replied_msg.caption or ""
        
        if not caption:
            await update.message.reply_text(
                "❌ **Add caption!**\n\n"
                "`/addpromo Your promotional text`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Save promo (auto-replaces old one)
        promo_data = {
            'file_id': photo.file_id,
            'caption': caption,
            'created_at': datetime.now().isoformat()
        }
        
        self.db.delete_all_promos()  # Remove old
        self.db.add_promo(promo_data)  # Add new
        
        await update.message.reply_text(
            "✅ **Promo Added!**\n\n"
            f"📝 {caption[:100]}{'...' if len(caption) > 100 else ''}\n\n"
            f"🎯 Will show after every download",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def delpromo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delpromo command (Admin only) - Remove promotional banner"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only command")
            return
        
        # Check and remove promo
        current_promo = self.db.get_current_promo()
        if not current_promo:
            await update.message.reply_text(
                "❌ **No promo found**\n\n"
                "Use `/addpromo` to add one first",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Delete promo
        self.db.delete_all_promos()
        
        await update.message.reply_text(
            "✅ **Promo removed**\n\n"
            "Users won't see promo after downloads anymore",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def addadmin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addadmin command (Primary Admin only)"""
        if not await self.is_primary_admin(update.effective_user.id):
            await update.message.reply_text("❌ Only primary admin can add admins")
            return
        
        if not context.args:
            await update.message.reply_text(
                "👑 **Add New Admin**\n\n"
                "Usage: `/addadmin <user_id>`\n\n"
                "Example: `/addadmin 123456789`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            new_admin_id = int(context.args[0])
            
            if new_admin_id in self.admin_user_ids:
                await update.message.reply_text(f"❌ User {new_admin_id} is already an admin")
                return
            
            # Add to memory
            self.admin_user_ids.append(new_admin_id)
            
            # Update .env file
            new_admin_ids = ','.join(map(str, self.admin_user_ids))
            await self.update_env_file('ADMIN_USER_IDS', new_admin_ids)
            
            await update.message.reply_text(
                f"✅ **Admin Added!**\n\n"
                f"👤 User ID: {new_admin_id}\n"
                f"🔢 Total Admins: {len(self.admin_user_ids)}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Use numbers only.")
    
    async def deladmin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deladmin command (Primary Admin only)"""
        if not await self.is_primary_admin(update.effective_user.id):
            await update.message.reply_text("❌ Only primary admin can remove admins")
            return
        
        if not context.args:
            await update.message.reply_text(
                "🗑️ **Remove Admin**\n\n"
                "Usage: `/deladmin <user_id>`\n\n"
                "Example: `/deladmin 123456789`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            admin_id = int(context.args[0])
            
            if admin_id == self.primary_admin_id:
                await update.message.reply_text("❌ Cannot remove primary admin")
                return
            
            if admin_id not in self.admin_user_ids:
                await update.message.reply_text(f"❌ User {admin_id} is not an admin")
                return
            
            # Remove from memory
            self.admin_user_ids.remove(admin_id)
            
            # Update .env file
            new_admin_ids = ','.join(map(str, self.admin_user_ids))
            await self.update_env_file('ADMIN_USER_IDS', new_admin_ids)
            
            await update.message.reply_text(
                f"✅ **Admin Removed!**\n\n"
                f"👤 User ID: {admin_id}\n"
                f"🔢 Total Admins: {len(self.admin_user_ids)}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Use numbers only.")
    
    async def update_env_file(self, key: str, value: str):
        """Update .env file with new value"""
        try:
            env_path = '.env'
            if os.path.exists(env_path):
                # Read current content
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                # Update or add the key
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith(f'{key}='):
                        lines[i] = f'{key}={value}\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'{key}={value}\n')
                
                # Write back
                with open(env_path, 'w') as f:
                    f.writelines(lines)
                    
        except Exception as e:
            logger.error(f"Error updating .env file: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors gracefully"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Try to send an error message to the user
        try:
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ An error occurred while processing your request. Please try again.",
                    parse_mode=None
                )
        except Exception:
            pass  # If we can't send error message, just log it
    
    async def setup_bot_commands(self, application):
        """Setup bot commands menu"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help message"),
            BotCommand("search", "Search for songs"),
            BotCommand("lyrics", "Search for lyrics"),
        ]
        
        await application.bot.set_my_commands(commands)
    
    def run(self):
        """Start the bot"""
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("search", self.search_command))
        application.add_handler(CommandHandler("lyrics", self.lyrics_command))
        
        # Admin commands
        application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        application.add_handler(CommandHandler("users", self.users_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("admins", self.admins_command))
        application.add_handler(CommandHandler("setchannel", self.setchannel_command))
        application.add_handler(CommandHandler("clearchannel", self.clearchannel_command))
        application.add_handler(CommandHandler("addpromo", self.addpromo_command))
        application.add_handler(CommandHandler("delpromo", self.delpromo_command))
        application.add_handler(CommandHandler("addadmin", self.addadmin_command))
        application.add_handler(CommandHandler("deladmin", self.deladmin_command))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Add text message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        # Start the bot
        print("🎵 Simple Music Bot is starting...")
        print("✅ All handlers registered successfully!")
        print("🔧 Features: MP3 downloads + Lyrics + Admin commands")
        print("👑 Admin: @in_yogeshwar (ID: 7176592290)")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = SimpleMusicBot()
    bot.run()
