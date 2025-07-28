# Simple Music Bot

A Telegram bot for downloading YouTube music as MP3 files and searching song lyrics. Built with Python, featuring a clean interface and multiple admin support.

## 🎵 Features

- **YouTube Music Downloads**: Search and download songs as high-quality MP3 files (192kbps)
- **MP4 Video Downloads**: Download videos in MP4 format with audio support
- **Direct URL Support**: Download directly from YouTube URLs (youtube.com, youtu.be, etc.)
- **Lyrics Search**: Find song lyrics using Genius API integration
- **Multiple Admin Support**: Support for multiple bot administrators with primary admin control
- **User Management**: Track users and download statistics
- **Broadcast System**: Send messages to all bot users
- **Promotional System**: Auto-display promotional content after downloads
- **Mobile-Friendly Interface**: Inline buttons optimized for mobile users
- **Auto-Delete Messages**: Automatic cleanup of processing messages
- **Clean Interface**: Simple, user-friendly Telegram interface

## 🚀 Commands

### Public Commands
- `/start` - Start the bot and see welcome message
- `/help` - Show help and available commands
- `/search <song>` - Search YouTube for songs
- `/lyrics <song>` - Search for song lyrics

### Admin Commands
- `/broadcast <message>` - Send message to all users
- `/users` - Show user statistics
- `/stats` - Show download statistics
- `/admins` - Show admin list

## 🔐 Admin Commands (for administrators only)

**Primary Admin:** @in_yogeshwar (ID: 7176592290)

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and see welcome message |
| `/help` | Show help and available commands |
| `/search <song>` | Search YouTube for songs |
| `/lyrics <song>` | Search for song lyrics |
| `/musicmenu` | Show music features menu (inline buttons) |
| `/broadcast <message>` | Send message to all users (admin only) |
| `/users` | Show user statistics (admin only) |
| `/stats` | Show download statistics (admin only) |
| `/admins` | Show admin list (admin only) |
| `/addpromo` | Add or update promo banner (admin only) |
| `/delpromo` | Remove current promo banner (admin only) |
| `/setchannel @channelusername` | Force users to join a channel (admin only) |
| `/clearchannel` | Remove forced join (admin only) |
| `/addadmin <user_id>` | Add new admin (primary admin only) |
| `/deladmin <user_id>` | Remove admin (primary admin only) |

### 🎯 Promotional System

### 👑 Admin Management System

The bot has a **hierarchical admin system** with one primary admin and multiple secondary admins:

#### **Primary Admin (Unchangeable)**
- **ID**: 7176592290 (@in_yogeshwar)
- **Powers**: All admin commands + add/remove other admins
- **Status**: Cannot be removed or changed

#### **Secondary Admins**
- **Powers**: All admin commands except add/remove admins
- **Management**: Can be added/removed by primary admin only
- **Commands**: 
  - `/addadmin <user_id>` - Add new admin
  - `/deladmin <user_id>` - Remove existing admin

#### **Admin Control Panel**
When any admin types `/addpromo`, they get a **mobile-friendly button panel**:
```
🛡️ Admin Control Panel
┌─────────────────────────┐
│ 📊 User Stats  📈 Bot Stats │
│ 📢 Broadcast   👥 Admin List │
│ 📺 Set Channel 🗑️ Clear Channel │
│ 🎯 Add Promo   ❌ Delete Promo │
│ ➕ Add Admin   ➖ Remove Admin │ ← Primary only
└─────────────────────────┘
```

### Admin Features
- **User Management**: Track and manage bot users
- **Broadcasting**: Send announcements to all users
- **Channel Management**: Force channel subscriptions
- **Promotional Content**: Automatic promotional banners after downloads
- **Statistics Monitoring**: View detailed usage analytics
- **Admin Management**: Primary admin can add/remove other admins
- **Mobile Control Panel**: Inline buttons for easy mobile administration
- **Auto-Cleanup**: Messages auto-delete to keep chats clean

