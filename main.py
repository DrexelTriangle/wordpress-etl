from xmltodict import *
from newUtility import *
from Author import *
from Article import *
from json import *
import os as OS 
from Controller import parseDictionary, dictQuery, dataDumping

def XmlSetup(wp_postsExportFile, wp_guestAuthorsExportFile):
    wpPostsDict, wpGuestAuthorsDict, authorData, articleData = {}, {}, {}, {}

    # Grab XML Content, convert to dictionary, grab author & article data  
    print("Converting Posts XML to Dictionary...")
    
    wpPostsDict = parseDictionary(wp_postsExportFile)
    wpGuestAuthorsDict = parseDictionary(wp_guestAuthorsExportFile)

    authorData = dictQuery(wpPostsDict, ['rss', 'channel', 'wp:author'])
    articleData = dictQuery(wpPostsDict, ['rss', 'channel', 'item'])
    guestAuthorData = dictQuery(wpGuestAuthorsDict, ['rss', 'channel', 'item'])

    print("> [xml-setup] Visualizing author dictionary...")
    visualizeDictionary(authorData, '.\\visualizations\\author-data.json')
    
    dataDumping(authorData, 'author-data.json')
    dataDumping(authorData, 'guest-author-data.json')
    dataDumping(authorData, 'article-data.json')

    print("> [xml-setup]: done.")
    return [authorData, articleData, guestAuthorData]


file1 = ".\\rawdata\\tri-wpdump_4-1-24.xml"
file2 = ".\\rawdata\\thetriangle.WordPress.2024-07-10.xml"
authorData, articleData, guestAuthorData = XmlSetup(file1, file2)


# # TODO: visualize dictionaries

# Process Authors
Author.processAuthors(authorData)
Author.processGuestAuthors(guestAuthorData)
Author.SQLifiy()

# TODO: Process the guest authors
# TODO: add a report file for the authors grabbed from the 

Article.processArticles(articleData)

print('> [main] author mapping.')
with open('result.txt', 'w+', encoding='utf-8') as file:
  longestStr = max(Article.map, key=len)
  unique = []
  unmapped = []
  names = []
  numbers = []
  if (OS.path.isfile('.\\output\\oldMappings.txt')):
    lines = []
    
    with open('.\\output\\oldMappings.txt', 'r+', encoding='utf-8') as file2:
      lines = file2.readlines()
      for i in range(len(lines)):
        temp = lines[i].strip().split(', ')
        temp[1] = int(temp[1])
        lines[i] = temp
        names.append(temp[0])
        numbers.append(temp[1])
      file2.close()
    for i in range(len(lines)):
      author = Author.getAuthor(lines[i][1] - 1)
      fName, lName = '', ''

      if (author.firstName == None):
        fName = ''
      else:
        fName = author.firstName
      
      if (author.lastName == None):
        lName = ''
      else:
        lName = author.lastName
      dsp = fName + ' ' + lName
      # print(dsp)

  for i in Article.map:
    dashes = '-' * (len(longestStr) - len(i) + 3)
    mapped = '' 
    for j in range(len(Author.authorDict)):
      obj = Author.getAuthor(j)
      # file.write(f'{i} {dashes} \n')
      identical = obj.meshname.strip() == i.strip()
      sim = similar(obj.meshname.strip(), i.strip()) > 0.85
      mappingExists = i.strip() in names

      if mappingExists:
        index = names.index(i.strip())
        numberMapping = numbers[index] - 1
        obj = Author.getAuthor(numberMapping)

      if (identical or sim or mappingExists):
        mapped = obj.meshname
        break
      
      else:
        mapped = ''
    if not(i in unique):
      if (not identical) and similar and mapped != '':
        file.write(f'{i} {dashes} {mapped}*\n')
      if mapped == '':
        unmapped.append(i)
        file.write(f'{i} {dashes}\n')
     

      unique.append(i)

  print(f'> [main] there are {len(unmapped)} unmapped authors.')
  print(f"> [main] type in 'start' to start mappping process...")
  usrInput = input('> [main] ')
  if (usrInput.strip() == 'start'):
    Article.manualMapping(unmapped)
  else:
    exit(7)

  file.close()

print()



