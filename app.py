import discord
import tomllib

intents = discord.Intents(messages=True, reactions=True)

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'logged in as {client.user}')


with open('config/auth.toml', 'rb') as f:
    config = tomllib.load(f)

client.run(config['discord']['token'])
