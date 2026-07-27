from Formatter.Formatter import Formatter
from Utils.MediaURL import canonicalize_media_url
import json

class ArticleFormatter(Formatter):
    EXCLUDED_SQL_FIELDS = {"authorCleanNames"}
    CMS_COLUMNS = [
        "id",
        "creation_date",
        "slug",
        "author_ids",
        "authors",
        "breaking_news",
        "comment_status",
        "description",
        "featured_img_id",
        "priority",
        "mod_date",
        "photo_url",
        "pub_date",
        "tags",
        "categories",
        "metadata",
        "text",
        "excerpt",
        "title",
    ]
    CMS_SCHEMA = {
        "id": "BIGINT PRIMARY KEY AUTO_INCREMENT",
        "creation_date": "DATETIME",
        "slug": "LONGTEXT",
        "author_ids": "LONGTEXT",
        "authors": "LONGTEXT",
        "breaking_news": "BOOL",
        "comment_status": "VARCHAR(255)",
        "description": "LONGTEXT",
        "featured_img_id": "BIGINT",
        "priority": "BOOL",
        "mod_date": "DATETIME",
        "photo_url": "LONGTEXT",
        "pub_date": "DATETIME",
        "tags": "LONGTEXT",
        "categories": "LONGTEXT",
        "metadata": "LONGTEXT",
        "text": "LONGTEXT",
        "excerpt": "LONGTEXT",
        "title": "LONGTEXT",
    }

    def __init__(self, articleData):
        super().__init__(articleData)

    def _normalize_obj(self, item):
        return item.data if hasattr(item, "data") else item

    def _normalize_datetime(self, value):
        if value in (None, "", "0000-00-00", "0000-00-00 00:00:00"):
            return None
        return value

    def _to_cms_row(self, obj):
        creation_date = self._normalize_datetime(
            obj.get("creationDate")
            or obj.get("creation_date")
            or obj.get("pubDate")
            or obj.get("modDate")
        )
        photo_url = obj.get("photoURL")
        if isinstance(photo_url, str):
            photo_url = canonicalize_media_url(photo_url)
            if not photo_url.strip():
                photo_url = None

        return {
            "id": obj.get("id"),
            "creation_date": creation_date,
            "slug": obj.get("slug"),
            "author_ids": obj.get("authorIDs"),
            "authors": obj.get("authors"),
            "breaking_news": obj.get("breakingNews"),
            "comment_status": obj.get("commentStatus"),
            "description": obj.get("description"),
            "featured_img_id": obj.get("featuredImgID"),
            "priority": obj.get("priority"),
            "mod_date": self._normalize_datetime(obj.get("modDate")),
            "photo_url": photo_url,
            "pub_date": self._normalize_datetime(obj.get("pubDate")),
            "tags": obj.get("tags"),
            "categories": obj.get("categories"),
            "metadata": obj.get("metadata"),
            "text": obj.get("text"),
            "excerpt": obj.get("excerpt"),
            "title": obj.get("title"),
        }

    def _to_sql_literal(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, (dict, list)):
            return self._esc(json.dumps(value, ensure_ascii=False))
        return self._esc(value)

    def _row_values(self, objects, columns):
        for obj in objects:
            row = self._to_cms_row(obj)
            yield f"({', '.join(self._to_sql_literal(row.get(col)) for col in columns)})"

    def iter_format(self, table="articles"):
        objects = [
            obj
            for item in self.data
            for obj in [self._normalize_obj(item)]
            if isinstance(obj, dict)
        ]
        if not objects:
            return

        columns = self.CMS_COLUMNS
        columnDefs = [f"`{column}` {self.CMS_SCHEMA[column]}" for column in columns]
        yield f"CREATE TABLE {table} ({', '.join(columnDefs)});"
        insertPrefix = f"INSERT INTO {table} ({', '.join(f'`{col}`' for col in columns)})"

        yield from self._insert_batches(insertPrefix, self._row_values(objects, columns))

    def format(self, table="articles"):
        self.sqlCommands = list(self.iter_format(table))
        return self.sqlCommands
