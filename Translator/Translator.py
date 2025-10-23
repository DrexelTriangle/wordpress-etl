from Translator.Author import *
from Translator.GuestAuthor import *
import json

class Translator:
    def __init__(self, source):
        self.source = source
        self.objCount = 0
        self.objDataDict = {}

    def translate(self):
        translation = []
        return translation
    
    def _log(self, fileDestination):
        # Log data into json
        with open(fileDestination, 'w+', encoding='utf-8') as file:
          json.dump(self.objDataDict, file, indent=4)
          file.close()

    def addObject(self, object):
        self.objDataDict.update({object.data["id"]: object.data})
        self.objCount += 1
        




