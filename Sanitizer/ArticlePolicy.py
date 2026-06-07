import re

from Sanitizer.Policy import Policy

class ArticlePolicy(Policy):
    def __init__(self, data):
        # ArticlePolicy doesn't use Policy's author-specific fields
        super().__init__(
            specialEdits={},
            specialFlags={},
            banList=[],
            data=data,
            isAuthor=False
        )

        # Patterns are precompiled once here rather than recompiled per article.
        # WordPress shortcode pattern
        self.shortcode_pattern = re.compile(r'\[(\w+)(?:\s+[^\]]+)?\](?:.*?\[/\1\])?')

        # Inline style pattern
        self.inline_style_pattern = re.compile(r'<[^>]+style=["\'](.*?)["\'][^>]*>')

        # Problematic character patterns to detect and log
        self.problematic_char_patterns = [
            (re.compile(r'[\u0000-\u0008\u000B\u000C\u000E-\u001F]'), 'control character'),
            (re.compile(r'[\u200B-\u200D\uFEFF]'), 'zero-width character'),
        ]
