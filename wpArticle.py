from progressBar import *
import time

class wpArticle:
    articleCount = 0
    generic_articleDict = {}
    misc_articleDict = {}
    articleTemp = ''

    def __init__(self, id, title, pubDate, modDate, description, commentStatus, tags, text):
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
                result += f'''text: \n\n{dict.text}\n\n'''
                result += f'''----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n'''
                wpArticle.articleTemp += result
                file.write(result)
            
                time.sleep(0.00001)
                printProgressBar(i + 1, len(list(wpArticle.generic_articleDict.keys())), length = 50)
        file.close()   



