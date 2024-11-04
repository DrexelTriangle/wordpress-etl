from Author import *

def dupAuthors(myLst):
  # grab data about duplicate authors
    with open('.\\stats\\duplicate-authors.csv', 'w+', encoding='utf-8') as file:
      file.write(f"first, last, email,\n")
      for dup in myLst:
        file.write(f"{dup[0]}, {dup[1]}, {dup[2]},\n")
      file.close()
    print("> [author.process-authors] wrote duplicate authors to \\stats\\duplicate-authors.csv")


def authorStats():
  noFirst, noLast, noEmail, normal = 0, 0, 0, 0
  isNoFirst, isNoLast, isNoEmail, isNormal = False, False, False, False

  with open('.\\stats\\authors-no-first-name.txt', 'w+', encoding='utf-8') as file_1, \
       open('.\\stats\\authors-no-last-name.txt', 'w+', encoding='utf-8') as file_2, \
       open('.\\stats\\authors-no-email.txt', 'w+', encoding='utf-8') as file_3, \
       open('.\\stats\\authors-normal.txt', 'w+', encoding='utf-8') as file_4:
    result = ''
    for i in range(len(Author.authorDict)):
      author = Author.getAuthor(i)
      isNoFirst = author.firstName == 'NO_FIRST'
      isNoLast = author.lastName == 'NO_LAST'
      isNoEmail = author.email == 'NO_EMAIL'
      isNormal = not(isNoFirst or isNoLast or isNoEmail)
      
      if isNoFirst:
        file_1.write(str(Author.getAuthor(i)))
        noFirst += 1

      if isNoLast:
        file_2.write(str(Author.getAuthor(i)))
        noLast += 1

      if isNoEmail:
        file_3.write(str(Author.getAuthor(i)))
        noEmail += 1
      
      if isNormal:
        file_4.write(str(Author.getAuthor(i)))
        normal += 1
          
    # print(f'> [author.process-authors] stats:')
    # if noFirst > 0:
    #    print(f'\t\t\t  {noFirst} with no first name')
    # if noLast > 0:
    #    print(f'\t\t\t  {noLast} with no last name')
    # if noEmail > 0:
    #    print(f'\t\t\t  {noEmail} with no email')
    # if normal > 0:
    #    print(f'\t\t\t  {normal} normal')
    # print(f'\t\t\t  {len(Author.authorDict)} total')

    file_1.close()
    file_2.close()
    file_3.close()
    file_4.close()
