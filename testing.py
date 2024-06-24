from classes.wpArticle import *

def writeArticlesToFile(fileLoc):
    with open(fileLoc, "w") as file:
        wpArticle.printArticles(fileLoc)
        file.close()