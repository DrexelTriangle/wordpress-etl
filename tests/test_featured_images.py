"""Tests for resolving a post's WordPress featured image into photo_url.

Run from the repo root:

    .venv/bin/python -m unittest tests.test_featured_images
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Extractor import Extractor
from Translator.ArticleTranslator import ArticleTranslator
from Translator.AuthorTranslator import AuthorTranslator


def meta(key, value):
    return {"wp:meta_key": key, "wp:meta_value": value}


WXR = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
  <item>
    <title>Here's your Sudoku :)</title>
    <content:encoded><![CDATA[[puzzleme set="abc" id="def" type="sudoku"]{filler}]]></content:encoded>
    <wp:post_id>59171</wp:post_id>
    <wp:post_name>heres-your-sudoku</wp:post_name>
    <wp:post_type>post</wp:post_type>
    <wp:post_date_gmt>2023-11-17 14:00:00</wp:post_date_gmt>
    <wp:post_modified_gmt>2023-11-17 14:00:00</wp:post_modified_gmt>
    <wp:comment_status>open</wp:comment_status>
    <category domain="category" nicename="sudoku">Sudoku</category>
    <wp:postmeta>
      <wp:meta_key>_thumbnail_id</wp:meta_key>
      <wp:meta_value>59172</wp:meta_value>
    </wp:postmeta>
  </item>
  <item>
    <title>Body image loses to the featured image</title>
    <content:encoded><![CDATA[<img src="https://www.thetriangle.org/wp-content/uploads/2023/11/in-body.jpg" />{filler}]]></content:encoded>
    <wp:post_id>59180</wp:post_id>
    <wp:post_name>featured-image-wins</wp:post_name>
    <wp:post_type>post</wp:post_type>
    <wp:post_date_gmt>2023-11-18 14:00:00</wp:post_date_gmt>
    <wp:post_modified_gmt>2023-11-18 14:00:00</wp:post_modified_gmt>
    <wp:comment_status>open</wp:comment_status>
    <category domain="category" nicename="news">News</category>
    <wp:postmeta>
      <wp:meta_key>_thumbnail_id</wp:meta_key>
      <wp:meta_value>59172</wp:meta_value>
    </wp:postmeta>
  </item>
  <item>
    <title>No featured image at all</title>
    <content:encoded><![CDATA[<img src="https://www.thetriangle.org/wp-content/uploads/2023/11/only-image.jpg" />{filler}]]></content:encoded>
    <wp:post_id>59190</wp:post_id>
    <wp:post_name>no-featured-image</wp:post_name>
    <wp:post_type>post</wp:post_type>
    <wp:post_date_gmt>2023-11-19 14:00:00</wp:post_date_gmt>
    <wp:post_modified_gmt>2023-11-19 14:00:00</wp:post_modified_gmt>
    <wp:comment_status>open</wp:comment_status>
    <category domain="category" nicename="news">News</category>
  </item>
  <item>
    <title>Screenshot 2023-11-14 123323</title>
    <content:encoded></content:encoded>
    <wp:post_id>59172</wp:post_id>
    <wp:post_name>screenshot-2023-11-14-123323</wp:post_name>
    <wp:post_type>attachment</wp:post_type>
    <wp:post_parent>59171</wp:post_parent>
    <wp:attachment_url>https://cms.thetriangle.org/wp-content/uploads/2023/11/sudoku.png</wp:attachment_url>
  </item>
</channel>
</rss>
""".replace("{filler}", "x" * 200)


class ThumbnailIDExtraction(unittest.TestCase):
    def setUp(self):
        self.translator = ArticleTranslator([])

    def test_reads_the_thumbnail_postmeta(self):
        self.assertEqual(self.translator._thumbnailID([meta("_thumbnail_id", "59172")]), 59172)

    def test_single_postmeta_arrives_as_a_bare_dict(self):
        self.assertEqual(self.translator._thumbnailID(meta("_thumbnail_id", "42")), 42)

    def test_missing_or_unusable_meta_keeps_the_wordpress_sentinel(self):
        self.assertEqual(self.translator._thumbnailID([meta("_edit_last", "101266")]), -1)
        self.assertEqual(self.translator._thumbnailID([meta("_thumbnail_id", "")]), -1)
        self.assertEqual(self.translator._thumbnailID(None), -1)


class ResolveFeaturedImages(unittest.TestCase):
    def setUp(self):
        self.translator = ArticleTranslator([])

    def _addArticle(self, articleID, featuredImgID, photoURL=None):
        self.translator.addObject({"id": articleID, "featuredImgID": featuredImgID, "photoURL": photoURL})

    def test_fills_in_a_missing_photo(self):
        self._addArticle(0, 59172)
        resolved = self.translator.resolveFeaturedImages({"59172": "https://cms.thetriangle.org/x.png"})
        self.assertEqual(resolved, 1)
        self.assertEqual(self.translator.objDataDict[0]["photoURL"], "https://cms.thetriangle.org/x.png")

    def test_featured_image_beats_the_first_image_in_the_body(self):
        # The body scan takes whatever image comes first, which for ~2,200
        # articles is not the picture the live site shows.
        self._addArticle(0, 59172, photoURL="wp-content/uploads/2023/11/in-body.jpg")
        self.assertEqual(self.translator.resolveFeaturedImages({"59172": "https://cms.thetriangle.org/x.png"}), 1)
        self.assertEqual(self.translator.objDataDict[0]["photoURL"], "https://cms.thetriangle.org/x.png")

    def test_unset_or_dangling_thumbnail_keeps_the_body_image(self):
        # No featured image (or one whose attachment is gone from the export):
        # the body scan is all there is, and it must survive.
        self._addArticle(0, -1, photoURL="wp-content/uploads/2023/11/in-body.jpg")
        self._addArticle(1, 99999)
        self.assertEqual(self.translator.resolveFeaturedImages({"59172": "https://cms.thetriangle.org/x.png"}), 0)
        self.assertEqual(self.translator.objDataDict[0]["photoURL"], "wp-content/uploads/2023/11/in-body.jpg")
        self.assertIsNone(self.translator.objDataDict[1]["photoURL"])


