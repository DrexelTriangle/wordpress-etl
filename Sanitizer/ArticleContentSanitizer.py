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
    
    def _log_shortcodes(self, content: str, article_id: str):
        """Detect and log WordPress shortcodes"""
        matches = re.findall(self.policies.shortcode_pattern, content)
        
        if matches:
            unique_codes = set(matches)
            for code in unique_codes:
                example = re.search(rf'\[{code}[^\]]*\](?:.*?\[/{code}\])?', content)
                if example:
                    self.shortcode_log.append({
                        "article_id": article_id,
                        "shortcode": code,
                        "example": example.group(0)[:self.policies.shortcode_example_length]
                    })
    
    def _log_inline_styles(self, content: str, article_id: str):
        """Detect and log inline styles"""
        matches = re.findall(self.policies.inline_style_pattern, content)
        
        if matches:
            for style in matches[:self.policies.max_inline_style_samples]:
                self.inline_style_log.append({
                    "article_id": article_id,
                    "style": style[:100]
                })
    
    def _log_invisible_chars(self, content: str, article_id: str):
        """Log invisible and problematic Unicode characters grouped by type"""
        for pattern, char_type in self.policies.invisible_char_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                unicode_code = f"U+{ord(match.group(0)):04X}"
                
                # Initialize char_type entry if not exists
                if char_type not in self.invisible_chars_log:
                    self.invisible_chars_log[char_type] = {
                        "unicodes": set(),
                        "occurrences": []
                    }
                
                # Add unicode to set (for unique list)
                self.invisible_chars_log[char_type]["unicodes"].add(unicode_code)
                
                # Add occurrence
                self.invisible_chars_log[char_type]["occurrences"].append({
                    "article_id": article_id,
                    "position": match.start()
                })
    
    def _fix_empty_alt(self, content: str) -> str:
        """Fix empty alt attributes in img tags"""
        if not self.policies.generate_alt_from_filename:
            return content
            
        def replace_alt(match):
            img_tag = match.group(0)
            if 'alt=""' in img_tag or 'alt=\'\'' in img_tag:
                src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
                if src_match:
                    filename = Path(src_match.group(1)).stem
                    alt_text = filename.replace('-', ' ').replace('_', ' ')
                    img_tag = re.sub(r'alt=["\']["\']', f'alt="{alt_text}"', img_tag)
            return img_tag
        
        return re.sub(r'<img[^>]*>', replace_alt, content)
    
    def _remove_dangerous_attrs(self, content: str) -> str:
        """Remove potentially dangerous HTML attributes"""
        for pattern, replacement in self.policies.dangerous_patterns:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        return content
    
    def _write_detailed_logs(self):
        """Write all detailed logs to files"""
        log_dir = Path("logs") / "article-sanitizer"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # WordPress shortcodes log
        if self.shortcode_log:
            with open(log_dir / "article_wp_shortcodes.json", 'w') as f:
                json.dump({"shortcodes": self.shortcode_log}, f, indent=4)
            print(f"Logged {len(self.shortcode_log)} WordPress shortcodes")
        
        # Inline styles log
        if self.inline_style_log:
            with open(log_dir / "article_inline_styles.json", 'w') as f:
                json.dump({"inline_styles": self.inline_style_log}, f, indent=4)
            print(f"Logged {len(self.inline_style_log)} inline styles")
        
        # Invisible characters log
        if self.invisible_chars_log:
            # Convert sets to lists for JSON serialization
            serializable = {
                char_type: {
                    "unicodes": sorted(list(data["unicodes"])),
                    "occurrences": data["occurrences"]
                }
                for char_type, data in self.invisible_chars_log.items()
            }
            with open(log_dir / "article_invisible_chars.json", 'w') as f:
                json.dump({"invisible_chars": serializable}, f, indent=4)
            total_occurrences = sum(len(data["occurrences"]) for data in self.invisible_chars_log.values())
            print(f"Logged {total_occurrences} invisible characters across {len(self.invisible_chars_log)} types")
