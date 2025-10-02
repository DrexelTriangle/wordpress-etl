from newUtility import *
from Author import *
import os as OS

class Article:
  articleCount = 0
  articleDict = {}
  articleTemp = ''
  artifacts = []
  map = []
  theoreticalCount = []

  def __init__(self, id, title, pubDate, modDate, description, commentStatus, tags, authors, text):
    Article.articleCount += 1
    self.data = {
      "authorIDs": [],
      "authors": authors,
      "breakingNews": 'null',
      "commentStatus": commentStatus,
      "description": description,
      "featuredImgID": -1,
      "id": Article.articleCount,
      "priority": False,
      "modDate": modDate,
      "pubDate": pubDate,
      "tags": tags,
      "text": text,
      "title": title, 
    }


    Article.articleDict.update({self.id : self})
    
  def __str__(self):
    result = ''
    result += f'id: {self.id}\n'
    result += f'\ttitle: {self.title}\n'
    result += f'\tpubDate: {self.pubDate}\n'
    result += f'\tmodDate: {self.modDate}\n'
    result += f'\tdescription: {self.description}\n'
    result += f'\tcommentStatus: {self.commentStatus}\n'
    result += f'\ttags: {self.tags}\n'
    result += f'\tauthors: {self.authors}\n'
    result += f'\ttext: \n\n{self.text}\n\n'
    
    return result 
    
  def getArticle(index):
    return Article.articleDict[index + 1]
    
  def visualize():
    print('> [article.visualize] visualizing articles')
    with open('.\\visualizations\\visualized-articles.txt', 'w+', encoding='utf-8') as file:
      result = ''
      for i in range(len(Article.articleDict)):
        file.write(str(Article.getArticle(i)))
      file.close()

  def processTags(myLst):
    result, tags, articleAuthors, artifacts = [], [], [], []
    try:
      for i in range(len(myLst)):
        temp = myLst[i]
        match(temp.get("@nicename")):
          case("crossword"):
            return -1
          case("comics"):  # get these comics outta here
            return -1
        match(temp.get('@domain')):
          case("post_tag"):
            tags.append(temp.get("#text"))
            break
          case("author"):
            aA = temp.get("#text").replace('.', '').replace('-', '').replace('_', '').replace(' ', '').lower()
            articleAuthors.append(temp.get("#text"))
            Article.map.append(aA)
            try:
              artifact = re.search(r"[^a-zA-Z\d\s:]", temp.get("#text")).group(0)
              if not(artifact in Article.artifacts):
                Article.artifacts.append(artifact)
            except AttributeError:
              continue
            break
    except KeyError:
      tags.append('NO_TAGS')
        
    tags.sort(reverse=True)
    result.append(tags)
    result.append(articleAuthors)
    

    return result


  def processArticles(articleData):
    blankArticleData = {
      "authorIDs": [],
      "authors": [],
      "breakingNews": False,
      "commentStatus": '',
      "description": '',
      "featuredImgID": -1,
      "id": Article.articleCount,
      "priority": False,
      "modDate": '',
      "photoCred": '',
      "pubDate": '',
      "tags": [],
      "text": '',
      "title": '', 
    }
    


    for i, item in enumerate(articleData):
      data = blankArticleData

      metaTags = []
      articlePost = articleData[i]

      data = {
        "authorIDs": [],
        "authors": [],
        "breakingNews": False,
        "commentStatus": articlePost.get('wp:comment_status'),
        "description": charMorph(articlePost.get('description')),
        "featuredImgID": -1,
        "id": Article.articleCount,
        "priority": False,
        "modDate": articlePost.get('wp:post_modified_gmt'),
        "photoCred": re.findall(r"(\/wp-content\/uploads\/.*\/)((.*)\.(jpg|png|jpeg))", text),
        "pubDate": pubDate = articlePost.get('wp:post_date_gmt'),
        "tags": [],
        "text": str(charMorph(articlePost.get('content:encoded'))).replace('"', '\\"'),
        "title": charMorph(articlePost.get('title')), 
      }




      if (data["title"] is not None):
        data["title"] = data["title"].replace('"', '\\"')
      
      tagsObj = articlePost.get('category')


      try:
        metaTags =  Article.processTags(tagsObj)
        if (metaTags == -1):
          continue 
        tags = metaTags[0]
        authors = metaTags[1]
      except TypeError:
        if (metaTags is None or data["text"] is None):
          continue
      
      if (data["text"] != "None" and len(data["text"]) > 100 and data["title"] != None and not ('_' in data["title"]) and not ('sudoku' in data["text"])):
        obj = Article(i, title,pubDate,modDate,description,comment_status, tags, authors, text)
  
        with open('.\\dumps\\temp.txt', 'a+', encoding='utf-8') as file:

          if (obj.text != "None"):
            result = ''
            result += f"{obj.title} -> {data["photoCred"]}\n"
            file.write(f"{result}")
            file.close()
    with open('.\\dumps\\temp.txt', 'a+', encoding='utf-8') as file: 
      file.write(f"\n\n{len(Article.articleDict)}")
      file.close()



