from utility import *

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
        self.username = generateUsername(self.firstName, self.lastName)
        self.email = email
        self.role = role
        
        wpAuthor.authorDict.update({self.id : self})
        wpAuthor.authorUsernames.append(self.username)
    
    def printAuthors():
        for i in wpAuthor.authorDict:
            str = f'''id: {wpAuthor.authorDict[i].id}\n\tfirstName: {wpAuthor.authorDict[i].firstName}\n\tlastName: {wpAuthor.authorDict[i].lastName}\n\tusername: {wpAuthor.authorDict[i].username}\n\temail: {wpAuthor.authorDict[i].email}\n\trole: {wpAuthor.authorDict[i].role}\n\n'''
            # print(str)
            wpAuthor.authorTemp += str