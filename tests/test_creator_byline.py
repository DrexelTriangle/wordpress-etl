"""Tests for the <dc:creator> byline fallback.

Run from the repo root:

    .venv/bin/python -m unittest tests.test_creator_byline
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Translator.ArticleTranslator import ArticleTranslator


def author_term(nicename, text):
    return {"@domain": "author", "@nicename": nicename, "#text": text}


def article_obj(terms, creator=None, text="x" * 200):
    return {
        "tags": terms,
        "categories": [],
        "text": text,
        "title": "A title",
        "creator": creator,
        "authors": [],
        "authorCleanNames": [],
    }


class CreatorFallback(unittest.TestCase):
    def setUp(self):
        self.translator = ArticleTranslator([])

    def test_creator_supplies_the_byline_when_there_is_no_author_term(self):
        # The regression: 2651 pre-Co-Authors-Plus posts carry their byline only
        # here, and every one of them used to come out with no author at all.
        obj = article_obj([], creator="john.chagaris")
        self.translator._processTags(obj)
        self.assertEqual(obj["authorCleanNames"], ["johnchagaris"])
        self.assertEqual(obj["authors"], ["john.chagaris"])

    def test_author_term_wins_and_creator_is_not_added(self):
        # Posts that have both must not gain a second, duplicate byline.
        self.translator.guestAuthorNames = {"cap-beeboop": "Michael Davis"}
        obj = article_obj([author_term("cap-beeboop", "beeboop")], creator="someone.else")
        self.translator._processTags(obj)
        self.assertEqual(obj["authors"], ["Michael Davis"])
        self.assertEqual(obj["authorCleanNames"], ["michaeldavis"])

    def test_email_shaped_handles_use_the_local_part(self):
        obj = article_obj([], creator="stefan.kusmirek@dev.thetriangle.org")
        self.translator._processTags(obj)
        self.assertEqual(obj["authorCleanNames"], ["stefankusmirek"])

    def test_missing_or_blank_creator_is_left_alone(self):
        for value in (None, "", "   ", 12345):
            obj = article_obj([], creator=value)
            self.translator._processTags(obj)
            self.assertEqual(obj["authorCleanNames"], [], f"for {value!r}")
            self.assertEqual(obj["authors"], [], f"for {value!r}")


if __name__ == "__main__":
    unittest.main()
