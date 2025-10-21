from Translator.Translator import Translator
from Translator.Article import Article
import os as OS
import json

class ArticleTranslator(Translator):  
  # Constructor
  def __init__(self, incomingData):
    super().__init__(incomingData)
    self.uniqueAuthorCleanNames = set()

    
  def translate(self):
    for i, item in enumerate(self.source):
      # create blank object, try to set data
      obj = Article()
      obj.setData(self.objCount, self.source[i])
      
      # handle title
      title = obj["title"]
      if (title is not None):
        obj["title"] = title.replace('"', '\\"')
      
      # tag object ->  
      obj.processTags()
      if (not obj.dataSanityCheck() or obj["tags"] == -1):
        continue
    
      self.objDataDict.update({obj["id"]: obj.data})
      self.uniqueAuthorCleanNames.update(obj["authorCleanNames"])
      self.objCount += 1


  def _visualize(self):
    with open('articles.json', 'w+', encoding='utf-8') as file:
      json.dump(self.objDataDict, file, indent=4)
      file.close()

  def _printUniqueAuthors(self):
    terminal_size = OS.get_terminal_size()
    names = sorted(list(self.uniqueAuthorCleanNames))
    longestName = len(max(names, key=len))
    columns = terminal_size.columns // longestName

    for i in range(len(names)):
      authorName = names[i]
      spaces = longestName - len(authorName)
      buf = (' ' * spaces) + authorName
      print(buf, end=' ')
      if (i + 1) % columns == 0:
        print()
    print('\n')

  

