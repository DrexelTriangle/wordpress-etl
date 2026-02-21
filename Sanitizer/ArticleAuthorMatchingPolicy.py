from Sanitizer.Policy import Policy
from Utils.Utility import Utility

class ArticleAuthorMatchingPolicy(Policy):
    def __init__(self, data, authors):
        # Map ambiguous/unknown author names to canonical authors
        specialEdits = {
            "paulie": "Paulie Loscalzo",
            "alexjones": "Alexandra Jones",
            "melodywumaddiepelchat": ["Melody Wu", "Maddie Pelchat"],
            "juliaconleykaseyshamisandtaylorclark": ["Julia Conley", "Kasey Shamis", "Taylor Clark"],
        }
        specialFlags = set()
        banList = []
        
        self.authors = authors or []
        self._author_lookup = self._buildAuthorLookup()
        self.specialEdits = specialEdits  # Store for use in matching logic
        
        super().__init__(specialEdits, specialFlags, banList, data, isAuthor=False)
    
    def _buildAuthorLookup(self):
        # Build a lookup dictionary for all authors by their cleaned names and logins
        lookup = {}
        clean = Utility.cleanDocument
        
        for author in self.authors:
            if hasattr(author, "data"):
                data = author.data
                author_id = data.get("id")
                display_name = data.get("display_name")
                login = data.get("login")
            elif isinstance(author, dict):
                author_id = author.get("id")
                display_name = author.get("display_name")
                login = author.get("login")
            else:
                continue
            
            # Add entry for display_name
            if display_name:
                key = clean(display_name, "similarity")
                if key:
                    existing = lookup.get(key)
                    if existing is None or (author_id is not None and author_id < existing[0]):
                        lookup[key] = (author_id, display_name)
            
            # Add entry for login (username)
            if login:
                key = clean(login, "similarity")
                if key:
                    existing = lookup.get(key)
                    if existing is None or (author_id is not None and author_id < existing[0]):
                        lookup[key] = (author_id, display_name)
        
        return lookup
