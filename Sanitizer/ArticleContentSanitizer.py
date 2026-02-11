import json
import re
from pathlib import Path
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.ArticlePolicy import ArticlePolicy
from Utils.WPContentSanitization import (
    sanitize_backslashes,
    fix_empty_alt,
    remove_dangerous_attrs,
    log_shortcodes,
    log_inline_styles,
    log_invisible_chars,
    write_detailed_logs
)


class ArticleContentSanitizer(Sanitizer):
    def __init__(self, data: list):
        super().__init__(data, policies=ArticlePolicy([]))
        self.shortcode_log = []
        self.inline_style_log = []
        self.invisible_chars_log = {}  # Changed to dict: char_type -> {unicodes: [...], occurrences: [...]}
    
    def _normalizeData(self):
        """Ensure all articles have required fields"""
        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if isinstance(article_data, dict):
                if 'text' not in article_data:
                    article_data['text'] = ""
    
    def _logChange(self, article_id, change_type, details):
        """Log content sanitization changes"""
        self.changes.append({
            "article_id": article_id,
            "change_type": change_type,
            "details": details
        })
    
    def _logConflict(self, article_id, issue_type, details):
        """Log issues that need manual review"""
        self.conflicts.append({
            "article_id": article_id,
            "issue_type": issue_type,
            "details": details
        })
        
    def sanitize(self):
        """Sanitize all article content"""
        self._normalizeData()
        
        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if not isinstance(article_data, dict):
                continue
            
            article_id = article_data.get("id", "unknown")
            original_text = article_data.get('text', '')
            
            if original_text:
                sanitized_text = self._sanitize_content(original_text, article_id)
                
                if sanitized_text != original_text:
                    article_data['text'] = sanitized_text
                    self._logChange(article_id, "content_sanitized", "Stripped backslashes and fixed HTML")
        
        self._write_detailed_logs()
        self._log("article-sanitizer/article_content_changes", "article-sanitizer/article_content_conflicts")
        return self.data
    
    def _sanitize_content(self, content: str, article_id: str) -> str:
        """Sanitize article text content"""
        if not content:
            return content
        
        # Strip excessive backslashes
        content = sanitize_backslashes(content)

        # Log issues
        self.shortcode_log.extend(log_shortcodes(content, article_id, self.policies.shortcode_pattern, self.policies.shortcode_example_length))
        self.inline_style_log.extend(log_inline_styles(content, article_id, self.policies.inline_style_pattern, self.policies.max_inline_style_samples))
        
        # Merge invisible chars log
        invisible_chars = log_invisible_chars(content, article_id, self.policies.invisible_char_patterns)
        for char_type, data in invisible_chars.items():
            if char_type not in self.invisible_chars_log:
                self.invisible_chars_log[char_type] = data
            else:
                self.invisible_chars_log[char_type]["unicodes"].update(data["unicodes"])
                self.invisible_chars_log[char_type]["occurrences"].extend(data["occurrences"])
        
        content = fix_empty_alt(content, self.policies.generate_alt_from_filename)
        content = remove_dangerous_attrs(content, self.policies.dangerous_patterns)
        
        return content
    
    def _write_detailed_logs(self):
        """Write all detailed logs to files"""
        write_detailed_logs(self.shortcode_log, self.inline_style_log, self.invisible_chars_log)
