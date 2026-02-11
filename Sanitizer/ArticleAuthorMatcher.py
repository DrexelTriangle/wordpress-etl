from Utils import NLP as nlp
from Utils.ArticleAuthorMatching import selectFromList, loadResolutionCache, saveResolutionCache, logUnknownAuthors
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.ArticleAuthorMatchingPolicy import ArticleAuthorMatchingPolicy
from Sanitizer.DiffChecker import DiffChecker


class ArticleAuthorMatcher(Sanitizer):
    def __init__(self, data: list, authors: list, guest_authors: list):
        super().__init__(data, policies=ArticleAuthorMatchingPolicy([], authors, guest_authors))
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
        """Match article authors: special edits → exact → similarity (0.9 auto, 0.8 manual)"""
        clean = nlp.cleanDocument
        lookup = self.policies._author_lookup
        
        # Collect unique names
        unique = {}
        for article in self.data:
            data = article.data if hasattr(article, "data") else article
            if not isinstance(data, dict):
                continue
            for name in (data.get("authorCleanNames") or []):
                if name:
                    key = clean(str(name), "similarity")
                    if key:
                        unique.setdefault(key, []).append((data.get("id", "unknown"), name))
        
        # Match each unique name
        flagged = []
        for clean_key, occurrences in unique.items():
            # Special edits
            special = next((v for k, v in self.policies.specialEdits.items() 
                          if clean(str(k), "similarity") == clean_key), None)
            if special:
                names = special if isinstance(special, list) else [special]
                authors = [next(((aid, dn) for _, (aid, dn) in lookup.items() 
                               if dn and (dn == n or clean(dn, "similarity") == clean(n, "similarity"))), None) 
                          for n in names]
                authors = [a for a in authors if a]
                if authors:
                    for aid, name in occurrences:
                        self.author_matches.setdefault(aid, {})[name] = authors if len(authors) > 1 else authors[0]
                        log_name = ", ".join([n for _, n in authors]) if len(authors) > 1 else authors[0][1]
                        self._logChange(aid, name, log_name)
                    continue
            
            # Exact match
            if clean_key in lookup:
                aid, dname = lookup[clean_key]
                for art_id, name in occurrences:
                    self.author_matches.setdefault(art_id, {})[name] = (aid, dname)
                continue
            
            # Similarity
            if not lookup:
                for art_id, name in occurrences:
                    self.unknown_authors.setdefault(name, []).append(art_id)
                continue
            
            candidates = list(lookup.items())
            checker = DiffChecker([clean_key] + [k for k, _ in candidates])
            best, best_sim, similar = None, 0.0, []
            
            for i, (_, (aid, dname)) in enumerate(candidates):
                sim = checker.compare(0, i + 1)
                if sim >= 0.9 and sim > best_sim:
                    best, best_sim = (aid, dname), sim
                elif sim >= 0.8:
                    similar.append((aid, dname, sim))
            
            if best:
                for art_id, name in occurrences:
                    self.author_matches.setdefault(art_id, {})[name] = best
                    self._logChange(art_id, name, best[1])
            elif similar:
                for art_id, name in occurrences:
                    flagged.append({"article_id": art_id, "author_name": name, "candidates": similar})
            else:
                for art_id, name in occurrences:
                    self.unknown_authors.setdefault(name, []).append(art_id)
        
        # Manual resolution
        if flagged:
            manualStart and manualStart()
            self._manualResolve(flagged)
            saveResolutionCache(self.resolution_cache)
            manualEnd and manualEnd()
        
        self._applyMatches()
    
    
    def _manualResolve(self, flagged: list):
        """Manual resolution for 0.8-0.9 similarity matches"""
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
        """Apply matched authors to articles"""
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