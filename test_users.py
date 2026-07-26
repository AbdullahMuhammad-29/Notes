import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from users import UserStore


@pytest.fixture
def users():
    return UserStore(db_path=tempfile.mktemp(suffix=".db"))


def test_create_user_and_login(users):
    user_id = users.create_user("alice", "securepass123")
    assert user_id is not None
    user = users.verify_login("alice", "securepass123")
    assert user is not None
    assert user["username"] == "alice"


def test_login_with_wrong_password_fails(users):
    users.create_user("alice", "securepass123")
    assert users.verify_login("alice", "wrongpassword") is None


def test_login_with_unknown_username_fails(users):
    assert users.verify_login("nobody", "anything123") is None


def test_duplicate_username_raises(users):
    users.create_user("alice", "securepass123")
    with pytest.raises(ValueError):
        users.create_user("alice", "anotherpass123")


def test_short_password_raises(users):
    with pytest.raises(ValueError):
        users.create_user("bob", "short")


def test_empty_username_raises(users):
    with pytest.raises(ValueError):
        users.create_user("", "securepass123")


def test_password_is_hashed_not_stored_plain(users):
    users.create_user("alice", "securepass123")
    user = users.verify_login("alice", "securepass123")
    assert user["password_hash"] != "securepass123"
