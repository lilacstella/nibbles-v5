from main import session_maker
from models.users_model import User


def get_user_nomnoms(discord_user_id: int) -> int:
    """
    Retrieves the nomnoms balance for a user by their Discord user ID.
    :param discord_user_id: discord user ID
    :return: nomnoms balance
    """
    with session_maker() as session:
        user = User.get_or_create(session, str(discord_user_id))
        return user.nomnoms


def add_user_nomnoms(discord_user_id: int, amount: int) -> int:
    """
    Adds nomnoms to a user's balance.
    :param discord_user_id: discord user ID
    :param amount: amount of nomnoms to add
    :return: updated nomnoms balance
    """
    if amount <= 0:
        raise ValueError("Amount to add must be positive.")

    with session_maker() as session:
        user = User.get_or_create(session, str(discord_user_id))
        user.nomnoms += amount
        session.commit()
        return user.nomnoms
