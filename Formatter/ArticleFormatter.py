from Formatter.Formatter import Formatter
import json

class ArticleFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def format(self, table="articles"):
        for id, obj in self.getObjDataDict().items():
            obj = obj.data
            command = f"""INSERT INTO {table} (id, title, description, text, tags, pubDate, modDate, priority, breakingNews, commentStatus, featuredImgID, photoCred)
                VALUES (
                    {id},
                    {self._esc(obj.get('title'))},
                    {self._esc(obj.get('description'))},
                    {self._esc(obj.get('text'))},
                    {self._esc(json.dumps(obj.get('tags'))) if obj.get('tags') else "NULL"},
                    {self._esc(obj.get('pubDate'))},
                    {self._esc(obj.get('modDate'))},
                    {int(obj.get('priority', 0))},
                    {int(obj.get('breakingNews', 0))},
                    {self._esc(obj.get('commentStatus'))},
                    {obj.get('featuredImgID') if obj.get('featuredImgID') is not None else "NULL"},
                    {self._esc(obj.get('photoCred'))}
                );
            """
            self.sqlCommands.append(command)
