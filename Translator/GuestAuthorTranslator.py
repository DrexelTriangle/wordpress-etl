from Translator.GuestAuthor import *
from Translator.Translator import *
from Utility.Utility import *
import json

class GuestAuthorTranslator(Translator):

    def __init__(self, source):
        super().__init__(source)
    
    def _extractMetadata(self, data):
        displayName, firstName, lastName, email, login = '', '', '', '', ''
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
        return [displayName, firstName, lastName, email, login, self.objCount]


    def translate(self):
        for guestAuthorData in self.source:
            metadata = self._extractMetadata(guestAuthorData['wp:postmeta'])
            guestAuthorObject = GuestAuthor(*metadata)
            self.addObject(guestAuthorObject)
