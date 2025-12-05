from Formatter.Formatter import *

class AuthorFormatter(Formatter):
    def __init__(self, authTranslator):
        super().__init__(authTranslator)
        
    def SQLify(self, table="authors"):
        for id, obj in self.getObjDataDict().items():
            command = f"""INSERT INTO {table} (id, display_name, first_name, last_name, email, login)
                VALUES (
                    {id},
                    {self._esc(obj.get('display_name'))},
                    {self._esc(obj.get('first_name'))},
                    {self._esc(obj.get('last_name'))},
                    {self._esc(obj.get('email'))},
                    {self._esc(obj.get('login'))}
                );
            """
            self.sqlCommands.append(command)
