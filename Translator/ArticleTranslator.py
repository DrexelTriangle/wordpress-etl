from Translator.Translator import Translator
from Translator.Article import Article
import os as OS
from Utils.Utility import Utility as U
import json

class ArticleTranslator(Translator):  
  # Constructor
  def __init__(self, incomingData):
    super().__init__(incomingData)
    self.uniqueAuthorCleanNames = set()

  def _getArticleData(self, data, noTextGrab=False):
    textData = ''
    
    if (noTextGrab):
      textData = 'TEST'
    else:
      textData = str(U._html_text_norm(data.get('content:encoded', Article.defaultValue))).replace('"', '\\"')
    
    authorIDs = []
    authors = []
    authorCleanNames = []
    breakingNews = False 
    commentStatus = data.get('wp:comment_status', Article.defaultValue)
    description = U._html_text_norm(data.get('description'))
    featuredImgID = -1
    id = self.objCount
    priority = False 
    modDate = data.get('wp:post_modified_gmt', Article.defaultValue),
    photoCred = None
    pubDate = data.get('wp:post_date_gmt', Article.defaultValue)
    tags = data.get('category')
    text = textData
    title = U._html_text_norm(data.get('title', Article.defaultValue))

    chunk1 = [authorIDs, authors, authorCleanNames]
    chunk2 = [breakingNews, commentStatus, description]
    chunk3 = [featuredImgID, id, priority, modDate]
    chunk4 = [photoCred, pubDate, tags, text, title]

    # return all article data as one contiguous list
    data = [*chunk1, *chunk2, *chunk3, *chunk4]
    return Article(*data)


  # NOTE: using to only load 9k of the article data
  def _shouldSkip(self, obj:Article, debugMode):
    title = obj["title"]
    if (title is None or not obj.dataSanityCheck(debugMode) or obj["tags"] == -1):
      return True 
    obj["title"] = title.replace('"', '\\"')
    return False


  def translate(self):
    debugMode = False
    for i, itm in enumerate(self.source):
      obj = self._getArticleData(itm, debugMode)
      obj.processTags()
      # NOTE: using to only load 9k of the article data
      if self._shouldSkip(obj, debugMode):
        continue
      else:
        self.addObject(obj)


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
  
  def _log(self, fileDestination):                      
    fileBuckets = []
    dictLen = len(self.objDataDict)
    remainder = dictLen % 1000
    bucketNum = (dictLen // 1000) + (1 if (remainder > 0) else 0)
    if not (OS.path.isdir(fileDestination)):
      OS.makedirs(fileDestination)

    for i in range(bucketNum):
      fileBuckets.append({})
    
    for i, itm in enumerate(self.objDataDict):
      bucket = i // 1000
      fileBuckets[bucket].update({i: self.objDataDict[i]})
    
    for i in range(len(fileBuckets)):
      bucket = fileBuckets[i]
      with open(f"{fileDestination}\\{i}.json", 'w+', encoding='utf-8') as file:
        json.dump(bucket, file, indent=4)
        file.close()


 


  



