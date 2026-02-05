from Utils import NLP as nlp

class DiffChecker:
    def __init__(self, documents: list):
        self._documents = documents
        if not documents:
            self._sigMatrix = None
            return
        self._shingles = [nlp.generateKShingles(doc, 2) for doc in documents]
        self._vocab = nlp.generateVocab(self._shingles)
        self._sparseVectors = [nlp.generateSparseVector(s, self._vocab) for s in self._shingles]
        self._sparseMatrix = nlp.generateSparseMatrix(self._sparseVectors)
        self._params = nlp.generateKHashParameters(150, 2**31 - 1)
        self._sigMatrix = nlp.generateSignatureMatrix(self._sparseMatrix, self._vocab, self._params)

    def compare(self, docA: int, docB: int) -> float:
        if self._sigMatrix is None:
            return 0.0
        return round(nlp.checkJaccardSignatureSimilarity(self._sigMatrix[:, docA], self._sigMatrix[:, docB]), 4)
