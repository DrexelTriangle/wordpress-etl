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

        data = [self.objCount, displayName, firstName, lastName, email, login]
        return Author(*data)
        
    
    def translate(self):
        for author in self.source:
            self.addObject(self._getAuthorData(author))
    
    def _log(self, fileDestination):
        with open(fileDestination, 'w+', encoding='utf-8') as file:
          json.dump(self.objDataDict, file, indent=4)
          file.close()
    
