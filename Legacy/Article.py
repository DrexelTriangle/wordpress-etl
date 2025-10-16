from newUtility import *
from Translator.Author import *
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
    self.priotity = False
    self.breakingNews = 'null'
    self.id = Article.articleCount
    self.title = title
    self.pubDate = pubDate
    self.modDate = modDate 
    self.description = description
    self.commentStatus = commentStatus
    self.tags = tags
    self.authors = authors
    self.text = text
    self.authorIDs = []
    self.featuredImgID = -1

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
    startColorCode = f"\033[38;2;255;234;0m"
    endColorCode = f"\033[0m"
    # print(f"{startColorCode}Error, no tags given{endColorCode}")
    result = []
    tags = []
    articleAuthors = []
    artifacts = []
    try:
      for i in range(len(myLst)):
        temp = myLst[i]
        if (temp.get('@nicename') == 'crossword'):
          return -1
        if (temp.get('@nicename') == 'comics'): #get these comics outta here
          return -1
        if (temp.get('@domain') == 'post_tag'):  
          tags.append(temp.get("#text"))
          ...
        if (temp.get('@domain') == 'author'):  
          aA = temp.get("#text").replace('.', '').replace('-', '').replace('_', '').replace(' ', '').lower()
          articleAuthors.append(temp.get("#text"))
          Article.map.append(aA)
          try:
            artifact = re.search(r"[^a-zA-Z\d\s:]", temp.get("#text")).group(0)
            if not(artifact in Article.artifacts):
              Article.artifacts.append(artifact)
          except AttributeError:
            continue
            ...
        # print(temp)
    except KeyError:
      tags.append('NO_TAGS')
        
    tags.sort(reverse=True)
    result.append(tags)
    result.append(articleAuthors)
    

    return result
      # print(tags)



    # for item in myLst:
    #     temp = [item.get("#text") if (item.get('@domain') == 'post_tag') else '' for item in myLst]
    #     temp.sort(reverse=True)
    #     return list(filter(lambda x: x != '', temp))   
    # ['.', '-', '_']

  def processArticles(articleData):
    # Insertion
    # Visualize

    for i, item in enumerate(articleData):
      title = '' #can never be none
      pubDate = '' #can never be none
      modDate = '' #can never be none. Can be in gmt / est
      description = '' #can be none
      comment_status = '' #can never be none
      priority = False
      breaking_news = False 
      metaTags = []
      tags = []
      authors = []
      photoCred = ''
      text = '' 


    
      articlePost = articleData[i]

      title = charMorph(articlePost.get('title'))
      if (title is not None):
        title = title.replace('"', '\\"')
      pubDate = articlePost.get('wp:post_date_gmt')
      modDate = articlePost.get('wp:post_modified_gmt')
      description = charMorph(articlePost.get('description'))
      comment_status = articlePost.get('wp:comment_status')
      text = str(charMorph(articlePost.get('content:encoded'))).replace('"', '\\"')
      photoCred = re.findall(r"(\/wp-content\/uploads\/.*\/)((.*)\.(jpg|png|jpeg))", text)

      try:
        metaTags =  Article.processTags(articlePost.get('category'))
        if (metaTags == -1):
          continue 
        tags = metaTags[0]
        authors = metaTags[1]
      except TypeError:
        if (metaTags is None or text is None):
          continue
      
      if (text != "None" and len(text) > 100 and title != None and not ('_' in title) and not ('sudoku' in title)):
        obj = Article(i, title,pubDate,modDate,description,comment_status, tags, authors, text)
  
        with open('.\\dumps\\temp.txt', 'a+', encoding='utf-8') as file:

          if (obj.text != "None"):
            result = ''
            result += f"{obj.title} -> {photoCred}\n"
            file.write(f"{result}")
            file.close()
    with open('.\\dumps\\temp.txt', 'a+', encoding='utf-8') as file: 
      file.write(f"\n\n{len(Article.articleDict)}")
      file.close()

  def SQLifiy():
    print("> [article.sqlify] writing SQL for articles...")
    with open('.\\output\\articles-sql.txt', "w+", encoding="utf-8") as file:
      for i in range(len(Article.articleDict)):
          itm = Article.getArticle(i)
          insertFields = 'article_id, title, pub_date, mod_date, description, priority, breaking_end_date, text, featured_img_id'
          insertValues = f'''{itm.id}, "{itm.title}", '{itm.pubDate}', '{itm.modDate}', "{itm.description}", {itm.priotity}, {itm.breakingNews}, "{itm.text}", {itm.featuredImgID}'''
          file.write(f"INSERT INTO tr_articles ({insertFields}) VALUES ({insertValues});\n")
      file.close()
    print("> [author.sqlify] done.")

