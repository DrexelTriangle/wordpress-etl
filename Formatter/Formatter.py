import json
from pathlib import Path
class Formatter():
    def __init__(self, data:list):
        self.data = data
        self.sqlCommands = []
        
    def getObjDataDict(self):
        return self.data.getObjDataDict()
        
    def _esc(self, value):
        if value is None:
            return "NULL"
        safe_value = str(value).replace("'", "''")
        return f"'{safe_value}'"

    def _logCommands(self, fileDestination):
        filePath = Path(fileDestination)
        filePath.parent.mkdir(parents=True, exist_ok=True)
        with filePath.open('w+', encoding='utf-8') as file:
          json.dump(self.sqlCommands, file, indent=4)
    
    def format(self, table):
        pass
    
    
