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
        # Position of each key in lookup order, so candidates can be scored in
        # that order (preserving tie-breaking) without scanning every key.
        self._order = {key: i for i, key in enumerate(self.keys)}
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
        # LSH surfaces only the handful of likely-similar keys; scan just those,
        # in lookup order, instead of walking the entire lookup.
        candidates = sorted(self.lsh.query(signature), key=self._order.__getitem__)
        best, best_sim, similar = None, 0.0, []
        for candidate_key in candidates:
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


def build_special_edits_index(special_edits, lookup, clean_func) -> dict:
    """Resolve every special-edit entry to lookup authors once, up front.

    Returns ``{clean_key: [(author_id, display_name), ...]}``. Replaces the
    former per-name scan that re-cleaned all special_edits keys and the whole
    lookup on every call. Semantics are preserved exactly: for each entry the
    first special_edits key (in dict order) wins for a given cleaned key, and
    each name resolves to the first lookup author (in lookup order) whose
    display name matches exactly or after cleaning.
    """
    exact, cleaned = {}, {}
    for order, (_, (aid, dn)) in enumerate(lookup.items()):
        if not dn:
            continue
        exact.setdefault(dn, (order, (aid, dn)))
        cleaned.setdefault(clean_func(dn, "similarity"), (order, (aid, dn)))

    def resolve(name):
        matches = [m for m in (exact.get(name), cleaned.get(clean_func(name, "similarity"))) if m]
        return min(matches, key=lambda m: m[0])[1] if matches else None

    index, seen = {}, set()
    for key, value in special_edits.items():
        clean_key = clean_func(str(key), "similarity")
        if clean_key in seen:
            continue
        seen.add(clean_key)
        names = value if isinstance(value, list) else [value]
        authors = [a for a in (resolve(n) for n in names) if a]
        if authors:
            index[clean_key] = authors
    return index


def apply_special_edits(clean_key, occurrences, special_index, log_change, author_matches) -> bool:
    authors = special_index.get(clean_key)
    if not authors:
        return False

    for art_id, name in occurrences:
        author_matches.setdefault(art_id, {})[name] = authors if len(authors) > 1 else authors[0]
        log_name = ", ".join(n for _, n in authors) if len(authors) > 1 else authors[0][1]
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

