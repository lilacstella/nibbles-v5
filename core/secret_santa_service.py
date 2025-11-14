from main import session_maker
from models.users_model import User
from models.secret_santa_model import SecretSantaAssignment, SecretSantaContext, SecretSantaMessageLog

import random
from typing import List


def create_secret_santa_game(guild_id: int | None, channel_id: int, user_ids: set[int]) -> None:
    """
    Registers users, randomizes assignments, and commits Secret Santa assignments to the DB.

    :param guild_id: Discord guild ID (or None for DMs)
    :param channel_id: Discord channel ID
    :param user_ids: collection of Discord user IDs (as strings)
    """
    with session_maker() as session:
        users: List["User"] = [User.get_or_create(session, str(_id)) for _id in user_ids]
    random.shuffle(users)

    with session_maker() as session:
        game = SecretSantaContext(guild_id=str(guild_id) if guild_id is not None else None, channel_id=str(channel_id),
                                  crazy_mode=False)
        session.add(game)
        for i in range(len(users)):
            a = SecretSantaAssignment(game, users[i], users[(i + 1) % len(users)])
            session.add(a)
        session.commit()


def create_special_secret_santa_game(guild_id: int | None, channel_id: int, user_ids: set[int]) -> None:
    """
    Registers users, randomizes assignments in crazy mode, and commits Secret Santa assignments to the DB.

    :param guild_id: discord guild ID
    :param channel_id: discord channel ID
    :param user_ids: collection of Discord user IDs (as strings)
    """
    with session_maker() as session:
        users: List["User"] = [User.get_or_create(session, str(_id)) for _id in user_ids]
    random.shuffle(users)

    config_num = random.randint(0, 2)
    gifting = {}
    match config_num:
        case 0:
            gifting = {
                0: {1, 2},
                1: {0, 3},
                2: {1, 3},
                3: {0, 2},
            }
        case 1:
            gifting = {
                0: {1, 3},
                1: {0, 2},
                2: {0, 3},
                3: {1, 2},
            }
        case 2:
            gifting = {
                0: {2, 3},
                1: {0, 3},
                2: {0, 1},
                3: {1, 2},
            }

    with session_maker() as session:
        game = SecretSantaContext(guild_id=str(guild_id) if guild_id is not None else None, channel_id=str(channel_id),
                                  crazy_mode=True)
        session.add(game)
        for gifter_idx, receiver_indices in gifting.items():
            for receiver_idx in receiver_indices:
                session.add(SecretSantaAssignment(game, users[gifter_idx], users[receiver_idx]))
        session.commit()


def does_secret_santa_game_exist(channel_id: int) -> bool:
    """
    Checks if a Secret Santa game already exists in the specified channel.

    :param channel_id: Discord channel ID
    :return: True if a game exists, False otherwise
    """
    with session_maker() as session:
        existing_game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        return existing_game is not None


def get_participants(channel_id: int) -> list[str]:
    """
    Returns a list of unique participant Discord IDs (gifters) for the Secret Santa game
    in the specified channel.

    :param channel_id: Discord channel ID
    :return: List of Discord user ID strings of participants (gifters)
    """
    with session_maker() as session:
        game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        if not game:
            return []

        # Query the distinct discord_user_id values for Users who are gifters in this game
        rows = (
            session.query(User.discord_user_id)
            .join(SecretSantaAssignment, SecretSantaAssignment.gifter_id == User.id)
            .filter(SecretSantaAssignment.context_id == game.id)
            .distinct()
            .all()
        )

        return [r[0] for r in rows]


def is_crazy_mode(channel_id: int) -> bool:
    """
    Checks if the Secret Santa game in the specified channel is in crazy mode.

    :param channel_id: Discord channel ID
    :return: Whether the game is in crazy mode
    """
    with session_maker() as session:
        game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        return game.crazy_mode


def get_one_recipient_discord_id(channel_id: int, giver_discord_id: str) -> str:
    """
    Retrieves the first recipient Discord ID for the given gift giver for the game in the specified channel.
    :param channel_id: The channel in which the Secret Santa game is taking place
    :param giver_discord_id: The Discord ID of the gift giver
    :return: The Discord ID of the first recipient assigned to the gift giver
    """
    with session_maker() as session:
        user = session.query(User).filter_by(discord_user_id=giver_discord_id).first()
        if not user:
            raise ValueError(f"User with discord_id {giver_discord_id} not found in db")

        # Filter the user's gifting assignments by channel
        for assignment in user.gifting_to:
            if assignment.context.channel_id == str(channel_id):
                return assignment.receiver.discord_user_id

        raise ValueError(f"No assignment found for user {giver_discord_id} in channel {channel_id}")


