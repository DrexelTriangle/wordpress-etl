from Formatter.Formatter import Formatter


class CommentFormatter(Formatter):
    CMS_COLUMNS = [
        "id",
        "article_id",
        "wp_post_id",
        "parent_id",
        "author_name",
        "author_email",
        "author_url",
        "author_ip",
        "author_user_id",
        "content",
        "created_at",
        "created_at_gmt",
        "status",
        "type",
    ]
    CMS_SCHEMA = {
        "id": "BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY",
        "article_id": "BIGINT NULL",
        "wp_post_id": "BIGINT NULL",
        "parent_id": "BIGINT NULL",
        "author_name": "LONGTEXT",
        "author_email": "LONGTEXT",
        "author_url": "LONGTEXT",
        "author_ip": "VARCHAR(255)",
        "author_user_id": "BIGINT",
        "content": "LONGTEXT",
        "created_at": "DATETIME",
        "created_at_gmt": "DATETIME",
        "status": "VARCHAR(32)",
        "type": "VARCHAR(32)",
    }
    CMS_INDEXES = [
        "INDEX idx_comments_article_status_created (article_id, status, created_at_gmt)",
        "INDEX idx_comments_wp_post_id (wp_post_id)",
        "INDEX idx_comments_parent_id (parent_id)",
    ]
    FIELD_MAP = {
        "id": "id",
        "article_id": "articleID",
        "wp_post_id": "wpPostID",
        "parent_id": "parentID",
        "author_name": "authorName",
        "author_email": "authorEmail",
        "author_url": "authorURL",
        "author_ip": "authorIP",
        "author_user_id": "authorUserID",
        "content": "content",
        "created_at": "createdAt",
        "created_at_gmt": "createdAtGMT",
        "status": "status",
        "type": "type",
    }

    def _normalize_obj(self, item):
        return item.data if hasattr(item, "data") else item

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

    def iter_format(self, table="comments"):
        objects = [
            obj
            for item in self.data
            for obj in [self._normalize_obj(item)]
            if isinstance(obj, dict)
        ]
        if not objects:
            return

        columns = self.CMS_COLUMNS
        column_defs = [f"`{column}` {self.CMS_SCHEMA[column]}" for column in columns]
        column_defs.extend(self.CMS_INDEXES)
        yield f"CREATE TABLE {table} ({', '.join(column_defs)});"
        insert_prefix = f"INSERT INTO {table} ({', '.join(f'`{col}`' for col in columns)})"
        yield from self._insert_batches(insert_prefix, self._row_values(objects, columns))

    def format(self, table="comments"):
        self.sqlCommands = list(self.iter_format(table))
        return self.sqlCommands
