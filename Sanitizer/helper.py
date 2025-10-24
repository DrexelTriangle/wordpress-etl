import re
import numpy as np
from joblib import Memory

memory = Memory("cache_dir", verbose=0)

def cleanDocument(document):
    document = re.sub("&amp;|\\W|_", "", document)
    document = document.lower()
    return document

@memory.cache
def generateKShingles(document, k):
    shingles = set()
    for i in range(len(document) - k + 1):
        shingles.add(document[i:i + k])
    return shingles

def generateVocab(shingleSets):
    vocab = set()
    for shingleSet in shingleSets:
        vocab = vocab.union(shingleSet)
    return vocab

@memory.cache
def generateSparseVector(shingleSet, vocab):
    vector = np.zeros(len(vocab))
    for i in range(len(vocab)):
        if vocab[i] is in shingleSet:
            vector[i] = 1
    return vector

@memory.cache
def generateDenseVector():
    pass

def checkCosineSimilarity(a, b):
    return np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))

#doc = "sa\0sa**sa&amp;saS#A$C___chi\tCn iXX%s tX^he[}\\| Xbest yay!"
#print(doc)
#clean = cleanDocument(doc)
#print(clean)
#print(generateKShingles(clean, 2))
