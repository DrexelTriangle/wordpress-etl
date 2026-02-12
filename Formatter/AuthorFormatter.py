from Formatter.Formatter import *

class AuthorFormatter(Formatter):
    def __init__(self, authData:list):
        super().__init__(authData)
        
    def format(self, table="authors"):
        createTbl = """CREATE TABLE authors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR,
        last_name VARCHAR,
        email VARCHAR,
        role INT
        ); """
        self.sqlCommands.append(createTbl)
        for auth in self.data:
            obj = auth.data
            command = f"""INSERT INTO {table} (id, display_name, first_name, last_name, email, login)
                VALUES (
                    {self._esc(obj.get('id'))},
                    {self._esc(obj.get('display_name'))},
                    {self._esc(obj.get('first_name'))},
                    {self._esc(obj.get('last_name'))},
                    {self._esc(obj.get('email'))},
                    {self._esc(obj.get('login'))}
                );
            """
            self.sqlCommands.append(command)
        return self.sqlCommands
