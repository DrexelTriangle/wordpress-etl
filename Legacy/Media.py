'''The Plan
    1. Create the Media Class
    2. Parse through the dump, check to see if the article has a file link to it
    3. If it does, create a new article class and write an sql statement for it, place it inside a file
        a) The things the media file needs is a 
        media_id -> autoincrement
        file_path -> name
        source -> source (If photocredit is null then source is populated)
        description -> description
        photo_cred_id -> photo_credit_id (We could make a list for this with all the photographers we grab each unique photographer from the metadata)
    4. If it doesn't, skip it
'''

from newUtility import *
from Translator.Author import *
import os as OS

class Media:
  mediaCount = 0
  mediaDict = {}

  def __init__(self, media_id, file_path, source, description, photo_cred_id):
    Media.mediaCount += 1
    self.media_id = Media.mediaCount
    self.file_path = file_path
    self.source = source    
    self.description = description
    self.photo_cred_id = photo_cred_id
   

    Media.mediaDict.update({self.media_id : self})
    
  def __str__(self):
    result = ''
    result += f'id: {self.media_id}\n'
    result += f'\tfile_path: {self.file_path}\n'
    result += f'\tsource: {self.source}\n'
    result += f'\tdescription: {self.description}\n'
    result += f'\tphoto_cred_id: {self.photo_cred_id}\n'
    
    return result 
    
  def getArticle(index):
    return Media.articleDict[index + 1]
    
  def visualize():
    print('> [article.visualize] visualizing articles')
    with open('.\\visualizations\\visualized-articles.txt', 'w+', encoding='utf-8') as file:
      result = ''
      for i in range(len(Media.articleDict)):
        file.write(str(Media.getArticle(i)))
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
        if (temp.get('@domain') == 'post_tag'):  
          tags.append(temp.get("#text"))
          ...
        if (temp.get('@domain') == 'author'):  
          aA = temp.get("#text").replace('.', '').replace('-', '').replace('_', '').replace(' ', '').lower()
          articleAuthors.append(temp.get("#text"))
          Media.map.append(aA)
          try:
            artifact = re.search(r"[^a-zA-Z\d\s:]", temp.get("#text")).group(0)
            if not(artifact in Media.artifacts):
              Media.artifacts.append(artifact)
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
    text = '' 


    for i, item in enumerate(articleData):
      articlePost = articleData[i]

      title = charMorph(articlePost.get('title'))
      if (title is not None):
        title = title.replace('"', '\\"')
      pubDate = articlePost.get('wp:post_date_gmt')
      modDate = articlePost.get('wp:post_modified_gmt')
      description = charMorph(articlePost.get('description'))
      comment_status = articlePost.get('wp:comment_status')
      text = str(charMorph(articlePost.get('content:encoded'))).replace('"', '\\"')
      try:
        metaTags =  Media.processTags(articlePost.get('category'))
        tags = metaTags[0]
        authors = metaTags[1]
      except TypeError:
        if (metaTags is None or text is None):
          continue
      
      obj = Media(i, title,pubDate,modDate,description,comment_status, tags, authors, text)
  
  def SQLifiy():
    print("> [article.sqlify] writing SQL for articles...")
    with open('.\\output\\articles-sql.txt', "w+", encoding="utf-8") as file:
      for i in range(len(Media.articleDict)):
          itm = Media.getArticle(i)
          insertFields = 'article_id, title, pub_date, mod_date, description, priority, breaking_end_date, text, featured_img_id'
          insertValues = f'''{itm.id}, "{itm.title}", '{itm.pubDate}', '{itm.modDate}', "{itm.description}", {itm.priotity}, {itm.breakingNews}, "{itm.text}", {itm.featuredImgID}'''
          file.write(f"INSERT INTO tr_articles ({insertFields}) VALUES ({insertValues});\n")
      file.close()
    print("> [author.sqlify] done.")

