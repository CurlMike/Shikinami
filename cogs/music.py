from discord.ext import commands
from discord import FFmpegPCMAudio
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import discord
import asyncio
import yt_dlp as youtube_dl
import os

class Music (commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API"))

        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIFY_ID"),
        client_secret=os.getenv("SPOTIFY_SECRET"),
        redirect_uri="http://localhost/"))

        self.queue = []

        self.voice_clients = {}

        self.downloading = False

        self.ytdl = youtube_dl.YoutubeDL({
            'format': 'bestaudio/best',
            'outtmpl': 'audio.mp3'
        })

    def spotify_albumRequest(self, alubmid):
        return self.spotify.album_tracks(
            album_id=alubmid,
        )

    def spotify_playlistSongsRequest(self, playlistId, offset=0):
        return self.spotify.playlist_tracks(
            playlist_id=playlistId,
            fields= "items,total,next,limit,offset",
            offset=offset
        )

    def yt_searchRequest(self, query):
        return self.youtube.search().list(
            q = query,
            part = "snippet",
            type = "video",
            maxResults = 1
        ).execute()

    def yt_videoRequest(self, videoId):
        return self.youtube.videos().list(
            id = videoId,
            part = 'snippet, contentDetails'
        ).execute()

    def yt_playlistSongsRequest(self, playlistId, pageToken=None):
        return self.youtube.playlistItems().list(
            playlistId = playlistId,
            part = 'snippet',
            maxResults = 50,
            pageToken = pageToken
        ).execute()
    
    async def wait_for_dl(self, url):
        if os.path.exists("./audio.mp3"):
            os.remove("audio.mp3")
        task = asyncio.get_event_loop()

        def download_video():
            try:
                self.ytdl.download([url])
            except youtube_dl.utils.DownloadError:
                raise youtube_dl.DownloadCancelled
            
            return "audio.mp3"
        
        audio = await task.run_in_executor(None, download_video)

        return FFmpegPCMAudio(audio)
    
    def build_embed(self, ctx, url:str=None):
        if url is not None:
            video_id = url[url.find("=") + 1:url.find("&")]
            response = self.yt_videoRequest(video_id)
        else: return
        
        embed = discord.Embed(title=response['items'][0]['snippet']['title'], url=url
        ,color=0xFF0000)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
        embed.set_thumbnail(url=response['items'][0]['snippet']['thumbnails']['default']['url'])
        embed.add_field(name="Duration", value=response['items'][0]['contentDetails']['duration'][2:].lower(), inline=False)
        embed.add_field(name="Channel", value=response['items'][0]['snippet']['channelTitle'], inline=True)
        published_date = response['items'][0]['snippet']['publishedAt']
        published_date = published_date.partition("T")[0]
        embed.add_field(name="Published on", value=published_date, inline=True)

        return embed
    
    async def play_next(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if len(self.queue) > 0:
            self.downloading = True
            url = self.queue.pop(0)

            if url.startswith("https://open.spotify.com"):
                spotifyPlIndex = url.find("playlist/")
                if spotifyPlIndex != -1:
                    playlistId = url[spotifyPlIndex + 9:url.find("?")]
                    response = self.spotify_playlistSongsRequest(playlistId)
                    nSongs = 0

                    while (nSongs < response['total']):
                        for track in response['items']:
                            song_name = track['track']['name']
                            artists = " ".join([artist['name'] for artist in track['track']['artists']])
                            url = song_name + " " + artists
                            self.queue.append(url)
                            nSongs += 1
                        if response['next']:
                            response = self.spotify_playlistSongsRequest(playlistId, offset=nSongs)

                    await ctx.send("**(From Spotify Playlist):** Added a total of " + str(nSongs) + " songs to the queue.")

                else:
                    albumid = url[url.find("album/") + 6: url.find("?")]
                    response = self.spotify_albumRequest(albumid)
                    nSongs = 0

                    while (nSongs < response['total']):
                        for track in response['items']:
                            song_name = track['name']
                            artists = " ".join([artist['name'] for artist in track['artists']])
                            url = song_name + " " + artists
                            self.queue.append(url)
                            nSongs += 1
                    
                    await ctx.send("**(From Spotify Album):** Added a total of " + str(nSongs) + " songs to the queue.")

                url = self.queue.pop(0)
                
            if not url.startswith("https://www.youtube.com"):
                response = self.yt_searchRequest(url)

                if 'items' in response and len(response['items']) > 0:
                    video_url = "https://www.youtube.com/watch?v="
                    video_id = response['items'][0]["id"]["videoId"]
                    channel_title = response['items'][0]['snippet']['channelTitle']
                    channel_title = channel_title.replace(" ", "")
                    url = video_url + video_id + "&ab_channel=" + channel_title
                else:
                    await ctx.send("Nothing found. Moving on.")
                    self.downloading = False
                    await self.play_next(ctx=ctx)
                    return
                
            else:
                plIndex = url.find('list=')
                if plIndex != -1:

                    plEndIndex = url.find('&', plIndex)
                    if plEndIndex == -1:
                        plEndIndex = len(url)

                    playlistId = url[plIndex + 5:plEndIndex]
                    nSongs = 0
                    response = self.yt_playlistSongsRequest(playlistId)

                    while (nSongs < response['pageInfo']['totalResults']):
                        for item in response['items']:
                            url = "https://youtube.com/watch?v=" + item['snippet']['resourceId']['videoId']
                            self.queue.append(url)
                            nSongs += 1
                        if response['nextPageToken']:
                            response = self.yt_playlistSongsRequest(playlistId, pageToken=response['nextPageToken'])

                    await ctx.send("**(From YouTube Playlist):** Added a total of " + str(nSongs) + " songs to the queue.")
                    self.downloading = False
                    await self.play_next(ctx=ctx)
                    return
            try:
                source = await self.wait_for_dl(url=url)
            except youtube_dl.utils.DownloadCancelled:
                await ctx.send("Invalid URL. Moving on.")
                self.downloading = False
                await self.play_next(ctx=ctx)
                return
            
            await ctx.send("**Now Playing:**")
            await ctx.send(embed=self.build_embed(ctx, url=url))
            self.downloading = False

            voice.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        else:
            await ctx.send("Finished playing.")

    # Play a song given an url
    @commands.command(name="play", pass_context = True)
    async def play(self, ctx, *, url:str=None):
        if ctx.message.author.voice:
            if url is None:
                await ctx.send("No query given. Write something after '!play'.")
                return
            if self.bot.voice_clients:
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                if (voice.is_playing() or voice.is_paused()) or self.downloading:
                    self.queue.append(url)
                    await ctx.send("Song added to queue.")
                    return
            else:
                channel = ctx.message.author.voice.channel
                voice = await channel.connect()
                await ctx.guild.change_voice_state(channel=channel, self_deaf=True)

            self.queue.append(url)
            await self.play_next(ctx)
        else:
            await ctx.send("Join a voice channel first.")

    # Join a voice channel if not in one
    @commands.command(name="join", pass_context=True)
    async def join(self, ctx):
        if self.bot.voice_clients:
            await ctx.send("I am already in a channel")
        else:
            if ctx.message.author.voice is not None:
                channel = ctx.message.author.voice.channel
                await channel.connect()
                await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
            else:
                await ctx.send("Join a channel first.")

    # Leave the voice channel if in one
    @commands.command(pass_context=True)
    async def leave(self, ctx):
        if (ctx.voice_client):
            await ctx.guild.voice_client.disconnect()
            await ctx.send("Disconnected from voice channel.")
            self.queue = []
            if (os.path.exists("audio.mp3")):
                os.remove("audio.mp3")
        else:
            await ctx.send("I am not in a voice channel.")

    # Skip the current song
    @commands.command(pass_context=True)
    async def skip(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing() or voice.is_paused():
            voice.stop()
            await ctx.send("Skipping...")
        else:
            await ctx.send("Currently not playing any music.")

    # Stop playing the current audio
    @commands.command(pass_context = True)
    async def stop(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing() or voice.is_paused():
            self.queue = []
            voice.stop()
            if (os.path.exists("audio.mp3")):
                os.remove("audio.mp3")
        else:
            await ctx.send("Currently not playing any music.")

    # Pause the current song
    @commands.command(pass_context = True)
    async def pause(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
        elif voice.is_paused():
            await ctx.send("Already paused.")
        else:
            await ctx.send("Nothing is playing.")

    # Resume the current song
    @commands.command(pass_context = True)
    async def resume(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
        elif not voice.is_playing():
            await ctx.send("Nothing is playing.")
        else:
            await ctx.send("Audio is already playing.")

async def setup(bot):
    await bot.add_cog(Music(bot))
        
