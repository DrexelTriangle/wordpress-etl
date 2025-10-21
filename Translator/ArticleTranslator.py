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
      obj = Article()
      obj.setData(self.objCount, self.source[i])
      title = obj["title"]

      if (title is not None):
        obj["title"] = title.replace('"', '\\"')
      
      obj.processTags()
      if (obj["title"] is None or not obj.dataSanityCheck() or obj["tags"] == -1):
        continue
    
      self.objDataDict.update({obj["id"]: obj.data})
      self.uniqueAuthorCleanNames.update(obj["authorCleanNames"])
      self.objCount += 1

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

  



