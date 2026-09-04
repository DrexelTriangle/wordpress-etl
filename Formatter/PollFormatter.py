from Formatter.Formatter import Formatter


class PollFormatter(Formatter):
    """Writes the poll archive table.

    The schema is duplicated from the CMS's own DDL (server/internal/database/
    polls.go) the same way CommentFormatter duplicates the comments table: the
    seed has to create the table before the application starts, so it cannot
    ask the application for the shape.
    """

    CMS_COLUMNS = [
        "id",
        "question",
        "status",
        "starts_at",
        "ends_at",
    ]
    CMS_SCHEMA = {
        "id": "BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY",
        "question": "VARCHAR(255) NOT NULL",
        "status": "VARCHAR(16) NOT NULL DEFAULT 'draft'",
        "starts_at": "DATETIME NULL",
        "ends_at": "DATETIME NULL",
        "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    }
    # created_at/updated_at are defaulted, so they are declared but never
    # written: a seeded row should carry the time it was loaded, not a made-up
    # one back-dated to the WordPress poll.
    CMS_DEFAULTED_COLUMNS = ["created_at", "updated_at"]
    CMS_INDEXES = [
        "INDEX idx_cms_polls_status (status)",
        "INDEX idx_cms_polls_starts_at (starts_at)",
    ]
    FIELD_MAP = {
        "id": "id",
        "question": "question",
        "status": "status",
        "starts_at": "startsAt",
        "ends_at": "endsAt",
    }

    def _to_sql_literal(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, int):
            return str(value)
        return self._esc(value)

    def _row_values(self, objects, columns):
        for obj in objects:
            yield f"({', '.join(self._to_sql_literal(obj.get(self.FIELD_MAP[col])) for col in columns)})"

    def _create_table(self, table):
        columns = self.CMS_COLUMNS + self.CMS_DEFAULTED_COLUMNS
        column_defs = [f"`{column}` {self.CMS_SCHEMA[column]}" for column in columns]
        column_defs.extend(self.CMS_INDEXES)
        return f"CREATE TABLE {table} ({', '.join(column_defs)});"

    def iter_format(self, table="cms_polls"):
        objects = [obj for obj in self.data if isinstance(obj, dict)]
        if not objects:
            return

        columns = self.CMS_COLUMNS
        yield self._create_table(table)
        insert_prefix = f"INSERT INTO {table} ({', '.join(f'`{col}`' for col in columns)})"
        yield from self._insert_batches(insert_prefix, self._row_values(objects, columns))

    def format(self, table="cms_polls"):
        self.sqlCommands = list(self.iter_format(table))
        return self.sqlCommands
