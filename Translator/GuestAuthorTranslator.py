from Translator.Author import *
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
        if data is None:
            data = []
        elif isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            data = []
        for metadata in data:
            if not isinstance(metadata, dict):
                continue
            key = metadata.get('wp:meta_key')
            value = metadata.get('wp:meta_value')
            if key is None:
                continue
            match key:
                case 'cap-display_name':
                    displayName = value
                case 'cap-user_email':
                    email = value
                case 'cap-first_name':
                    firstName = value
                case 'cap-last_name':
                    lastName = value
                case 'cap-user_login':
                    login = value
        return [self.objCount, displayName, firstName, lastName, email, login]


    def translate(self):
        for guestAuthorData in self.source:
            metadata = self._extractMetadata(guestAuthorData.get('wp:postmeta'))
            guestAuthorObject = Author(*metadata)
            self.addObject(guestAuthorObject)

    def listAuthors(self):
        return [
            Author(
                auid=gauth["id"],
                display_name=gauth["display_name"],
                first_name=gauth["first_name"],
                last_name=gauth["last_name"],
                email=gauth["email"],
                login=gauth["login"],
            )
            for gauth in self.objDataDict.values()
        ]
