from Utils import NLP as nlp
from Utils.ArticleAuthorMatching import (
    selectFromList,
    loadResolutionCache,
    saveResolutionCache,
    logUnknownAuthors,
    collect_unique_author_names,
    apply_special_edits,
    apply_exact_match,
    apply_similarity_match,
)
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.ArticleAuthorMatchingPolicy import ArticleAuthorMatchingPolicy
from Sanitizer.DiffChecker import DiffChecker


class ArticleAuthorMatcher(Sanitizer):
    def __init__(self, data: list, authors: list):
        super().__init__(data, policies=ArticleAuthorMatchingPolicy([], authors))
        self.unknown_authors = {}
        self.author_matches = {}
        self.resolution_cache = loadResolutionCache()
    
    def _normalizeData(self):
        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if isinstance(article_data, dict) and "authorCleanNames" not in article_data:
                article_data["authorCleanNames"] = []
    
    def _logChange(self, article_id, old_name, new_name):
        self.changes.append({"article_id": article_id, "old_author": old_name, "new_author": new_name})
    
    def _logConflict(self, article_id, author_name, candidates):
        self.conflicts.append({"article_id": article_id, "author_name": author_name, "candidates": candidates})
    
    def sanitize(self, manualStart=None, manualEnd=None, clear: bool = True):
        self._normalizeData()
        self._matchArticleAuthors(manualStart, manualEnd, clear)
        logUnknownAuthors(self.unknown_authors)
        self._log("article-sanitizer/article_author_mappings", "article-sanitizer/article_author_conflicts")
        return self.data

    def _matchArticleAuthors(self, manualStart=None, manualEnd=None, clear: bool = True):
        lookup = self.policies._author_lookup
        unique = collect_unique_author_names(self.data, nlp.cleanDocument)
        flagged = []

        for clean_key, occurrences in unique.items():
            if apply_special_edits(clean_key, occurrences, lookup, self.policies.specialEdits, nlp.cleanDocument, self._logChange, self.author_matches):
                continue
            if apply_exact_match(clean_key, occurrences, lookup, self.author_matches):
                continue
            apply_similarity_match(clean_key, occurrences, lookup, DiffChecker, self._logChange, self.author_matches, self.unknown_authors, flagged)

        if flagged:
            manualStart and manualStart()
            self._manualResolve(flagged)
            saveResolutionCache(self.resolution_cache)
            manualEnd and manualEnd()

        self._applyMatches()
    
    
    def _manualResolve(self, flagged: list):
        for i, item in enumerate(flagged):
            aid, name, cands = item["article_id"], item["author_name"], item["candidates"]
            
            # Check cache
            if name in self.resolution_cache:
                author_id, dname = self.resolution_cache[name]
                self.author_matches.setdefault(aid, {})[name] = (author_id, dname)
                self._logChange(aid, name, dname)
                print(f"Cached: '{name}' → '{dname}' (Article {aid})")
                continue
            
            # Interactive selection
            prompt = f"Article {aid}: '{name}' ({i+1}/{len(flagged)})"
            choice = selectFromList(prompt, cands, lambda i, c: f"{c[1]} ({c[2]:.0%})")
            
            if choice == -1:  # Unknown
                self.unknown_authors.setdefault(name, []).append(aid)
                print("  → Unknown")
            else:
                author_id, dname, sim = cands[choice]
                self.resolution_cache[name] = (author_id, dname)
                self.author_matches.setdefault(aid, {})[name] = (author_id, dname)
                self._logChange(aid, name, dname)
                self._logConflict(aid, name, cands)
                print(f"  → {dname}")
    
    def _applyMatches(self):
        # Apply matched authors to articles
        for article in self.data:
            data = article.data if hasattr(article, "data") else article
            if not isinstance(data, dict):
                continue
            
            matches = self.author_matches.get(data.get("id", "unknown"), {})
            ids, names = [], []
            
            for name in (data.get("authorCleanNames") or []):
                if name in matches:
                    match = matches[name]
                    entries = match if isinstance(match, list) else [match]
                    for aid, dname in entries:
                        ids.append(aid)
                        names.append(dname)
            
            data["authorIDs"] = ids
            data["authors"] = names