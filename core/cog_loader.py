# core/cog_loader.py
import os
from discord.ext import commands

async def load_all_cogs(bot):
    """Automatically load all .py files inside /cogs folder."""
    cogs_dir = os.path.join(os.path.dirname(__file__), "..", "cogs")
    cogs_dir = os.path.abspath(cogs_dir)

    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"  ✅ Loaded cog: {extension}")
            except Exception as e:
                print(f"  ❌ Failed to load {extension}: {e}")