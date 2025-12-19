from Translator.Author import *
from Translator.Translator import *

class AuthorTranslator(Translator):
    def __init__(self, source):
        super().__init__(source)

    def _getAuthorData(self, author):
        displayName = author['wp:author_display_name']
        firstName = author['wp:author_first_name']
        lastName = author['wp:author_last_name']
        email = author['wp:author_email']
        login = author['wp:author_login']

        return [self.objCount, displayName, firstName, lastName, email, login]
        
    
    def translate(self):
        for author in self.source:
            authorData = self._getAuthorData(author)
            authorObject = Author(*authorData)
            self.addObject(authorObject)

    def listAuthors(self):
        return [
            Author(
                auid=auth["id"],
                login=auth["login"],
                email=auth["email"],
                display_name=auth["display_name"],
                first_name=auth["first_name"],
                last_name=auth["last_name"],
            )
            for auth in self.objDataDict.values()
        ]
    
