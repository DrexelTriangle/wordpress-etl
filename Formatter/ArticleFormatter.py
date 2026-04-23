from Formatter.Formatter import Formatter
import json

class ArticleFormatter(Formatter):
    WORDPRESS_IMAGE_BASE_URL = "https://www.thetriangle.org"
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
            lowered = photo_url.strip().lower()
            trimmed = photo_url.strip()
            if trimmed == "":
                photo_url = None
            elif lowered.startswith("http://") or lowered.startswith("https://"):
                photo_url = trimmed
            elif trimmed.startswith("//"):
                photo_url = f"https:{trimmed}"
            elif lowered.startswith("www.thetriangle.org/"):
                photo_url = f"https://{trimmed}"
            elif lowered.startswith("wp-content/"):
                photo_url = f"{self.WORDPRESS_IMAGE_BASE_URL}/{trimmed}"
            elif trimmed.startswith("/wp-content/"):
                photo_url = f"{self.WORDPRESS_IMAGE_BASE_URL}{trimmed}"
            else:
                photo_url = trimmed

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
        if isinstance(value, (dict, list)):
            return self._esc(json.dumps(value, ensure_ascii=False))
        return self._esc(value)

    def format(self, table="articles"):
        objects = [self._normalize_obj(item) for item in self.data if isinstance(self._normalize_obj(item), dict)]
        if not objects:
            return self.sqlCommands

        rows = [self._to_cms_row(obj) for obj in objects]
        columns = self.CMS_COLUMNS
        columnDefs = [f"`{column}` {self.CMS_SCHEMA[column]}" for column in columns]
        createTbl = f"CREATE TABLE {table} ({', '.join(columnDefs)});"
        insertPrefix = f"INSERT INTO {table} ({', '.join(f'`{col}`' for col in columns)})"

        self.sqlCommands.append(createTbl)
        for row in rows:
            values = ", ".join(self._to_sql_literal(row.get(col)) for col in columns)
            values = f"VALUES({values})"
            command = f"{insertPrefix} {values};"
            self.sqlCommands.append(command)
        return self.sqlCommands
