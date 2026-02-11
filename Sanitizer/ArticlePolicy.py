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
        
        # WordPress shortcode pattern
        self.shortcode_pattern = r'\[(\w+)(?:\s+[^\]]+)?\](?:.*?\[/\1\])?'
        
        # Inline style pattern
        self.inline_style_pattern = r'<[^>]+style=["\'](.*?)["\'][^>]*>'
        
        # Problematic character patterns to detect and log
        self.problematic_char_patterns = [
            (r'[\u0000-\u001F]', 'control character'),
            (r'[\u200B-\u200D\uFEFF]', 'zero-width character'),
            (r'\u00A0', 'non-breaking space'),
            (r'[^\x00-\x7F]', 'non_ascii'),
        ]
