import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module
from store import NoteStore
from users import UserStore


def client():
    db_path = tempfile.mktemp(suffix=".db")
    app_module.store = NoteStore(db_path=db_path)
    app_module.users = UserStore(db_path=db_path)
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def signup(c, username="alice", password="securepass123"):
    return c.post("/signup", data={"username": username, "password": password, "confirm": password},
                  follow_redirects=True)


def test_index_redirects_when_logged_out():
    c = client()
    resp = c.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_signup_creates_account_and_logs_in():
    c = client()
    resp = signup(c)
    assert resp.status_code == 200
    assert b"NoteNest" in resp.data
    resp2 = c.get("/")
    assert resp2.status_code == 200  # no redirect to login - already authenticated


def test_signup_with_mismatched_passwords_shows_error():
    c = client()
    resp = c.post("/signup", data={"username": "alice", "password": "securepass123", "confirm": "different123"})
    assert b"don&#39;t match" in resp.data or b"don't match" in resp.data


def test_signup_with_duplicate_username_shows_error():
    c = client()
    signup(c, username="alice")
    c.get("/logout")
    resp = c.post("/signup", data={"username": "alice", "password": "anotherpass123", "confirm": "anotherpass123"})
    assert b"already taken" in resp.data


def test_login_with_correct_credentials():
    c = client()
    signup(c, username="alice", password="securepass123")
    c.get("/logout")
    resp = c.post("/login", data={"username": "alice", "password": "securepass123"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"NoteNest" in resp.data


def test_login_with_wrong_password_shows_error():
    c = client()
    signup(c, username="alice", password="securepass123")
    c.get("/logout")
    resp = c.post("/login", data={"username": "alice", "password": "wrongpass"})
    assert b"Invalid username or password" in resp.data


def test_create_note_after_login():
    c = client()
    signup(c)
    resp = c.post("/new", data={"title": "My first note", "body": "hello", "tags": "test"},
                   follow_redirects=True)
    assert resp.status_code == 200
    assert b"My first note" in resp.data


def test_users_only_see_their_own_notes():
    c1 = client()
    signup(c1, username="alice")
    c1.post("/new", data={"title": "Alice's note", "body": "private"})
    c1.get("/logout")

    signup(c1, username="bob")
    resp = c1.get("/")
    assert b"Alice's note" not in resp.data


def test_view_note_shows_ai_summary_for_long_note():
    c = client()
    signup(c)
    long_body = (
        "Python is a popular programming language known for its readability. "
        "It was created by Guido van Rossum and released in 1991. "
        "Python supports multiple programming paradigms including procedural and object oriented styles. "
        "The language has a large standard library covering everything from web servers to file compression."
    )
    c.post("/new", data={"title": "About Python", "body": long_body, "tags": ""})
    resp = c.get("/note/1")
    assert b"AI SUMMARY" in resp.data


def test_view_note_shows_related_notes():
    c = client()
    signup(c)
    c.post("/new", data={"title": "Python basics", "body": "Python is a great programming language"})
    c.post("/new", data={"title": "Python advanced", "body": "Python decorators are a programming feature"})
    resp = c.get("/note/1")
    assert b"Related notes" in resp.data


def test_add_suggested_tag():
    c = client()
    signup(c)
    c.post("/new", data={"title": "Note", "body": "some content here", "tags": ""})
    c.post("/note/1/add-tag", data={"tag": "important"})
    note = app_module.store.get(1, user_id=1)
    assert "important" in note["tags"]
