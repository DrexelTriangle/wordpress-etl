from Author import * 
from Article import *

def checkForUnmappedAuthors(mustReplace):
  # mapping: checks that every ArticleAuthor name exiists in the local database
  print('> [menu.mapping] author mapping.')
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

      if mapped == '':
        unmapped.append(i)
      unique.append(i)

  return unmapped
