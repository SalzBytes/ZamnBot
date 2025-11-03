import discord
from discord.ext import commands
import random

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        channel = member.guild.system_channel

        # Find general
        if channel is None:
            channel = discord.utils.get(member.guild.text_channels, name="general")
        # First channel
        if channel is None and member.guild.text_channels:
            channel = member.guild.text_channels[0]

        if channel is None:
            return

        embed = discord.Embed(
            title=f"👋 Welcome to {member.guild.name}!",
            description=f"Hello, {member.display_name}! Hope you've brought Pizza. 🍕",
            color=discord.Color.green(),
        )
        if member.display_avatar:
            embed.set_thumbnail(url=member.avatar.url)

        await channel.send(
            f"A new member has arrived! Give a warm welcome to {member.mention}!",
            embed=embed,
        )

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        await ctx.reply(f"🏓 | ...pong! In {round(self.bot.latency * 1000)}ms")

    @commands.hybrid_command(
        name="avatar", aliases=["a"], description="Display your avatar"
    )
    async def get_avatar(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author

        embed = discord.Embed(
            title=f"@{target.display_name}'s Avatar", color=discord.Color.dark_blue()
        )
        embed.set_image(url=target.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command()
    async def poll(ctx, *, title, question):
        embed = discord.Embed(title=title, description=question)
        poll_message = await ctx.send(embed=embed)
        await poll_message.add_reaction("👍")
        await poll_message.add_reaction("👎")

async def setup(bot):
    await bot.add_cog(Utilities(bot))
