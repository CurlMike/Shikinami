from click import pass_context
from discord.ext import commands
import discord

class Admin (commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.voice_clients = {}

    @commands.command(name="disconnect", pass_context = True)
    async def disconnect(self, ctx, member: discord.Member):
        if ctx.message.author.guild_permissions.move_members:
            if member.voice:
                await member.move_to(None)
                await ctx.send(f"{member.mention} has been kicked from the voice channel.")
            else:
                await ctx.send(member.mention + " is not in that voice channel.")
        else:
            await ctx.send("You don't have permissions to do that.")

    @commands.command(name="kick", pass_context = True)
    async def kick(self, ctx, member: discord.Member, *, reason:str):
        if ctx.message.author.guild_permissions.kick_members:
            await member.kick(reason=reason)
            await ctx.send(f"{member.mention} was kicked from the server.")
            await ctx.send("**Reason: **" + reason)
        else:
            await ctx.send("You don't have permissions to do that.")

    @commands.command(name="ban", pass_context = True)
    async def ban(self, ctx, member: discord.Member, *, reason:str):
        if ctx.message.author.guild_permissions.ban_members:
            await member.ban(reason=reason)
            await ctx.send(f"{member.mention} was permanently banned from the server.")
            await ctx.send("**Reason: **" + reason)
        else:
            await ctx.send("You don't have permissions to do that.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
