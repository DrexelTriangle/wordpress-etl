from Formatter.Formatter import *


class AuthorFormatter(Formatter):
    def __init__(self, authData: list):
        super().__init__(authData)

    def _row_values(self):
        for auth in self.data:
            obj = auth.data
            id_val = self._esc(obj.get('id'))
            display_name = self._esc(obj.get('display_name'))
            first_name = self._esc(obj.get('first_name'))
            last_name = self._esc(obj.get('last_name'))
            email = self._esc(obj.get('email'))
            login = self._esc(obj.get('login'))

            yield f"({id_val}, {display_name}, {first_name}, {last_name}, {email}, {login})"

    def iter_format(self, table="authors"):
        createTbl = (
            f"CREATE TABLE {table} ("
            "id BIGINT PRIMARY KEY AUTO_INCREMENT, "
            "display_name VARCHAR(255), "
            "first_name VARCHAR(255), "
            "last_name VARCHAR(255), "
            "email VARCHAR(255), "
            "login VARCHAR(255)"
            ");"
        )
        insertPrefix = f"INSERT INTO {table} (id, display_name, first_name, last_name, email, login)"
        yield createTbl
        yield from self._insert_batches(insertPrefix, self._row_values())

    def format(self, table="authors"):
        self.sqlCommands = list(self.iter_format(table))
        return self.sqlCommands
