from Formatter.Formatter import Formatter
import json

class ArticleFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def format(self, table="articles"):
        createTbl = """CREATE TABLE articles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR
        pub_date DATETIME
        mod_date DATETIME
        description VARCHAR
        comment_status VARCHAR
        priority BOOL
        breaking_news BOOL
        tags VARCHAR
        text STRING
        ); """
        self.sqlCommands.append(createTbl)
        for obj in self.data:
            command = f"""INSERT INTO {table} (id, title, description, text, tags, pubDate, modDate, priority, breakingNews, commentStatus, featuredImgID, photoCred)
                VALUES (
                    {self._esc(obj.get('id'))},
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
        return self.sqlCommands
