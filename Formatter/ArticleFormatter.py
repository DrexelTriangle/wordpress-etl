from Formatter.Formatter import Formatter
import json

class ArticleFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def format(self, table="articles"):
        createTbl = "CREATE TABLE articles (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description VARCHAR(255), `text` TEXT, tags TEXT, pub_date DATETIME, mod_date DATETIME, priority BOOL, breaking_news BOOL, comment_status VARCHAR(255), photo_url VARCHAR(255));"
        insertPrefix = f"INSERT INTO {table} (title, description, text, tags, pub_date, mod_date, priority, breaking_news, comment_status, photo_url)"

        self.sqlCommands.append(createTbl)
        for obj in self.data:
            id = self._esc(obj.get('id'))
            title = self._esc(obj.get('title'))
            description = self._esc(obj.get('description'))
            text = self._esc(obj.get('text'))
            tags = self._esc(json.dumps(obj.get('tags'))) if obj.get('tags') else "NULL"
            pubDate = self._esc(obj.get('pubDate'))
            modDate = self._esc(obj.get('modDate'))
            priority = int(obj.get('priority', 0))
            breakingNews = int(obj.get('breakingNews', 0))
            commentStatus = self._esc(obj.get('commentStatus'))
            photoURL = obj.get('featuredImgID') if obj.get('featuredImgID') is not None else "NULL"

            values = f"VALUES({title}, {description}, {text}, {tags}, {pubDate}, {modDate}, {priority}, {breakingNews}, {commentStatus}, {photoURL})"

            command = f"{insertPrefix} {values};"
            self.sqlCommands.append(command)
        return self.sqlCommands
