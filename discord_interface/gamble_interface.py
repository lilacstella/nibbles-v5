import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import pytz
import secrets
import asyncio

from core.transaction_service import add_user_nomnoms


class Gamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spun_today = set()
        self.reset_spun_today.start()

    @app_commands.command(name="spin", description="Spin the wheel once a day for nom noms! (Jackpot of 10,000)")
    @app_commands.allowed_installs(guilds=True, users=False)
    async def spin(self, interaction: discord.Interaction):
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
                              color=color,
                              url=thumbnail_url)
        embed.set_image(url="https://i.pinimg.com/originals/94/cc/d5/94ccd56f2a24d1eb9486d86fcee0b3b1.gif")
        embed.set_author(name=user.display_name)
        embed.set_footer(text="best of luck!", icon_url="https://cdn.discordapp.com/emojis/948031133281562724.webp")

        await interaction.response.send_message(content="Spinning the Wheel of Fortune", embed=embed)

        if secrets.randbelow(100) == 0:
            result = 10000
        else:
            result = secrets.randbelow(2100 - 700) + 701

        new_bal = add_user_nomnoms(user.id, result)
        self.spun_today.add(user.id)

        embed = discord.Embed(title="**REWARDS**", color=color, url=thumbnail_url)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_author(name=user.display_name)
        embed.add_field(name="Prize", value=f"{result} nom noms", inline=False)
        embed.add_field(name="Current Balance", value=str(new_bal), inline=False)

        await asyncio.sleep(3)
        await interaction.edit_original_response(content='Wheel of Fortune Results', embed=embed)

    @tasks.loop(time=datetime.time(hour=3, minute=30, tzinfo=pytz.timezone('America/Chicago')))
    async def reset_spun_today(self):
        self.spun_today.clear()


async def setup(bot):
    await bot.add_cog(Gamble(bot=bot))
