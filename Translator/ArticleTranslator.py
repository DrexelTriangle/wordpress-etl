from Utility import Utility as U
from Translator.Translator import Translator
import os as OS
import re
import json
import sys

class ArticleTranslator(Translator):
  byteSize = 0
  articleCount = 0
  articleDict = {}
  map = set()

  
  # Constructor
  def __init__(self, incomingData):
    super().__init__(incomingData)
    self.source.update(incomingData)
    ArticleTranslator.articleDict.update({self.source["id"] : self.source})
    ArticleTranslator.articleCount += 1
  
  
  def translate(articleData):
    for i, item in enumerate(articleData):
      metaTags, data = [], ArticleTranslator._blankArticle()
      data = ArticleTranslator._setData(articleData[i])

      if (data["title"] is not None):
        data["title"] = data["title"].replace('"', '\\"')
      
      tagsObj = articleData[i].get('category')
      try:
        metaTags =  ArticleTranslator.processTags(tagsObj)
        if (metaTags == -1):
          continue 
        data["tags"] = metaTags[0]
        data["authors"] = metaTags[1]
      except TypeError:
        if (metaTags is None or data["text"] is None):
          continue
      
      if (ArticleTranslator._dataSanityCheck(data)):
        obj = ArticleTranslator(data)
        ArticleTranslator.byteSize += sys.getsizeof(obj)
    
  def __str__(self):
    result = ""
    for key, value in self.source.items():
      result += f"{key}: {value}\n"
    result += "\n"
    return result 
  


  def _dataSanityCheck(data):
    isTextNotNull = data["text"] != "None" and len(data["text"]) > 100 
    isTextNotSudoku = isTextNotNull and ('sudoku' not in data["text"])
    isTitleNotNull = data["title"] != None 
    isTitleNotUnderscore = isTitleNotNull and ('_' not in data["title"]) 

    return isTextNotSudoku and isTitleNotUnderscore

    
  def _blankArticle():
    return {
      "authorIDs": [],
      "authors": [],
      "breakingNews": False,
      "commentStatus": '',
      "description": '',
      "featuredImgID": -1,
      "id": -1,
      "priority": False,
      "modDate": '',
      "photoCred": '',
      "pubDate": '',
      "tags": [],
      "text": '',
      "title": '', 
    }

  def _setData(data:dict):
    return {
      "authorIDs": [], # for author/article linking (author<->linking)
      "authors": [],
      "breakingNews": False,
      "commentStatus": data.get('wp:comment_status'),
      "description": U._html_text_norm(data.get('description')),
      "featuredImgID": -1,
      "id": ArticleTranslator.articleCount,
      "priority": False,
      "modDate": data.get('wp:post_modified_gmt'),
      "photoCred": None,
      "pubDate": data.get('wp:post_date_gmt'),
      "tags": [],
      "text": str(U._html_text_norm(data.get('content:encoded'))).replace('"', '\\"'),
      "title": U._html_text_norm(data.get('title')), 
    }
   
  def _visualize():
    with open('articles.json', 'w+', encoding='utf-8') as file:
      # json.dump(ArticleTranslator.articleDict, file, indent=2)
      json.dump(ArticleTranslator.articleDict, file, indent=4)
      file.close()

  def processTags(myLst):
    result, tags, articleAuthors = [], [], []
    try:
      for i in range(len(myLst)):
        temp = myLst[i]
        nicename = temp.get("@nicename")
        domain = temp.get("@domain")
        text = temp.get("#text")


        if (nicename in {"crossword", "comics"}):
          return -1
        if (domain == "post_tag"):
          tags.append(text)
        elif (domain == "author"):
          cleanName = temp.get("#text").translate(str.maketrans('', '', '.-_ ')).lower()
          articleAuthors.append(temp.get("#text"))
          ArticleTranslator.map.add(cleanName)

    except KeyError:
      tags.append('NO_TAGS')

    tags.sort(reverse=True)
    result.append(tags)
    result.append(articleAuthors)
    return result


  



