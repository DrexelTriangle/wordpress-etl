import json
class Formatter():
    def __init__(self, data):
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
        with open(fileDestination, 'w+', encoding='utf-8') as file:
          json.dump(self.sqlCommands, file, indent=4)
          file.close()
    
    def format(self, table):
        pass
    
    