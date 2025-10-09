from Author import *
class Translator:
    translation = 'rawr xD'

    def __init__(self, source):
        self.source = source

    def translate(self):
        return translation

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

