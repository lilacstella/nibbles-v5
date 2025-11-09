import secrets

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View


# Helper functions to avoid duplicating choice/phrase logic
def _parse_options(options: str) -> list[str]:
    """Parse a user-supplied options string into a list of choices.

    Supports comma-separated lists or space-separated tokens.
    """
    if ',' in options:
        return [x.strip() for x in options.split(',') if x.strip()]
    return [x.strip() for x in options.split() if x.strip()]


def _make_choice_phrases(choice: str) -> list[str]:
    """Return a list of templated response strings for a chosen option."""
    return [
        f'Nibbles thinks  __{choice}__  is the right option!',
        f'Of course __{choice}__ is the way to go!',
        f"Nibbles thinks __{choice}__ is da best. It's tasty after all!",
        f'After consulting my degree in Abstract Mathematics, Nibbles thinks __{choice}__ is the right choice.',
        f"Nibbles likes __{choice}__ because it has the most nom noms",
        f"How about ... __{choice}__",
    ]


def _choice_history(chosen: list[str], remaining: list[str]) -> str:
    """Format the history string shown under the choice message."""
    if remaining:
        return ", ".join(f"~~{c}~~" for c in chosen) + f", {', '.join(remaining)}"
    return ", ".join(f"~~{c}~~" for c in chosen)


def _render_choice_output(picked: str, chosen: list[str], remaining: list[str]) -> str:
    """Build the final message content (one of the templated phrases + history).

    This centralizes the logic used by both the command and the reroll button so
    they stay consistent and DRY.
    """
    messages = _make_choice_phrases(picked)
    if remaining:
        messages.append(f"Why would you choose {secrets.choice(remaining)}, choose __{picked}__!")
    history = _choice_history(chosen, remaining)
    return f"{secrets.choice(messages)}\n\n-# {history}"


class RerollButton(Button):
    def __init__(self, choices: list[str], chosen: list[str]):
        super().__init__(emoji="🔁", style=discord.ButtonStyle.primary)
        self.choices = choices
        self.chosen = chosen

    async def callback(self, interaction: discord.Interaction) -> None:
        if len(self.choices) == 0:
            await interaction.response.defer()
            return

        # pick a new choice and update shared state
        picked = secrets.choice(self.choices)
        self.chosen.append(picked)
        self.choices.remove(picked)

        if len(self.choices) == 0:
            self.disabled = True
            view = View(timeout=0)
        else:
            view = View(timeout=None)
        view.add_item(self)

        content = _render_choice_output(picked, self.chosen, self.choices)

        await interaction.response.edit_message(content=content, view=view)


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="choose", description="Have Nibbles choose between multiple options for you!")
    @discord.app_commands.describe(
        options='what would you like nibbles to choose from (comma separated)'
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def choose(self, interaction: discord.Interaction, options: str):
        choices = _parse_options(options)

        if len(choices) < 2:
            await interaction.response.send_message("Nibbles needs at least two options to choose from!", ephemeral=True)
            return

        picked = secrets.choice(choices)
        choices.remove(picked)

        view = View(timeout=None)
        chosen_list = [picked]
        # give the button a copy of the remaining choices so it can mutate them independently
        view.add_item(RerollButton(choices.copy(), chosen_list))

        content = _render_choice_output(picked, chosen_list, choices)

        await interaction.response.send_message(content, view=view)


async def setup(bot):
    await bot.add_cog(Misc(bot=bot))
