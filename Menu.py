from Author import * 
from Article import *

def mapping(mustReplace):
  print('> [menu.mapping] author mapping.')
  with open('result.txt', 'w+', encoding='utf-8') as file:
    longestStr = max(Article.map, key=len)
    unique = []
    unmapped = []

    for i in Article.map:
      mapped = '' 
      dashes = '-' * (len(longestStr) - len(i) + 3)
      for j in range(len(Author.authorDict)):
        mapped = ''
        obj = Author.getAuthor(j)

        identical = obj.meshname.strip() == i.strip()
        sim = similar(obj.meshname.strip(), i.strip()) > 0.85
        mappingExists = i.strip() in mustReplace

        if (identical or sim or mappingExists):
          mapped = obj.meshname
          break
          
      if not(i in unique):
        if (not identical) and sim and mapped != '':
          file.write(f'{i} {dashes} {mapped}*\n')
        if mapped == '':
          unmapped.append(i)
          file.write(f'{i} {dashes}\n')
      

        unique.append(i)

    return unmapped
  file.close()
          
def checkForMending():
  existing = []
  mustReplace = []
  newAuthors = '.\\output\\newAuthorMappings.txt'
  mappings = '.\\output\\oldMappings.txt'
  print('> [menu.check-for-mending] checking for mending...')

  if (OS.path.isfile(newAuthors)):
    lines = []
    with open(newAuthors, 'r+', encoding='utf-8') as file:
      lines = file.readlines()
      for i in range(len(lines)):
        fields = lines[i].strip().split(',')
        obj = Author(fields[0], fields[1], fields[2])
      file.close()
  
  Author.visualize()

  if (OS.path.isfile(mappings)):
    lines = []
    with open(mappings, 'r+', encoding='utf-8') as file:
      lines = file.readlines()
      for i in range(len(lines)):
        fields = lines[i].strip().split(',')
        if ('[' in fields[1]):
          fields[1] = fields[1].replace('[', '').replace(']', '').split()
        existing.append(fields[1])
        mustReplace.append(fields[0])

  return existing, mustReplace

def binding(existing, mustReplace):
  print(f'> [article.binding] Double checking all article authors having a map...')
  count = 0
  for i in range(len(Article.articleDict)):
    articleObj = Article.getArticle(i)
    articleObj.authors = list(map(lambda x: x.replace('.', '').replace('-', '').replace('_', '').replace(' ', '').lower(), articleObj.authors))

    for j in range(len(articleObj.authors)):
      author = articleObj.authors[j]
      found = False

      for k in range(len(Author.authorDict)):
        identical = Author.getAuthor(k).meshname.strip() == author.strip()
        sim = similar(Author.getAuthor(k).meshname.strip(), author.strip()) > 0.85
        mappingExists = author.strip() in mustReplace

        if (identical or sim):
          found = True
          articleObj.authors[j] = Author.getAuthor(k).meshname
        elif (mappingExists):
          found = True
          articleObj.authors[j] = existing[mustReplace.index(author.strip())]
          continue
      if (not found):
        count += 1
    
  return count

def beginMapping(unmapped):
  if (len(unmapped) > 0):
    print(f'> [main] there are {len(unmapped)} unmapped authors.')
    print(f"> [main] type in 'start' to start mappping process...")
    usrInput = input('> [main] ')
    if (usrInput.strip() == 'start'):
      manualMapping(unmapped)
    else:
      exit(7)
  else: 
    print(f'> [main] There are 0 unmapped authors.')

