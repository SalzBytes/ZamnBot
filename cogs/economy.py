import discord
from discord.ext import commands
import asyncpg as acpg
import os
from dotenv import load_dotenv
import datetime
import math
from core.databasehandler import DatabaseHandler

load_dotenv()
db_url = os.getenv("DATABASE_URL")

CLAIM_COOLDOWN_SECONDS = 8 * 60 * 60  # 8 hours
DAILY_REWARD = 500
INTEREST_RATE = 0.005  # 0.5%


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool: acpg.Pool = self.bot.db_pool
        self.handler: DatabaseHandler = self.bot.db_handler
        if self.pool is None:
            print("Warning: Database pool is None in Economy cog!")

    @commands.Cog.listener()
    async def on_ready(self):
        if self.pool is not None:
            return

    @commands.hybrid_command(
        name="daily", aliases=["claim"], description="Claim your daily credits"
    )
    async def daily(self, ctx: commands.Context):
        user_id = ctx.author.id

        try:
            claimed, daily_bonus, new_balance, streak, seconds_remaining = (
                await self.handler.process_daily_claim(
                    user_id=user_id,
                    daily_amount=DAILY_REWARD,
                    interest_rate=INTEREST_RATE,
                    cooldown=CLAIM_COOLDOWN_SECONDS,
                )
            )
            if claimed:
                body = (
                    f"🪙 You received **{daily_bonus} points**!\n"
                    f"✅ You're on a **{streak+1} claim streak**!"
                )
                embed = discord.Embed(
                    title="💰 Reward Claimed! [8 Hours]",
                    description=body,
                    color=discord.Color.gold(),
                )
                embed.set_footer(text=f"Your new balance is: {new_balance} points")
                await ctx.send(embed=embed)
            elif seconds_remaining:
                minutes, seconds = divmod(seconds_remaining, 60)
                hours, minutes = divmod(minutes, 60)

                return await ctx.send(
                    f"⏰ No **{ctx.author.display_name}**! You need to wait "
                    f"**{int(hours)}h {int(minutes)}m {int(seconds)}s**."
                )
            else:
                return await ctx.send("There was an error")

        except Exception as e:
            print(f"Daily command error for {ctx.author.id}: {e}")
            await ctx.send("An error occurred while processing your claim.")

    @commands.hybrid_command(
        name="balance", aliases=["b", "bl"], description="Display your current credits"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        if target.bot:
            return await ctx.send("Sir, That's a bot")
        user_id = target.id
        try:
            record = await self.handler.get_user_balance(user_id)
        except Exception as e:
            print(f"Error while getting user balance with id {user_id} : {e}")
            return await ctx.reply("There was a problem can not get your balance")

        embed = discord.Embed(title="💰 Balance", color=discord.Color.blue())

        if ctx.author.avatar:
            embed.set_thumbnail(url=target.avatar.url)

        if target == ctx.author:
            embed.description = f"**{target.display_name}**, your current balance is:"
            embed.add_field(
                name="Current Points",
                value=f"**{record['points']}** points",
                inline=False,
            )
            embed.add_field(
                name="Streak", value=f"**{record['daily_count']}** 🔥", inline=False
            )
        else:
            embed.description = f"**{target.display_name}**'s current balance is:"
            embed.add_field(
                name="Current Points",
                value=f"**{record['points']}** points",
                inline=False,
            )
            embed.add_field(
                name="Streak", value=f"**{record['daily_count']}** 🔥", inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="share", aliases=["sc"], description="Share your credits to other user"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def share_credits(
        self, ctx: commands.Context, member: discord.Member, amount: int
    ):
        if member.bot:
            return await ctx.send("You can't give points to bots.")
        if member is ctx.author:
            return await ctx.send("You can't give credits to yourself.")

        processed, new_balance = await self.handler(ctx.author.id, member.id, amount)

        if processed:
            if new_balance > 0:
                await ctx.send(
                    f"**{ctx.author.display_name}** gives **{member.display_name}** {amount} credits"
                )
            else:
                await ctx.send(
                    f"**{ctx.author.display_name}**, you don't have enough points."
                )
        else:
            await ctx.send("There is an error while processing the command.")

    @commands.command(name="givecredits")
    @commands.is_owner()
    async def give_balance(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("Amount must be a number.")
        if member.bot:
            return await ctx.send("Sir that is a bot.")
        target = member
        user_id = target.id
        try:
            new_balance = await self.handler.add_points(user_id=user_id, amount=amount)
        except Exception as e:
            print(f"Error while giving user balance with id {user_id} : {e}")
            return await ctx.reply("There was a problem")
        await ctx.send(
            f"Gave {member.display_name} {amount} credits! New Balance: {new_balance}"
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if ctx.command not in self.get_commands():
            return
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                f"**{ctx.author.display_name}** |🚫 Invalid argument."
            )
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f"**{ctx.author.display_name}** |⏳ Wait {round(error.retry_after,1)}s to use that command again."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
