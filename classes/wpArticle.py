from progressBar import *
from utility import *

class wpArticle:
    articleCount = 0
    generic_articleDict = {}
    misc_articleDict = {}
    articleTemp = ''

    def __init__(self, id, title, pubDate, modDate, description, commentStatus, tags, authors, text):
        wpArticle.articleCount += 1
        self.priotity = False
        self.breakingNews = False
        self.id = id
        self.title = title
        self.pubDate = pubDate
        self.modDate = modDate 
        self.description = description
        self.commentStatus = commentStatus
        self.tags = tags
        self.authors = authors
        self.text = text

        wpArticle.generic_articleDict.update({self.id : self})


    def printArticles(file3_loc):
        print("┌── Writing Articles to File...")
    
        printProgressBar(0, len(list(wpArticle.generic_articleDict.keys())), length = 50)
        with open(file3_loc, "a", encoding="utf-8") as file:
            for i, item in enumerate(list(wpArticle.generic_articleDict.keys())):
                result = ''
                dict = wpArticle.generic_articleDict[i]
                result += f'''id: {dict.id}\n'''
                result += f'''title: {dict.title}\n'''
                result += f'''pubDate: {dict.pubDate}\n'''
                result += f'''modDate: {dict.modDate}\n''' 
                result += f'''description: {dict.description}\n'''
                result += f'''commentStatus: {dict.commentStatus}\n'''
                result += f'''tags: {dict.tags}\n'''
                result += f'''authors: {dict.authors}\n'''
                result += f'''text: \n\n{dict.text}\n\n'''
                result += f'''----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n'''
                wpArticle.articleTemp += result
                file.write(result)
            
                printProgressBar(i + 1, len(list(wpArticle.generic_articleDict.keys())), length = 50)
        file.close()   

def processArticles(articleData):
    title = '' #can never be none
    pubDate = '' #can never be none
    modDate = '' #can never be none. Can be in gmt / est
    description = '' #can be none
    comment_status = '' #can never be none
    priority = False
    breaking_news = False 
    tags = []
    authors = []
    text = '' 

    printProgressBar(0, len(articleData), length = 50)
    for i, item in enumerate(articleData):
        articlePost = articleData[i]

        title = charMorph(articlePost.get('title'))
        pubDate = articlePost.get('wp:post_date_gmt')
        modDate = articlePost.get('wp:post_modified_gmt')
        description = charMorph(articlePost.get('description'))
        comment_status = articlePost.get('wp:comment_status')
        metaTags =  processArticleTags(articlePost.get('category'))
        tags = metaTags[0]
        authors = metaTags[1]
        text = str(charMorph(articlePost.get('content:encoded')))
        objArt = wpArticle(i, title,pubDate,modDate,description,comment_status,tags, authors, text)


        printProgressBar(i + 1, len(articleData), length = 50)
    print()

