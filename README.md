# NoteNest — Personal Notes App

A multi-user notes app with real signup/login, Markdown rendering, tags, search, and local AI features that need no paid API and no internet — an auto-summary, suggested tags, related notes, and smart search, all powered by classic TF-IDF/frequency-based NLP running entirely on your machine.

## Features

- **Real accounts**: sign up with a username/password, log in, log out — each user only ever sees their own notes
- Create, edit, and delete notes written in Markdown
- Notes rendered to formatted HTML (headings, code blocks, tables, bold/italic, etc.)
- Tag notes and search by title or tag
- **AI summary** — a 1-2 sentence extractive summary auto-generated for longer notes
- **Suggested tags** — keywords pulled from the note's own content, one click to add
- **Related notes** — other notes (of yours) ranked by how similar their content is
- **Smart search** — toggle to rank results by relevance to your query instead of exact text match

## Tech Stack

Python 3 · Flask · SQLite · `markdown` · Jinja2 · `werkzeug.security` (password hashing) · scikit-learn (TF-IDF + cosine similarity — **no LLM API, no cost**)

## Project Structure

```
notes-app/
├── app.py               # Flask routes
├── store.py               # NoteStore - SQLite CRUD, scoped by user_id
├── users.py                # UserStore - signup/login, hashed passwords
├── nlp_utils.py              # local AI: summarize(), extract_keywords(), rank_notes_by_similarity()
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── signup.html
│   ├── index.html
│   ├── view.html            # shows the AI summary, suggested tags, related notes
│   └── editor.html
├── static/
│   └── style.css
└── tests/
    ├── test_store.py          # includes per-user isolation tests
    ├── test_users.py
    ├── test_nlp_utils.py
    └── test_app.py
```

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Run it

```bash
python app.py
```

Open `http://localhost:5001` and click **Create an account** to sign up — no default/shared credentials, every user creates their own login.

For production use, set a real secret key (used to sign session cookies):

```bash
export NOTES_SECRET_KEY="a-long-random-string"
```

## How Multi-User Works

- `users` table: `username` (unique), `password_hash` (via `werkzeug.security.generate_password_hash` — passwords are never stored in plain text), `created_at`
- Every note has a `user_id`. `NoteStore` requires a `user_id` on every single read *and* write (`get`, `update`, `delete`, `list`) and filters by it in SQL — so even a bug in a route handler can't accidentally leak one user's note to another; the store itself won't return or modify a row that doesn't belong to the requesting user
- The session cookie stores `user_id` after login/signup; `@login_required` checks for it on every protected route

## How the AI Features Work (and why they need no API key)

Everything here is classic, local NLP — no LLM, no API call, no cost, works fully offline:

- **Summary**: sentences are scored by how many "important" (non-stopword, frequently-used) words they contain — a simplified version of Luhn's algorithm — and the top-scoring sentences are returned in their original order. Only shown when it actually shortens the note.
- **Suggested tags**: TF-IDF is computed across your notes, and the highest-scoring terms *for this note specifically* (that aren't already tags) are shown as one-click suggestions.
- **Related notes**: every note (of yours) is turned into a TF-IDF vector, and cosine similarity finds the closest matches to the note you're viewing.
- **Smart search**: instead of a plain `LIKE` substring match, your query and your notes are TF-IDF vectors, ranked by cosine similarity — so a search can surface a conceptually relevant note even if it doesn't contain your exact search words as substrings.

## Running Tests

```bash
python -m pytest tests/ -v
```

## Possible Improvements

*(Being upfront about the corners cut for a demo project — good things to know before deploying this anywhere public.)*

- No CSRF protection yet (would add `Flask-WTF` for that)
- No password reset / email verification flow
- Rendered Markdown is inserted with `| safe` — fine for a note's own author, but would need sanitizing (e.g. `bleach`) if notes could ever be shared or viewed by other users
- TF-IDF keyword extraction and similarity are lexical, not truly semantic — swapping in sentence embeddings (e.g. `sentence-transformers`, still free/local) would catch paraphrases that share no exact words
- Rate limiting on login/signup to slow down brute-force attempts
- Full-text search (SQLite FTS5) as a faster alternative to scanning all notes for "smart search"

## License

MIT — see [LICENSE](LICENSE).
