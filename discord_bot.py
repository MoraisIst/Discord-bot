# filepath: /home/morais/discord_bot/bot/discord_bot.py
"""Discord Music Bot - Stream audio from YouTube to voice channels."""

import asyncio
import os
import sys
import traceback
from collections import deque
from typing import Optional
import time
import api
import uvicorn
import discord
import yt_dlp
from discord.ext import commands
from dotenv import load_dotenv

# ============================================================================
# DATA MODELS
# ============================================================================


class Track:
    """Represents a music track with metadata."""

    def __init__(self, url: str, title: str, duration: int, thumbnail: Optional[str]):
        self.url = url
        self.title = title
        self.duration = duration
        self.thumbnail = thumbnail


# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not set in .env file")

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",  # no video
}

# ============================================================================
# UTILITIES
# ============================================================================


def parse_input(query: str) -> str:
    """Convert user input to yt-dlp compatible search query."""
    if query.startswith(("https://", "http://", "www.")):
        return query
    return f"ytsearch:{query}"


def get_audio_info(query: str) -> Track:
    """Extract audio URL and metadata from YouTube."""
    search = parse_input(query)

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(search, download=False)
        if "entries" in info:
            info = info["entries"][0]

        return Track(
            url=info["url"],
            title=info.get("title", "Unknown"),
            duration=info.get("duration", 0),
            thumbnail=info.get("thumbnail"),
        )


# ============================================================================
# MUSIC COG
# ============================================================================


