"""Per-article content transform run by the sanitizer's worker processes.

Kept deliberately lightweight: it imports only the sanitization helpers and
Utility, never the heavy matching stack (minhashlib via Policy). That keeps the
per-worker import cost low under the thread-safe ``forkserver``/``spawn`` start
methods, which re-import the worker's module in each worker process.
"""
import re

from Utils.MediaURL import rewrite_media_urls_in_html
from Utils.Utility import Utility
from Utils.WPContentSanitization import (
    sanitize_backslashes,
    convert_caption_shortcodes,
    convert_puzzleme_shortcodes,
    add_missing_paragraph_tags,
)

# Categories whose articles never get an excerpt (comics/puzzles pages).
_PUZZLE_CATEGORIES = frozenset({
    "comics", "comic", "comics & puzzles", "puzzles", "crossword", "sudoku",
})
_PUZZLE_EMBED_PATTERN = re.compile(r"\[puzzleme|pm-embed-div", re.IGNORECASE)


def _excerpt_for(text, categories):
    """Excerpt for already-sanitized text, suppressed for comics/puzzle posts."""
    normalized = {str(c).strip().lower() for c in (categories or []) if c is not None}
    if normalized & _PUZZLE_CATEGORIES:
        return ""
    if _PUZZLE_EMBED_PATTERN.search(text):
        return ""
    return Utility._build_excerpt(text, max_words=100)


def process_article(payload):
    """Pure, picklable per-article transform.

    Takes (idx, text, categories); returns (idx, sanitized_or_None, fixes,
    excerpt). ``sanitized`` is None when the text is unchanged, so the original
    text never has to travel back over the IPC boundary in that case.
    """
    idx, text, categories = payload
    original = text or ""
    if not original:
        return (idx, None, [], "")

    fixes = []
    sanitized = sanitize_backslashes(original)
    if sanitized != original:
        fixes.append("backslashes stripped")

    before = sanitized
    sanitized = convert_caption_shortcodes(sanitized)
    if sanitized != before:
        fixes.append("caption shortcodes converted")

    before = sanitized
    sanitized = convert_puzzleme_shortcodes(sanitized)
    if sanitized != before:
        fixes.append("puzzleme shortcodes converted")

    before = sanitized
    sanitized = add_missing_paragraph_tags(sanitized)
    if sanitized != before:
        fixes.append("paragraph tags restored")

    before = sanitized
    sanitized = rewrite_media_urls_in_html(sanitized)
    if sanitized != before:
        fixes.append("media urls rewritten")

    excerpt = _excerpt_for(sanitized, categories)
    changed = sanitized != original
    return (idx, sanitized if changed else None, fixes, excerpt)
