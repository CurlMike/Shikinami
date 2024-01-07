from discord.ext import commands
from discord import FFmpegPCMAudio
from googleapiclient.discovery import build
import discord
import yt_dlp as youtube_dl
import os

youtube = build("youtube", "v3", developerKey=os.environ.get("YOUTUBE_API"))
CHANNEL_ID = 376359510723264512

voice_clients = {}

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors' : [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }]
}

ytdl = youtube_dl.YoutubeDL()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Play a song given an url
@bot.command(pass_context = True)
async def play(ctx, *, url:str=None):
    if ctx.message.author.voice:
        if bot.voice_clients:
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if voice.is_playing() or voice.is_paused():
                await ctx.send("I'm already playing something.")
                return
        else:
            channel = ctx.message.author.voice.channel
            voice = await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
        if url is None:
            await ctx.send("No query given. Write something after '!play'.")
            return

        if url.startswith("https://www.youtube.com"):
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except youtube_dl.utils.DownloadError:
                await ctx.send("Invalid URL.")
                return

            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    os.rename(file, "audio.mp3")  
            source = FFmpegPCMAudio("audio.mp3")
            voice.play(source)
        else:
            request = youtube.search().list(
                q = url,
                part = "snippet",
                type = "video",
                maxResults = 1
            )
            response = request.execute()

            if 'items' in response and len(response['items']) > 0:
                video_url = "https://www.youtube.com/watch?v="
                video_id = response['items'][0]["id"]["videoId"]
                channel_title = response['items'][0]['snippet']['channelTitle']
                channel_title = channel_title.replace(" ", "")
                video_url += video_id + "&ab_channel=" + channel_title

                try:
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                except youtube_dl.utils.DownloadError:
                    await ctx.send("Invalid URL.")
                    return

                for file in os.listdir("./"):
                    if file.endswith(".mp3"):
                        os.rename(file, "audio.mp3")  
                source = FFmpegPCMAudio("audio.mp3")
                voice.play(source)
                await ctx.send("Currently playing: " + video_url)
            else:
                await ctx.send("Nothing found.")
                return
    else:
        await ctx.send("Join a voice channel first.")

# Join a voice channel if not in one
@bot.command(pass_context=True)
async def join(ctx):
    if bot.voice_clients:
        await ctx.send("I am already in a channel")
    else:
        channel = ctx.message.author.voice.channel
        await channel.connect()
        await ctx.guild.change_voice_state(channel=channel, self_deaf=True)

# Leave the voice channel if in one
@bot.command(pass_context=True)
async def leave(ctx):
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Disconnected from voice channel.")
        if (os.path.exists("audio.mp3")):
            os.remove("audio.mp3")
    else:
        await ctx.send("I am not in a voice channel.")


# Stop playing the current audio
@bot.command(pass_context = True)
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
        voice.stop()
        if (os.path.exists("audio.mp3")):
            os.remove("audio.mp3")
    else:
        await ctx.send("Currently not playing any music.")

# Pause the current song
@bot.command(pass_context = True)
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    elif voice.is_paused():
        await ctx.send("Already paused.")
    else:
        await ctx.send("Nothing is playing.")

# Resume the current song
@bot.command(pass_context = True)
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("Audio is already playing.")

bot.run(os.environ.get("DISCORD_BOT"))