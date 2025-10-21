from Utility import Utility as U
from Translator.Translator import Translator
from Translator.Article import Article
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


  def _log(self):
    # Log data into json
    with open('log\\articles.json', 'w+', encoding='utf-8') as file:
      json.dump(self.objDataDict, file, indent=4)
      file.close()


