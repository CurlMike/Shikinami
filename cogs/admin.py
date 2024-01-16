from discord.ext import commands
import discord

class Admin (commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.voice_clients = {}

async def setup(bot):
    await bot.add_cog(Admin(bot))
