from Formatter.Formatter import Formatter
import json

class SeoFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def format(self, table="seo"):
        createTbl = f"CREATE TABLE {table} (id INT AUTO_INCREMENT PRIMARY KEY, article_id INT, yoast_tag_data, VARCHAR);"
        insertPrefix = f"INSERT INTO {table} (id, article_id, yoast_tag_data)"

        self.sqlCommands.append(createTbl)
        for obj in self.data:
            id = self._esc(obj.get('id'))
            yoast_tag_data = self._esc(str(obj.get('metadata')))
            values = f"VALUES({id}, {id}, {yoast_tag_data})"
            command = f"{insertPrefix} {values};"
            self.sqlCommands.append(command)
        return self.sqlCommands
