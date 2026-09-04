import json
from pathlib import Path

from Utils.SiteProfile import id_offset

class Translator:
    def __init__(self, source):
        self.source = source
        # Ids are a per-run counter, not the WordPress post id. Loading a second
        # source site into the same tables restarts at 0 and collides with the
        # first, so the offset moves this run past the previous high-water mark.
        # Articles, authors and guest authors all share it, which keeps the
        # article->author links consistent across the shift.
        self.objCount = id_offset()
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
            file.close()

    def addObject(self, object):
        payload = object.data if hasattr(object, "data") else object
        self.objDataDict.update({payload["id"]: payload})
        self.objCount += 1
        
    def getObjList(self):
        return list(self.objDataDict.values())
        
