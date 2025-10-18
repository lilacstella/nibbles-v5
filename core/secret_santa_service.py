from main import session_maker
from models.users_model import User
from models.secret_santa_model import SecretSantaAssignment

import random

def create_secret_santa_game(user_ids: set[int], gift_count: int) -> None:
    """
    Registers users, randomizes assignments, and commits Secret Santa assignments to the DB.
    Args:
        :param user_ids: List of Discord user IDs (as strings)
        :param gift_count: the number of gifts that each participant will give and receive
    """
    with session_maker() as session:
        users = [User.get_or_create(session, id) for id in user_ids]
    n = len(user_ids)

    if n <= gift_count + 1:
        raise ValueError('Impossible to create secret santa with such arrangement')
    if gift_count > 5:
        raise ValueError('Please request explicit privileges to have more gifting assignment')

    unique_random_offsets = []
    while len(set(unique_random_offsets)) < gift_count:
        unique_random_offsets = [random.randint(1, n - 1) for _ in range(gift_count)]

    assignments = {}
    for i in range(n):
       assignments[users[i]] = set(users[(i + offset) % n] for offset in unique_random_offsets)

    with session_maker() as session:
        SecretSantaAssignment.create(session, assignments)


# questions: TODO
# does it uphold the criteria? lets run simulations
# how many times do we have to randomize?
