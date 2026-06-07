from Formatter.Formatter import Formatter
import json


class SeoFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def _row_values(self):
        count = 1
        for obj in self.data:
            article_id = self._esc(obj.get('id'))
            metadata = obj.get('metadata')
            if isinstance(metadata, (dict, list)):
                yoast_tag_data = self._esc(json.dumps(metadata, ensure_ascii=False))
            else:
                yoast_tag_data = self._esc(metadata)
            yield f"({count}, {article_id}, {yoast_tag_data})"
            count += 1

    def iter_format(self, table="seo"):
        createTbl = (
            f"CREATE TABLE {table} ("
            "id BIGINT PRIMARY KEY, "
            "article_id BIGINT NOT NULL, "
            "yoast_tag_data LONGTEXT"
            ");"
        )
        insertPrefix = f"INSERT INTO {table} (id, article_id, yoast_tag_data)"

        yield createTbl
        yield from self._insert_batches(insertPrefix, self._row_values())

    def format(self, table="seo"):
        self.sqlCommands = list(self.iter_format(table))
        return self.sqlCommands
