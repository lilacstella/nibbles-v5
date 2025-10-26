import tomllib
import discord
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
        await self.load_extension("discord_interface.secret_santa_interface")
        # print(self.tree)
        # print(await self.tree.sync(guild=discord.Object(id='805821298193465384')))
        print(await self.tree.sync(guild=discord.Object(id='607298393370394625')))

with open('config/env.toml', 'rb') as f:
    env = tomllib.load(f)

engine = create_engine(env[env['env']]['connection_string'], echo=True)
session_maker = sessionmaker(bind=engine)


with open('config/auth.toml', 'rb') as f:
    config = tomllib.load(f)

# Load cogs and run bot
if __name__ == "__main__":
    bot = Bot()
    bot.run(config['discord']['token'])
