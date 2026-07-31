import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.MediaInventory import (
    collect_media_references,
    iter_media_attachments,
    reconcile_media,
    write_media_reports,
)


EXPORT_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss
  xmlns:wp="http://wordpress.org/export/1.2/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
>
  <channel>
    <item>
      <title>Sample Post</title>
      <content:encoded><![CDATA[<img src="https://www.thetriangle.org/wp-content/uploads/2020/01/a-300x200.jpg">]]></content:encoded>
      <wp:post_id>10</wp:post_id>
      <wp:post_type><![CDATA[post]]></wp:post_type>
    </item>
    <item>
      <title><![CDATA[Main image]]></title>
      <guid isPermaLink="false">https://www.thetriangle.org/wp-content/uploads/2020/01/a.jpg</guid>
      <excerpt:encoded><![CDATA[Caption text]]></excerpt:encoded>
      <wp:post_id>55</wp:post_id>
      <wp:post_parent>10</wp:post_parent>
      <wp:post_name><![CDATA[main-image]]></wp:post_name>
      <wp:post_date_gmt><![CDATA[2020-01-02 03:04:05]]></wp:post_date_gmt>
      <wp:post_type><![CDATA[attachment]]></wp:post_type>
      <wp:attachment_url><![CDATA[https://www.thetriangle.org/wp-content/uploads/2020/01/a.jpg]]></wp:attachment_url>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_attached_file]]></wp:meta_key>
        <wp:meta_value><![CDATA[2020/01/a.jpg]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_attachment_metadata]]></wp:meta_key>
        <wp:meta_value><![CDATA[a:2:{s:4:"file";s:13:"2020/01/a.jpg";s:5:"sizes";a:1:{s:6:"medium";a:1:{s:4:"file";s:14:"a-300x200.jpg";}}}]]></wp:meta_value>
      </wp:postmeta>
    </item>
  </channel>
</rss>
"""


class MediaInventoryTest(unittest.TestCase):
    def test_parse_attachment_and_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wp-posts.xml"
            path.write_text(EXPORT_XML, encoding="utf-8")

            attachments = list(iter_media_attachments(path))

        self.assertEqual(len(attachments), 1)
        attachment = attachments[0]
        self.assertEqual(attachment.attachment_id, "55")
        self.assertEqual(attachment.parent_id, "10")
        self.assertEqual(attachment.primary_path, "wp-content/uploads/2020/01/a.jpg")
        self.assertIn("wp-content/uploads/2020/01/a-300x200.jpg", attachment.file_paths)

    def test_collect_references_and_reconcile(self):
        articles = [
            {
                "id": 10,
                "slug": "sample-post",
                "text": '<img src="/wp-content/uploads/2020/01/a-300x200.jpg"><img src="wp-content/uploads/2020/01/missing.jpg">',
                "photoURL": "https://www.thetriangle.org/wp-content/uploads/2020/01/a.jpg",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wp-posts.xml"
            path.write_text(EXPORT_XML, encoding="utf-8")
            attachments = list(iter_media_attachments(path))

        references = collect_media_references(articles)
        rows = reconcile_media(attachments, references)
        status_by_path = {row["destination_path"]: row["status"] for row in rows}

        self.assertEqual(status_by_path["wp-content/uploads/2020/01/a.jpg"], "referenced_with_attachment")
        self.assertEqual(status_by_path["wp-content/uploads/2020/01/a-300x200.jpg"], "referenced_with_attachment")
        self.assertEqual(status_by_path["wp-content/uploads/2020/01/missing.jpg"], "referenced_missing_attachment")

    def test_write_media_reports(self):
        articles = [{"id": 10, "slug": "sample-post", "text": '<img src="/wp-content/uploads/2020/01/a.jpg">'}]
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "wp-posts.xml"
            output_dir = Path(tmp) / "media"
            xml_path.write_text(EXPORT_XML, encoding="utf-8")

            summary = write_media_reports(articles, output_dir=output_dir, posts_source=xml_path)

            self.assertEqual(summary["attachments"], 1)
            self.assertTrue((output_dir / "attachments.csv").exists())
            self.assertTrue((output_dir / "referenced_media.csv").exists())
            self.assertTrue((output_dir / "reconciliation.csv").exists())
            self.assertTrue((output_dir / "copy_manifest.csv").exists())
            self.assertTrue((output_dir / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()
