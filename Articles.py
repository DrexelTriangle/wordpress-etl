from Utility import Utility as U
from Author import *
import os as OS
import re
import json

class Article:
  articleCount = 0
  articleDict = {}
  map = set()

  
  # Constructor
  def __init__(self, incomingData):
    self.data = {}
    self.data.update(incomingData)
    Article.articleDict.update({self.data["id"] : self.data})
    Article.articleCount += 1
  
  
  def processArticles(articleData):
    for i, item in enumerate(articleData):
      metaTags, data = [], Article._blankArticle()
      data = Article._setData(articleData[i])

      if (data["title"] is not None):
        data["title"] = data["title"].replace('"', '\\"')
      
      tagsObj = articleData[i].get('category')
      try:
        metaTags =  Article.processTags(tagsObj)
        if (metaTags == -1):
          continue 
        data["tags"] = metaTags[0]
        data["authors"] = metaTags[1]
      except TypeError:
        if (metaTags is None or data["text"] is None):
          continue
      
      if (Article._dataSanityCheck(data)):
        obj = Article(data)
    
  def __str__(self):
    result = ""
    for key, value in self.data.items():
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
      "id": Article.articleCount,
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
      # json.dump(Article.articleDict, file, indent=2)
      json.dump(Article.articleDict, file, indent=2)
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
          Article.map.add(cleanName)

    except KeyError:
      tags.append('NO_TAGS')

    tags.sort(reverse=True)
    result.append(tags)
    result.append(articleAuthors)
    return result


  



