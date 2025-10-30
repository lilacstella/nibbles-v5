from main import session_maker
from models.users_model import User
from models.secret_santa_model import SecretSantaAssignment, SecretSantaContext, SecretSantaMessageLog

import random
from typing import List
from sqlalchemy import func

def create_secret_santa_game(guild_id: int | None, channel_id: int, user_ids: set[int]) -> None:
    """
    Registers users, randomizes assignments, and commits Secret Santa assignments to the DB.
    Args:
        :param guild_id:
        :param channel_id:
        :param user_ids: List of Discord user IDs (as strings)
    """
    with session_maker() as session:
        users: List["User"] = [User.get_or_create(session, str(_id)) for _id in user_ids]
    random.shuffle(users)

    with session_maker() as session:
        game = SecretSantaContext(guild_id=str(guild_id) if guild_id is not None else None, channel_id=str(channel_id), crazy_mode=False)
        session.add(game)
        for i in range(len(users)):
            a = SecretSantaAssignment(game, users[i], users[(i + 1) % len(users)])
            session.add(a)
        session.commit()

def create_special_secret_santa_game(guild_id: int | None, channel_id: int, user_ids: set[int]) -> None:
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
        game = SecretSantaContext(guild_id=str(guild_id) if guild_id is not None else None, channel_id=str(channel_id), crazy_mode=True)
        session.add(game)
        for gifter_idx, receiver_indices in gifting.items():
            for receiver_idx in receiver_indices:
                session.add(SecretSantaAssignment(game, users[gifter_idx], users[receiver_idx]))
        session.commit()


def does_secret_santa_game_exist(channel_id: int) -> bool:
    """
    Checks if a Secret Santa game already exists in the specified channel.
    Args:
        :param channel_id: Discord channel ID
    Returns:
        :return: True if a game exists, False otherwise
    """
    with session_maker() as session:
        existing_game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        return existing_game is not None


def get_num_participants(channel_id: int) -> int:
    """
    Returns the number of participants in the Secret Santa game in the specified channel.

    :param channel_id: Discord channel ID
    :return: Number of participants
    """
    with session_maker() as session:
        game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        if not game:
            return 0
        count = session.query(func.count(func.distinct(SecretSantaAssignment.gifter_id))).scalar()
        return count

def is_crazy_mode(channel_id: int) -> bool:
    """

    :param channel_id:
    :return:
    """
    with session_maker() as session:
        game = session.query(SecretSantaContext).filter_by(channel_id=str(channel_id)).first()
        return game.crazy_mode

def  get_one_recipient_discord_id(channel_id: int, giver_discord_id: str) -> str:
    with session_maker() as session:
        user = session.query(User).filter_by(discord_user_id=giver_discord_id).first()
        if not user:
            raise ValueError(f"User with discord_id {giver_discord_id} not found in db")
        
        # Filter the user's gifting assignments by channel
        for assignment in user.gifting_to:
            if assignment.context.channel_id == str(channel_id):
                return assignment.receiver.discord_user_id
        
        raise ValueError(f"No assignment found for user {giver_discord_id} in channel {channel_id}")

def get_second_recipient_discord_id(channel_id: int, giver_discord_id: str) -> str:
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

def log_message_sent(discord_channel_id: int, discord_message_id: int, author_discord_id: int) -> None:
    with session_maker() as session:
        user = session.query(User).filter_by(discord_user_id=str(author_discord_id)).first()
        if not user:
            raise ValueError(f"User with discord_id {author_discord_id} not found in db")

        log_entry = SecretSantaMessageLog(
            origin_discord_channel_id=str(discord_channel_id),
            discord_message_id=str(discord_message_id),
            author=user
        )
        session.add(log_entry)
        session.commit()

def find_message_log_by_message_id(discord_message_id: int) -> dict:
    with session_maker() as session:
        log_entry = session.query(SecretSantaMessageLog).filter_by(discord_message_id=str(discord_message_id)).first()
        info = {
            "author_discord_id": log_entry.author.discord_user_id,
            "origin_discord_channel_id": log_entry.origin_discord_channel_id
        }
        return info
