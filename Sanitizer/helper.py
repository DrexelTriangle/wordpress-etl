import re

def cleanDocument(document):
    document = re.sub("&amp;|\\W|_", "", document)
    document = document.lower()
    return document

def generateKShingles(document, k):
    shingles = set()
    for i in range(len(document) - k + 1):
        shingles.add(document[i:i + k])
    return shingles

doc = "sa\0sa**sa&amp;saS#A$C___chi\tCn iXX%s tX^he[}\\| Xbest yay!"
print(doc)
clean = cleanDocument(doc)
print(clean)
print(generateKShingles(clean, 2))
