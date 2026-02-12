from Formatter.Formatter import Formatter
import json

class ArtAuthFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def format(self, table="articles_authors"):
        createTbl = """CREATE TABLE articles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        author_id INT,
        articles_id INT,
        ); """
        self.sqlCommands.append(createTbl)
        count = 1
        for obj in self.data:
            artId = obj['id']
            authIdLst = obj['authorIDs']
            emptyValue = -1

            if len(authIdLst) == 0:
                command = f"""INSERT INTO {table} (id, author_id, articles_id)
                VALUES (
                    {count},
                    {artId},
                    {emptyValue},
                );
                """
                count += 1
                self.sqlCommands.append(command)
            else:
                for authId in authIdLst:
                    command = f"""INSERT INTO {table} (id, author_id, articles_id)
                        VALUES (
                            {count},
                            {artId},
                            {authId},
                        );
                    """
                    count += 1
                    self.sqlCommands.append(command)
        return self.sqlCommands
