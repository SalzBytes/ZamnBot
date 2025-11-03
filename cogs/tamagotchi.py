import os
from discord.ext import commands


class Tamagotchi(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.pool = None
        # if self.pool is None:
        #     print("Warning: Database pool is None in Economy cog!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Tamagotchi(bot=bot))
