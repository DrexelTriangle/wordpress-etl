from Translator.Translator import Translator
from Translator.Article import Article
import os as OS
from Utility import Utility as U

class ArticleTranslator(Translator):  
  # Constructor
  def __init__(self, incomingData):
    super().__init__(incomingData)
    self.uniqueAuthorCleanNames = set()

  def _getArticleData(self, data):
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
    text = str(U._html_text_norm(data.get('content:encoded', Article.defaultValue))).replace('"', '\\"')
    title = U._html_text_norm(data.get('title', Article.defaultValue))

    chunk1 = [authorIDs, authors, authorCleanNames]
    chunk2 = [breakingNews, commentStatus, description]
    chunk3 = [featuredImgID, id, priority, modDate]
    chunk4 = [photoCred, pubDate, tags, text, title]

    # return all article data as one contiguous list
    return [*chunk1, *chunk2, *chunk3, *chunk4]


  # NOTE: using to only load 9k of the article data
  def _shouldSkip(self, obj:Article):
    title = obj["title"]
    if (title is None or not obj.dataSanityCheck() or obj["tags"] == -1):
      return False 
    obj["title"] = title.replace('"', '\\"')
    return True


  def translate(self):
    for i, itm in enumerate(self.source):
      objData = self._getArticleData(itm)
      obj = Article(*objData)
      obj.processTags()
      # NOTE: using to only load 9k of the article data
      if self._shouldSkip(obj):
        continue
      else:
        self.objDataDict.update({obj["id"]: obj.data})
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

  



