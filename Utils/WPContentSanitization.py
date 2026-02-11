import json
import re
from pathlib import Path


def sanitize_backslashes(content: str) -> str:
    """Strip excessive backslashes (double-escaped quotes and backslashes)"""
    content = content.replace('\\"', '"')
    content = content.replace('\\\\', '\\')
    return content


def fix_empty_alt(content: str, generate_alt_from_filename: bool = True) -> str:
    """Fix empty alt attributes in img tags by generating from filename"""
    if not generate_alt_from_filename:
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


def remove_dangerous_attrs(content: str, dangerous_patterns: list) -> str:
    """Remove potentially dangerous HTML attributes and patterns"""
    for pattern, replacement in dangerous_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    return content


def log_shortcodes(content: str, article_id: str, shortcode_pattern: str, shortcode_example_length: int = 100) -> list:
    """Detect and log WordPress shortcodes"""
    shortcode_log = []
    matches = re.findall(shortcode_pattern, content)
    
    if matches:
        unique_codes = set(matches)
        for code in unique_codes:
            example = re.search(rf'\[{code}[^\]]*\](?:.*?\[/{code}\])?', content)
            if example:
                shortcode_log.append({
                    "article_id": article_id,
                    "shortcode": code,
                    "example": example.group(0)[:shortcode_example_length]
                })
    
    return shortcode_log


def log_inline_styles(content: str, article_id: str, inline_style_pattern: str, max_samples: int = 5) -> list:
    """Detect and log inline CSS styles"""
    inline_style_log = []
    matches = re.findall(inline_style_pattern, content)
    
    if matches:
        for style in matches[:max_samples]:
            inline_style_log.append({
                "article_id": article_id,
                "style": style[:100]
            })
    
    return inline_style_log


def log_problematic_chars(content: str, article_id: str, problematic_char_patterns: list) -> dict:
    """Log invisible and problematic Unicode characters grouped by type"""
    problematic_chars_log = {}
    
    for pattern, char_type in problematic_char_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            unicode_code = f"U+{ord(match.group(0)):04X}"
            
            # Initialize char_type entry if not exists
            if char_type not in problematic_chars_log:
                problematic_chars_log[char_type] = {
                    "unicodes": set(),
                    "occurrences": []
                }
            
            # Add unicode to set (for unique list)
            problematic_chars_log[char_type]["unicodes"].add(unicode_code)
            
            # Add occurrence
            problematic_chars_log[char_type]["occurrences"].append({
                "article_id": article_id,
                "position": match.start()
            })
    
    return problematic_chars_log


def replace_problematic_chars(content: str, problematic_char_patterns: list) -> str:
    """Replace problematic Unicode characters with their Unicode escape representation"""
    for pattern, _ in problematic_char_patterns:
        def replace_func(match):
            char = match.group(0)
            unicode_repr = f"[U+{ord(char):04X}]"
            return unicode_repr
        content = re.sub(pattern, replace_func, content)
    return content


def write_detailed_logs(shortcode_log: list, inline_style_log: list, problematic_chars_log: dict):
    """Write all detailed content sanitization logs to files"""
    log_dir = Path("logs") / "article-sanitizer"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # WordPress shortcodes log
    if shortcode_log:
        with open(log_dir / "article_wp_shortcodes.json", 'w') as f:
            json.dump({"shortcodes": shortcode_log}, f, indent=4)
        print(f"Logged {len(shortcode_log)} WordPress shortcodes")
    
    # Inline styles log
    if inline_style_log:
        with open(log_dir / "article_inline_styles.json", 'w') as f:
            json.dump({"inline_styles": inline_style_log}, f, indent=4)
        print(f"Logged {len(inline_style_log)} inline styles")
    
    # Problematic characters log
    if problematic_chars_log:
        # Convert sets to lists for JSON serialization
        serializable = {
            char_type: {
                "unicodes": sorted(list(data["unicodes"])),
                "occurrences": data["occurrences"]
            }
            for char_type, data in problematic_chars_log.items()
        }
        with open(log_dir / "article_problematic_chars.json", 'w') as f:
            json.dump({"problematic_chars": serializable}, f, indent=4)
        total_occurrences = sum(len(data["occurrences"]) for data in problematic_chars_log.values())
        print(f"Logged {total_occurrences} problematic characters across {len(problematic_chars_log)} types")
