import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import models.secret_santa_model as secret_santa

# Holder tests for functions, use @pytest.mark.parametrize to create multiple test cases
@pytest.mark.parametrize("user_id, item_name, item_comment, item_link", [
    ("user1", "Toy Car", "A small red toy car", "http://example.com/toycar"),
    ("user2", "Doll", None, None),
    ("user3", "Board Game", "Fun for the whole family", "http://example.com/boardgame"),
])
def test_create_wishlist_item(user_id, item_name, item_comment, item_link):
    # do whatever
    print(f"Creating wishlist item for user_id={user_id}, item_name={item_name}, "
          f"item_comment={item_comment}, item_link={item_link}")
    # check whatever
    assert True