#### 🎯 Example: User Download Flow with Promotion
```
1. User downloads "Sahiba (Slowed + Reverb)"
2. User chooses: 🎵 MP3 (audio) 
3. Bot sends: 🎧 MP3 file (3.54 MB, 192kbps) 
4. Bot sends: ✅ Download Complete!
5. Bot sends: ━━━━━━━━━━━━━━━━━━━
6. Bot sends: [Your Promo Image]
            🎵 New song on Spotify!
            https://open.spotify.com/track/abc
7. Processing message auto-deletes after 30 seconds
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)
- YouTube API Key (from Google Cloud Console)
- Genius API Token (from Genius.com)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd YTMusicLabBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Bot Configuration
   BOT_TOKEN=your_telegram_bot_token
   YOUTUBE_API_KEY=your_youtube_api_key
   GENIUS_API_TOKEN=your_genius_api_token
   
   # Admin Configuration (comma-separated for multiple admins)
   ADMIN_USER_IDS=admin_user_id_1,admin_user_id_2
   
   # Optional Configuration
   DATABASE_PATH=bot_database.db
   DOWNLOADS_DIR=downloads
   TEMP_DIR=temp
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## 📱 Usage

### For Users
1. **Search for music**: Send any song name or use `/search <song>`
2. **Download from URL**: Send any YouTube URL directly
3. **Get lyrics**: Use `/lyrics <song>` or click "📝 Get Lyrics" in search results
4. **Download**: Click the download button and receive your MP3 file

### For Admins
- Use admin commands to manage users and broadcast messages
- View statistics and user activity
- Manage the bot effectively

## 🏗️ Project Structure

```
YTMusicLabBot/
├── main.py              # Main bot application
├── database.py          # Database management
├── youtube_service.py   # YouTube integration
├── lyrics_service.py    # Genius API integration
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── .gitignore          # Git ignore file
├── README.md           # This file
├── downloads/          # Downloaded files (temporary)
├── temp/               # Temporary processing files
└── bot_database.db     # SQLite database (auto-created)
```

## 🔧 Dependencies

- **python-telegram-bot** (22.3) - Telegram Bot API wrapper
- **yt-dlp** (2024.12.13) - YouTube downloader
- **python-dotenv** (1.0.1) - Environment variable management
- **requests** (2.31.0) - HTTP requests for Genius API

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | Yes |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | Yes |
| `GENIUS_API_TOKEN` | Genius API access token | Yes |
| `ADMIN_USER_IDS` | Comma-separated admin user IDs | Yes |
| `DATABASE_PATH` | SQLite database file path | No |
| `DOWNLOADS_DIR` | Downloads directory | No |
| `TEMP_DIR` | Temporary files directory | No |

### Getting API Keys

1. **Telegram Bot Token**:
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Copy the provided token

2. **YouTube API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable YouTube Data API v3
   - Create credentials (API Key)

3. **Genius API Token**:
   - Go to [Genius API](https://genius.com/api-clients)
   - Create a new app
   - Copy the client access token

## 🚫 What's NOT Included

This bot is designed to be simple and focused. It does NOT include:
- Audio effects or processing
- Video thumbnails
- Third-party audio enhancement
- FFmpeg dependencies
- Complex audio formats
- Advertisement systems
- SEO or metadata embedding

## 📊 Database

The bot uses SQLite database with the following tables:
- **users**: User information and activity tracking
- **downloads**: Download history and statistics
- **bot_settings**: Bot configuration (forced channels, etc.)
- **promos**: Promotional content (images and captions)

## 🔒 Security

- Admin access is restricted to configured user IDs
- Environment variables keep sensitive data secure
- Database stores minimal user information
- Temporary files are automatically cleaned up

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Bot not responding**: Check if bot token is correct and bot is started

3. **Download failures**: Verify YouTube API key and internet connection

4. **Lyrics not found**: Check Genius API token and song spelling

### Logs

The bot provides detailed logging. Check console output for error messages and debugging information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is for educational purposes. Users are responsible for complying with YouTube's Terms of Service and copyright laws. Only download content you have rights to or that is in the public domain.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [Genius API](https://docs.genius.com/) - Lyrics data provider

---

**Enjoy your Simple Music Bot! 🎵**
