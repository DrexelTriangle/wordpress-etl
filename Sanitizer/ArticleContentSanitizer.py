from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.ArticlePolicy import ArticlePolicy
from Utils.WPContentSanitization import (
    sanitize_backslashes,
    log_shortcodes,
    log_inline_styles,
    log_problematic_chars,
    replace_problematic_chars,
    write_detailed_logs
)

class ArticleContentSanitizer(Sanitizer):
    def __init__(self, data: list):
        super().__init__(data, policies=ArticlePolicy([]))
        self.shortcode_log = []
        self.inline_style_log = []
        self.problematic_chars_log = {}
    
    def _logChange(self, article_id, change_type, details):
        self.changes.append({
            "article_id": article_id,
            "change_type": change_type,
            "details": details
        })
    
    def _logConflict(self, article_id, issue_type, details):
        self.conflicts.append({
            "article_id": article_id,
            "issue_type": issue_type,
            "details": details
        })
    
    def _normalizeData(self):
        """Ensure all articles end with punctuation"""
        for article in self.data:
            if 'text' not in article:
                article['text'] = ""
            
            text = article.get('text', '')
            if text and not text.endswith(('.', '!', '?', ':', ';', '"', "'")):
                article['text'] = text + "."
        
    def sanitize(self):
        self._normalizeData()
        
        for article in self.data:
            article_id = article.get("id", "unknown")
            original_text = article.get('text', '')
            if not original_text:
                continue
            fixes = []
            sanitized_text = original_text
            
            # Strip excessive backslashes
            sanitized_text = sanitize_backslashes(sanitized_text)
            if sanitized_text != original_text:
                fixes.append("backslashes stripped")
            
            # Log and replace problematic chars
            problematic_chars = log_problematic_chars(sanitized_text, article_id, self.policies.problematic_char_patterns)
            for char_type, data in problematic_chars.items():
                if char_type not in self.problematic_chars_log:
                    self.problematic_chars_log[char_type] = data
                else:
                    self.problematic_chars_log[char_type]["unicodes"].update(data["unicodes"])
                    self.problematic_chars_log[char_type]["occurrences"].extend(data["occurrences"])
            
            sanitized_text_before_replace = sanitized_text
            sanitized_text = replace_problematic_chars(sanitized_text, self.policies.problematic_char_patterns)
            if sanitized_text != sanitized_text_before_replace:
                fixes.append("problematic characters replaced")
            
            # Log other issues
            self.shortcode_log.extend(log_shortcodes(sanitized_text, article_id, self.policies.shortcode_pattern, self.policies.shortcode_example_length))
            self.inline_style_log.extend(log_inline_styles(sanitized_text, article_id, self.policies.inline_style_pattern, self.policies.max_inline_style_samples))
            
            # Update article and log if anything changed
            if sanitized_text != original_text:
                article['text'] = sanitized_text
                self._logChange(article_id, "content_sanitized", "; ".join(fixes))
        
        self._write_detailed_logs()
        self._log("article-sanitizer/article_content_changes", "article-sanitizer/article_content_conflicts")
        return self.data
    
    def _write_detailed_logs(self):
        write_detailed_logs(self.shortcode_log, self.inline_style_log, self.problematic_chars_log)
