"""Tests for ArticleEmbeddingsFormatter's embedding source. Run from the repo root:

    .venv/bin/python -m unittest tests.test_article_embeddings

These do not load a model -- they pin the *text* that gets embedded, which is the
half that has to agree with the CMS.
"""
import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Formatter.ArticleEmbeddingsFormatter import ArticleEmbeddingsFormatter

MAX_CHARS = 5000

# The CMS reconciler decides an article needs re-embedding by comparing this hash
# to the one stored beside the vector. This formatter seeds the migrated archive
# with rows the CMS did not write, so both sides must derive the hash from
# byte-identical text -- otherwise every seeded row reads as stale and the whole
# archive is re-embedded through the sidecar after each reseed.
#
# The identical table lives in the CMS at
# server/internal/database/article_embeddings_test.go. Changing one without the
# other breaks the contract; that is exactly what these goldens catch.
GOLDENS = [
    (
        "tags and entity-decoded body",
        {"title": "Tuition freeze", "tags": "campus,money",
         "text": "<p>Hello &amp; welcome</p><div>world</div>"},
        "ef099c229d1e5a3b4541abe9c57491b2467711de61aab5124bc1724dc7f9bcbd",
        51,
    ),
    (
        "empty parts are dropped, not joined as blanks",
        {"title": "  Spaced  ", "tags": "", "text": "<p>a</p>\n\n<p>b</p>"},
        "55b414e3ba68401d30466d433fa01cbf79a3352cc2cfd5ae5c379ae8541d9013",
        11,
    ),
    (
        "non-ASCII survives intact",
        {"title": "Unicode café — naïve", "tags": "résumé", "text": "<p>éèê x</p>"},
        "dc79ead758b72f0e0cf244f00c419fde0eb64b78ad288d18e0dbb8ea88d6c64f",
        35,
    ),
    (
        # Strip tags first, then unescape. Unescaping first would turn this
        # escaped markup into real tags and delete the text.
        "escaped markup is content, not tags",
        {"title": "Escaped", "tags": "", "text": "&lt;b&gt;not a tag&lt;/b&gt;"},
        "a758e80e1119052a28e974bd8d1ad0877967624298e8ac78749dbbc8a957cb9e",
        25,
    ),
    (
        # Truncation counts characters, matching the CMS's rune-wise cut. A
        # byte-wise cut on either side would land mid-character.
        "long multi-byte body truncates by character",
        {"title": "Long", "tags": "", "text": "<p>" + ("xé " * 4000) + "</p>"},
        "3a05bd7c947bd63317524a41c5e75e8b5cf6b711ba6554d515f475067e93a949",
        5000,
    ),
    (
        "an entirely empty article",
        {"title": "", "tags": "", "text": "<p></p>"},
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        0,
    ),
    (
        "numeric and named entities in tags and body",
        {"title": "Entities", "tags": "a&amp;b", "text": "<p>&nbsp;&#39;quoted&#39;</p>"},
        "e7da0a366df46c77542065f919a89e4267b30cc5030c5f206ca60b69a6a3b356",
        27,
    ),
]


def formatter(rows=None):
    return ArticleEmbeddingsFormatter(
        rows or [], model="BAAI/bge-small-en-v1.5", batch_size=8, max_chars=MAX_CHARS
    )


class EmbeddingSourceMatchesCMS(unittest.TestCase):
    def test_goldens(self):
        fmt = formatter()
        for name, row, want_hash, want_len in GOLDENS:
            with self.subTest(name):
                blob = fmt._embedding_source(row)
                self.assertEqual(len(blob), want_len, blob)
                got = hashlib.sha256(blob.encode("utf-8")).hexdigest()
                self.assertEqual(got, want_hash, blob)


class NormalizeArticles(unittest.TestCase):
    def test_carries_the_hash_and_skips_unusable_rows(self):
        fmt = formatter([
            {"id": 2, "title": "Second", "tags": "", "text": "<p>b</p>"},
            {"id": 1, "title": "First", "tags": "", "text": "<p>a</p>"},
            {"id": None, "title": "No id", "tags": "", "text": "<p>c</p>"},
            {"id": "not-a-number", "title": "Bad id", "tags": "", "text": "<p>d</p>"},
            {"id": 3, "title": "", "tags": "", "text": "<p></p>"},
        ])
        rows = fmt._normalize_articles()

        # Sorted by id, and the three unusable rows are gone: no id, an
        # unparseable id, and one with no text to embed at all.
        self.assertEqual([row["id"] for row in rows], [1, 2])
        for row in rows:
            self.assertEqual(
                row["hash"], hashlib.sha256(row["text"].encode("utf-8")).hexdigest()
            )


if __name__ == "__main__":
    unittest.main()
