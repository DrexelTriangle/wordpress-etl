from Translator.GuestAuthor import *
from Translator.Translator import *
from Utils.Utility import *

class GuestAuthorTranslator(Translator):

    def __init__(self, source):
        super().__init__(source)
    
    def _extractMetadata(self, data):
        displayName = None
        email = None
        firstName = None
        lastName = None
        login = None
        for metadata in data:
            match metadata['wp:meta_key']:
                case 'cap-display_name':
                    displayName = metadata['wp:meta_value']
                case 'cap-user_email':
                    email = metadata['wp:meta_value']
                case 'cap-first_name':
                    firstName = metadata['wp:meta_value']
                case 'cap-last_name':
                    lastName = metadata['wp:meta_value']
                case 'cap-user_login':
                    login = metadata['wp:meta_value']
        return [self.objCount, displayName, firstName, lastName, email, login]


    def translate(self):
        for guestAuthorData in self.source:
            metadata = self._extractMetadata(guestAuthorData['wp:postmeta'])
            guestAuthorObject = GuestAuthor(*metadata)
            self.addObject(guestAuthorObject)

    def listGuestAuthors(self):
        return [
            GuestAuthor(
                gauid=gauth["id"],
                display_name=gauth["display_name"],
                first_name=gauth["first_name"],
                last_name=gauth["last_name"],
                email=gauth["email"],
                login=gauth["login"],
            )
            for gauth in self.objDataDict.values()
        ]
