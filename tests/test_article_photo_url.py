"""Tests for ArticleFormatter photo_url normalization. Run from the repo root:

    .venv/bin/python -m unittest tests.test_article_photo_url
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Formatter.ArticleFormatter import ArticleFormatter


class PhotoURLNormalization(unittest.TestCase):
    def _photo_url(self, value):
        return ArticleFormatter([])._to_cms_row({"photoURL": value})["photo_url"]

    def test_wordpress_sentinels_become_null(self):
        # WordPress signals "no featured image" with -1. It arrives as an int or
        # as a string depending on the export path; both must end up NULL rather
        # than a literal "-1" that consumers render as <img src="-1">.
        for value in (-1, "-1", " -1 ", 0, "0", None, "", "   "):
            with self.subTest(value=value):
                self.assertIsNone(self._photo_url(value))

    def test_real_urls_are_canonicalized_not_dropped(self):
        got = self._photo_url(
            "https://www.thetriangle.org/wp-content/uploads/2016/03/image.jpg"
        )
        self.assertIsNotNone(got)
        self.assertTrue(got.endswith("/wp-content/uploads/2016/03/image.jpg"))

    def test_missing_key_is_null(self):
        self.assertIsNone(ArticleFormatter([])._to_cms_row({})["photo_url"])


if __name__ == "__main__":
    unittest.main()
