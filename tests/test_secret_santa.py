import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core.secret_santa_service as secret_santa_service
import models.secret_santa_model as secret_santa_model

# mock secret santa context
def secret_santa_context_mock(guild_id, channel_id):
    mock = MagicMock(spec=secret_santa_model.SecretSantaContext)
    mock.guild_id = guild_id
    mock.channel_id = channel_id
    return mock


# mock secret santa assignment
def secret_santa_assignment_mock(gifter_id, receiver_id):
    mock = MagicMock(spec=secret_santa_model.SecretSantaAssignment)
    mock.secret_santa_context = secret_santa_context_mock(123, 456)
    mock.gifter_id = gifter_id
    mock.receiver_id = receiver_id
    return mock


# Example test using the mocks
def test_secret_santa_assignment_mock():
    assignment = secret_santa_assignment_mock(1, 2)
    assert assignment.gifter_id == 1
    assert assignment.receiver_id == 2
    assert assignment.secret_santa_context.guild_id == 123
    assert assignment.secret_santa_context.channel_id == 456
    
@pytest.mark.parametrize("n, gift_count, users, expected_exception", [
    (4, 2, [MagicMock(id=i) for i in range(4)], None),
    (5, 2, [MagicMock(id=i) for i in range(5)], None),
    (4, 3, [MagicMock(id=i) for i in range(4)], ValueError),
    (6, 6, [MagicMock(id=i) for i in range(6)], ValueError),
])
def test_create_valid_assignment(n, gift_count, users, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            secret_santa_service.create_valid_assignment(n, gift_count, users)
    else:
        assignments = secret_santa_service.create_valid_assignment(n, gift_count, users)
        assert len(assignments) == n
        seen_assignments = set()
        for gifter, receivers in assignments.items():
            assert len(receivers) == gift_count
            assert gifter not in receivers
            assert frozenset(receivers) not in seen_assignments
            seen_assignments.add(frozenset(receivers))

def exaustive_test_create_valid_assignment():
    for _ in range(100):
        test_create_valid_assignment(4, 2, [MagicMock(id=i) for i in range(4)], None)
    for _ in range(100):
        test_create_valid_assignment(10, 5, [MagicMock(id=i) for i in range(5)], None)
    for _ in range(100):
        test_create_valid_assignment(25, 5, [MagicMock(id=i) for i in range(10)], None)