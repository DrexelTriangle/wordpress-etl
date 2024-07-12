from classes.wpArticle import *
from classes.wpAuthor import *
from pprint import *

def writeArticlesToFile(fileLoc):
    with open(fileLoc, "w") as file:
        wpArticle.printArticles(fileLoc)
        file.close()

def visualizeDictionary(myDict, fileLoc):
    output = pformat(myDict)
    with open(fileLoc, 'w+') as file:
        file.write(output)
        file.close()

def locateAllAuthors():
    uniqueAuthors = []
    maxLen = 0
    colors = ['\033[0;31m', '\033[0;32m', '\033[0;34m', '\033[0;33m', '\033[0;36m'] 
    found = '\033[0;30m'
    

    for i in range(len(wpArticle.generic_articleDict)):
        article = wpArticle.generic_articleDict[i]
        if (len(article.authors) > 0):
            for j in range(len(article.authors)):
                authorName = article.authors[j]
                if not(authorName in uniqueAuthors):
                    uniqueAuthors.append(authorName)
                    if (len(article.authors[j]) > maxLen):
                        maxLen = len(article.authors[j])

    print(f"\n\nALL ARTICLE AUTHORS: {len(uniqueAuthors)} found")    
    print('-' * (5 * maxLen))
    uniqueAuthors.sort()
    for i in range(len(uniqueAuthors)):
        end = '\033[0m'
        textColor = ''
        authorExists = False
        
        space = ' ' * (maxLen - len(uniqueAuthors[i]))
        newAuthorName = uniqueAuthors[i].replace('-', '')
        for j in wpAuthor.authorDict:
            auth =  wpAuthor.authorDict[j]
            if (auth.firstName == None and auth.lastName == None):
                continue
            else:
                if (auth.firstName != None):
                    db_authName = auth.firstName.lower().replace(' ', '')
                if (auth.lastName != None):
                    db_authName += auth.lastName.lower().replace(' ', '')

            if (db_authName == newAuthorName):
                authorExists = True
                break
        
        if (authorExists):
            textColor = '\x1B[3m' + found
            end += '\x1B[0m' 
        else: 
            textColor = colors[i % 5]

        print(f"{textColor}{space}{uniqueAuthors[i]}{end}", end=' ')
        if ((i + 1) % 5 == 0):
            print('\n')

    print()