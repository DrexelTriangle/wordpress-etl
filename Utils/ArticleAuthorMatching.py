from pathlib import Path
import json
import sys
import tty
import termios


def loadResolutionCache():
    """Load previously resolved author name mappings from cache file"""
    cache_path = Path("logs") / "article-sanitizer" / "article_author_resolution_cache.json"
    if not cache_path.exists():
        return {}
    
    try:
        with cache_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return payload.get("resolutions", {}) if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def saveResolutionCache(cache):
    """Save author name resolutions to cache file"""
    log_dir = Path("logs") / "article-sanitizer"
    log_dir.mkdir(parents=True, exist_ok=True)
    cache_path = log_dir / "article_author_resolution_cache.json"
    
    with cache_path.open("w", encoding="utf-8") as file:
        json.dump({"resolutions": cache}, file, indent=4)


def logUnknownAuthors(unknown_authors):
    """Write unknown authors to log file"""
    if not unknown_authors:
        return
    
    log_path = Path("logs") / "article-sanitizer" / "article_author_unknown.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Merge with existing
    existing = {}
    if log_path.exists():
        try:
            with log_path.open("r", encoding="utf-8") as f:
                existing = json.load(f).get("unknown_authors", {})
        except (OSError, json.JSONDecodeError):
            pass
    
    for name, ids in unknown_authors.items():
        existing[name] = sorted(set(existing.get(name, []) + ids))
    
    with log_path.open("w", encoding="utf-8") as f:
        json.dump({"unknown_authors": existing}, f, indent=4)


def selectFromList(prompt: str, options: list, format_option=None) -> int:
    """
    Interactive arrow key selection from a list.
    
    Args:
        prompt: Header text to display
        options: List of items to choose from
        format_option: Optional function to format each option (receives (index, item))
    
    Returns:
        Index of selected item, or -1 if user chose unknown ('u')
    """
    def getch():
        """Get single character from stdin"""
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    
    ptr = 0
    while True:
        # Clear and display
        print("\033[2J\033[H")  # Clear screen
        print(f"{prompt}\n")
        
        for i, option in enumerate(options):
            marker = "→" if i == ptr else " "
            if format_option:
                text = format_option(i, option)
            else:
                text = str(option)
            print(f"  {marker} {text}")
        
        print("\n↑↓ to navigate | Enter to select | 'u' for unknown")
        
        # Get input
        ch = getch()
        
        if ch == '\x1b':  # ESC sequence (arrow keys)
            getch()  # [
            direction = getch()
            if direction == 'A':  # Up
                ptr = max(0, ptr - 1)
            elif direction == 'B':  # Down
                ptr = min(len(options) - 1, ptr + 1)
        elif ch in ('\r', '\n'):  # Enter
            return ptr
        elif ch in ('u', 'U'):  # Unknown
            return -1
