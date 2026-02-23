from Formatter.Formatter import *

class AuthorFormatter(Formatter):
    def __init__(self, authData:list):
        super().__init__(authData)
        
    def format(self, table="authors"):
        createTbl = "CREATE TABLE authors (id INT AUTO_INCREMENT PRIMARY KEY, first_name VARCHAR(255), last_name VARCHAR(255), email VARCHAR(255), role INT);"
        insertPrefix = f"INSERT INTO {table} (display_name, first_name, last_name, email, login)"
        self.sqlCommands.append(createTbl)
        for auth in self.data:
            obj = auth.data
            id = self._esc(obj.get('id'))
            displayName = self._esc(obj.get('display_name'))
            firstName = self._esc(obj.get('first_name'))
            lastName = self._esc(obj.get('last_name'))
            email = self._esc(obj.get('email'))
            login = self._esc(obj.get('login'))

            command = f"{insertPrefix} VALUES ({displayName},{firstName},{lastName},{email},{login});"
            self.sqlCommands.append(command)
        return self.sqlCommands
