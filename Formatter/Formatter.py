class Formatter():
    def __init__(self, translator):
        self.objDataDict = translator.getObjDataDict()
        self.sqlCommands = []
    
    def SQLify(self, table):
        pass
    
    