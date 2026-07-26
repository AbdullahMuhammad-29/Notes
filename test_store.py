import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from store import NoteStore


@pytest.fixture
def store():
    return NoteStore(db_path=tempfile.mktemp(suffix=".db"))


def test_create_and_get(store):
    note_id = store.create(1, "First note", "Hello **world**", tags="personal")
    note = store.get(note_id, user_id=1)
    assert note["title"] == "First note"
    assert note["tags"] == "personal"


def test_update(store):
    note_id = store.create(1, "Old title", "old body")
    assert store.update(note_id, 1, "New title", "new body", "work") is True
    note = store.get(note_id, 1)
    assert note["title"] == "New title"
    assert note["body"] == "new body"


def test_delete(store):
    note_id = store.create(1, "Temp", "body")
    assert store.delete(note_id, 1) is True
    assert store.get(note_id, 1) is None


def test_list_search_by_title(store):
    store.create(1, "Grocery list", "milk, eggs")
    store.create(1, "Meeting notes", "discuss roadmap")
    results = store.list(1, query="grocery")
    assert len(results) == 1
    assert results[0]["title"] == "Grocery list"


def test_list_search_by_tag(store):
    store.create(1, "Note A", "body", tags="urgent")
    store.create(1, "Note B", "body", tags="later")
    results = store.list(1, query="urgent")
    assert len(results) == 1
    assert results[0]["title"] == "Note A"


def test_notes_are_isolated_per_user(store):
    store.create(1, "User 1's note", "private stuff")
    store.create(2, "User 2's note", "different private stuff")
    assert len(store.list(1)) == 1
    assert len(store.list(2)) == 1
    assert store.list(1)[0]["title"] == "User 1's note"


def test_user_cannot_get_another_users_note(store):
    note_id = store.create(1, "User 1's note", "private")
    assert store.get(note_id, user_id=2) is None


def test_user_cannot_update_another_users_note(store):
    note_id = store.create(1, "Original", "body")
    changed = store.update(note_id, 2, "Hacked title", "hacked body")
    assert changed is False
    assert store.get(note_id, 1)["title"] == "Original"


def test_user_cannot_delete_another_users_note(store):
    note_id = store.create(1, "Mine", "body")
    assert store.delete(note_id, 2) is False
    assert store.get(note_id, 1) is not None
