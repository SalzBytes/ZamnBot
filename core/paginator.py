import discord
from typing import List, Deque, Optional, Union
from collections import deque
import sys, traceback

class PaginatorView(discord.ui.View):
    embeds: List[discord.Embed]
    queue: Deque[discord.Embed]
    len: int
    current_page: int
    message: Optional[discord.Message] = None

    def __init__(self, embeds: List[discord.Embed], timeout = 30):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.queue = deque(embeds)
        self.len = len(embeds)
        self.current_page = 1

    @discord.ui.button(label="Prev")
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.queue.rotate(1)
        embed: discord.Embed = self.queue[0]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next")
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.queue.rotate(-1)
        embed: discord.Embed = self.queue[0]
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)