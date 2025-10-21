from Translator.GuestAuthor import *
from Translator.Translator import *
from Utility import *
import json

class GuestAuthorTranslator(Translator):

    def __init__(self, source):
        super().__init__(source)
    
    def translate(self):
        for guestAuthorData in self.source:
            # Find data in raw data
            for metadata in guestAuthorData['wp:postmeta']:
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
            
            guestAuthorObject = GuestAuthor(displayName, firstName, lastName, email, login, self.objCount)
            self.objDataDict.update({guestAuthorObject.data["id"]: guestAuthorObject.data})
            self.objCount += 1

    def _log(self):
        with open('log\\gAuth.json', 'w+', encoding="utf-8") as file:
            json.dump(self.objDataDict, file, indent=4)
            