import os
from discord.ext import commands
import random
import asyncpg as acpg

SLOTS_SYMBOLS = ["🍒", "🍇", "🍊", "🍋", "💰", "💎"]
WIN_MULTIPLIER = 5


class Gamba(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(
        name="slots", aliases=["sl"], description="Play slots machine"
    )
    async def slots(self, ctx):
        results = [random.choice(SLOTS_SYMBOLS) for _ in range(3)]
        display_results = f"|{'|'.join(results)}|"

        if results[0] == results[1] == results[2]:
            winnings = 100 * WIN_MULTIPLIER
            message = (
                f"**🎰 SLOT MACHINE SPIN 🎰**\n\n"
                f"**{display_results}**\n\n"
                f"🎉 **JACKPOT!** {results[0]}x3! You won {winnings} points! 🎉"
            )
        else:
            message = (
                f"**🎰 SLOT MACHINE SPIN 🎰**\n\n"
                f"**{display_results}**\n\n"
                f"Try again next time! Better luck soon. 💔"
            )

        await ctx.send(message)

    @commands.hybrid_command(name="roulette", description="Play a roulette game")
    async def roulette(self, ctx: commands.Context, trials: int = 1):
        CHAMBER = 6
        await ctx.send(f"Pulling the trigger for {trials} times...")
        marked_chamber = random.randint(1, CHAMBER)
        for trial in range(trials):
            pull_result = random.randint(1, CHAMBER)

            if marked_chamber == pull_result:
                await ctx.send(
                    f"**{ctx.author.display_name}**, You are dead after {trial+1} times"
                )
                return

        await ctx.send(f"**{ctx.author.display_name}**, You are still alive!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Gamba(bot=bot))
