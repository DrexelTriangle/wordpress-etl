from utility import *
from progressBar import *

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

def processAuthors(authorData):
    fName = ''
    lName = ''
    email = ''

    printProgressBar(0, len(authorData), length = 50)
    for i, item in enumerate(authorData):
        author = authorData[i]

        if ( (author.get('wp:author_first_name') is None) and (author.get('wp:author_last_name') is None)):
            name = charMorph(author.get('wp:author_display_name'))
            newName = parseName(name)
            fName = newName[0]
            lName = newName[1]
        else:
            fName = charMorph(author.get('wp:author_first_name'))
            lName = charMorph(author.get('wp:author_last_name'))

        if ( (author.get('wp:author_email') is not None) ):
            email = charMorph(author.get('wp:author_email'))

        obj = wpAuthor(fName, lName, email)

        printProgressBar(i + 1, len(authorData), length = 50)
    print()
