from Utils import NLP as nlp
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.ArticlePolicy import ArticlePolicy
from Sanitizer.DiffChecker import DiffChecker


class ArticleSanitizer(Sanitizer):
    def __init__(self, data: list, authors: list, guest_authors: list):
        policy = ArticlePolicy([], authors, guest_authors)
        super().__init__(data, policies=policy)
        self.unknown_authors = {}  # Changed to dict: author_name -> [article_ids]
        self.author_matches = {}  # Cache for matched authors per article
        self.resolution_cache = self._loadResolutionCache()  # Load previous resolutions
  
    # Implementing abstract methods
    def _loadResolutionCache(self):
        """Load previously resolved author name mappings from cache file"""
        from pathlib import Path
        import json
        
        cache_path = Path("logs") / "article_author_resolution_cache.json"
        if not cache_path.exists():
            return {}
        
        try:
            with cache_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            return payload.get("resolutions", {}) if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}
    
    def _normalizeData(self):
        """Normalize article author names for matching"""
        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if not isinstance(article_data, dict):
                continue
            
            # Ensure authorCleanNames exists
            if "authorCleanNames" not in article_data:
                article_data["authorCleanNames"] = []
    
    def sanitize(self, manualStart=None, manualEnd=None, clear: bool = True):
        """
        Sanitize articles by matching author names to existing authors.
        Uses DiffChecker with thresholds: 0.9 for auto-match, 0.8 for flagging conflicts.
        """
        self._normalizeData()
        self._matchArticleAuthors(manualStart, manualEnd, clear)
        self._logUnknownAuthors()
        self._log("article_mappings", "article_conflicts")
        return self.data

    def _logChange(self, article_id, old_name, new_name):
        """Log when an article author name is updated"""
        self.changes.append({
            "article_id": article_id,
            "old_author": old_name,
            "new_author": new_name
        })
    
    def _logConflict(self, article_id, author_name, candidates):
        """Log when multiple similar authors are found"""
        self.conflicts.append({
            "article_id": article_id,
            "author_name": author_name,
            "candidates": candidates
        })

    # Article specific methods
    def _matchArticleAuthors(self, manualStart=None, manualEnd=None, clear: bool = True):
        """
        Match article author names to existing authors using DiffChecker.
        Similar to Policy._autoResolve but adapted for article author matching.
        """
        clean = nlp.cleanDocument
        author_lookup = self.policies._author_lookup
        
        # Collect all unique author names from articles
        unique_names = {}  # clean_key -> [(article_id, original_name), ...]
        
        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if not isinstance(article_data, dict):
                continue
            
            article_id = article_data.get("id", "unknown")
            clean_names = article_data.get("authorCleanNames") or []
            
            for original_name in clean_names:
                if not original_name:
                    continue
                key = clean(str(original_name), "similarity")
                if not key:
                    continue
                
                if key not in unique_names:
                    unique_names[key] = []
                unique_names[key].append((article_id, original_name))
        
        # Try to match each unique name
        flaggedMatches = []  # For manual resolution
        
        for clean_key, occurrences in unique_names.items():
            # Try exact match first
            exact_match = author_lookup.get(clean_key)
            if exact_match:
                author_id, display_name = exact_match
                for article_id, original_name in occurrences:
                    self.author_matches[article_id] = self.author_matches.get(article_id, {})
                    self.author_matches[article_id][original_name] = (author_id, display_name)
                continue
            
            # Use DiffChecker for similarity matching
            candidates = [(lookup_key, author_id, display_name) 
                         for lookup_key, (author_id, display_name) in author_lookup.items()]
            
            if not candidates:
                # No authors to match against
                for article_id, original_name in occurrences:
                    self._logUnknownAuthor(original_name, article_id)
                continue
            
            # Prepare for DiffChecker
            candidate_names = [lookup_key for lookup_key, _, _ in candidates]
            diffChecker = DiffChecker([clean_key] + candidate_names)
            
            best_match = None
            best_similarity = 0.0
            similar_matches = []  # For threshold >= 0.8
            
            for idx, (lookup_key, author_id, display_name) in enumerate(candidates):
                sim = diffChecker.compare(0, idx + 1)  # Compare clean_key (index 0) with each candidate
                
                if sim >= 0.9:
                    # Auto-match threshold
                    if sim > best_similarity:
                        best_similarity = sim
                        best_match = (author_id, display_name, sim)
                elif sim >= 0.8:
                    # Flag for manual resolution
                    similar_matches.append((author_id, display_name, sim))
            
            if best_match:
                # Found a strong match (>= 0.9)
                author_id, display_name, sim = best_match
                for article_id, original_name in occurrences:
                    self.author_matches[article_id] = self.author_matches.get(article_id, {})
                    self.author_matches[article_id][original_name] = (author_id, display_name)
                    self._logChange(article_id, original_name, display_name)
            elif similar_matches:
                # Found similar matches that need manual resolution (0.8-0.9)
                for article_id, original_name in occurrences:
                    flaggedMatches.append({
                        "article_id": article_id,
                        "author_name": original_name,
                        "clean_key": clean_key,
                        "candidates": similar_matches
                    })
            else:
                # No match found
                for article_id, original_name in occurrences:
                    self._logUnknownAuthor(original_name, article_id)
        
        # Manual resolution for flagged matches
        if flaggedMatches:
            if manualStart:
                manualStart()
            self._manualResolveAuthors(flaggedMatches, clear)
            self._saveResolutionCache()  # Persist cache after manual resolutions
            if manualEnd:
                manualEnd()
        
        # Update all articles with matched authors
        self._applyAuthorMatches()
    
    def _saveResolutionCache(self):
        """Save author name resolutions to cache file for future runs"""
        from pathlib import Path
        import json
        
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        cache_path = log_dir / "article_author_resolution_cache.json"
        
        with cache_path.open("w", encoding="utf-8") as file:
            json.dump(
                {"resolutions": self.resolution_cache},
                file,
                indent=4
            )
    
    def _manualResolveAuthors(self, flagged: list, clear: bool = True):
        """
        Manual resolution for author matches with similarity between 0.8-0.9.
        Similar to Policy._manualResolve but adapted for article authors.
        """
        from Utils.Utility import Utility
        from Animator import Animator
        
        for i, match_info in enumerate(flagged):
            article_id = match_info["article_id"]
            author_name = match_info["author_name"]
            candidates = match_info["candidates"]
            
            # Check if this author name was previously resolved
            if author_name in self.resolution_cache:
                cached_author_id, cached_display_name = self.resolution_cache[author_name]
                self.author_matches[article_id] = self.author_matches.get(article_id, {})
                self.author_matches[article_id][author_name] = (cached_author_id, cached_display_name)
                self._logChange(article_id, author_name, cached_display_name)
                print(f"Applied cached resolution: '{author_name}' → '{cached_display_name}' (Article {article_id})")
                continue
            
            # Display the conflict
            print(f"\nArticle {article_id}: Author name '{author_name}'")
            print(f"Found {len(candidates)} similar matches:")
            for idx, (author_id, display_name, sim) in enumerate(candidates):
                print(f"  [{idx}] {display_name} (ID: {author_id}, similarity: {sim:.2f})")
            print(f"  [s] Skip - mark as unknown")
            
            while True:
                choice = input("Choose an option (number, s to skip, or q to quit): ").strip().lower()
                
                if choice == 'q':
                    return
                elif choice == 's':
                    self._logUnknownAuthor(author_name, article_id)
                    break
                else:
                    try:
                        idx = int(choice)
                        if 0 <= idx < len(candidates):
                            author_id, display_name, sim = candidates[idx]
                            # Cache this resolution for future use
                            self.resolution_cache[author_name] = (author_id, display_name)
                            self.author_matches[article_id] = self.author_matches.get(article_id, {})
                            self.author_matches[article_id][author_name] = (author_id, display_name)
                            self._logChange(article_id, author_name, display_name)
                            self._logConflict(article_id, author_name, 
                                            [(aid, dname, s) for aid, dname, s in candidates])
                            break
                        else:
                            print("Invalid index. Try again.")
                    except ValueError:
                        print("Invalid input. Try again.")
    
    def _applyAuthorMatches(self):
        """Apply the matched authors to all articles"""
        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if not isinstance(article_data, dict):
                continue
            
            article_id = article_data.get("id", "unknown")
            matches = self.author_matches.get(article_id, {})
            
            author_ids = []
            author_names = []
            clean_names = article_data.get("authorCleanNames") or []
            
            for original_name in clean_names:
                if original_name in matches:
                    author_id, display_name = matches[original_name]
                    author_ids.append(author_id)
                    author_names.append(display_name)
            
            article_data["authorIDs"] = author_ids
            article_data["authors"] = author_names
    
    def _findAuthorMatch(self, author_name: str):
        '''
        Find an author by exact match or similarity matching.
        Returns (author_id, display_name) tuple or None if no match found
        '''
        if not author_name:
            return None
        
        clean = nlp.cleanDocument
        key = clean(str(author_name), "similarity")
        
        # Try exact match first
        exact_match = self.policies._author_lookup.get(key)
        if exact_match:
            return exact_match
        
        # Fallback to similarity matching using DiffChecker
        return self._findSimilarAuthor(key)
    
    def _findSimilarAuthor(self, clean_key: str):
        '''
        Find the most similar author using DiffChecker.
        Returns (author_id, display_name) tuple or None if no match above 0.9 threshold
        '''
        author_lookup = self.policies._author_lookup
        candidates = [(lookup_key, author_id, display_name) 
                     for lookup_key, (author_id, display_name) in author_lookup.items()]
        
        if not candidates:
            return None
        
        candidate_names = [lookup_key for lookup_key, _, _ in candidates]
        diffChecker = DiffChecker([clean_key] + candidate_names)
        
        best_match = None
        best_similarity = 0.0
        
        for idx, (lookup_key, author_id, display_name) in enumerate(candidates):
            sim = diffChecker.compare(0, idx + 1)
            if sim >= 0.9 and sim > best_similarity:
                best_similarity = sim
                best_match = (author_id, display_name)
        
        return best_match
    
    def _logUnknownAuthor(self, author_name: str, article_id):
        '''Track an unknown author that failed to match any existing author'''
        if author_name not in self.unknown_authors:
            self.unknown_authors[author_name] = []
        if article_id not in self.unknown_authors[author_name]:
            self.unknown_authors[author_name].append(article_id)
    
    def _logUnknownAuthors(self):
        '''Write unknown authors to a log file'''
        if not self.unknown_authors:
            return
        
        from pathlib import Path
        import json
        
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "article_unknown_authors.json"
        
        # Load existing unknown authors if file exists
        existing = {}
        if log_path.exists():
            try:
                with log_path.open("r", encoding="utf-8") as file:
                    payload = json.load(file)
                existing = payload.get("unknown_authors", {}) if isinstance(payload, dict) else {}
                if not isinstance(existing, dict):
                    existing = {}
            except (OSError, json.JSONDecodeError):
                existing = {}
        
        # Merge with existing data
        merged = dict(existing)
        for author_name, article_ids in self.unknown_authors.items():
            if author_name in merged:
                # Merge article IDs and deduplicate
                merged[author_name] = sorted(list(set(merged[author_name] + article_ids)))
            else:
                merged[author_name] = sorted(article_ids)
        
        with log_path.open("w", encoding="utf-8") as file:
            json.dump(
                {"unknown_authors": merged},
                file,
                indent=4
            )