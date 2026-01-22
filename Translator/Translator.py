import json
from pathlib import Path

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
        filePath = Path(fileDestination)
        filePath.parent.mkdir(parents=True, exist_ok=True)
        with filePath.open('w+', encoding='utf-8') as file:
          json.dump(self.objDataDict, file, indent=4)

    def addObject(self, object):
        self.objDataDict.update({object.data["id"]: object.data})
        self.objCount += 1
        
    def getObjDataDict(self):
        return self.objDataDict
        