def manualMapping(myLst):
  print("\033c", end="")
  mappings = []
  newAuthors = []
  running = True
  while(running):
    
    for i in range(len(myLst)):
      print("\033c", end="")
      print('[article-mapping-tool]\n')
      print(f'> is author {myLst[i]} an existing author?\n')
      print(f'  1. Yes, this is an existing author.')
      print(f'  2. No, this is not an existing author.')
      print(f'  3. This author is actually multiple authors.')
      print(f'  4. Skip for now.')
      print()
      choice = input('> ')
      if (choice == ''):
        choice = '4'

      try:
        match(int(choice.strip())):
          case 1:
            singleAuthor(myLst[i], mappings)
          case 2:
            createAuthor(newAuthors)
          case 3:  
            mapMultiple(myLst[i], newAuthors, mappings)
          case 4:
            continue
          case 5:
            running = False
            break
          case _:
            print('invalid')
            exit(7)
      except ValueError:
        break

  choice = input('> overwrite mapping files?')
  if (choice.strip() == '1'):
    with open('.\\output\\oldMappings.txt', 'w+', encoding='utf-8') as file:
      for i in mappings:
        file.write(str(i) + '\n')
    with open('.\\output\\newAuthorMappings.txt', 'w+', encoding='utf-8') as file:
      for i in newAuthors:
        file.write(str(i) + '\n')

def singleAuthor(itm, mappings):
  while True:
    singleAuthor = int(input('> Enter author number: ').strip())
    temp = Author.getAuthor(singleAuthor - 1)
    print(f'> Map {itm} to the Author {temp.firstName} {temp.lastName}?\n')
    print(f'  1. Yes')
    print(f'  2. No')
    print()
    confirmation = input('> ')
    try:
      match(int(confirmation.strip())):
        case 1:
          print('result: yes')
          mappings.append(f'{itm}, {temp.meshname}')
          break
        case 2:
          print("\033c")
          print('Aborted')
        case _:
          print("\033c")
          print('Invalid Input')
    except ValueError:
      print("\033c")
      print('Invalid Input')

def createAuthor(newAuthors): 
  while True:
    firstName = 'NO_FIRST'
    lastName = 'NO_LAST'
    email = 'NO_EMAIL'

    firstName = input('Enter first name: ').strip()
    lastName = input('Enter last name: ').strip()
    email = input('Enter email:').strip()

    if email == '':
      exit(7)


    print(f"id.{len(Author.authorDict) + 1} -> {firstName} {lastName}, {email}")
    print(f'> Create this author?\n')
    print(f'  1. Yes')
    print(f'  2. No')
    print()

    confirmation = input('> ')
    try:
      match(int(confirmation.strip())):
        case 1:
          print('result: yes')
          newAuthors.append(f'{firstName}, {lastName}, {email}')
          obj = Author(firstName, lastName, email)
          Author.visualize()
          break
        case 2:
            print("\033c")
            print('Aborted')
        case _:
          print("\033c")
          print('Invalid Input')
    except ValueError:
      print("\033c")
      print('Invalid Input')      

def mapMultiple(authorStr, newAuthors, mappings):
  print("\033c")
  multiple = []
  usrPrompt = f"Do we need to create any new authors for {authorStr}?"
  option = confirmationPrompt(usrPrompt)
  match(option):
    case 1:
      while True:
        createAuthor(newAuthors)
        option = confirmationPrompt(f'Are there any more authors we need to create?')
        if (option == 2):
          break 
        else:
          print('\033c')
  print('end match')
  print(f"New authors have been added to the session database. Make sure to add these new numbers to your following string: {multiple}")
  multipleAuthors = input('> Enter author numbers, separated by dashes: ').strip()
  tempLst = multipleAuthors.strip().split('-')
  aggregate = []
  for j in tempLst:
    itm = Author.getAuthor(int(j) - 1)
    print(f'{j} - {itm.firstName} {itm.lastName}')
    aggregate.append(itm.meshname)
  option = confirmationPrompt(f"map {authorStr} to {str(aggregate)}?")
  match(option):
    case 1:
      print('result: yes')
      mappings.append(f'{authorStr}, {str(aggregate)}')
    case 2:
      print('result: no')
  
def confirmationPrompt(prompt):
  while True:
    print(prompt)
    print(f'  1. Yes')
    print(f'  2. No')
    print()

    confirmation = input('> ')
    try:
      match(int(confirmation.strip())):
        case 1:
          return 1
        case 2:
          return 2
        case _:
          print("\033c")
          print('Invalid Input')
    except ValueError:
      print("\033c")
      print('Invalid Input')

