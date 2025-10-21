from Translator.Author import *
from Translator.Translator import *

class AuthorTranslator(Translator):
    def __init__(self, source):
        super().__init__(source)
    
    def translate(self):
        authors = []
        for author in self.source:
            authorObject = Author(int(author['wp:author_id']), 
                                  author['wp:author_login'], 
                                  author['wp:author_email'],
                                  author['wp:author_display_name'], 
                                  author['wp:author_first_name'], 
                                  author['wp:author_last_name'])
            authors.append(authorObject)
        return authors
    
    def _log(self):
        # Log data into json
        pass
    