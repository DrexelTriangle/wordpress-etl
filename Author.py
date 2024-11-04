from newUtility import *
from progressBar import *

class Author:
  authorCount = 0
  authorDict = {}
  usernames = []
  unique_emails = []
  authorsVisualized = ''


  def __init__(self, firstName:str, lastName:str, email:str, role:int = 1):
    Author.authorCount += 1
    self.id = Author.authorCount
    self.firstName = firstName
    self.lastName = lastName
    self.username = generateUsername(self.firstName, self.lastName)
    self.meshname = generateMeshname(self.firstName, self.lastName)
    self.email = email
    self.role = role
    self.alias = ""
    
    
    Author.authorDict.update({self.id : self})
    Author.usernames.append(self.username)
    if not (self.email in Author.unique_emails):
      Author.unique_emails.append(self.email)
  
  def __str__(self):
    result = ""
    result += f"id: {self.id}\n"
    result += f"\tFirst Name: {self.firstName}\n"
    result += f"\tLast Name: {self.lastName}\n"
    result += f"\tusername: {self.username}\n"
    result += f"\tmeshname: {self.meshname}\n"
    result += f"\temail: {self.email}\n"
    result += f"\trole: {self.role}\n\n"

    return result
      
  def getAuthor(index: int) -> "Author":
    return Author.authorDict[index + 1]
  
  def visualize():
    # visualized authors
    with open('.\\visualizations\\visualized-authors.txt', 'w+', encoding='utf-8') as file:
      result = ''
      for i in range(len(Author.authorDict)):
        file.write(str(Author.getAuthor(i)))
      file.close()
    
    
      

  def processAuthors(authorData):
    print('> [author.process-authors] processing authors...')
    fName, lName, email = '', '', ''
    authorDupes = []

    for i, item in enumerate(authorData):
        authorName, authorDisplayName, authorEmail = '', '', '', 
        email = 'NO_EMAIL'
        authorObj = authorData[i]
        authorName = [authorObj.get('wp:author_first_name'), authorObj.get('wp:author_last_name')]
        authorDisplayName = authorObj.get('wp:author_display_name')
        authorEmail = authorObj.get('wp:author_email')


        # if !(first && last), attempt to parse email for name 
        if ((authorName[0] == None) and (authorName[0] == None)):
            newName = attemptNameParse(charMorph(authorDisplayName))
            fName = newName[0]
            lName = newName[1]
        else:
            fName = charMorph(authorName[0])
            lName = charMorph(authorName[1])
        if (authorEmail != None):
          email = charMorph(authorEmail)
        
        # Only add user if not already inside object dictionary. 
        username = generateUsername(fName, lName)
        isAllValuesEmpty = (fName == 'NO_FIRST') and (lName == 'NO_LAST') and (email == 'NO_EMAIL') 
        bySomeone = (fName == 'By')
        
        if not(username in Author.usernames or isAllValuesEmpty or bySomeone):
          obj = Author(fName, lName, email)
        else:
          authorDupes.append([fName, lName, email])

        # dupAuthor(authorDupes)

    Author.visualize()
    
    print('> [author.process-authors] done.')

  def processGuestAuthors(authorData):
    print('> [author.process-guest-authors] processing guest authors...')
    fName, lName, email, displayName = '', '', '', ''
    authorDupes = []
    total = len(authorData)

    for i, item in enumerate(authorData):
      data = authorData[i].get('wp:postmeta')
      for j in range(len(data)): 
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
                fName = charMorph(temp2[0])
                lName = charMorph(temp2[1])
            else:
                fName = displayName 

        # Only add user if not already inside object dictionary. 
        tempUsername = generateUsername(fName, lName)
        isAllValuesEmpty = (fName == 'NO_FIRST') and (lName == 'NO_LAST') and (email == 'NO_EMAIL') 
        
        if not(tempUsername in Author.usernames or isAllValuesEmpty):
            obj = Author(fName, lName, email)
        else:
            authorDupes.append([fName, lName, email])
        

    

    # TODO: Visualize authors
    Author.visualize()
    print('> [author.process-guest-authors] done.')

  def SQLifiy():
    print("> [author.sqlify] writing SQL for authors...")
    with open('.\\output\\authors-sql.txt', "w+", encoding="utf-8") as file:
      file.write("CREATE TABLE authors (id, first_name VARCHAR(256), last_name VARCHAR(256), email VARCHAR(256), role int);\n")
      for i in range(len(Author.authorDict)):
          itm = Author.getAuthor(i)
          file.write(f"INSERT INTO authors (id, first_name, last_name, email, role) VALUES ({itm.id}, {itm.firstName}, {itm.lastName}, {itm.email}, {itm.role});\n")
      file.close()
    print("> [author.sqlify] done.")

