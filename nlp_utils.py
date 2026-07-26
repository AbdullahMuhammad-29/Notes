"""Lightweight, fully local NLP helpers for the notes app - no external AI
API, no cost, no internet required. Classic techniques only:
  - extractive summarization via word-frequency sentence scoring
    (a simplified version of Luhn's algorithm)
  - TF-IDF for keyword extraction and note-to-note similarity
"""
import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
WORD_RE = re.compile(r"[a-zA-Z']+")


def _split_sentences(text):
    text = (text or "").strip()
    if not text:
        return []
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]


def summarize(text, num_sentences=2):
    """Extractive summary: scores each sentence by the frequency of the
    words it contains, then returns the top-scoring sentences in their
    original order. Returns the original text unchanged if it's already
    short enough."""
    sentences = _split_sentences(text)
    if len(sentences) <= num_sentences:
        return (text or "").strip()

    words = [w.lower() for w in WORD_RE.findall(text) if w.lower() not in ENGLISH_STOP_WORDS]
    if not words:
        return " ".join(sentences[:num_sentences])

    freq = Counter(words)
    max_freq = max(freq.values())
    for word in freq:
        freq[word] /= max_freq

    scores = []
    for sentence in sentences:
        sentence_words = [w.lower() for w in WORD_RE.findall(sentence)]
        score = sum(freq.get(w, 0) for w in sentence_words) / len(sentence_words) if sentence_words else 0
        scores.append(score)

    top_indices = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)[:num_sentences]
    top_indices.sort()
    return " ".join(sentences[i] for i in top_indices)


def extract_keywords(text, top_n=5, corpus=None):
    """Extracts top keywords from `text`. Uses TF-IDF against `corpus` (other
    documents) when there's enough to compare against for meaningful IDF
    weighting; otherwise falls back to plain word frequency."""
    words = [w.lower() for w in WORD_RE.findall(text or "") if w.lower() not in ENGLISH_STOP_WORDS and len(w) > 2]
    if not words:
        return []

    if corpus and len([c for c in corpus if c and c.strip()]) >= 2:
        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            matrix = vectorizer.fit_transform(list(corpus) + [text])
            feature_names = vectorizer.get_feature_names_out()
            scores = matrix[-1].toarray()[0]
            ranked = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
            keywords = [term for term, score in ranked if score > 0][:top_n]
            if keywords:
                return keywords
        except ValueError:
            pass  # too little text to build a vocabulary - fall through

    freq = Counter(words)
    return [word for word, _ in freq.most_common(top_n)]


def rank_notes_by_similarity(query_text, notes, top_n=5):
    """Ranks `notes` (each needs 'title' and 'body' keys) by TF-IDF cosine
    similarity to `query_text`. Returns [(note, score), ...] sorted
    descending, excluding zero-similarity results."""
    if not notes:
        return []

    documents = [f"{n['title']} {n['body']}" for n in notes] + [query_text]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return []

    query_vec = matrix[-1]
    note_vecs = matrix[:-1]
    similarities = cosine_similarity(query_vec, note_vecs)[0]

    ranked = sorted(zip(notes, similarities), key=lambda pair: pair[1], reverse=True)
    return [(note, score) for note, score in ranked if score > 0][:top_n]
