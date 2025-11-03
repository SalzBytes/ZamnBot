import discord
from discord.ext import commands
import asyncpg as acpg
from dotenv import load_dotenv
from core.databasehandler import DatabaseHandler
from core.paginator import PaginatorView
from typing import List
import traceback
import sys

class Memetics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.pool: acpg.Pool = self.bot.db_pool
        self.handler: DatabaseHandler = self.bot.db_handler

    @commands.hybrid_command(name="memetics", description="Shows a paginated list of all memetic records.")
    async def show_memetics(self, ctx: commands.Context):
        try:
            embeds: List[discord.Embed] = []
            records = await self.handler.get_memetics()

            if not records:
                return await ctx.send ("No memetics were found.")
            
            page_number = 1
            for chunk_records in discord.utils.as_chunks(records,10):
                embed = discord.Embed(title=f"Memetics - {page_number}", color=discord.Color.blue())
                for r in chunk_records:
                    embed.add_field(
                        name=f"{r["name"]} {r["icon"]}", value=r["description"], inline=False
                    )
                embeds.append(embed)
                page_number += 1

            total_pages = len(embeds)
            for i, embed in enumerate(embeds):
                embed.set_footer(text=f"Page {i + 1}/{total_pages}")

            view = PaginatorView(embeds=embeds)
            message = await ctx.send(embed=embeds[0], view=view)
            view.message = message #set the current embed to disable later

        except Exception:
            traceback.print_exc(file=sys.stderr)

async def setup(bot: commands.Bot):
    await bot.add_cog(Memetics(bot))
