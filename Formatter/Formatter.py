import re
import os


class Formatter():
    _ZERO_DATE_RE = re.compile(r"^0{4}-0{2}-0{2}(?: 0{2}:0{2}:0{2})?$")
    DEFAULT_SQL_BATCH_SIZE = 50

    def __init__(self, data: list):
        self.data = data
        self.sqlCommands = []

    def _esc(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, str) and self._ZERO_DATE_RE.match(value):
            return "NULL"

        # MariaDB/MySQL string literal escaping: preserve backslashes and quotes.
        safe_value = str(value).replace("\\", "\\\\").replace("'", "''")
        return f"'{safe_value}'"

    def _sql_batch_size(self):
        raw = os.getenv("WP_SQL_BATCH_SIZE", "")
        if raw:
            try:
                value = int(raw)
                if value > 0:
                    return value
            except ValueError:
                pass
        return self.DEFAULT_SQL_BATCH_SIZE

    def _insert_batches(self, insert_prefix, row_values):
        batch_size = self._sql_batch_size()
        batch = []
        for values in row_values:
            batch.append(values)
            if len(batch) >= batch_size:
                yield f"{insert_prefix} VALUES {', '.join(batch)};"
                batch.clear()
        if batch:
            yield f"{insert_prefix} VALUES {', '.join(batch)};"
