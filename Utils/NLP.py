import re
import numpy as np
import hashlib
from functools import lru_cache
from joblib import Memory, hash as joblib_hash
from numpy.typing import NDArray
from pathlib import Path

cacheDirectory = Path(__file__).resolve().parent / "cacheDirectory" # Stable cache location across CWDs
memory = Memory(cacheDirectory, verbose=0)
_LRU_MAXSIZE = 128

class _ArrayKey:
    __slots__ = ("arr", "_hash")
    def __init__(self, arr: NDArray):
        self.arr = arr
        self._hash = joblib_hash(arr)
    def __hash__(self) -> int:
        return hash(self._hash)
    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ArrayKey) and self._hash == other._hash

# Precompiled regex patterns to avoid recompilation overhead on hot paths
_AMP_PATTERN = re.compile("&amp;")
_DOT_PATTERN = re.compile("\\.(?=\\w\\w)")
_AUTHOR_CLEAN_PATTERN = re.compile("^by-|^By-|^By |^by |[^\\w ^'^\\.^-]|_|\\d")
_AUTHOR_SPLIT_PATTERN = re.compile(r"&amp;|&|\\band\\b|,")
_SIMILARITY_PATTERN = re.compile("[^\\w]| |\\d|_")

# Purges document of unwanted characters and ensures uniformity of text
def cleanDocument(document: str, type: str) -> str:
    def uppercaseMatch(match):
        return match.group(0).upper()
    match type:
        case "author_single":
            document = document.split("@")
            document = _AMP_PATTERN.sub("&", document[0])
            document = _DOT_PATTERN.sub(" ", document)
            document = _AUTHOR_CLEAN_PATTERN.sub("", document).strip()
            document = re.sub("^\\w| \\w", uppercaseMatch, document)
            return document
        case "author_multiple":
            documents = _AUTHOR_SPLIT_PATTERN.split(document)
            return [_AUTHOR_CLEAN_PATTERN.sub("", doc).strip() for doc in documents]
        case "similarity":
            return _SIMILARITY_PATTERN.sub("", document).lower()
        case "article":
            return document
    return document
        
# Generates slices (shingles) of text using a sliding window of size k
@memory.cache # Disk cache for repeated runs
def _generateKShingles_impl(document: str, k: int) -> NDArray[np.int64]:
    if len(document) < k:
        return np.array([], dtype=np.int64)
    return np.unique([int(hashlib.sha1(document[i:i + k].encode()).hexdigest(), 16) % (2**31 - 1) for i in range(len(document) - k + 1)]) # Uses deterministic hashing function to reduce overhead

@lru_cache(maxsize=_LRU_MAXSIZE) # In-memory LRU for hot calls
def generateKShingles(document: str, k: int) -> NDArray[np.int64]:
    return _generateKShingles_impl(document, k)

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
@memory.cache # Disk cache for repeated runs
def _generateSparseVector_impl(shingleSet: NDArray[np.int64], vocab: NDArray[np.int64]) -> NDArray[np.uint8]:
    return np.isin(vocab, shingleSet, assume_unique=True).astype(np.uint8) # Uses numpy one-hot-encoding mask to reduce overhead

@lru_cache(maxsize=_LRU_MAXSIZE) # In-memory LRU for hot calls
def _generateSparseVector_lru(shingleKey: _ArrayKey, vocabKey: _ArrayKey) -> NDArray[np.uint8]:
    return _generateSparseVector_impl(shingleKey.arr, vocabKey.arr)

def generateSparseVector(shingleSet: NDArray[np.int64], vocab: NDArray[np.int64]) -> NDArray[np.uint8]:
    return _generateSparseVector_lru(_ArrayKey(shingleSet), _ArrayKey(vocab))

# Returns a matrix where each column is a document represented by a sparse vector
def generateSparseMatrix(sparseVectors: list[NDArray[np.uint8]]) -> NDArray[np.uint8]:
    return np.column_stack(sparseVectors)

# Generates a matrix of dense vectors through which similarity tests may be conducted
@memory.cache # Disk cache for repeated runs
def _generateSignatureMatrix_impl(sparseMatrix: NDArray[np.uint8], vocab: NDArray[np.int64], hashParams: NDArray[np.int64], p: int = 2**31 -1) -> NDArray[np.float64]:
    nHashes = len(hashParams)
    _, nDocs = sparseMatrix.shape # nRows = shingles, nDocs = documents
    signatureMatrix = np.full((nHashes, nDocs), np.inf) # Creates a matrix where there is a row for each hash function and column for each document where every index is initialized to infinity
    a = hashParams[:, 0][:, None]
    b = hashParams[:, 1][:, None]
    hashes = (a * vocab[None, :] + b) % p  # Precompute all hash values for each shingle
    sparseMask = sparseMatrix.astype(bool, copy=False)
    for column in range(nDocs):
        rows = sparseMask[:, column]
        if np.any(rows):
            signatureMatrix[:, column] = np.min(hashes[:, rows], axis=1)
    return signatureMatrix

@lru_cache(maxsize=_LRU_MAXSIZE) # In-memory LRU for hot calls
def _generateSignatureMatrix_lru(sparseKey: _ArrayKey, vocabKey: _ArrayKey, hashKey: _ArrayKey, p: int) -> NDArray[np.float64]:
    return _generateSignatureMatrix_impl(sparseKey.arr, vocabKey.arr, hashKey.arr, p)

def generateSignatureMatrix(sparseMatrix: NDArray[np.uint8], vocab: NDArray[np.int64], hashParams: NDArray[np.int64], p: int = 2**31 -1) -> NDArray[np.float64]:
    return _generateSignatureMatrix_lru(_ArrayKey(sparseMatrix), _ArrayKey(vocab), _ArrayKey(hashParams), p)

# Calculates the Jaccard similarity of two documents represented by dense vectors (signatures) -- this is an estimation of the actually similariity
def checkJaccardSignatureSimilarity(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
    return float(np.mean(a == b))

# Calculates the Jaccard similarity of two documents represented as sparse vectors (one-hot-encodings) -- this is a fully accurate calculation of similarity
def checkJaccardSetSimilarity(a: set[int], b: set[int]) -> float:
    return len(a & b) / len(a | b)
