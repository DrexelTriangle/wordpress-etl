"""Tests for resolving a post's author term to the real guest author name.

Run from the repo root:

    .venv/bin/python -m unittest tests.test_guest_author_names
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Translator.ArticleTranslator import ArticleTranslator


def author_term(nicename, text):
    return {"@domain": "author", "@nicename": nicename, "#text": text}


def article_obj(terms, text="x" * 200, title="A title"):
    return {
        "tags": terms,
        "categories": [],
        "text": text,
        "title": title,
        "authors": [],
        "authorCleanNames": [],
    }


class ResolveAuthorTerms(unittest.TestCase):
    def setUp(self):
        self.translator = ArticleTranslator([])

    def test_slug_handle_resolves_to_real_name(self):
        # The regression: the term text is the slug, and this slug looks
        # nothing like the name, so the article used to end up with no byline.
        self.translator.guestAuthorNames = {"cap-beeboop": "Michael Davis"}
        obj = article_obj([author_term("cap-beeboop", "beeboop")])
        self.translator._processTags(obj)
        self.assertEqual(obj["authors"], ["Michael Davis"])
        self.assertEqual(obj["authorCleanNames"], ["michaeldavis"])

    def test_accented_name_comes_from_the_export_not_the_slug(self):
        self.translator.guestAuthorNames = {
            "cap-maria-paula-mijares": "María Paula Mijares"
        }
        obj = article_obj([author_term("cap-maria-paula-mijares", "maria-paula-mijares")])
        self.translator._processTags(obj)
        self.assertEqual(obj["authors"], ["María Paula Mijares"])

    def test_falls_back_to_term_text_when_unmapped(self):
        self.translator.guestAuthorNames = {}
        obj = article_obj([author_term("cap-someone", "Some One")])
        self.translator._processTags(obj)
        self.assertEqual(obj["authors"], ["Some One"])

    def test_multiple_authors_each_resolve(self):
        self.translator.guestAuthorNames = {
            "cap-beeboop": "Michael Davis",
            "cap-carter": "Carter Blake",
        }
        obj = article_obj([
            author_term("cap-beeboop", "beeboop"),
            author_term("cap-carter", "carter"),
        ])
        self.translator._processTags(obj)
        self.assertEqual(obj["authors"], ["Michael Davis", "Carter Blake"])


if __name__ == "__main__":
    unittest.main()
