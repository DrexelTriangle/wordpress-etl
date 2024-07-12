from classes.wpArticle import *
from pprint import *

def writeArticlesToFile(fileLoc):
    with open(fileLoc, "w") as file:
        wpArticle.printArticles(fileLoc)
        file.close()

def visualizeDictionary(myDict, fileLoc):
    output = pformat(myDict)
    with open(fileLoc, 'w+') as file:
        file.write(output)
        file.close()

