from Utils.Utility import Utility
from Utils.ArticleAuthorMatching import (
    AuthorSimilarityIndex,
    loadResolutionCache,
    saveResolutionCache,
    logUnknownAuthors,
    collect_unique_author_names,
    build_special_edits_index,
    apply_special_edits,
    apply_exact_match,
    apply_similarity_match,
)
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.ArticleAuthorMatchingPolicy import ArticleAuthorMatchingPolicy


class ArticleAuthorMatcher(Sanitizer):
    def __init__(self, data: list, authors: list, best_guess: bool = False):
        super().__init__(data, policies=ArticleAuthorMatchingPolicy([], authors))
        self.unknown_authors = {}
        self.author_matches = {}
        self.resolution_cache = loadResolutionCache()
        self.best_guess = best_guess
        self._on_progress = None
    
    def _normalizeData(self):
        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if isinstance(article_data, dict) and "authorCleanNames" not in article_data:
                article_data["authorCleanNames"] = []
    
    def _logChange(self, article_id, old_name, new_name):
        self.changes.append({"article_id": article_id, "old_author": old_name, "new_author": new_name})
    
    def _logConflict(self, article_id, author_name, candidates):
        self.conflicts.append({"article_id": article_id, "author_name": author_name, "candidates": candidates})
    
    def sanitize(self, select_author=None, clear: bool = True):
        self._normalizeData()
        self._matchArticleAuthors(select_author)
        logUnknownAuthors(self.unknown_authors)
        self._log("article-sanitizer/article_author_mappings", "article-sanitizer/article_author_conflicts")
        return self.data

    def _matchArticleAuthors(self, select_author=None):
        def progress(message):
            if self._on_progress:
                self._on_progress(message)

        lookup = self.policies._author_lookup
        progress("collecting unique author names")
        unique = collect_unique_author_names(self.data, Utility.cleanDocument)
        flagged = []

        progress("indexing authors")
        index = AuthorSimilarityIndex(lookup)
        special_index = build_special_edits_index(self.policies.specialEdits, lookup, Utility.cleanDocument)

        progress("matching authors")
        for clean_key, occurrences in unique.items():
            if apply_special_edits(clean_key, occurrences, special_index, self._logChange, self.author_matches):
                continue
            if apply_exact_match(clean_key, occurrences, lookup, self.author_matches):
                continue
            apply_similarity_match(clean_key, occurrences, index, self._logChange, self.author_matches, self.unknown_authors, flagged)

        if flagged:
            self._manualResolve(flagged, select_author)
            saveResolutionCache(self.resolution_cache)

        self._applyMatches()

    def _resolveCachedMatch(self, name):
        """A cached decision, re-resolved against the CURRENT export's authors.

        The cache stores (author_id, display_name), but WordPress renumbers
        authors between exports, so the stored id routinely belongs to somebody
        else next time. Ava Buckingham was 554 and is now 553 (that id no longer
        exists, so her articles lost their author); Mary Elizabeth Hoffman was
        338, and 338 is now Snehal Yarlagadda -- silently crediting her articles
        to a different person, which no integrity check catches because the row
        does exist.

        The cached decision means "this byline is that PERSON", so the name is
        what carries over and the id is looked up fresh. If the person is not in
        this export at all, returns None so the caller falls through to normal
        resolution rather than trusting a dead id.
        """
        entry = self.resolution_cache.get(name)
        if not entry:
            return None
        try:
            _, cachedName = entry
        except (TypeError, ValueError):
            return None
        if not cachedName:
            return None

        key = Utility.cleanDocument(cachedName, "similarity")
        current = self.policies._author_lookup.get(key) if key else None
        if current is None:
            return None
        return current

    def _manualResolve(self, flagged: list, select_author=None):
        for i, item in enumerate(flagged):
            aid, name, cands = item["article_id"], item["author_name"], item["candidates"]

            cached = self._resolveCachedMatch(name)
            if cached is not None:
                author_id, dname = cached
                # Refresh so the cache heals itself instead of carrying a stale
                # id forward into every future run.
                self.resolution_cache[name] = (author_id, dname)
                self.author_matches.setdefault(aid, {})[name] = (author_id, dname)
                self._logChange(aid, name, dname)
                continue

            if self.best_guess:
                # Unattended runs -- rebuilding the seed for a migration test --
                # must not stop on a prompt, and must reach the same answer every
                # time. Highest similarity wins. The choice still lands in the
                # resolution cache, so a later interactive run can correct it.
                choice = max(range(len(cands)), key=lambda index: cands[index][2]) if cands else -1
            else:
                prompt = f"Article {aid}: '{name}' ({i + 1}/{len(flagged)})"
                choice = select_author(prompt, cands, lambda i, c: f"{c[1]} ({c[2]:.0%})") if select_author else -1

            if choice == -1:
                self.unknown_authors.setdefault(name, []).append(aid)
            else:
                author_id, dname, sim = cands[choice]
                self.resolution_cache[name] = (author_id, dname)
                self.author_matches.setdefault(aid, {})[name] = (author_id, dname)
                self._logChange(aid, name, dname)
                self._logConflict(aid, name, cands)
    
    def _applyMatches(self):
        # Apply matched authors to articles
        for article in self.data:
            data = article.data if hasattr(article, "data") else article
            if not isinstance(data, dict):
                continue
            
            matches = self.author_matches.get(data.get("id", "unknown"), {})
            ids, names = [], []
            # A byline that names the same person twice must still produce one
            # link: articles_authors has no unique constraint, so a repeat wrote
            # a duplicate row and the byline rendered the name twice.
            seen = set()

            for name in (data.get("authorCleanNames") or []):
                if name in matches:
                    match = matches[name]
                    entries = match if isinstance(match, list) else [match]
                    for aid, dname in entries:
                        if aid in seen:
                            continue
                        seen.add(aid)
                        ids.append(aid)
                        names.append(dname)

            data["authorIDs"] = ids
            data["authors"] = names
