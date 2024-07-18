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


file7_loc = ".\\dumps\\authorDump.txt"

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


def processGuestAuthors(guestAuthorData):
    fName = ''
    lName = ''
    email = ''

    printProgressBar(0, len(guestAuthorData), length = 50)
    for i, item in enumerate(guestAuthorData):
        fName = ''
        lName = ''
        email = ''
        displayName = ''
        data = guestAuthorData[i].get('wp:postmeta')
        for j in range(len(data)):
            #print(data[j])
            value = data[j]
            if (value.get('wp:meta_key') == 'cap-first_name'):
                if not(value.get('wp:meta_value') is None):
                    fName = value.get('wp:meta_value')
            if (value.get('wp:meta_key') == 'cap-last_name'):
                if not(value.get('wp:meta_value') is None):
                    lName = value.get('wp:meta_value')
            
            if (value.get('wp:meta_key') == 'cap-user_email'):
                if not(value.get('wp:meta_value') is None):
                    email = value.get('wp:meta_value')

            if (value.get('wp:meta_key') == 'cap-display_name'):
                displayName = value.get('wp:meta_value')

        if (fName == '' and lName == '' and email == ''):
            #print(displayName)
            if (len(displayName.split(' ')) == 2):
                temp2 = displayName.split(' ')
                fName = temp2[0]
                lName = temp2[1]
            else:
                fName = displayName 
            
        # print(f"{fName} {lName}  \033[0;30m\x1B[3m({email})\x1B[0m\033[0m")
        obj = wpAuthor(fName.lower().capitalize(), lName.lower().capitalize(), email)
        printProgressBar(i + 1, len(guestAuthorData), length = 50)
           

        
    print()

def loopList(lst):
    lst.append(lst[0])
    lst.pop(0)
    return lst


def mendUnfoundAuthors(unfound):
    bottomMsgCount = 0
    while(len(unfound) > 0):
        unfoundMsg = f"[\033[0;33m{unfound[0]}\033[0m] was not found in the database."
        print(unfoundMsg)
        
        options = True
        while(options):
            try:
                usrInput = int(input(f"\t1. find existing author\n\t2. create new author\n\t3. skip\n\t4. exit\n\n> "))
                match usrInput:
                    case 4:
                        wpAuthor.printAuthors()
                        with open(file7_loc, "w+", encoding="utf-8") as file:
                            file.write(wpAuthor.authorTemp)
                            file.close()
                        exit(7)
                        break
                    case 3:
                        unfound = loopList(unfound)
                        print('\033[1A\033[K' * (7),end='')
                        options = False
                        break
                    case 2:
                        print('\033[1A\033[K' * (7), end='')
                        print(f"CREATING AUTHOR for [\033[0;33m{unfound[0]}\033[0m]")
                        while(1):
                            firstName = input((f"    \033[0;30mFirst Name:\033[0m ")).strip()
                            lastName = input((f"    \033[0;30mLast Name:\033[0m ")).strip()
                            email = input((f"    \033[0;30mEmail:\033[0m ")).strip()

                            spaces = f"{firstName}, {lastName}, {email}"
                            createdAuthor = f"\033[0;31m{firstName}\033[0m, \033[0;31m{lastName}\033[0m, \033[0;31m{email}\033[0m"
                            print("      ┌" + ("─" * (len(spaces) + 2)) +"┐" )
                            print(f"      │ {createdAuthor} │")
                            print("      └" + ("─" * (len(spaces) + 2)) +"┘" )

                            usrChoice = input("\n    Create author? (y/n) > ")
                            match usrChoice:
                                case 'y':
                                    obj = wpAuthor(firstName, lastName, email)
                                    unfound.pop(0)
                                    print('\033[1A\033[K' * (9),end='')
                                    break            
                                case _:
                                    continue
                        options = False
                        break
                    case _:
                        exit(7)
                        
            except ValueError:
                exit(7)
