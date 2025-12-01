import re
import os
import numpy as np
import hashlib
from joblib import Memory
from numpy.typing import NDArray

cacheDirectory = os.path.join(".", "cacheDirectory") # Create persistent cache for efficient reruns of ETL pipeline
memory = Memory(cacheDirectory, verbose=0)

# Purges document of unwanted characters and ensures uniformity of text
def cleanDocument(document: str, type: str) -> str:
    def uppercaseMatch(match):
        return match.group(0).upper()
    match type:
        case "author_single":
            document = document.split("@")
            document = re.sub("&amp;", "&", document[0])
            document = re.sub("\\.(?=\\w\\w)", " ", document)
            document = re.sub("by-|By-|By |by |[^\\w ^'^\\.^-]|_|\\d", "", document).strip()
            document = re.sub("^\\w| \\w", uppercaseMatch, document)
            return document
        case "author_multiple":
            documents = re.split(r"&|&amp;|\band\b|,", document)
            for i in range(len(documents)):
                documents[i] = re.sub("by-|By-|By |by |[^\\w ]|_", "", documents[i]).strip()
            return documents
        case "similarity":
            return re.sub("[^\\w]| |\\d|_", "", document).lower()
        case "article":
            pass
        
# Generates slices (shingles) of text using a sliding window of size k
@memory.cache # Uses LRU to cache previous results and avoid re-running function
def generateKShingles(document: str, k: int) -> NDArray[np.int64]:
    return np.unique([int(hashlib.sha1(document[i:i + k].encode()).hexdigest(), 16) % (2**31 - 1) for i in range(len(document) - k + 1)]) # Uses deterministic hashing function to reduce overhead

# Creates a common vocab that is a set of every shingle present in all documents
def generateVocab(shingleSets: list[NDArray[np.int64]]) -> NDArray[np.int64]:
    return np.unique(np.concatenate(shingleSets)) # Uses numpy to reduce overhead

# Returns k hash parameters (a, b) where the number is between 1|0 and a large prime p
def generateKHashParameters(k: int, p: int) -> NDArray[np.int64]:
    np.random.seed(42) # Uses const seed to ensure determistic (cacheable) parameters
    a = np.random.randint(1, p, size=k, dtype=np.int64) # Generate k random a values
    b = np.random.randint(0, p, size=k, dtype=np.int64) # Generate k random b values
    return np.column_stack((a, b)) # Return an ndarray of a,b pairs

# Creates a vector that represents a document via its overlap with common vocab (see one-hot-encoding)
@memory.cache # Uses LRU to cache previous results and avoid re-running function
def generateSparseVector(shingleSet: NDArray[np.int64], vocab: NDArray[np.int64]) -> NDArray[np.uint8]:
    return np.isin(vocab, shingleSet).astype(np.uint8) # Uses numpy one-hot-encoding mask to reduce overhead

# Returns a matrix where each column is a document represented by a sparse vector
def generateSparseMatrix(sparseVectors: list[NDArray[np.uint8]]) -> NDArray[np.uint8]:
    return np.column_stack(sparseVectors)

# Generates a matrix of dense vectors through which similarity tests may be conducted
@memory.cache # Uses LRU to cache previous results and avoid re-running function
def generateSignatureMatrix(sparseMatrix: NDArray[np.uint8], vocab: NDArray[np.int64], hashParams: NDArray[np.int64], p: int = 2**31 -1) -> NDArray[np.float64]:
    nHashes = len(hashParams)
    nRows, nDocs = sparseMatrix.shape # nRows = shingles, nDocs = documents
    signatureMatrix = np.full((nHashes, nDocs), np.inf) # Creates a matrix where there is a row for each hash function and column for each document where every index is initialized to infinity
    for row in range(nRows):
        hashes = [(a * vocab[row] + b) % p for a, b in hashParams]
        for column in range(nDocs):
            if sparseMatrix[row, column] == 1:
                for i in range(nHashes):
                    signatureMatrix[i, column] = min(signatureMatrix[i, column], hashes[i])
    return signatureMatrix

# Calculates the Jaccard similarity of two documents represented by dense vectors (signatures) -- this is an estimation of the actually similariity
def checkJaccardSignatureSimilarity(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
    return float(np.mean(a == b))

# Calculates the Jaccard similarity of two documents represented as sparse vectors (one-hot-encodings) -- this is a fully accurate calculation of similarity
def checkJaccardSetSimilarity(a: set[int], b: set[int]) -> float:
    return len(a & b) / len(a | b)
