from Formatter.Formatter import Formatter
import json

class ArticleFormatter(Formatter):
    EXCLUDED_SQL_FIELDS = {"authorCleanNames"}

    def __init__(self, articleData):
        super().__init__(articleData)

    def _normalize_obj(self, item):
        return item.data if hasattr(item, "data") else item

    def _to_sql_literal(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (dict, list)):
            return self._esc(json.dumps(value, ensure_ascii=False))
        return self._esc(value)

    def format(self, table="articles"):
        objects = [self._normalize_obj(item) for item in self.data if isinstance(self._normalize_obj(item), dict)]
        if not objects:
            return self.sqlCommands

        # Keep stable ordering by first occurrence; always move "id" to the front if present.
        seen = set()
        columns = []
        for obj in objects:
            for key in obj.keys():
                if key in self.EXCLUDED_SQL_FIELDS:
                    continue
                if key not in seen:
                    seen.add(key)
                    columns.append(key)
        if "id" in columns:
            columns.remove("id")
            columns.insert(0, "id")

        columnDefs = []
        for column in columns:
            if column == "id":
                columnDefs.append("`id` BIGINT PRIMARY KEY")
            else:
                columnDefs.append(f"`{column}` LONGTEXT")

        createTbl = f"CREATE TABLE {table} ({', '.join(columnDefs)});"
        insertPrefix = f"INSERT INTO {table} ({', '.join(f'`{col}`' for col in columns)})"

        self.sqlCommands.append(createTbl)
        for obj in objects:
            values = ", ".join(self._to_sql_literal(obj.get(col)) for col in columns)
            values = f"VALUES({values})"
            command = f"{insertPrefix} {values};"
            self.sqlCommands.append(command)
        return self.sqlCommands
