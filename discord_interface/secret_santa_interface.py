from core.secret_santa_service import create_secret_santa_game, create_special_secret_santa_game, \
    does_secret_santa_game_exist, get_num_participants, get_recipient_discord_id, is_crazy_mode
from main import config

import discord
from discord import app_commands
from discord.ui import Button, LayoutView, ActionRow, TextDisplay, Container
from discord.ext import commands

# channel_id: LobbyPage
secret_santa_lobbies: dict[int, "LobbyPage"] = {}


# Lobby buttons
class Join(Button):
    def __init__(self):
        super().__init__(emoji="<:NibblesYes:869957381134647316>",
                         label="Join",
                         style=discord.ButtonStyle.success,
                         custom_id="secret_santa_join")

    async def callback(self, interaction: discord.Interaction):
        secret_santa_lobbies[interaction.channel_id].add_participant(interaction.user.id)
        secret_santa_lobbies[interaction.channel_id].update()
        view = LayoutView(timeout=None)
        view.add_item(secret_santa_lobbies[interaction.channel_id])
        await interaction.response.edit_message(view=view)


class Leave(Button):
    def __init__(self):
        super().__init__(emoji="🚪", label="Leave", style=discord.ButtonStyle.danger, custom_id="secret_santa_leave")

    async def callback(self, interaction: discord.Interaction):
        secret_santa_lobbies[interaction.channel_id].participants.discard(interaction.user.id)
        secret_santa_lobbies[interaction.channel_id].update()
        view = LayoutView(timeout=None)
        view.add_item(secret_santa_lobbies[interaction.channel_id])
        await interaction.response.edit_message(view=view)


class Start(Button):
    def __init__(self):
        super().__init__(emoji="🎅", label="Start",
                         style=discord.ButtonStyle.primary,
                         custom_id="secret_santa_start")

    async def callback(self, interaction: discord.Interaction):
        secret_santa_lobbies[interaction.channel_id].start()
        view = LayoutView(timeout=0)
        view.add_item(secret_santa_lobbies[interaction.channel_id])
        secret_santa_lobbies[interaction.channel_id].set_expire()
        secret_santa_lobbies[interaction.channel_id].update()
        await interaction.response.edit_message(view=view)
        del secret_santa_lobbies[interaction.channel_id]


class StartPlus(Button):
    def __init__(self):
        super().__init__(emoji="🎅", label="Start+",
                         style=discord.ButtonStyle.primary,
                         custom_id="secret_santa_start_plus")

    async def callback(self, interaction: discord.Interaction):
        secret_santa_lobbies[interaction.channel_id].special_start()
        view = LayoutView(timeout=0)
        view.add_item(secret_santa_lobbies[interaction.channel_id])
        secret_santa_lobbies[interaction.channel_id].set_expire()
        secret_santa_lobbies[interaction.channel_id].update()
        await interaction.response.edit_message(view=view)
        del secret_santa_lobbies[interaction.channel_id]


# used for keeping track of a game before it starts
class LobbyPage(Container):
    def __init__(self, guild_id, channel_id):
        super().__init__()
        # all these values are discord ids
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.participants = set()
        self.expire = False

        self.update()

    def add_participant(self, user_id: int):
        self.participants.add(user_id)

    def start(self):
        create_secret_santa_game(self.guild_id, self.channel_id, self.participants)

    def special_start(self):
        create_special_secret_santa_game(self.guild_id, self.channel_id, self.participants)

    def set_expire(self):
        self.expire = True

    def update(self):
        self.clear_items()
        participant_mentions = [f"<@{user_id}>" for user_id in self.participants]
        self.add_item(TextDisplay("## Nice List:"))
        self.add_item(TextDisplay("\n".join(participant_mentions) if participant_mentions else "No participants yet."))
        ar = ActionRow(Join(), Leave())
        if self.expire:
            for children in ar.walk_children():
                children.disabled = True
        self.add_item(ar)
        buttons = [Start()]
        if str(self.channel_id) in config['discord']['special_secret_santa_channels']:
            buttons.append(StartPlus())

        if self.expire:
            for button in buttons:
                button.disabled = True

        self.add_item(ActionRow(*buttons))

