from Translator.Author import *
from Translator.Translator import *

class AuthorTranslator(Translator):
    def __init__(self, source):
        super().__init__(source)

    def _getAuthorData(self, author):
        count = self.objCount
        login = author['wp:author_login']
        email = author['wp:author_email']
        displayName = author['wp:author_display_name']
        firstName = author['wp:author_first_name']
        lastName = author['wp:author_last_name']

        return [count, login, email, displayName, firstName, lastName]
        
    
    def translate(self):
        for author in self.source:
            authorData = self._getAuthorData(author)
            authorObject = Author(*authorData)
            self.addObject(authorObject)
    
