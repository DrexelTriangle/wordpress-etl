import unittest

from Formatter.CommentFormatter import CommentFormatter


class CommentFormatterTest(unittest.TestCase):
    def test_format_emits_cms_comments_schema(self):
        commands = CommentFormatter(
            [
                {
                    "id": 1,
                    "articleID": 10,
                    "wpPostID": 100,
                    "parentID": 0,
                    "authorName": "Author",
                    "authorEmail": "author@example.com",
                    "authorURL": None,
                    "authorIP": "127.0.0.1",
                    "authorUserID": 0,
                    "content": "Comment",
                    "createdAt": "2026-07-30 12:00:00",
                    "createdAtGMT": "2026-07-30 16:00:00",
                    "status": "approved",
                    "type": "comment",
                }
            ]
        ).format("comments")

        self.assertIn("`id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY", commands[0])
        self.assertIn(
            "INDEX idx_comments_article_status_created (article_id, status, created_at_gmt)",
            commands[0],
        )
        self.assertIn("INDEX idx_comments_wp_post_id (wp_post_id)", commands[0])
        self.assertIn("INDEX idx_comments_parent_id (parent_id)", commands[0])


if __name__ == "__main__":
    unittest.main()
