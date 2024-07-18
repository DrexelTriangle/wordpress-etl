from classes.wpArticle import *
from classes.wpAuthor import *
from pprint import *
import re

def writeArticlesToFile(fileLoc):
    with open(fileLoc, "w") as file:
        wpArticle.printArticles(fileLoc)
        file.close()

def visualizeDictionary(myDict, fileLoc):
    output = pformat(myDict)
    with open(fileLoc, 'w+') as file:
        file.write(output)
        file.close()

def edgeAuthorCheck(authorName):
    filteredAuthors = []
    result = authorName
    temp = []


    # joins (-and-)
    # result = re.sub("-and-", " ", result)
    # if (result != authorName):
    #     result = re.sub("-and-", " ", result)
    #     temp.append(result.split(" "))
    #     for i in range(len(temp)):
    #         print(temp[i])
    #         exit(1)
    #         temp[i] = re.sub("-[0-9]", "", temp[i])
    #         temp[i] = re.sub("[0-9]", "", temp[i])
    #     return temp
    
    # - numbers
    result = re.sub("-[0-9]", "", result)
    
    # numbers
    result = re.sub("[0-9]", "", result)

    if (result != authorName):
        temp = [result]

    return temp

    

def locateAllAuthors():
    uniqueAuthors, unfoundAuthors, strips = [], [], []
    maxLen = 0
    colors = ['\033[0;31m', '\033[0;32m', '\033[0;34m', '\033[0;33m', '\033[0;36m'] 
    found = '\033[0;30m'
    count = 0
    
    # Grab unique authors
    for i in range(len(wpArticle.generic_articleDict)):
        article = wpArticle.generic_articleDict[i]
        if (len(article.authors) > 0):
            for j in range(len(article.authors)):
                authorName = article.authors[j]
                if not(authorName in uniqueAuthors):
                    uniqueAuthors.append(authorName)
                    if (len(article.authors[j]) > maxLen):
                        maxLen = len(article.authors[j])

    print(f"\nARTICLE AUTHORS: {len(uniqueAuthors)} unique authors", end=", ")    
    uniqueAuthors.sort()

    # Find unfound authors 
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
                    db_authName = auth.firstName.lower().replace(' ', '').replace('-', "")
                if (auth.lastName != None):
                    db_authName += auth.lastName.lower().replace(' ', '').replace('-', "")

            if (db_authName == newAuthorName):
                authorExists = True
                break
        
        if (authorExists):
            textColor = '\x1B[3m' + found
            end += '\x1B[0m' 
        else: 
            textColor = "\033[0;33m"
            count += 1
            unfoundAuthors.append(uniqueAuthors[i])
                    
        #print(f"{textColor}{space}{uniqueAuthors[i]}{end}", end=' ')
        # if ((i + 1) % 5 == 0):
        #     print('\n')
    print(f"{len(unfoundAuthors)} unfound")
    #4print(count)
    skipCount = 0
    while(len(unfoundAuthors) > 0):
        unfoundMsg = f"[\033[0;33m{unfoundAuthors[0]}\033[0m] was not found in the database."
        print(unfoundMsg)
        choice = -1
        invalid = 0
        while(1):
            def invalidInput(invalid):
                comments = ["i dont even know why ur still going at this point", "bro it isnt even funny just give up", "let it go", "cross that bridge fam", "dawg if i was you i wouldnt feel myself dawg \033[3mif i was you i would KILL myself\033[0m", 
                        "yeah ur kinda cooked man i dont even know what youre doing", "i went to finished land and they all knew you", "Get ready to learn Chinese, buddy.", "they might as well put u on a plate and serve u up like in The Bear cause you are cooked", 
                        "G I V E    U P", "ɹǝʌo sʇᴉ oɹq dn ǝʌᴉƃ"]
                
                invalid += 1
                count = ""
                temp = 0
                
                if (invalid > 1):
                    count = f"({invalid})"
                    temp = 1
                if (10 < invalid and invalid <= 10 + len(comments)):
                    count = f"({comments[invalid % len(comments)]})"
                
                print ('\033[1A\033[K' * (6 + (temp)), end='')
                print(f'\033[0;31mInavlid Character {count}\033[0m')
                return invalid



            try:
                usrInput = int(input("\t1. find existing author\n\t2. create new author\n\t3. skip\n\t4. exit\n\n> "))
                match usrInput:
                    case 4:
                        exit(1)
                    case 3:
                        unfoundAuthors.append(unfoundAuthors[0])
                        unfoundAuthors.pop(0)
                        print('\033[1A\033[K' * (7), end='')
                        
                        break
                    case 2:
                        print('\033[1A\033[K' * (7), end='')
                        print(f"CREATING AUTHOR for [\033[0;33m{unfoundAuthors[0]}\033[0m]")
                        firstName = input((f"    \033[0;30mFirst Name:\033[0m ")).strip()
                        lastName = input((f"    \033[0;30mLast Name:\033[0m ")).strip()
                        email = input((f"    \033[0;30mEmail:\033[0m ")).strip()

                        spaces = f"{firstName}, {lastName}, {email}"
                        createdAuthor = f"\033[0;31m{firstName}\033[0m, \033[0;31m{lastName}\033[0m, \033[0;31m{email}\033[0m"
                        print("      ┌" + ("─" * (len(spaces) + 2)) +"┐" )
                        print(f"      │ {createdAuthor} │")
                        print("      └" + ("─" * (len(spaces) + 2)) +"┘" )

                        usrChoice = input("\n    Create author? (y/n) > ")
                        exit(7)
                    case _:
                        invalid = invalidInput(invalid)
                        
            except ValueError:
                invalid = invalidInput(invalid)

                    

            

    print()