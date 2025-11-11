from core.secret_santa_service import create_secret_santa_game, create_special_secret_santa_game, \
    does_secret_santa_game_exist, get_num_participants, is_crazy_mode, \
    get_one_recipient_discord_id, get_second_recipient_discord_id, log_message_sent, find_message_log_by_message_id, \
    get_cogifter_for_recipient
from main import auth_config
from discord_interface.utils import get_or_fetch_user

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
    def __init__(self, plus: bool = False):
        self.plus = plus
        if plus:
            label = "Start+"
        else:
            label = "Start"

        super().__init__(emoji="🎅", label=label,
                         style=discord.ButtonStyle.primary,
                         custom_id="secret_santa_start")

    async def callback(self, interaction: discord.Interaction):
        if self.plus:
            secret_santa_lobbies[interaction.channel_id].special_start()
        else:
            secret_santa_lobbies[interaction.channel_id].start()
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
        if str(self.channel_id) in auth_config['discord']['special_secret_santa_channels']:
            buttons.append(Start(plus=True))

        if self.expire:
            for button in buttons:
                button.disabled = True

        self.add_item(ActionRow(*buttons))

# ====================================================
# POST START GAME
# ====================================================
class ShowRecipientButton(Button):
    def __init__(self):
        super().__init__(label="Show my recipient",
                         style=discord.ButtonStyle.success,
                         custom_id="show_recipient")

    async def callback(self, interaction: discord.Interaction):
        user_id = get_one_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        user = await get_or_fetch_user(interaction.client, int(user_id))
        if user is None:
            await interaction.response.send_message("Could not find your assigned recipient "
                                                    "(no active game or you're not registered).", ephemeral=True)
            return

        output = f"Your assigned recipient is: {user.mention}"
        if is_crazy_mode(interaction.channel_id):
            user_id_2 = get_second_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
            user_2 = await get_or_fetch_user(interaction.client, int(user_id_2))
            output += f" and {user_2.mention}"
        await interaction.response.send_message(output, ephemeral=True)


class MsgRecipientButton(Button):
    def __init__(self, order: int = 1):
        self.order = order
        super().__init__(label=f"Message your recipient {order}",
                         style=discord.ButtonStyle.primary,
                         custom_id="message_recipient")

    async def callback(self, interaction: discord.Interaction):
        # open a modal to collect the message to send
        if self.order == 1:
            user_id = get_one_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        else:
            user_id = get_second_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        user = await get_or_fetch_user(interaction.client, int(user_id))
        modal = MessageRecipientModal(interaction.channel_id, user, title=f"Message your recipient {user.display_name}")
        await interaction.response.send_modal(modal)


# will only exist in crazy mode
class MsgCoGifterButton(Button):
    def __init__(self, order: int):
        self.order = order
        super().__init__(label=f"Message your co-gifter {order}",
                         style=discord.ButtonStyle.gray,
                         custom_id="message_co_gifter")

    async def callback(self, interaction: discord.Interaction):
        if self.order == 1:
            recipient_id = get_one_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        else:
            recipient_id = get_second_recipient_discord_id(interaction.channel_id, str(interaction.user.id))
        recipient = await get_or_fetch_user(interaction.client, int(recipient_id))
        co_gifter_id = get_cogifter_for_recipient(interaction.channel_id, str(interaction.user.id), recipient_id)
        co_gifter = await get_or_fetch_user(interaction.client, int(co_gifter_id))

        modal = MsgCoGifterModal(interaction.channel_id, recipient, co_gifter)
        await interaction.response.send_modal(modal)


class MessageRecipientModal(discord.ui.Modal):
    # a multi-line text input for the message
    message = discord.ui.TextInput(
        label="Message",
        style=discord.TextStyle.paragraph,
        placeholder="Write a short message to your recipient...",
        required=True,
        max_length=2000,
    )

    def __init__(self, channel_id: int, recipient_user: discord.User, title="Message your recipient"):
        super().__init__(title=title)
        self.recipient = recipient_user
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        # look up the assigned recipient for this channel and giver
        content = self.message.value.strip()
        if not content:
            await interaction.response.send_message("Message was empty.", ephemeral=True)
            return

        dm_content = (f"### You have a message from your Secret Santa:\n"
                      f"origin: <#{self.channel_id}>\n\n{content}\n"
                      f"-# *Reply to this message to respond*")
        try:
            message = await self.recipient.send(dm_content)
            log_message_sent(self.channel_id, message.id, interaction.user.id, to_gift_recipient=True)
        except discord.HTTPException:
            await interaction.response.send_message("Failed to send DM — the recipient may have DMs disabled.",
                                                    ephemeral=True)
            return

        # confirm to the sender (ephemeral so only they see it)
        await interaction.response.send_message(f"Your message was sent to {self.recipient.mention}", ephemeral=True)

