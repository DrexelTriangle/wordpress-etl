import tempfile
import unittest
from pathlib import Path

from Utils.WPComments import load_wordpress_comments


WP_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss
  xmlns:wp="http://wordpress.org/export/1.2/"
>
  <channel>
    <item>
      <title>Sample Post</title>
      <wp:post_id>37853</wp:post_id>
      <wp:post_type><![CDATA[post]]></wp:post_type>
      <wp:comment>
        <wp:comment_id>1288</wp:comment_id>
        <wp:comment_author><![CDATA[James Russel]]></wp:comment_author>
        <wp:comment_author_email><![CDATA[james@example.com]]></wp:comment_author_email>
        <wp:comment_author_url></wp:comment_author_url>
        <wp:comment_author_IP><![CDATA[127.0.0.1]]></wp:comment_author_IP>
        <wp:comment_date><![CDATA[2016-12-26 15:29:00]]></wp:comment_date>
        <wp:comment_date_gmt><![CDATA[2016-12-26 20:29:00]]></wp:comment_date_gmt>
        <wp:comment_content><![CDATA[First comment]]></wp:comment_content>
        <wp:comment_approved><![CDATA[1]]></wp:comment_approved>
        <wp:comment_type><![CDATA[comment]]></wp:comment_type>
        <wp:comment_parent>0</wp:comment_parent>
        <wp:comment_user_id>0</wp:comment_user_id>
      </wp:comment>
      <wp:comment>
        <wp:comment_id>1289</wp:comment_id>
        <wp:comment_author><![CDATA[James Russel]]></wp:comment_author>
        <wp:comment_date><![CDATA[2016-12-26 15:29:00]]></wp:comment_date>
        <wp:comment_date_gmt><![CDATA[2016-12-26 20:29:00]]></wp:comment_date_gmt>
        <wp:comment_content><![CDATA[Reply]]></wp:comment_content>
        <wp:comment_approved><![CDATA[0]]></wp:comment_approved>
        <wp:comment_parent>1288</wp:comment_parent>
        <wp:comment_user_id>0</wp:comment_user_id>
      </wp:comment>
      <wp:comment>
        <wp:comment_id>1290</wp:comment_id>
        <wp:comment_author><![CDATA[Spam Bot]]></wp:comment_author>
        <wp:comment_date><![CDATA[2016-12-26 15:30:00]]></wp:comment_date>
        <wp:comment_date_gmt><![CDATA[2016-12-26 20:30:00]]></wp:comment_date_gmt>
        <wp:comment_content><![CDATA[Spam comment]]></wp:comment_content>
        <wp:comment_approved><![CDATA[spam]]></wp:comment_approved>
        <wp:comment_parent>0</wp:comment_parent>
        <wp:comment_user_id>0</wp:comment_user_id>
      </wp:comment>
    </item>
  </channel>
</rss>
"""


class WPCommentsTest(unittest.TestCase):
    def test_load_wordpress_comments_maps_article_and_parent_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            wp_path = Path(tmp) / "wp-posts.xml"
            wp_path.write_text(WP_XML, encoding="utf-8")

            comments = load_wordpress_comments(wp_path, [{"id": 5168, "wpPostID": 37853}])

        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0]["id"], 1288)
        self.assertEqual(comments[0]["articleID"], 5168)
        self.assertEqual(comments[0]["wpPostID"], 37853)
        self.assertEqual(comments[0]["status"], "approved")
        self.assertEqual(comments[0]["type"], "comment")
        self.assertEqual(comments[0]["authorUserID"], 0)
        self.assertEqual(comments[1]["parentID"], 1288)
        self.assertEqual(comments[1]["status"], "pending")
        self.assertNotIn(1290, [comment["id"] for comment in comments])


if __name__ == "__main__":
    unittest.main()
