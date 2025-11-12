import tomllib
import discord
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

with open('config/env.toml', 'rb') as f:
    env_config = tomllib.load(f)

with open('config/auth.toml', 'rb') as f:
    auth_config = tomllib.load(f)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents(dm_messages=True)
        )

    async def on_ready(self):
        print(f'logged in as {self.user}')

    async def on_message(self, message: discord.Message):
        # Ignore messages from bots (including self after sending)
        if message.author and message.author.bot:
            return

        # If this message is a reply to another message and that referenced message
        # was authored by this bot, defer handling to the SecretSanta cog (if present).

        ref = getattr(message, "reference", None)
        if ref and getattr(ref, "message_id", None):
            referenced = None
            # try resolved object first (may be present if cached)
            referenced = getattr(ref, "resolved", None)
            if referenced is None:
                try:
                    referenced = await message.channel.fetch_message(ref.message_id)
                except Exception:
                    referenced = None

            if referenced and referenced.author and referenced.author.id == (self.user.id if self.user else None):
                cog = self.get_cog("SecretSanta")
                if cog and hasattr(cog, "on_reply_to_msg"):
                    try:
                        await cog.on_reply_to_msg(message)
                        return
                    except Exception as e:
                        # don't crash the bot on handler errors; log and continue
                        print("Error in SecretSanta.on_reply_to_msg:", e)

        # otherwise, other on_message handlers

    # the method to override in order to run whatever you need before your bot starts
    async def setup_hook(self):
        await self.load_extension("discord_interface.secret_santa_interface")
        await self.load_extension("discord_interface.misc_interface")

        if env_config['env'] == 'prod' or env_config['sync']:
            print("syncing commands globally")
            print(await self.tree.sync())

engine = create_engine(env_config[env_config['env']]['connection_string'], echo=True)
session_maker = sessionmaker(bind=engine)

# Load cogs and run bot
if __name__ == "__main__":
    bot = Bot()
    bot.run(auth_config['discord']['token'])
