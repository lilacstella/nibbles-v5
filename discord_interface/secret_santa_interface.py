from core.secret_santa_service import create_secret_santa_game

import discord
from discord import app_commands
from discord.ui import Button, View
from discord.ext import commands

# these objects are relevant prior to locking in an assignment
class SecretSantaSession:
    def __init__(self, guild_id: int, channel_id: int):
        # all these values are discord ids
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.participants = set()

    def add_participant(self, user_id: int):
        self.participants.add(user_id)

    def start(self, gift_count: int):
        create_secret_santa_game(self.guild_id, self.channel_id, self.participants, gift_count)

# channel_id: SecretSantaSession
secret_santa_sessions = {}

class JoinSecretSantaSession(Button):
    def __init__(self):
        super().__init__(label="join")

    async def callback(self, interaction: discord.Interaction):
        secret_santa_sessions[interaction.channel_id].add_participant(str(interaction.user.id))
        await interaction.response.send_message(f"hi {interaction.user.name}")

class StartSecretSantaSession(Button):
    def __init__(self):
        super().__init__(label="start")

    async def callback(self, interaction: discord.Interaction):
        secret_santa_sessions[interaction.channel_id].start(gift_count=2)
        await interaction.response.send_message("start da gam")

class SecretSanta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="start a new secret santa session")
    @app_commands.guilds(805821298193465384)
    async def start_secret_santa(self, interaction: discord.Interaction):
        secret_santa_sessions[interaction.channel_id] = SecretSantaSession(interaction.guild_id, interaction.channel_id)
        view = View(timeout=600)
        view.add_item(JoinSecretSantaSession())
        view.add_item(StartSecretSantaSession())
        await interaction.response.send_message(interaction.user.mention, view=view)

async def setup(bot):
    await bot.add_cog(SecretSanta(bot=bot))
