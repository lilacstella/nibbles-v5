import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import pytz
import secrets
import asyncio

from core.transaction_service import get_user_nomnoms, add_user_nomnoms


class Gamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard = {}
        self.spun_today = set()
        self.reset_spun_today.start()

    def cog_unload(self):
        self.reset_spun_today.cancel()

    @app_commands.command()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, private_channels=True, dms=True)
    async def balance(self, interaction: discord.Interaction):
        """
        Check your nom noms balance.
        """
        user = interaction.user
        balance = get_user_nomnoms(user.id)

        if hasattr(user, 'guild_avatar') and user.guild_avatar:
            thumbnail_url = user.guild_avatar.url
        else:
            thumbnail_url = user.avatar.url
        color = discord.Colour(secrets.randbelow(0xFFFFFF))

        embed = discord.Embed(title="**NOM NOMS BALANCE**",
                              color=color)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_author(name=user.display_name)
        embed.add_field(name="Current Balance", value=f"{balance} 🍪", inline=False)

        await interaction.response.send_message(content="Your Nom Noms Balance", embed=embed)

    @app_commands.command()
    @app_commands.allowed_installs(guilds=True, users=False)
    async def spin(self, interaction: discord.Interaction) -> None:
        """
        Spin the wheel once a day for nom noms! (Jackpot of 10,000)
        """
        user = interaction.user
        if user.id in self.spun_today:
            await interaction.response.send_message("You have already spun the wheel today. Please try again tomorrow!",
                                                    ephemeral=True)
            return

        if hasattr(user, 'guild_avatar') and user.guild_avatar:
            thumbnail_url = user.guild_avatar.url
        else:
            thumbnail_url = user.avatar.url
        color = discord.Colour(secrets.randbelow(0xFFFFFF))
        embed = discord.Embed(title="**SPINNING**",
                              color=color)
        embed.set_image(url="https://i.pinimg.com/originals/94/cc/d5/94ccd56f2a24d1eb9486d86fcee0b3b1.gif")
        embed.set_author(name=user.display_name)
        embed.set_footer(text="best of luck!", icon_url="https://cdn.discordapp.com/emojis/948031133281562724.webp")

        await interaction.response.send_message(content="Spinning the Wheel of Fortune", embed=embed)

        jackpot_probability = 100
        jackpot_prize = 10000

        max_prize = 2100
        min_prize = 700
        if secrets.randbelow(jackpot_probability) == 0:
            result = jackpot_prize
        else:
            result = secrets.randbelow(max_prize - min_prize) + min_prize

        new_highscore = False
        if self.leaderboard.get(interaction.channel_id, (None, 0))[1] < result:
            self.leaderboard[interaction.channel_id] = interaction.user, result
            new_highscore = True

        new_bal = add_user_nomnoms(user.id, result)
        self.spun_today.add(user.id)

        embed = discord.Embed(title="**REWARDS**", color=color)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_author(name=user.display_name)
        embed.add_field(name="Prize", value=f"{result} 🍪", inline=False)
        embed.add_field(name="Current Balance", value=str(new_bal), inline=False)
        if new_highscore:
            embed.set_footer(text=f"You got a new highscore! 👑 {user.display_name}")
        else:
            user, score = self.leaderboard[interaction.channel_id]
            embed.set_footer(text=f"High score today: {score} 🍪 by 👑 {user.display_name}")

        spin_animation_duration = 3
        await asyncio.sleep(spin_animation_duration)
        await interaction.edit_original_response(content='Wheel of Fortune Results', embed=embed)

    @tasks.loop(time=datetime.time(hour=3, minute=30, tzinfo=pytz.timezone('America/Chicago')))
    async def reset_spun_today(self):
        """
        Resets the spun_today set every day at 3:30 AM Central Time.
        """
        self.spun_today.clear()
        self.leaderboard.clear()


async def setup(bot):
    await bot.add_cog(Gamble(bot=bot))
