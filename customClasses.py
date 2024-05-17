import utility as util

class wpAuthor:
    authorCount = 0
    authorDict = {}
    authorUsernames = []
    authorTemp = ''

    def __init__(self, firstName:str, lastName:str, email:str, role:int = 1):
        wpAuthor.authorCount += 1
        self.id = wpAuthor.authorCount
        self.firstName = firstName
        self.lastName = lastName
        self.username = util.generateUsername(self.firstName, self.lastName)
        self.email = email
        self.role = role
        
        wpAuthor.authorDict.update({self.id : self})
        wpAuthor.authorUsernames.append(self.username)
    
    def printAuthors():
        for i in wpAuthor.authorDict:
            str = f'''id: {wpAuthor.authorDict[i].id}\n\tfirstName: {wpAuthor.authorDict[i].firstName}\n\tlastName: {wpAuthor.authorDict[i].lastName}\n\tusername: {wpAuthor.authorDict[i].username}\n\temail: {wpAuthor.authorDict[i].email}\n\trole: {wpAuthor.authorDict[i].role}\n\n'''
            # print(str)
            wpAuthor.authorTemp += str

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class wpArticle:
    articleCount = 0
    generic_articleDict = {}
    misc_articleDict = {}
    articleTemp = ''

    def __init__(self, id, title, pubDate, modDate, description, commentStatus, tags, text):
        wpArticle.articleCount += 1
        self.priotity = False
        self.breakingNews = False
        self.id = id
        self.title = title
        self.pubDate = pubDate
        self.modDate = modDate 
        self.description = description
        self.commentStatus = commentStatus
        self.tags = tags
        self.text = text

    def printGenericAuthors(index):
        result = ''
        dict = wpArticle.generic_articleDict[index]
        result += f'''id: {dict.id}\n'''
        result += f'''title: {dict.title}\n'''
        result += f'''pubDate: {dict.pubDate}\n'''
        result += f'''modDate: {dict.modDate}\n''' 
        result += f'''description: {dict.description}\n'''
        result += f'''commentStatus: {dict.commentStatus}\n'''
        result += f'''tags: {dict.tags}\n'''
        result += f'''text: {dict.text}\n\n'''
        return result
    
    


