import json
import re
from pathlib import Path

_HAS_PARAGRAPHS_PATTERN = re.compile(r'(?is)<p\b')
_BLOCK_TAG_PATTERN = re.compile(
    r'(?is)^<(?:figure|figcaption|blockquote|ul|ol|li|h[1-6]|table|thead|tbody|tr|td|th|pre|code|hr|iframe|script|style)\b'
)
_COMMENT_PATTERN = re.compile(r'(?is)^<!--')
_CAPTION_SHORTCODE_PATTERN = re.compile(
    r'(?is)(?:<p>\s*)?\[caption(?P<attrs>[^\]]*)\](?P<body>.*?)\[/caption\](?:\s*</p>)?'
)
_PUZZLEME_SHORTCODE_PATTERN = re.compile(
    r'(?is)(?:<p>\s*)?(?:<strong>\s*)?\[puzzleme(?P<attrs>[^\]]*)\](?:\s*</strong>)?(?:\s*</p>)?'
)
_SHORTCODE_ATTR_PATTERN = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
_FIRST_IMAGE_PATTERN = re.compile(r'(?is)<img\b[^>]*>')
_SLUG_NON_ALNUM_PATTERN = re.compile(r'[^a-z0-9-]+')
_PARAGRAPH_SPLIT_PATTERN = re.compile(r'\n\s*\n+')
# Union of every problematic-character class, for a single cheap pre-scan before
# the per-type finditer work below.
_ANY_PROBLEMATIC_CHAR_PATTERN = re.compile(
    '[\u0000-\u0008\u000B\u000C\u000E-\u001F\u200B-\u200D\uFEFF]'
)


def sanitize_backslashes(content: str) -> str:
    # Strip excessive backlashes
    content = content.replace('\\"', '"')
    content = content.replace('\\\\', '\\')
    return content

def log_shortcodes(content: str, article_id: str, shortcode_pattern: re.Pattern) -> list:
    # Log WP shortcodes
    shortcode_log = []
    matches = shortcode_pattern.findall(content)
    
    if matches:
        unique_codes = set(matches)
        for code in unique_codes:
            example = re.search(rf'\[{code}[^\]]*\](?:.*?\[/{code}\])?', content)
            if example:
                shortcode_log.append({
                    "article_id": article_id,
                    "shortcode": code,
                    "example": example.group(0)
                })
    return shortcode_log


def log_inline_styles(content: str, article_id: str, inline_style_pattern: re.Pattern) -> list:
    inline_style_log = []
    matches = inline_style_pattern.findall(content)
    
    if matches:
        for style in matches:
            inline_style_log.append({
                "article_id": article_id,
                "style": style
            })
    
    return inline_style_log


def log_problematic_chars(content: str, article_id: str, problematic_char_patterns: list) -> dict:
    problematic_chars_log = {}

    # One cheap pass over the union class; the vast majority of articles have no
    # problematic characters, so skip the per-type finditer work entirely.
    if not _ANY_PROBLEMATIC_CHAR_PATTERN.search(content):
        return problematic_chars_log

    for pattern, char_type in problematic_char_patterns:
        matches = pattern.finditer(content)
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


def add_missing_paragraph_tags(content: str) -> str:
    # Keep already-paragraphized content untouched.
    if _HAS_PARAGRAPHS_PATTERN.search(content):
        return content

    normalized = content.replace('\r\n', '\n').replace('\r', '\n')
    chunks = _PARAGRAPH_SPLIT_PATTERN.split(normalized)
    rebuilt = []

    for chunk in chunks:
        block = chunk.strip()
        if not block:
            continue

        # Preserve existing block-level structures without wrapping.
        if _BLOCK_TAG_PATTERN.match(block) or _COMMENT_PATTERN.match(block):
            rebuilt.append(block)
            continue

        rebuilt.append(f"<p>{block}</p>")

    if not rebuilt:
        return content
    return "\n".join(rebuilt)


def convert_caption_shortcodes(content: str) -> str:
    # The pattern always requires the literal "[caption"; skip the DOTALL scan
    # entirely when it can't possibly match.
    if '[caption' not in content:
        return content

    def normalize_id(value: str) -> str:
        normalized = value.strip().lower().replace("_", "-")
        return _SLUG_NON_ALNUM_PATTERN.sub('-', normalized).strip("-")

    def build_figure(match: re.Match) -> str:
        attrs = dict(_SHORTCODE_ATTR_PATTERN.findall(match.group("attrs") or ""))
        body = (match.group("body") or "").strip()
        image_match = _FIRST_IMAGE_PATTERN.search(body)
        if not image_match:
            return match.group(0)

        image_html = image_match.group(0).strip()
        caption_html = body[image_match.end():].strip()

        raw_id = attrs.get("id", "").strip()
        normalized_id = normalize_id(raw_id) if raw_id else ""
        align = attrs.get("align", "").strip()
        width = attrs.get("width", "").strip()

        figure_attrs = []
        if raw_id:
            figure_attrs.append(f'id="{raw_id}"')
        if normalized_id:
            figure_attrs.append(f'aria-describedby="caption-{normalized_id}"')
        if width.isdigit():
            figure_attrs.append(f'style="width: {width}px"')

        classes = ["wp-caption"]
        if align:
            classes.append(align)
        figure_attrs.append(f'class="{" ".join(classes)}"')

        figcaption_html = ""
        if caption_html:
            figcaption_attrs = ['class="wp-caption-text"']
            if normalized_id:
                figcaption_attrs.insert(0, f'id="caption-{normalized_id}"')
            figcaption_html = f'<figcaption {" ".join(figcaption_attrs)}>{caption_html}</figcaption>'

        return f'<figure {" ".join(figure_attrs)}>{image_html}{figcaption_html}</figure>'

    return _CAPTION_SHORTCODE_PATTERN.sub(build_figure, content)


def convert_puzzleme_shortcodes(content: str) -> str:
    # The pattern always requires the literal "[puzzleme"; skip the DOTALL scan
    # entirely when it can't possibly match.
    if '[puzzleme' not in content.lower():
        return content

    puzzle_height_by_type = {
        "crossword": "700px",
        "wordsearch": "700px",
        "wordrow": "700px",
    }

    def build_embed(match: re.Match) -> str:
        attrs = dict(_SHORTCODE_ATTR_PATTERN.findall(match.group("attrs") or ""))
        embed_set = attrs.get("set", "").strip()
        embed_id = attrs.get("id", "").strip()
        puzzle_type = attrs.get("type", "").strip().lower()
        if not embed_set or not embed_id or not puzzle_type:
            return match.group(0)

        embed_height = puzzle_height_by_type.get(puzzle_type, "700px")
        return (
            f'<div class="pm-embed-div" '
            f'data-id="{embed_id}" data-set="{embed_set}" '
            f'data-puzzleType="{puzzle_type}" data-height="{embed_height}" '
            f'data-embedparams="embed=wp"></div>'
        )

    return _PUZZLEME_SHORTCODE_PATTERN.sub(build_embed, content)


def write_detailed_logs(shortcode_log: list, inline_style_log: list, problematic_chars_log: dict):
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
