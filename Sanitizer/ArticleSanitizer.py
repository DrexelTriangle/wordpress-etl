from Utils import NLP as nlp
from Translator.Article import Article
from Sanitizer.Sanitizer import Sanitizer
# from Sanitizer.Policy import Policy


class ArticleSanitizer(Sanitizer):
    def __init__(self, data: list, authors: list, guest_authors: list):
        super().__init__(data, policies=None)
        self.authors = authors or []
        self.guest_authors = guest_authors or []
  
    # Implementing abstrac methods
    def _normalizeData(self):
        pass
    
    def sanitize(self):
        self._updateInvalidAuthorNames()
        return self.data

    def _logChange(self):
        pass
    
    def _logConflict(self):
        pass

    # Article specific methods
    def _updateInvalidAuthorNames(self): 
        '''
        For each article
        Set authorIds and authors to empty
        For each author name in the authorCleanNames
        Check if author name is an existing author name (ignore case & space), if so, append into authorIds, and append their actual name into authorNames
        '''
        authors = [*self.authors, *self.guest_authors]
        lookup = {}
        clean = nlp.cleanDocument

        for author in authors:
            if hasattr(author, "data"):
                data = author.data
                author_id = data.get("id")
                display_name = data.get("display_name")
            elif isinstance(author, dict):
                author_id = author.get("id")
                display_name = author.get("display_name")
            else:
                continue
            if not display_name:
                continue
            key = clean(display_name, "similarity")
            if not key:
                continue
            existing = lookup.get(key)
            if existing is None or (author_id is not None and author_id < existing[0]):
                lookup[key] = (author_id, display_name)

        for article in self.data:
            article_data = article.data if hasattr(article, "data") else article
            if not isinstance(article_data, dict):
                continue
            author_ids = []
            author_names = []
            clean_names = article_data.get("authorCleanNames") or []
            for clean_name in clean_names:
                if not clean_name:
                    continue
                key = clean(str(clean_name), "similarity")
                match = lookup.get(key)
                if not match:
                    continue
                author_id, display_name = match
                author_ids.append(author_id)
                author_names.append(display_name)
            article_data["authorIDs"] = author_ids
            article_data["authors"] = author_names