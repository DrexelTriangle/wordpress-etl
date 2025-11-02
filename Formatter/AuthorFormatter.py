from Formatter import Formatter

class AuthorFormatter(Formatter):
    def __init__(self, authTranslator):
        super().__init__(authTranslator)
        
        
    def SQLify(self,table="authors"):
        for id, obj in super().objDataDict.items():
            command = f"""
            INSERT INTO {table} (id, display_name, first_name, last_name, email, login)
            VALUES ({id}, {obj['display_name']}, {obj['first_name']}, {obj['last_name']}, {obj['email']}, {obj['login']});
            """
            super().sqlCommands.append(command)
            