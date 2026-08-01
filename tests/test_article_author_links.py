"""Tests for article->author link building.

Run from the repo root:

    .venv/bin/python -m unittest tests.test_article_author_links
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Sanitizer.ArticleAuthorMatcher import ArticleAuthorMatcher


AUTHORS = [
    {"id": 553, "display_name": "Ava Buckingham", "login": "ava-buckingham"},
    {"id": 343, "display_name": "Mary Elizabeth Hoffman", "login": "mary-elizabeth-hoffman"},
    {"id": 338, "display_name": "Snehal Yarlagadda", "login": "snehal-yarlagadda"},
    {"id": 32, "display_name": "Shreya Srinivasan", "login": "shreya-srinivasan"},
]


def matcher(articles=None, cache=None):
    m = ArticleAuthorMatcher(articles or [], AUTHORS)
    m.resolution_cache = cache or {}
    return m


class ResolveCachedMatch(unittest.TestCase):
    def test_stale_id_is_reresolved_by_name(self):
        # Ava Buckingham was 554 in the export this was answered against; she is
        # 553 now, and 554 exists nowhere, so trusting it orphaned 9 links.
        m = matcher(cache={"abuckingham": (554, "Ava Buckingham")})
        self.assertEqual(m._resolveCachedMatch("abuckingham"), (553, "Ava Buckingham"))

    def test_reused_id_does_not_credit_the_wrong_person(self):
        # The dangerous case: 338 was Hoffman, and in this export 338 is a
        # different real person. The row exists, so no integrity check catches
        # it -- her articles simply get his name.
        m = matcher(cache={"elizabethhoffman": (338, "Mary Elizabeth Hoffman")})
        resolved = m._resolveCachedMatch("elizabethhoffman")
        self.assertEqual(resolved, (343, "Mary Elizabeth Hoffman"))
        self.assertNotEqual(resolved[0], 338)

    def test_person_absent_from_this_export_falls_through(self):
        m = matcher(cache={"someone": (900, "Someone Gone")})
        self.assertIsNone(m._resolveCachedMatch("someone"))

    def test_uncached_name_returns_none(self):
        self.assertIsNone(matcher()._resolveCachedMatch("nobody"))

    def test_malformed_entry_returns_none(self):
        m = matcher(cache={"bad": None, "worse": (1,)})
        self.assertIsNone(m._resolveCachedMatch("bad"))
        self.assertIsNone(m._resolveCachedMatch("worse"))


class ApplyMatches(unittest.TestCase):
    def test_repeated_byline_produces_one_link(self):
        # articles_authors has no unique constraint, so a doubled byline wrote
        # two identical rows and rendered the name twice.
        article = {
            "id": 7715,
            "authorCleanNames": ["shreyasrinivasan", "shreyasrinivasan"],
        }
        m = matcher([article])
        m.author_matches = {7715: {"shreyasrinivasan": (32, "Shreya Srinivasan")}}
        m._applyMatches()
        self.assertEqual(article["authorIDs"], [32])
        self.assertEqual(article["authors"], ["Shreya Srinivasan"])

    def test_distinct_coauthors_are_both_kept(self):
        article = {
            "id": 1,
            "authorCleanNames": ["avabuckingham", "shreyasrinivasan"],
        }
        m = matcher([article])
        m.author_matches = {
            1: {
                "avabuckingham": (553, "Ava Buckingham"),
                "shreyasrinivasan": (32, "Shreya Srinivasan"),
            }
        }
        m._applyMatches()
        self.assertEqual(article["authorIDs"], [553, 32])
        self.assertEqual(article["authors"], ["Ava Buckingham", "Shreya Srinivasan"])


if __name__ == "__main__":
    unittest.main()
