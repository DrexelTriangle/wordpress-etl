from pathlib import Path
import json

from minhashlib import MinHash, MinHashLSH, similarity


class AuthorSimilarityIndex:
    """Precomputes a MinHash signature for every author in the lookup and indexes
    them in an LSH, built once and reused for all unknown names.

    Previously each unknown name constructed a fresh MinHash and compared itself
    against the entire lookup, recomputing both signatures on every comparison.
    This computes each author signature once and only scores the handful of
    candidates LSH surfaces, while preserving the exact match/flag thresholds and
    lookup-order tie-breaking of the original scan.
    """

    def __init__(self, lookup: dict, threshold: float = 0.7):
        self.lookup = lookup
        self.minhash = MinHash()
        self.keys = list(lookup.keys())
        self.signatures = {key: self.minhash.signature(key) for key in self.keys}
        self.lsh = MinHashLSH(threshold=threshold, num_perm=self.minhash.num_perm)
        for key in self.keys:
            self.lsh.insert(key, self.signatures[key])

    def match(self, clean_key: str):
        """Return ``(best, similar)`` for ``clean_key``.

        ``best`` is ``(author_id, display_name)`` for the highest-scoring candidate
        with similarity >= 0.9, else ``None``. ``similar`` is the list of
        ``(author_id, display_name, similarity)`` candidates in ``[0.8, 0.9)``,
        in lookup order.
        """
        signature = self.minhash.signature(clean_key)
        candidates = set(self.lsh.query(signature))
        best, best_sim, similar = None, 0.0, []
        for candidate_key in self.keys:
            if candidate_key not in candidates:
                continue
            sim = similarity(signature, self.signatures[candidate_key])
            aid, dname = self.lookup[candidate_key]
            if sim >= 0.9 and sim > best_sim:
                best, best_sim = (aid, dname), sim
            elif sim >= 0.8:
                similar.append((aid, dname, sim))
        return best, similar

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


def apply_similarity_match(clean_key, occurrences, index, log_change, author_matches, unknown_authors, flagged):
    if not index.lookup:
        for art_id, name in occurrences:
            unknown_authors.setdefault(name, []).append(art_id)
        return

    best, similar = index.match(clean_key)

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

