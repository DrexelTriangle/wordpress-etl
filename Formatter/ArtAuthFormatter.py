from Formatter.Formatter import Formatter


class ArtAuthFormatter(Formatter):
    def __init__(self, articleData):
        super().__init__(articleData)

    def format(self, table="articles_authors"):
        createTbl = (
            f"CREATE TABLE {table} ("
            "id BIGINT PRIMARY KEY, "
            "author_id BIGINT NOT NULL, "
            "articles_id BIGINT NOT NULL"
            ");"
        )
        insertPrefix = f"INSERT INTO {table} (id, author_id, articles_id)"
        self.sqlCommands.append(createTbl)

        count = 1
        for obj in self.data:
            artId = obj.get('id')
            authIdLst = obj.get('authorIDs') or []

            for authId in authIdLst:
                values = f"VALUES ({count}, {authId}, {artId})"
                command = f"{insertPrefix} {values};"
                count += 1
                self.sqlCommands.append(command)

        return self.sqlCommands
