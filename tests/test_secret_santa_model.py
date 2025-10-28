import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
