from discord.ext import commands
import discord

TOKEN = "MTE5MzMwNTE4OTYyOTgzNzQxNg.GPV__o.oOAF25BbUKZI4rolc3YjacIUwIYSrOywa1ujN8"
CHANNEL_ID = 376359510723264512

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("boas")

bot.run(TOKEN)