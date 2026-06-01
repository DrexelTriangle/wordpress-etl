import re


class Formatter():
    _ZERO_DATE_RE = re.compile(r"^0{4}-0{2}-0{2}(?: 0{2}:0{2}:0{2})?$")

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
