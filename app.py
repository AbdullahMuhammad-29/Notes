import os
from functools import wraps

from flask import Flask, request, redirect, render_template, session, url_for, abort
import markdown as md

from store import NoteStore
from users import UserStore
from nlp_utils import summarize, extract_keywords, rank_notes_by_similarity

app = Flask(__name__)
app.secret_key = os.environ.get("NOTES_SECRET_KEY", "dev-secret-change-me")
store = NoteStore()
users = UserStore()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user_id():
    return session["user_id"]


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if password != confirm:
            error = "Passwords don't match."
        else:
            try:
                user_id = users.create_user(username, password)
                session["user_id"] = user_id
                session["username"] = username.strip()
                return redirect(url_for("index"))
            except ValueError as exc:
                error = str(exc)
    return render_template("signup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = users.verify_login(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    query = request.args.get("q", "")
    smart = request.args.get("smart") == "1"
    user_id = current_user_id()

    if query and smart:
        ranked = rank_notes_by_similarity(query, store.list(user_id), top_n=25)
        notes = [note for note, _score in ranked]
    else:
        notes = store.list(user_id, query or None)

    return render_template("index.html", notes=notes, query=query, smart=smart)


@app.route("/note/<int:note_id>")
@login_required
def view_note(note_id):
    user_id = current_user_id()
    note = store.get(note_id, user_id)
    if not note:
        abort(404)
    html_body = md.markdown(note["body"], extensions=["fenced_code", "tables"])

    other_notes = [n for n in store.list(user_id) if n["id"] != note_id]

    auto_summary = summarize(note["body"], num_sentences=2)
    summary = auto_summary if len(auto_summary) < len(note["body"]) * 0.85 else None

    existing_tags = {t.strip().lower() for t in note["tags"].split(",")} if note["tags"] else set()
    keywords = extract_keywords(note["body"], top_n=6, corpus=[n["body"] for n in other_notes])
    suggested_tags = [k for k in keywords if k.lower() not in existing_tags][:5]

    related_notes = rank_notes_by_similarity(f"{note['title']} {note['body']}", other_notes, top_n=3)

    return render_template(
        "view.html", note=note, html_body=html_body,
        summary=summary, suggested_tags=suggested_tags, related_notes=related_notes,
    )


@app.route("/note/<int:note_id>/add-tag", methods=["POST"])
@login_required
def add_tag(note_id):
    user_id = current_user_id()
    note = store.get(note_id, user_id)
    if not note:
        abort(404)
    new_tag = request.form.get("tag", "").strip()
    if new_tag:
        existing = [t.strip() for t in note["tags"].split(",") if t.strip()] if note["tags"] else []
        if new_tag.lower() not in [t.lower() for t in existing]:
            existing.append(new_tag)
        store.update(note_id, user_id, note["title"], note["body"], ", ".join(existing))
    return redirect(url_for("view_note", note_id=note_id))


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_note():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "")
        tags = request.form.get("tags", "").strip()
        if title:
            note_id = store.create(current_user_id(), title, body, tags)
            return redirect(url_for("view_note", note_id=note_id))
    return render_template("editor.html", note=None)


@app.route("/edit/<int:note_id>", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    user_id = current_user_id()
    note = store.get(note_id, user_id)
    if not note:
        abort(404)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "")
        tags = request.form.get("tags", "").strip()
        if title:
            store.update(note_id, user_id, title, body, tags)
            return redirect(url_for("view_note", note_id=note_id))
    return render_template("editor.html", note=note)


@app.route("/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    store.delete(note_id, current_user_id())
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
