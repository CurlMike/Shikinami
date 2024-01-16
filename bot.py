from discord.ext import commands
import discord
import asyncio
import os

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

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

async def load():
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    await load()
    await bot.start(os.getenv("DISCORD_BOT"))

asyncio.run(main())