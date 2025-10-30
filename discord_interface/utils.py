import discord

async def get_or_fetch_user(client, user_id: int) -> discord.User | None:
  try:
      return client.get_user(user_id) or await client.fetch_user(user_id)
  except discord.NotFound:
      return None
