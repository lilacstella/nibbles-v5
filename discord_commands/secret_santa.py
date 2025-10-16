from discord import app_commands
from discord.ext import commands


# all cogs inherit from this base class
class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # adding a bot attribute for easier access

    @app_commands.command(name="ping", description="the second best command in existence")
    @app_commands.guilds(805821298193465384)
    async def slash_pingcmd(self, interaction):
        """the second best command in existence"""
        await interaction.response.send_message(interaction.user.mention)

async def setup(bot):
    await bot.add_cog(ExampleCog(bot=bot))