def get_cogifter_for_recipient(channel_id: int, gifter_discord_id: str, recipient_discord_id: str) -> str:
    """
    Retrieves the Discord ID of the co-gifter for a given recipient in crazy mode.
    :param channel_id: the channel in which the Secret Santa game is taking place
    :param gifter_discord_id: the discord ID of the gifter requesting the co-gifter
    :param recipient_discord_id: the discord ID of the recipient for which the gifter shares a co-gifter
    :return: the discord ID of the other co-gifter
    """
    with session_maker() as session:
        user = session.query(User).filter_by(discord_user_id=recipient_discord_id).first()
        if not user:
            raise ValueError(f"User with discord_id {recipient_discord_id} not found in db")

        for assignment in user.receiving_from:
            if assignment.context.channel_id == str(
                    channel_id) and assignment.gifter.discord_user_id != gifter_discord_id:
                return assignment.gifter.discord_user_id

        raise ValueError(f"No second gifter found for recipient {recipient_discord_id} in channel {channel_id}")


def get_second_recipient_discord_id(channel_id: int, giver_discord_id: str) -> str:
    """
    Retrieves the second recipient Discord ID for the given gift giver for the game in the specified channel.
    :param channel_id: the channel in which the Secret Santa game is taking place
    :param giver_discord_id: The Discord ID of the gift giver
    :return: The Discord ID of the second recipient assigned to the gift giver
    """
    with session_maker() as session:
        user = session.query(User).filter_by(discord_user_id=giver_discord_id).first()
        if not user:
            raise ValueError(f"User with discord_id {giver_discord_id} not found in db")

        # Get all assignments for this user in this channel
        channel_assignments = [
            assignment for assignment in user.gifting_to
            if assignment.context.channel_id == str(channel_id)
        ]

        if len(channel_assignments) >= 2:
            return channel_assignments[1].receiver.discord_user_id
        raise ValueError(f"No second assignment found for user {giver_discord_id} in channel {channel_id}")


def log_message_sent(discord_channel_id: int,
                     discord_message_id: int,
                     author_discord_id: int,
                     to_gift_recipient: bool) -> None:
    """
    Logs a Secret Santa related message sent by a user so that it can be replied to later.
    :param discord_channel_id: The channel in which the message was sent
    :param discord_message_id: The ID of the message sent
    :param author_discord_id: Discord ID of the original author of the message
    :param to_gift_recipient: Whether the message was sent to the gift recipient or a cogifter
    """
    with session_maker() as session:
        user = session.query(User).filter_by(discord_user_id=str(author_discord_id)).first()
        if not user:
            raise ValueError(f"User with discord_id {author_discord_id} not found in db")

        log_entry = SecretSantaMessageLog(
            origin_discord_channel_id=str(discord_channel_id),
            discord_message_id=str(discord_message_id),
            author=user,
            to_gift_recipient=to_gift_recipient
        )
        session.add(log_entry)
        session.commit()


def find_message_log_by_message_id(discord_message_id: int) -> dict:
    """
    Retrieves the log entry for a Secret Santa message by its Discord message ID.
    :param discord_message_id:
    :return: the log entry info as a dict
    """
    with session_maker() as session:
        log_entry = session.query(SecretSantaMessageLog).filter_by(discord_message_id=str(discord_message_id)).first()
        info = {
            "author_discord_id": log_entry.author.discord_user_id,
            "origin_discord_channel_id": log_entry.origin_discord_channel_id,
            "to_gift_recipient": log_entry.to_gift_recipient
        }
        return info

def get_all_assignments(channel_id: int) -> list[tuple[str, str]]:
    """
    Retrieves all Secret Santa assignments for the game in the specified channel.

    :param channel_id: Discord channel ID
    :return: List of tuples of gifter and receiver Discord IDs
    """
    with session_maker() as session:
        game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        if not game:
            return []
        assignments = session.query(SecretSantaAssignment).filter_by(context=game).all()
        return [(assignment.gifter.discord_user_id, assignment.receiver.discord_user_id) for assignment in assignments]

def delete_secret_santa_game(channel_id: int) -> None:
    """
    Deletes the Secret Santa game and all associated assignments and logs from the specified channel.

    :param channel_id: Discord channel ID
    """
    with session_maker() as session:
        game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        if game:
            session.query(SecretSantaMessageLog).filter_by(origin_discord_channel_id=str(channel_id)).delete()
            session.delete(game)
            session.commit()
