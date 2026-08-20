"""Tests for the per-source-site knobs that let the pipeline extract a second
WordPress (therectangle.org) without changing what it does for thetriangle.org.

Every test asserts both halves: the default reproduces the Triangle behaviour,
and the override does the new thing.

Run from the repo root:

    .venv/bin/python -m unittest tests.test_site_profile
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Translator.ArticleTranslator import ArticleTranslator
from Utils.MediaURL import canonicalize_media_url, rewrite_media_urls_in_html
from Utils.SiteProfile import (
    category_term_source,
    id_offset,
    keep_short_posts_with_image,
    legacy_media_hosts,
    min_body_length,
)

BASE = "https://media.example.net"
RECT_IMG = "https://www.therectangle.org/wp-content/uploads/2026/03/logo.png"


def env(**overrides):
    return mock.patch.dict(os.environ, overrides, clear=False)


def category_term(nicename, text):
    return {"@domain": "category", "@nicename": nicename, "#text": text}


def article_obj(terms=None, text="x" * 200, title="A title", featuredImgID=None):
    return {
        "tags": terms if terms is not None else [],
        "categories": [],
        "text": text,
        "title": title,
        "authors": [],
        "authorCleanNames": [],
        "featuredImgID": featuredImgID,
        "creator": None,
    }


class LegacyMediaHosts(unittest.TestCase):
    def test_default_still_rewrites_both_triangle_domains(self):
        self.assertEqual(
            legacy_media_hosts(), ("thetriangle.org", "therectangle.org")
        )
        self.assertEqual(
            canonicalize_media_url(RECT_IMG, base=BASE),
            f"{BASE}/wp-content/uploads/2026/03/logo.png",
        )

    def test_dropping_the_rectangle_leaves_its_live_urls_alone(self):
        # The whole point: extracting the Rectangle itself must not rewrite its
        # own working image URLs onto a media base that has never held them.
        with env(LEGACY_MEDIA_HOSTS="thetriangle.org"):
            self.assertEqual(canonicalize_media_url(RECT_IMG, base=BASE), RECT_IMG)
            # ...while the Triangle's own uploads still canonicalize.
            self.assertEqual(
                canonicalize_media_url(
                    "https://www.thetriangle.org/wp-content/uploads/a.jpg", base=BASE
                ),
                f"{BASE}/wp-content/uploads/a.jpg",
            )

    def test_body_html_respects_the_host_list(self):
        html = f'<img src="{RECT_IMG}">'
        self.assertIn(BASE, rewrite_media_urls_in_html(html, base=BASE))
        with env(LEGACY_MEDIA_HOSTS="thetriangle.org"):
            self.assertEqual(rewrite_media_urls_in_html(html, base=BASE), html)

    def test_empty_list_keeps_absolute_urls_but_still_fixes_relative_ones(self):
        # A site already serving uploads at their final URL opts out by host,
        # but relative refs still have to be made absolute to work at all.
        with env(LEGACY_MEDIA_HOSTS=""):
            self.assertEqual(legacy_media_hosts(), ())
            self.assertEqual(canonicalize_media_url(RECT_IMG, base=BASE), RECT_IMG)
            self.assertEqual(
                canonicalize_media_url("wp-content/uploads/a.jpg", base=BASE),
                f"{BASE}/wp-content/uploads/a.jpg",
            )
            self.assertEqual(
                rewrite_media_urls_in_html('<img src="/wp-content/uploads/a.jpg">', base=BASE),
                f'<img src="{BASE}/wp-content/uploads/a.jpg">',
            )


class BodyLengthFloor(unittest.TestCase):
    def setUp(self):
        self.translator = ArticleTranslator([])

    def test_default_floor_is_unchanged(self):
        self.assertEqual(min_body_length(), 100)
        self.assertFalse(keep_short_posts_with_image())
        self.assertFalse(self.translator._dataSanityCheck(article_obj(text="short")))

    def test_lowering_the_floor_keeps_a_short_post(self):
        with env(MIN_BODY_LENGTH="10"):
            self.assertTrue(
                self.translator._dataSanityCheck(article_obj(text="x" * 20))
            )

    def test_image_only_post_survives_when_exempted(self):
        # HORSE-O-SCOPES and WHO IS BETTER have literally empty post_content on
        # the live Rectangle: the featured image is the entire joke.
        empty = article_obj(text="", featuredImgID="4213")
        self.assertFalse(self.translator._dataSanityCheck(empty))
        with env(KEEP_SHORT_POSTS_WITH_IMAGE="true"):
            self.assertTrue(self.translator._dataSanityCheck(empty))

    def test_exemption_does_not_rescue_a_short_post_with_no_image(self):
        with env(KEEP_SHORT_POSTS_WITH_IMAGE="true"):
            self.assertFalse(
                self.translator._dataSanityCheck(article_obj(text="short"))
            )

    def test_bodyless_post_survives_the_tag_drop_path_too(self):
        # Regression: _processTags marks a bodyless post tags=-1 and returns
        # before the length floor is ever consulted, so honouring the exemption
        # only in _dataSanityCheck rescued nothing. Caught on real data -- the
        # live export produced 225 of 228 posts with the exemption "on".
        from Utils.Constants import DEFAULT_VALUE

        obj = article_obj(
            [category_term("comics", "Funnies")],
            text=DEFAULT_VALUE,
            featuredImgID="1212",
        )
        self.translator._processTags(obj)
        self.assertEqual(obj["tags"], -1)

        with env(KEEP_SHORT_POSTS_WITH_IMAGE="true"):
            obj = article_obj(
                [category_term("comics", "Funnies")],
                text=DEFAULT_VALUE,
                featuredImgID="1212",
            )
            self.translator._processTags(obj)
            self.assertNotEqual(obj["tags"], -1)
            self.assertEqual(obj["categories"], ["Funnies"])
            self.assertTrue(self.translator._dataSanityCheck(obj))

    def test_bodyless_post_with_no_image_is_still_dropped(self):
        from Utils.Constants import DEFAULT_VALUE

        with env(KEEP_SHORT_POSTS_WITH_IMAGE="true"):
            obj = article_obj([category_term("comics", "Funnies")], text=DEFAULT_VALUE)
            self.translator._processTags(obj)
            self.assertEqual(obj["tags"], -1)

    def test_sentinel_minus_one_does_not_count_as_an_image(self):
        # featuredImgID uses -1 for "no featured image", and -1 is truthy. A
        # plain truth test rescued a bodyless draft that had no image at all.
        from Utils.Constants import DEFAULT_VALUE

        with env(KEEP_SHORT_POSTS_WITH_IMAGE="true"):
            self.assertFalse(
                self.translator._dataSanityCheck(
                    article_obj(text="short", featuredImgID=-1)
                )
            )
            obj = article_obj(
                [category_term("uncategorized", "Uncategorized")],
                text=DEFAULT_VALUE,
                featuredImgID=-1,
            )
            self.translator._processTags(obj)
            self.assertEqual(obj["tags"], -1)
            # A real id still counts, including as the string the export yields.
            self.assertTrue(
                self.translator._dataSanityCheck(
                    article_obj(text="short", featuredImgID="1212")
                )
            )

    def test_bad_value_is_rejected_loudly(self):
        with env(MIN_BODY_LENGTH="lots"):
            with self.assertRaises(ValueError):
                min_body_length()


class IdOffset(unittest.TestCase):
    def test_default_starts_at_zero(self):
        self.assertEqual(id_offset(), 0)
        self.assertEqual(ArticleTranslator([]).objCount, 0)

    def test_offset_moves_the_id_sequence_past_the_first_site(self):
        with env(ID_OFFSET="900000"):
            translator = ArticleTranslator([])
            self.assertEqual(translator.objCount, 900000)
            translator.addObject({"id": translator.objCount})
            self.assertEqual(translator.objCount, 900001)


class CategoryTermSource(unittest.TestCase):
    def setUp(self):
        self.translator = ArticleTranslator([])

    def test_default_records_display_text(self):
        self.assertEqual(category_term_source(), "text")
        obj = article_obj([category_term("farts-and-entertainment", "Farts & Enter-pain-ment")])
        self.translator._processTags(obj)
        self.assertEqual(obj["categories"], ["Farts & Enter-pain-ment"])

    def test_nicename_mode_records_the_stable_slug(self):
        # The Rectangle rewrites its section display names for the joke every
        # year; the slugs stay put, so text-matching zeroes out after a rename.
        with env(CATEGORY_TERM_SOURCE="nicename"):
            obj = article_obj([category_term("trufactz", "Olds")])
            self.translator._processTags(obj)
            self.assertEqual(obj["categories"], ["trufactz"])

    def test_post_tags_are_untouched_by_the_setting(self):
        with env(CATEGORY_TERM_SOURCE="nicename"):
            obj = article_obj([
                {"@domain": "post_tag", "@nicename": "drexel", "#text": "Drexel"},
                category_term("sporps", "Fuck it, we ball"),
            ])
            self.translator._processTags(obj)
            self.assertEqual(obj["tags"], ["Drexel"])
            self.assertEqual(obj["categories"], ["sporps"])

    def test_bad_value_is_rejected_loudly(self):
        with env(CATEGORY_TERM_SOURCE="slug"):
            with self.assertRaises(ValueError):
                category_term_source()


if __name__ == "__main__":
    unittest.main()
