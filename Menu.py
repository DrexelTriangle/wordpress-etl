from Author import * 

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
            multipleAuthors = input('> Enter author numbers, separated by dashes: ').strip()
            tempLst = multipleAuthors.strip().split('-')
            for j in tempLst:
              itm = Author.getAuthor(int(j) - 1)
              print(f'{j} - {itm.firstName} {itm.lastName}')
            
            confirmation = input('> ')
            match(int(confirmation.strip())):
              case 0:
                print('result: yes')
                mappings.append(f'{myLst[i]}, {tempLst}')
              case 1:
                print('result: no')
          
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
        file.write(i)
    with open('.\\output\\newAuthorMappings.txt', 'w+', encoding='utf-8') as file:
      for i in newAuthors:
        file.write(i)

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