class ExtractAndResolve(unittest.TestCase):
    """The regression end to end: the attachment <item> is streamed *after* the
    post that points at it, so the fix only works if resolution happens once the
    whole file has been read."""

    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()
        self.postsPath = Path(self.tempDir.name) / "wp-posts.xml"
        self.postsPath.write_text(WXR, encoding="utf-8")
        self.addCleanup(self.tempDir.cleanup)

    def _translate(self):
        articles = ArticleTranslator([])
        extractor = Extractor(str(self.postsPath), str(self.postsPath))
        attachmentURLs = extractor._translatePosts(str(self.postsPath), articles, AuthorTranslator([]))
        articles.resolveFeaturedImages(attachmentURLs)
        return {obj["slug"]: obj for obj in articles.getObjList()}

    def test_shortcode_only_post_gets_its_featured_image(self):
        article = self._translate()["heres-your-sudoku"]
        self.assertEqual(article["featuredImgID"], 59172)
        self.assertEqual(
            article["photoURL"],
            "https://cms.thetriangle.org/wp-content/uploads/2023/11/sudoku.png",
        )

    def test_featured_image_replaces_the_body_image(self):
        article = self._translate()["featured-image-wins"]
        self.assertEqual(
            article["photoURL"],
            "https://cms.thetriangle.org/wp-content/uploads/2023/11/sudoku.png",
        )

    def test_body_image_is_kept_when_no_featured_image_is_set(self):
        article = self._translate()["no-featured-image"]
        self.assertEqual(article["featuredImgID"], -1)
        self.assertEqual(article["photoURL"], "wp-content/uploads/2023/11/only-image.jpg")

    def test_attachments_are_not_translated_as_articles(self):
        self.assertEqual(
            sorted(self._translate()),
            ["featured-image-wins", "heres-your-sudoku", "no-featured-image"],
        )


class ExtractIntoMemoryAndTranslate(unittest.TestCase):
    """The same resolution down the *other* pipeline.

    `WP_FUSED_EXTRACT_TRANSLATE=0` extracts every <item> into a list first and
    translates it afterwards, so featured images resolve inside
    `ArticleTranslator.translate` rather than `Extractor._translatePosts`. That
    is a second implementation of the same behavior, and the two are only
    correct if they agree -- hence the comparison test at the end.
    """

    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()
        self.postsPath = Path(self.tempDir.name) / "wp-posts.xml"
        self.postsPath.write_text(WXR, encoding="utf-8")
        self.addCleanup(self.tempDir.cleanup)

    def _translateInMemory(self):
        extractor = Extractor(str(self.postsPath), str(self.postsPath))
        # _xml2Dict rather than getData: getData deletes the export directory
        # on its way out, which a test has no business doing.
        extractor._xml2Dict(str(self.postsPath), str(self.postsPath))
        articles = ArticleTranslator(extractor.data["art"])
        articles.translate()
        return {obj["slug"]: obj for obj in articles.getObjList()}

    def _translateStreaming(self):
        articles = ArticleTranslator([])
        extractor = Extractor(str(self.postsPath), str(self.postsPath))
        attachmentURLs = extractor._translatePosts(str(self.postsPath), articles, AuthorTranslator([]))
        articles.resolveFeaturedImages(attachmentURLs)
        return {obj["slug"]: obj for obj in articles.getObjList()}

    def test_shortcode_only_post_gets_its_featured_image(self):
        article = self._translateInMemory()["heres-your-sudoku"]
        self.assertEqual(article["featuredImgID"], 59172)
        self.assertEqual(
            article["photoURL"],
            "https://cms.thetriangle.org/wp-content/uploads/2023/11/sudoku.png",
        )

    def test_featured_image_replaces_the_body_image(self):
        article = self._translateInMemory()["featured-image-wins"]
        self.assertEqual(
            article["photoURL"],
            "https://cms.thetriangle.org/wp-content/uploads/2023/11/sudoku.png",
        )

    def test_body_image_is_kept_when_no_featured_image_is_set(self):
        article = self._translateInMemory()["no-featured-image"]
        self.assertEqual(article["featuredImgID"], -1)
        self.assertEqual(article["photoURL"], "wp-content/uploads/2023/11/only-image.jpg")

    def test_attachments_are_not_translated_as_articles(self):
        self.assertEqual(
            sorted(self._translateInMemory()),
            ["featured-image-wins", "heres-your-sudoku", "no-featured-image"],
        )

    def test_both_pipelines_agree(self):
        # The guard against the two paths drifting: whichever one a run picks,
        # every article must come out with the same image.
        inMemory = self._translateInMemory()
        streaming = self._translateStreaming()
        self.assertEqual(sorted(inMemory), sorted(streaming))
        self.assertEqual(
            {slug: obj["photoURL"] for slug, obj in inMemory.items()},
            {slug: obj["photoURL"] for slug, obj in streaming.items()},
        )
        self.assertEqual(
            {slug: obj["featuredImgID"] for slug, obj in inMemory.items()},
            {slug: obj["featuredImgID"] for slug, obj in streaming.items()},
        )


if __name__ == "__main__":
    unittest.main()
