# Discord Music Bot

A Discord bot that streams audio from YouTube directly to voice channels. Built with discord.py and yt-dlp.

## Features

✓ Stream YouTube videos and audio to Discord voice channels  
✓ Search for songs by title  
✓ Queue system for multiple songs  
✓ Play, pause, resume, skip, and stop controls  
✓ Automatic error handling and recovery  

## Quick Start

1. Install system dependencies (see **System Requirements** below)
2. Clone/extract this repository
3. Follow the **Installation** steps below
4. Run the bot with `python discord_bot.py`
5. Use commands in Discord!

## System Requirements

### Prerequisites
- Python 3.10 or higher
- Git (optional, for cloning)
- A Discord server where you have permissions

### Audio Libraries (Required!)

These must be installed system-wide **before** running the bot:

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y libopus0 libopus-dev libffi-dev ffmpeg
```

#### macOS
```bash
brew install opus ffmpeg libffi
```

#### Windows
1. Download FFmpeg: https://ffmpeg.org/download.html
2. Add FFmpeg to your PATH
3. Install Visual C++ build tools (if not already installed)

## Installation

### Step 1: Setup Virtual Environment

```bash
cd discord_bot
python3 -m venv bot-env
```

Activate the virtual environment:

**Linux/macOS:**
```bash
source bot-env/bin/activate
```

**Windows:**
```bash
bot-env\Scripts\activate
```

You should see `(bot-env)` at the start of your terminal line.

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install "discord.py[voice]" yt-dlp python-dotenv
```

### Step 3: Get Your Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** and give it a name (e.g., "Music Bot")
3. Go to the **"Bot"** section and click **"Add Bot"**
4. Under **TOKEN**, click **"Copy"** to copy your bot token
5. **Save this token - you'll need it in the next step**

### Step 4: Create `.env` File

In the `bot/` directory, create a file named `.env` and add:

```env
DISCORD_TOKEN=your_bot_token_here
```

Replace `your_bot_token_here` with the token you copied in Step 3.

### Step 5: Add Bot to Your Server

1. In Developer Portal, go to **OAuth2** → **URL Generator**
2. Select scopes: `bot`
3. Select permissions:
   - Send Messages
   - Connect (voice)
   - Speak
4. Copy the generated URL and open it in your browser
5. Select your server and click **Authorize**

### Step 6: Run the Bot

Navigate to the `bot/` directory and run:

```bash
cd bot
python discord_bot.py
```

You should see:
```
   Bot logged in as YourBotName#1234
```

**Success!** Your bot is now running. Go to your Discord server and try `!join`.

## Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `!join` | `!cum` | Join your voice channel |
| `!leave` | - | Leave voice channel |
| `!play <URL or search>` | - | Play song from YouTube |
| `!skip` | - | Skip current track |
| `!stop` | - | Stop playback and clear queue |
| `!pause` | - | Pause playback |
| `!resume` | - | Resume playback |