class MsgCoGifterModal(discord.ui.Modal):
    def __init__(self, channel_id: int, recipient: discord.User, co_gifter_user: discord.User):
        super().__init__(title="Message your co-gifter", custom_id="msg_co_gifter_modal")
        self.message = discord.ui.TextInput(
            label="Message",
            style=discord.TextStyle.paragraph,
            placeholder=f"Write an anonymous message to the cogifter of your recipient {recipient.display_name}",
            required=True,
            max_length=2000,
            custom_id="msg_co_gifter_modal_input"
        )
        self.add_item(self.message)

        self.recipient = recipient
        self.co_gifter = co_gifter_user
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        # look up the assigned co-gifter for this channel and giver
        content = self.message.value.strip()
        if not content:
            await interaction.response.send_message("Message was empty.", ephemeral=True)
            return

        dm_content = (f"### You have a message from Secret Santa:\n"
                      f"from: your co-gifter for {self.recipient.mention}\n"
                      f"origin: <#{self.channel_id}>\n\n{content}\n"
                      f"-# *Reply to this message to respond*")
        try:
            message = await self.co_gifter.send(dm_content)
            log_message_sent(self.channel_id, message.id, interaction.user.id, to_gift_recipient=False)
        except discord.HTTPException:
            await interaction.response.send_message("Failed to send DM — the co-gifter may have DMs disabled.",
                                                    ephemeral=True)
            return

        # confirm to the sender (ephemeral so only they see it)
        await interaction.response.send_message(f"Your message was sent to your co-gifter", ephemeral=True)

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
        self.add_item(ActionRow(ShowRecipientButton()))
        if crazy_mode:
            self.add_item(ActionRow(MsgRecipientButton(1), MsgRecipientButton(2)))
            self.add_item(ActionRow(MsgCoGifterButton(1), MsgCoGifterButton(2)))
        else:
            self.add_item(ActionRow(MsgRecipientButton()))

class SecretSanta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="secret-santa", description="Start or view a secret santa session in this channel.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def secret_santa(self, interaction: discord.Interaction):
        # prevent use in one-on-one DMs but allow group chats
        if interaction.channel and isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("Cannot start a secret santa session in this channel.", ephemeral=True)
            return
        view = LayoutView(timeout=None)
        if does_secret_santa_game_exist(interaction.channel_id):
            page = StatusPage(interaction.channel_id, crazy_mode=is_crazy_mode(interaction.channel_id))
            view.add_item(page)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        if interaction.channel_id in secret_santa_lobbies:
            page = secret_santa_lobbies[interaction.channel_id]
        else:
            secret_santa_lobbies[interaction.channel_id] = page = LobbyPage(str(interaction.guild_id),
                                                                            str(interaction.channel_id))
        view.add_item(page)

        await interaction.response.send_message(view=view)

    async def on_reply_to_msg(self, message: discord.Message):
        """Called from Bot.on_message when a user replies to one of the bot's messages.

        We'll attempt to forward the textual content of the reply as a Secret Santa DM to the
        recipient assigned to the replying user in the channel where the reply occurred.
        """
        if not message.content or not message.content.strip():
            await message.channel.send(f"Your reply was empty; nothing sent.")
            return

        # check the logs of messages for the message that this is responding to, and the original
        # author of that message is the recipient of this message
        log_entry = find_message_log_by_message_id(message.reference.message_id)
        if not log_entry:
            print("could not find message in db")
            return

        user = await get_or_fetch_user(self.bot, int(log_entry['author_discord_id']))
        from_field = message.author.mention if log_entry['to_gift_recipient'] else "co-gifter"
        dm_content = (f"## You have a reply to your message:\n"
                      f"*from*: {from_field}\n"
                      f"*originating from*: <#{log_entry['origin_discord_channel_id']}>\n\n"
                      f"{message.content.strip()}")
        try:
            await user.send(dm_content)
        except discord.HTTPException:
            await message.channel.send(
                f"<@{message.author.id}> Failed to send DM — the recipient may have DMs disabled.")
            return

        await message.channel.send(f"Your reply to the message was sent.")


async def setup(bot):
    await bot.add_cog(SecretSanta(bot=bot))
