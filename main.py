from xmltodict import *
from newUtility import *
from Author import *
from Article import *
from json import *
import os as OS 
from Controller import XmlSetup
from Menu import *

# Setup
file1 = ".\\rawdata\\tri-wpdump_4-1-24.xml"
file2 = ".\\rawdata\\thetriangle.WordPress.2024-07-10.xml"
authorData, articleData, guestAuthorData = XmlSetup(file1, file2)

# Process Authors
Author.processAuthors(authorData)
Author.processGuestAuthors(guestAuthorData)

# Process Articles
Article.processArticles(articleData)

# TODO: Mending
print('> [main] author mapping.')
with open('result.txt', 'w+', encoding='utf-8') as file:
  longestStr = max(Article.map, key=len)
  unique = []
  unmapped = []
  names = []
  numbers = []

  existing = []
  mustReplace = []
  if (OS.path.isfile('.\\output\\newAuthorMappings.txt')):
    lines = []
    with open('.\\output\\newAuthorMappings.txt', 'r+', encoding='utf-8') as file2:
      lines = file2.readlines()
      for i in range(len(lines)):
        fields = lines[i].strip().split(',')
        obj = Author(fields[0], fields[1], fields[2])
        Author.visualize()
      file2.close()

  if (OS.path.isfile('.\\output\\oldMappings.txt')):
    lines = []
    with open('.\\output\\oldMappings.txt', 'r+', encoding='utf-8') as file2:
      lines = file2.readlines()
      for i in range(len(lines)):
        fields = lines[i].strip().split(',')
        if ('[' in fields[1]):
          fields[1] = fields[1].replace('[', '').replace(']', '').split()
        existing.append(fields[1])
        mustReplace.append(fields[0])

  for i in Article.map:
    dashes = '-' * (len(longestStr) - len(i) + 3)
    mapped = '' 
    for j in range(len(Author.authorDict)):
      obj = Author.getAuthor(j)
      # file.write(f'{i} {dashes} \n')
      identical = obj.meshname.strip() == i.strip()
      sim = similar(obj.meshname.strip(), i.strip()) > 0.85
      mappingExists = i.strip() in mustReplace

      if (identical or sim or mappingExists):
        mapped = obj.meshname
        break
      else:
        mapped = ''
        
    if not(i in unique):
      if (not identical) and sim and mapped != '':
        file.write(f'{i} {dashes} {mapped}*\n')
      if mapped == '':
        unmapped.append(i)
        file.write(f'{i} {dashes}\n')
     

      unique.append(i)

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
    print(f'> [main] Double checking all article authors having a map...')
  count = 0
  for i in range(len(Article.articleDict)):
    articleObj = Article.getArticle(i)
    articleObj.authors = list(map(lambda x: x.replace('.', '').replace('-', '').replace('_', '').replace(' ', '').lower(), articleObj.authors))
    for i in range(len(articleObj.authors)):
      author = articleObj.authors[i]
      found = False
      for k in range(len(Author.authorDict)):
        identical = Author.getAuthor(k).meshname.strip() == author.strip()
        sim = similar(Author.getAuthor(k).meshname.strip(), author.strip()) > 0.85
        mappingExists = author.strip() in mustReplace

        if (identical or sim):
          found = True
          articleObj.authors[i] = Author.getAuthor(k).meshname
        elif (mappingExists):
          found = True
          articleObj.authors[i] = existing[mustReplace.index(author.strip())]
          continue
      if (not found):
        count += 1
        # print(articleObj.authors)

  if (count == 0):
    print(f'> [main] All article authors have been locally mapped. Everything is accounted for!')

  Author.SQLifiy()
  Article.SQLifiy()

  file.close()

# TODO: SQLify Authors and Articles
print()



