from pathlib import Path
import json
import os

def collect_unique_author_names(data: list, clean_func) -> dict:
    unique = {}
    for article in data:
        article_data = article.data if hasattr(article, "data") else article
        if not isinstance(article_data, dict):
            continue
        for name in (article_data.get("authorCleanNames") or []):
            if not name:
                continue
            key = clean_func(str(name), "similarity")
            if key:
                unique.setdefault(key, []).append((article_data.get("id", "unknown"), name))
    return unique


def apply_special_edits(clean_key, occurrences, lookup, special_edits, clean_func, log_change, author_matches) -> bool:
    special = next(
        (v for k, v in special_edits.items() if clean_func(str(k), "similarity") == clean_key),
        None,
    )
    if not special:
        return False

    names = special if isinstance(special, list) else [special]
    authors = [
        next(
            ((aid, dn) for _, (aid, dn) in lookup.items()
             if dn and (dn == n or clean_func(dn, "similarity") == clean_func(n, "similarity"))),
            None,
        )
        for n in names
    ]
    authors = [a for a in authors if a]
    if not authors:
        return False

    for art_id, name in occurrences:
        author_matches.setdefault(art_id, {})[name] = authors if len(authors) > 1 else authors[0]
        log_name = ", ".join([n for _, n in authors]) if len(authors) > 1 else authors[0][1]
        log_change(art_id, name, log_name)
    return True


def apply_exact_match(clean_key, occurrences, lookup, author_matches) -> bool:
    if clean_key not in lookup:
        return False
    aid, dname = lookup[clean_key]
    for art_id, name in occurrences:
        author_matches.setdefault(art_id, {})[name] = (aid, dname)
    return True


def apply_similarity_match(clean_key, occurrences, lookup, diff_checker_cls, log_change, author_matches, unknown_authors, flagged):
    if not lookup:
        for art_id, name in occurrences:
            unknown_authors.setdefault(name, []).append(art_id)
        return

    candidates = list(lookup.items())
    checker = diff_checker_cls([clean_key] + [k for k, _ in candidates])
    best, best_sim, similar = None, 0.0, []

    for i, (_, (aid, dname)) in enumerate(candidates):
        sim = checker.compare(0, i + 1)
        if sim >= 0.9 and sim > best_sim:
            best, best_sim = (aid, dname), sim
        elif sim >= 0.8:
            similar.append((aid, dname, sim))

    if best:
        for art_id, name in occurrences:
            author_matches.setdefault(art_id, {})[name] = best
            log_change(art_id, name, best[1])
    elif similar:
        for art_id, name in occurrences:
            flagged.append({"article_id": art_id, "author_name": name, "candidates": similar})
    else:
        for art_id, name in occurrences:
            unknown_authors.setdefault(name, []).append(art_id)
            
            
def loadResolutionCache():
    # Cache previously resolved authors
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
    # TUI selection
    def readInput():
        try:
            if os.name == "nt":
                import msvcrt
                firstChar = msvcrt.getch()
                if firstChar in (b'\x00', b'\xe0'):
                    secondChar = msvcrt.getch()
                    mapping = {
                        b'H': 'UP',
                        b'P': 'DOWN',
                        b'K': 'LEFT',
                        b'M': 'RIGHT',
                    }
                    return mapping.get(secondChar, None)
                if firstChar == b'\r':
                    return 'ENTER'

                return firstChar.decode('utf-8')
                
            else:
                import sys
                import termios
                import tty
                """Get single character from stdin"""
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                    if ch == '\x1b':
                        sys.stdin.read(1)  # skip '['
                        direction = sys.stdin.read(1)

                        mapping = {
                            'A': 'UP',
                            'B': 'DOWN',
                            'C': 'RIGHT',
                            'D': 'LEFT'
                        }
                        return mapping.get(direction)
                    if ch == '\r':
                        return 'ENTER'

                    return ch
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
          pass
    
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
        key = readInput()
        if (key == 'UP'):
            ptr = max(0, ptr - 1)
        elif (key == 'DOWN'):
            ptr = min(len(options) - 1, ptr + 1)
        elif (key == 'ENTER'): 
            return ptr
        elif key in ('u', 'U'):
            return -1