# ====================================================
# POST START GAME
# ====================================================
async def get_or_fetch_member(interaction, user_id: int) -> discord.User | None:
  try:
    return interaction.client.get_user(user_id) or await interaction.client.fetch_user(user_id)
  except discord.NotFound:
    return None

class MsgRecipientButton(Button):
    def __init__(self):
        super().__init__(label="Message your recipient",
                         style=discord.ButtonStyle.primary,
                         custom_id="message_recipient_1")

    async def callback(self, interaction: discord.Interaction):
        # open a modal to collect the message to send
        user_ids = get_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        user = await get_or_fetch_member(interaction, int(user_ids[0]))

        print(user_ids, user)
        modal = MessageRecipientModal(title=f"Message your recipient {user.display_name}")
        await interaction.response.send_modal(modal)


class MsgRecipientButton2(Button):
    def __init__(self):
        super().__init__(label="Message your 2nd recipient",
                         style=discord.ButtonStyle.primary,
                         custom_id="message_recipient_2")

    async def callback(self, interaction: discord.Interaction):
        # open a modal to collect the message to send
        user_ids = get_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        user = await get_or_fetch_member(interaction, int(user_ids[1]))
        modal = MessageRecipientModal(title=f"Message your recipient {user.display_name}")
        await interaction.response.send_modal(modal)


class MessageRecipientModal(discord.ui.Modal, title="Message your recipient"):
    # a multi-line text input for the message
    message = discord.ui.TextInput(
        label="Message",
        style=discord.TextStyle.paragraph,
        placeholder="Write a short message to your recipient...",
        required=True,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # look up the assigned recipient for this channel and giver
        content = self.message.value.strip()
        if not content:
            await interaction.response.send_message("Message was empty.", ephemeral=True)
            return

        recipient_discord_id = get_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        if not recipient_discord_id:
            await interaction.response.send_message("Could not find your assigned recipient (no active game or you're not registered).", ephemeral=True)
            return

        try:
            recipient_user = await interaction.client.fetch_user(int(recipient_discord_id))
        except Exception:
            await interaction.response.send_message("Failed to look up the recipient user on Discord.", ephemeral=True)
            return

        # send the DM as the bot; include a short header to indicate it's a Secret Santa message
        dm_content = f"## You have a message from your Secret Santa:\n\n{content}"
        try:
            await recipient_user.send(dm_content)
        except discord.HTTPException:
            await interaction.response.send_message("Failed to send DM — the recipient may have DMs disabled.", ephemeral=True)
            return

        # confirm to the sender (ephemeral so only they see it)
        await interaction.response.send_message(f"Your message was sent to <@{recipient_discord_id}>.", ephemeral=True)


class StatusPage(Container):
    def __init__(self, channel_id, crazy_mode: bool = False):
        super().__init__()
        self.channel_id = channel_id
        self.crazy_mode = crazy_mode
        num = get_num_participants(channel_id)
        self.add_item(
            TextDisplay(
                f"## Your Secret Santa has {num} participants"
            )
        )

        if crazy_mode:
            ar = ActionRow(MsgRecipientButton(), MsgRecipientButton2())
        else:
            ar = ActionRow(MsgRecipientButton())
        self.add_item(ar)


class SecretSanta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="secret-santa", description="View the secret santa session in this channel.")
    @app_commands.guilds(805821298193465384)
    async def secret_santa(self, interaction: discord.Interaction):
        view = LayoutView(timeout=None)
        if does_secret_santa_game_exist(interaction.channel_id):
            page = StatusPage(interaction.channel_id, crazy_mode=is_crazy_mode(interaction.channel_id))
            view.add_item(page)
            await interaction.response.send_message(view=view)
            return

        if interaction.channel_id in secret_santa_lobbies:
            page = secret_santa_lobbies[interaction.channel_id]
        else:
            secret_santa_lobbies[interaction.channel_id] = page = LobbyPage(str(interaction.guild_id),
                                                                            str(interaction.channel_id))
        view.add_item(page)

        await interaction.response.send_message(view=view)


async def setup(bot):
    await bot.add_cog(SecretSanta(bot=bot))
