from discord.ext import commands
from discord import FFmpegPCMAudio
import discord
import yt_dlp as youtube_dl
import os

TOKEN = "MTE5MzMwNTE4OTYyOTgzNzQxNg.GPV__o.oOAF25BbUKZI4rolc3YjacIUwIYSrOywa1ujN8"
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
async def play(ctx, url:str):
    if (ctx.message.author.voice):
        channel = ctx.message.author.voice.channel
        voice = await channel.connect()
        await ctx.guild.change_voice_state(channel=channel, self_deaf=True)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, "audio.mp3")
    
        source = FFmpegPCMAudio("audio.mp3")
        voice.play(source)
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
    else:
        await ctx.send("I am not in a voice channel.")


# Stop playing the current audio
@bot.command(pass_context = True)
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if (voice.is_playing):
        voice.stop()
    else:
        await ctx.send("Currently not playing any music.")

# Pause the current song
@bot.command(pass_context = True)
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if (voice.is_playing):
        voice.pause()
    else:
        await ctx.send("Nothing is paused.")

# Resume the current song
@bot.command(pass_context = True)
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if (voice.is_playing):
        voice.resume()
    else:
        await ctx.send("Audio is already playing.")

bot.run(TOKEN)