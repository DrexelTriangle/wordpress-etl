from Sanitizer.Policy import Policy


class ArticlePolicy(Policy):
    def __init__(self, data):
        """
        Policy for article content sanitization.
        Defines patterns and rules for cleaning HTML content.
        """
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
            (r'[\u0000-\u001F]', 'control character'),  # Control chars
            (r'[\u200B-\u200D]', 'zero-width character'),  # Zero-width
            (r'\u202E', 'right-to-left override'),
            (r'\u00A0', 'non-breaking space'),
            (r'[\uFEFF]', 'zero-width no-break space'),
            (r'[^\x00-\x7F]', 'non_ascii'),  # All non-ASCII characters
        ]
        
        # Configuration
        self.max_inline_style_samples = 5  # Max samples to log per article
        self.shortcode_example_length = 100  # Max chars for example
        self.generate_alt_from_filename = True  # Auto-generate alt text from filenames
