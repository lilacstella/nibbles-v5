import discord
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.none()
        )

    async def on_ready(self):
        print(f'logged in as {self.user}')

    # the method to override in order to run whatever you need before your bot starts
    async def setup_hook(self):
        await self.load_extension("discord_interface.secret_santa")
        # print(self.tree)
        # print(await self.tree.sync(guild=discord.Object(id='805821298193465384')))

import tomllib
with open('config/auth.toml', 'rb') as f:
    config = tomllib.load(f)

# Load cogs and run bot
if __name__ == "__main__":
    bot = Bot()
    bot.run(config['discord']['token'])
