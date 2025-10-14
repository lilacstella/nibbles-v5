import discord
import tomllib
from sqlalchemy import create_engine
from models.base import Base
from models.users import User
from models.secret_santa import SecretSantaAssignment

intents = discord.Intents(messages=True, reactions=True)
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'logged in as {client.user}')

# Load DB connection string and set up engine
with open('config/env.toml', 'rb') as f:
    env_config = tomllib.load(f)
connection_string = env_config[env_config['env']]['connection_string']
engine = create_engine(connection_string, echo=True)
Base.metadata.create_all(engine)

with open('config/auth.toml', 'rb') as f:
    config = tomllib.load(f)

client.run(config['discord']['token'])
