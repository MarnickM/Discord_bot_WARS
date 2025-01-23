import discord
from discord.ui import View
from discord import ui
from typing import Optional, List
from database import database
import aiohttp
db_operations = database.DatabaseConnection()

API_NAME = "https://api.galaxylifegame.net/Users/name?name="


class buttonMenu(View):
    def __init__(self,pages: List, name: str): # user: Optional[discord.User] = None => is the user who can only interact with the button
        super().__init__(timeout=259200)
        self.pages = pages
        self.name = name
        

    async def get_page(self, page):
        if isinstance(page, str):
            return page
        elif isinstance(page, discord.Embed):
            return page
        return None


    async def show_page(self, page:int, interaction: discord.Interaction):
        page = await self.get_page(self.pages[page])
        await interaction.response.edit_message(embed=page, view=self)

    @ui.button(label="stats", emoji="🔎" , style=discord.ButtonStyle.gray)
    async def stats(self, interaction: discord.Interaction, button):
        await self.show_page(0, interaction)

    @ui.button(label="coords", emoji="🪐" , style=discord.ButtonStyle.gray)
    async def coords(self, interaction: discord.Interaction, button):
        await self.show_page(1, interaction)

    @ui.button(label="status", emoji="❔" , style=discord.ButtonStyle.gray)
    async def status(self, interaction: discord.Interaction, button):
        await self.show_page(2, interaction)
    
    @ui.button(label="alliance status", emoji="🛰️" , style=discord.ButtonStyle.gray)
    async def alliance_coords(self, interaction: discord.Interaction, button):
        await self.show_page(3, interaction)

    # @ui.button(label="alliance status", emoji="🌌" , style=discord.ButtonStyle.gray)
    # async def alliance_coords(self, interaction: discord.Interaction, button):
    #     await self.show_page(3, interaction)

    # add a user variable to the __init__ method to make this work and limit the usage of the button to a specific user
    # async def interaction_check(self, interaction: discord.Interaction) -> bool:
    #     if user:
    #         if interaction.user == self.user:
    #             await interaction.response.send_message("You are not allowed to interact with this button", ephemeral=True)
    #             return False
    #     return True