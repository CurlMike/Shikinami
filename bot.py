from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from googleapiclient.discovery import build
import discord
import asyncio
import yt_dlp as youtube_dl
import os

youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API"))

voice_clients = {}

queue = []

downloading = False

ytdl = youtube_dl.YoutubeDL({
    'format': 'bestaudio/best',
    'outtmpl': 'audio.mp3'
})

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

def yt_searchRequest(query):
    request = youtube.search().list(
        q = query,
        part = "snippet",
        type = "video",
        maxResults = 1
    )
    response = request.execute()

    return response

def yt_videoRequest(videoId):
    request = youtube.videos().list(
        id = videoId,
        part = 'snippet, contentDetails'
    )
    response = request.execute()

    return response

async def wait_for_dl(url):
    if os.path.exists("./audio.mp3"):
        os.remove("audio.mp3")
    task = asyncio.get_event_loop()

    def download_video():
        try:
            ytdl.download([url])
        except youtube_dl.utils.DownloadError:
            raise youtube_dl.DownloadCancelled
        
        return "audio.mp3"
    
    audio = await task.run_in_executor(None, download_video)

    return FFmpegPCMAudio(audio)

def build_embed(ctx, url:str=None):
    if url is not None:
        start = url.find("=")
        end = url.find("&")
        video_id = url[start + 1:end]
        response = yt_videoRequest(video_id)
    else: return
    
    embed = discord.Embed(title=response['items'][0]['snippet']['title'], url=url
    ,color=0x800080)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
    embed.set_thumbnail(url=response['items'][0]['snippet']['thumbnails']['default']['url'])
    embed.add_field(name="Duration", value=response['items'][0]['contentDetails']['duration'][2:].lower(), inline=False)
    embed.add_field(name="Channel", value=response['items'][0]['snippet']['channelTitle'], inline=True)
    published_date = response['items'][0]['snippet']['publishedAt']
    published_date = published_date.partition("T")[0]
    embed.add_field(name="Published on", value=published_date, inline=True)

    return embed

async def play_next(ctx):
    global downloading
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if len(queue) > 0:
        downloading = True
        url = queue.pop(0)
        if not url.startswith("https://www.youtube.com"):
            response = yt_searchRequest(url)

            if 'items' in response and len(response['items']) > 0:
                video_url = "https://www.youtube.com/watch?v="
                video_id = response['items'][0]["id"]["videoId"]
                channel_title = response['items'][0]['snippet']['channelTitle']
                channel_title = channel_title.replace(" ", "")
                url = video_url + video_id + "&ab_channel=" + channel_title
            else:
                await ctx.send("Nothing found. Moving on.")
                await play_next(ctx=ctx)
                downloading = False
                return

        try:
            source = await wait_for_dl(url=url)
        except youtube_dl.utils.DownloadCancelled:
            await ctx.send("Invalid URL. Moving on.")
            downloading = False
            await play_next(ctx=ctx)
            return
        
        await ctx.send("**Now Playing:**")
        await ctx.send(embed=build_embed(ctx, url=url))
        downloading = False

        voice.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
    else:
        await ctx.send("Finished playing.")

# Play a song given an url
@bot.command(pass_context = True)
async def play(ctx, *, url:str=None):
    if ctx.message.author.voice:
        if url is None:
            await ctx.send("No query given. Write something after '!play'.")
            return
        if bot.voice_clients:
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if (voice.is_playing() or voice.is_paused()) or downloading:
                queue.append(url)
                await ctx.send("Song added to queue.")
                return
        else:
            channel = ctx.message.author.voice.channel
            voice = await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)

        queue.append(url)
        await play_next(ctx)
    else:
        await ctx.send("Join a voice channel first.")

# Join a voice channel if not in one
@bot.command(pass_context=True)
async def join(ctx):
    if bot.voice_clients:
        await ctx.send("I am already in a channel")
    else:
        if ctx.message.author.voice is not None:
            channel = ctx.message.author.voice.channel
            await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
        else:
            await ctx.send("Join a channel first.")

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

# Skip the current song
@bot.command(pass_context=True)
async def skip(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
        voice.stop()
    else:
        await ctx.send("Currently not playing any music.")

# Stop playing the current audio
@bot.command(pass_context = True)
async def stop(ctx):
    global queue
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing() or voice.is_paused():
        queue = []
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
    elif not voice.is_playing():
        await ctx.send("Nothing is playing.")
    else:
        await ctx.send("Audio is already playing.")

# Help command
@bot.command(pass_context = True)
async def shikihelp(ctx):
    embed = discord.Embed(title="Commands", color=0x800080, 
    description="Get help with all the commands here.")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
    embed.add_field(name="!play", value="Plays a youtube video of your choice. Use URL or keywords.", inline=False)
    embed.add_field(name="!stop", value="Stops playing the current song.", inline=False)
    embed.add_field(name="!pause", value="Pauses the current playing video.", inline=False)
    embed.add_field(name="!resume", value="Resumes playing the current video, if paused.", inline=False)
    embed.add_field(name="!join", value="Joins the user who wrote the command.", inline=False)
    embed.add_field(name="!leave", value="Leaves the voice channel if in one.", inline=False)

    await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_BOT"))