from core.secret_santa_service import create_secret_santa_game

import discord
from discord import app_commands, Embed
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

class Join(Button):
    def __init__(self):
        super().__init__(label="join", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        secret_santa_sessions[interaction.channel_id].add_participant(interaction.user.id)
        embeds[interaction.channel_id].update()
        await interaction.response.edit_message(embed=embeds[interaction.channel_id])

class Leave(Button):
    def __init__(self):
        super().__init__(label="leave", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        secret_santa_sessions[interaction.channel_id].participants.remove(interaction.user.id)
        embeds[interaction.channel_id].update()
        await interaction.response.edit_message(embed=embeds[interaction.channel_id])

class Start(Button):
    def __init__(self):
        super().__init__(label="start", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        secret_santa_sessions[interaction.channel_id].start(gift_count=2)
        await interaction.response.send_message("start da gam")

class StatusPage(Embed):
    def __init__(self, session: SecretSantaSession):
        super().__init__(title="Secret Santa Session")
        self.session = session
        self.update()

    def update(self):
        self.clear_fields()
        participant_mentions = [f"<@{user_id}>" for user_id in self.session.participants]
        self.add_field(name="Participants", value="\n".join(participant_mentions) if participant_mentions else "No participants yet.")
        

# channel_id: SecretSantaSession
secret_santa_sessions = {}
embeds = {}

class SecretSanta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="start a new secret santa session")
    @app_commands.guilds(805821298193465384)
    async def start_secret_santa(self, interaction: discord.Interaction):
        secret_santa_sessions[interaction.channel_id] = SecretSantaSession(interaction.guild_id, interaction.channel_id)
        view = View(timeout=None)
        view.add_item(Join())
        view.add_item(Leave())
        view.add_item(Start())
        embeds[interaction.channel_id] = StatusPage(secret_santa_sessions[interaction.channel_id])
        await interaction.response.send_message(view=view, embed=embeds[interaction.channel_id])

async def setup(bot):
    await bot.add_cog(SecretSanta(bot=bot))
