"""Tests for the Yoast SEO fields ArticleFormatter lifts into their own columns.
Run from the repo root:

    .venv/bin/python -m unittest tests.test_article_seo_fields
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Formatter.ArticleFormatter import ArticleFormatter


class SeoColumns(unittest.TestCase):
    def _row(self, metadata):
        return ArticleFormatter([])._to_cms_row({"metadata": metadata})

    def test_yoast_keys_land_in_their_columns(self):
        row = self._row({
            "_yoast_wpseo_focuskw": "Soda Fest",
            "_yoast_wpseo_metadesc": "A creative genius is impossible to stop.",
            "_yoast_wpseo_title": "Store profile: Styles inspired by Marc",
            "_yoast_wpseo_linkdex": "61",
        })
        self.assertEqual(row["focus_keyword"], "Soda Fest")
        self.assertEqual(row["meta_description"], "A creative genius is impossible to stop.")
        self.assertEqual(row["seo_title"], "Store profile: Styles inspired by Marc")

    def test_legacy_text_input_key_fills_the_keyphrase(self):
        # Older posts wrote the keyphrase only to the _text_input key.
        row = self._row({"_yoast_wpseo_focuskw_text_input": "Drexel"})
        self.assertEqual(row["focus_keyword"], "Drexel")

    def test_canonical_key_wins_over_the_legacy_one(self):
        row = self._row({
            "_yoast_wpseo_focuskw": "current",
            "_yoast_wpseo_focuskw_text_input": "stale",
        })
        self.assertEqual(row["focus_keyword"], "current")

    def test_yoast_templates_are_dropped(self):
        # "%%title%% %%sep%% %%sitename%%" only means something inside WordPress;
        # importing it verbatim would put placeholder text in the CMS editor.
        row = self._row({
            "_yoast_wpseo_title": "%%title%% %%sep%% %%sitename%%",
            "_yoast_wpseo_metadesc": "%%excerpt%%",
        })
        self.assertIsNone(row["seo_title"])
        self.assertIsNone(row["meta_description"])

    def test_blank_and_missing_metadata_are_null(self):
        for metadata in ({}, None, "-1", [], {"_yoast_wpseo_focuskw": "   "}):
            with self.subTest(metadata=metadata):
                row = self._row(metadata)
                self.assertIsNone(row["focus_keyword"])
                self.assertIsNone(row["meta_description"])
                self.assertIsNone(row["seo_title"])

    def test_metadata_list_form_is_merged(self):
        row = self._row([
            {"_yoast_wpseo_focuskw": "girl"},
            {"_yoast_wpseo_title": "The new IT girl"},
        ])
        self.assertEqual(row["focus_keyword"], "girl")
        self.assertEqual(row["seo_title"], "The new IT girl")

    def test_metadata_blob_is_still_emitted(self):
        metadata = {"_yoast_wpseo_focuskw": "Drexel"}
        self.assertEqual(self._row(metadata)["metadata"], metadata)

    def test_columns_and_schema_stay_in_step(self):
        for column in ("focus_keyword", "meta_description", "seo_title"):
            self.assertIn(column, ArticleFormatter.CMS_COLUMNS)
            self.assertIn(column, ArticleFormatter.CMS_SCHEMA)


class SeoSql(unittest.TestCase):
    def test_insert_carries_the_seo_values(self):
        statements = list(ArticleFormatter([
            {"id": 1, "title": "T", "metadata": {"_yoast_wpseo_focuskw": "Soda Fest"}}
        ]).iter_format("articles"))
        create, inserts = statements[0], "\n".join(statements[1:])
        self.assertIn("`focus_keyword` LONGTEXT", create)
        self.assertIn("`meta_description` LONGTEXT", create)
        self.assertIn("`seo_title` LONGTEXT", create)
        self.assertIn("Soda Fest", inserts)


if __name__ == "__main__":
    unittest.main()
