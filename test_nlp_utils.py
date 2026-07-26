import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nlp_utils import summarize, extract_keywords, rank_notes_by_similarity

LONG_TEXT = (
    "Python is a popular programming language known for its readability. "
    "It was created by Guido van Rossum and released in 1991. "
    "Python supports multiple programming paradigms including procedural and object oriented styles. "
    "The language has a large standard library covering everything from web servers to file compression. "
    "Many companies including Google, Netflix, and Instagram use Python in production. "
    "Python's package manager pip makes it easy to install third party libraries."
)


def test_summarize_short_text_returns_unchanged():
    short_text = "Just one sentence here."
    assert summarize(short_text, num_sentences=2) == short_text


def test_summarize_long_text_shortens_it():
    summary = summarize(LONG_TEXT, num_sentences=2)
    assert len(summary) < len(LONG_TEXT)
    assert summary.strip() != ""


def test_summarize_empty_text_returns_empty():
    assert summarize("", num_sentences=2) == ""


def test_extract_keywords_returns_relevant_words():
    keywords = extract_keywords(LONG_TEXT, top_n=5)
    assert len(keywords) > 0
    assert any(k.lower() in ("python", "programming", "language") for k in keywords)


def test_extract_keywords_empty_text_returns_empty_list():
    assert extract_keywords("", top_n=5) == []


def test_extract_keywords_with_corpus_uses_tfidf():
    corpus = ["the cat sat on the mat", "dogs are loyal animals"]
    keywords = extract_keywords("Python is a great programming language for data science", top_n=3, corpus=corpus)
    assert len(keywords) > 0


def test_rank_notes_by_similarity_orders_by_relevance():
    notes = [
        {"id": 1, "title": "Python basics", "body": "Python is a programming language"},
        {"id": 2, "title": "Grocery list", "body": "milk eggs bread butter"},
        {"id": 3, "title": "Advanced Python", "body": "Python decorators and generators explained"},
    ]
    ranked = rank_notes_by_similarity("python programming tips", notes, top_n=3)
    assert len(ranked) >= 1
    top_note, top_score = ranked[0]
    assert "python" in top_note["title"].lower()


def test_rank_notes_by_similarity_empty_list_returns_empty():
    assert rank_notes_by_similarity("anything", [], top_n=5) == []
