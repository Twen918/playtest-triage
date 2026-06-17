"""Lexical deduplication of near-identical feedback items.

Different playtesters often report the same issue in nearly the same words.
Merging those before classification (1) makes the report show how *often*
an issue was hit -- frequency is a prioritization signal -- and (2) reduces
the number of items sent to the API.

This is token-based (word-level) similarity via difflib, so it catches
near-verbatim repeats, not paraphrases. Semantic dedup (embeddings) is a
roadmap item. Greedy single-pass clustering is O(n^2) in the worst case,
which is fine at playtest scale (tens to hundreds of notes).
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _normalize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into words."""
    return re.sub(r"[^\w\s]", "", text.lower()).split()


def similarity(a: str, b: str) -> float:
    """Word-level similarity ratio between two strings, in [0, 1]."""
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def merge_similar(
    items: list[str], threshold: float = 0.8
) -> list[tuple[str, int]]:
    """Greedily cluster near-duplicate items.

    Returns (representative_text, count) pairs in first-seen order.
    The representative is always the first occurrence, so the earliest
    phrasing of an issue is what appears in the report.
    """
    clusters: list[tuple[str, int]] = []
    for item in items:
        for i, (representative, count) in enumerate(clusters):
            if similarity(item, representative) >= threshold:
                clusters[i] = (representative, count + 1)
                break
        else:
            clusters.append((item, 1))
    return clusters
