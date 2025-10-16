import discord
from discord import app_commands
from discord.ui import Button, View
from discord.ext import commands

class JoinSecretSanta(Button):
    def __init__(self):
        super().__init__(label="join")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("hi")

class SecretSanta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="start a new secret santa session")
    @app_commands.guilds(805821298193465384)
    async def start_secret_santa(self, interaction: discord.Interaction):
        # start an embed
        # put a button to add the user to the embed
        # maintain a secret santa object with bot
        view = View(timeout=180)
        view.add_item(JoinSecretSanta())
        await interaction.response.send_message(interaction.user.mention, view=view)

async def setup(bot):
    await bot.add_cog(SecretSanta(bot=bot))
