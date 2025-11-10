import re
import os
import numpy as np
import random
from joblib import Memory

cacheDirectory = os.path.join(".", "cacheDirectory")
memory = Memory(cacheDirectory, verbose=0)

# Purges document of unwanted characters and ensures uniformity of text
def cleanDocument(document: str) -> str:
    return re.sub("&amp;|\\W|_", "", document).lower()

# Generates slices of text using a sliding window of k size
@memory.cache # Uses LRU to cache previous results and avoid re-running function
def generateKShingles(document: str, k: int) -> set:
    return {document[i:i + k] for i in range(len(document) - k + 1)}

# Creates a common vocab that is a set of every shingle present in all documents
def generateVocab(shingleSets: list[set]) -> set:
    return set().union(*shingleSets)

# Returns k hash parameters (a, b) where the number is between 1 and a large prime p
def generateKHashParameters(k: int, p: int) -> list[tuple[int, int]]:
    return [((random.randint(1, p-1), random.randint(0, p-1))) for i in range(k)]

# Creates a vector that represents a document via its overlap with common vocab
@memory.cache # Uses LRU to cache previous results and avoid re-running function
def generateSparseVector(shingleSet: set, vocab: set) -> np.ndarray:
    vocab = sorted(vocab)
    return np.array([1 if i in shingleSet else 0 for i in vocab], dtype=int) 

def generateSparseMatrix(sparseVectors: list[np.ndarray]) -> np.ndarray:
    return np.column_stack((sparseMatrix, vector))

def hashRow(r: np.ndarray, a: int, b: int, p: int):


# Generates a matrix of dense vectors through which similarity tests may be conducted
@memory.cache # Uses LRU to cache previous results and avoid re-running function
def generateSignatureMatrix(sparseMatrix, hashParams: list[tuple[int, int]], p: int) -> np.ndarray:
    signatureMatrix = np.full(len(hashParams, len(sparseVectors), np.inf)
    for row in sparseMatrix:
        hashes = np.empty(len(hashParams))
        for param in hashParams:
            rowHash = hashRow(row, param[0], param[1], p)
        
        

# Calculates the cosine similarity of two documents represented by dense vectors (signatures)
def checkCosineSimilarity(a: np.ndarray, b: np.ndarray):
    return np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))

#TESTING
if __name__ == "__main__":
    doc = "sa\0sa**sa&amp;saS#A$C___chi\tCn iXX%s tX^he[}\\| Xbest yay!"
    print(doc)
    clean = cleanDocument(doc)
    print(clean)
    print(generateKShingles(clean, 2))
