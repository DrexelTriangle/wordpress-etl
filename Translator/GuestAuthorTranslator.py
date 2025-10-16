from Translator.GuestAuthor import *
from Translator.Translator import *

class GuestAuthorTranslator(Translator):

    def __init__(self, source):
        super().__init__(source)
    
    def translate(self):
        guestAuthors = []
        for guestAuthor in self.source:
            guestAuthorObject = GuestAuthor(
                                guestAuthor['title'],
                                guestAuthor['title'].split(' ')[0],
                                guestAuthor['title'].split(' ')[1]
                                )
            guestAuthors.append(guestAuthorObject)
        return guestAuthors
    
    