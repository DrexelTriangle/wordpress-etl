from Formatter.Formatter import Formatter
import json

class ArtAuthFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def format(self, table="articles_authors"):
        createTbl = "CREATE TABLE articles (id INT AUTO_INCREMENT PRIMARY KEY, author_id INT, articles_id INT);"
        insertPrefix = f"INSERT INTO {table} (author_id, articles_id)"
        self.sqlCommands.append(createTbl)
        count = 1
        for obj in self.data:
            artId = obj['id']
            authIdLst = obj['authorIDs']
            emptyValue = -1
            default = len(authIdLst) == 0

            for authId in authIdLst:
                authId = emptyValue if default else authId
                values = f"VALUES ({artId}, {authId})"
                command = f"{insertPrefix} {values};"
                count += 1
                self.sqlCommands.append(command)

        return self.sqlCommands