class MusicCog(commands.Cog):
    """Handles music playback in voice channels."""

    _instance: Optional["MusicCog"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MusicCog, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "MusicCog":
        if cls._instance is None:
            raise ValueError("MusicCog instance not created yet.")
        return cls._instance

    def __init__(self, bot: commands.Bot):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.bot = bot
        self.queue: deque[Track] = deque()
        self.current: Optional[Track] = None
        self._vc: Optional[discord.VoiceClient] = None
        self.track_time: float = 0
        self._last_play_time: float = 0

    def is_inVoice(self) -> bool:
        """Check if bot is currently connected to a voice channel."""
        return self._vc is not None and self._vc.is_connected()

    def get_playback_time(self) -> float:
        """Calculate current playback time of the track."""
        if not self._vc or not self.current:
            return 0.0
        if self._vc.is_paused():
            return self.track_time

        elapsed = time.time() - self._last_play_time

    async def _cleanup(self) -> None:
        """Disconnect from voice and clear playback state."""
        if self._vc:
            try:
                await self._vc.disconnect(force=True)
            except Exception as e:
                print(f"[CLEANUP] Error disconnecting: {e}")
            self._vc = None
        self.queue.clear()
        self.current = None

    async def _ensure_connected(self, ctx: commands.Context) -> bool:
        """Connect to user's voice channel or return False."""
        # Validate user is in voice
        if not isinstance(ctx.author, discord.Member):
            await ctx.send("This command can only be used in a server.")
            return False

        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to use this command.")
            return False

        target_channel = ctx.author.voice.channel

        # Already connected to correct channel
        if self._vc and self._vc.is_connected() and self._vc.channel == target_channel:
            return True

        # Move to different channel
        if self._vc and self._vc.is_connected():
            try:
                await self._vc.move_to(target_channel)
                return True
            except Exception as e:
                print(f"[VOICE] Failed to move to {target_channel}: {e}")
                await self._cleanup()

        # Connect fresh
        try:
            self._vc = await target_channel.connect(reconnect=False)
            return True

        except discord.errors.ConnectionClosed as e:
            if e.code == 4017:
                await ctx.send(
                    "**Error**: Missing audio libraries. "
                    "See SETUP.md for installation instructions."
                )
            else:
                await ctx.send(f"Failed to connect: Error {e.code}")
            return False

        except Exception as e:
            print(f"[VOICE] Connection error: {e}")
            traceback.print_exc()
            await ctx.send(f"Failed to connect to voice channel: {e}")
            return False

    def _play_next(self, error: Optional[Exception] = None) -> None:
        """Callback to play next track in queue."""
        if error:
            print(f"[PLAYBACK] Error: {error}")

        # Stop if disconnected
        if not self._vc or not self._vc.is_connected():
            self.current = None
            return

        # Play next queued track
        if self.queue:
            self.current = self.queue.popleft()
            try:
                source = discord.FFmpegPCMAudio(self.current.url, **FFMPEG_OPTIONS)
                self._vc.play(source, after=self._play_next)
            except Exception as e:
                print(f"[PLAYBACK] Error starting next track: {e}")
                self.current = None
        else:
            self.current = None

    async def _play_impl(self, query: str) -> tuple[bool, str]:
        """Internal method to handle play logic."""
        if not self._vc or not self._vc.is_connected():
            return False, "Not connected to a voice channel."
        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None, get_audio_info, query
            )
        except Exception as e:
            return False, f"Error fetching audio: {e}"

        if self._vc.is_playing():
            self.queue.append(info)
            return True, f"Added to queue: **{info.title}**"
        else:
            source = discord.FFmpegPCMAudio(info.url, **FFMPEG_OPTIONS)
            self.current = info
            self._vc.play(source, after=self._play_next)
            self._last_play_time = time.time()
            return True, f"Now playing: **{info.title}**"

    # ========================================================================
    # COMMANDS
    # ========================================================================

    @commands.command(name="join", aliases=["cum"])
    async def join(self, ctx: commands.Context) -> None:
        """Connect bot to your voice channel."""
        if await self._ensure_connected(ctx):
            await ctx.send(f"Joined **{ctx.author.voice.channel.name}**.")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context) -> None:
        """Disconnect bot from voice channel."""
        await self._cleanup()
        await ctx.send("Left the voice channel and cleared the queue.")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Play audio from YouTube URL or search term.

        Usage: !play <url or search term>
        """
        success, message = await self._play_impl(query)
        await ctx.send(message)

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context) -> None:
        """Skip the current track."""
        if self._vc and self._vc.is_playing():
            self._vc.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context) -> None:
        """Stop playback and clear the queue."""
        if self._vc and self._vc.is_playing():
            self._vc.stop()
            self.queue.clear()
            self.current = None
            await ctx.send("Stopped playback and cleared the queue.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        """Pause the current track."""
        if self._vc and self._vc.is_playing():
            self._vc.pause()
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> None:
        """Resume paused playback."""
        if self._vc and self._vc.is_paused():
            self._vc.resume()
            await ctx.send("Resumed.")
        else:
            await ctx.send("Nothing is paused.")

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Handle bot being kicked/disconnected from voice."""
        # Only handle bot's own state changes
        if member.id != self.bot.user.id:
            return

        # Cleanup if bot disconnected
        if before.channel and not after.channel:
            print("[VOICE] Bot was disconnected from voice channel")
            await self._cleanup()

    @play.error
    async def play_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Handle errors in play command."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: `!play <url or search term>`")


# ============================================================================
# BOT SETUP
# ============================================================================


async def main() -> None:
    """Initialize and run the bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready() -> None:
        """Print login confirmation."""
        print(f"✓ Bot logged in as {bot.user}")

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """Process commands from messages."""
        if message.author == bot.user:
            return
        await bot.process_commands(message)

    @bot.event
    async def on_error(event, *args, **kwargs):
        print(f"Error in {event}: {sys.exc_info()}")

    await bot.add_cog(MusicCog(bot))

    config = uvicorn.Config(api.app, host="0.0.0.0", port=8001, log_level="warning")
    server = uvicorn.Server(config)

    try:
        await asyncio.gather(server.serve(), bot.start(TOKEN))
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    except Exception as e:
        print(f"Error starting bot or API server: {e}")
        traceback.print_exc()
    finally:
        await bot.close()
        await server.shutdown()


if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
