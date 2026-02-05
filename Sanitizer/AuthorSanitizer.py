import json
from Utils import NLP as nlp
import re
from pathlib import Path
from Translator.Author import Author
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.Policy import Policy

class AuthorSanitizer(Sanitizer):
    def __init__(self, data: list, policies: PolicyDict, logDir: str = "./log"):
        super().__init__(data, policies, logDir)
        self.lastAuid = len(data) - 1

    # nlp implementation for similarity checking
    def _generateSigMatrix(self, authors):
        shingles = [nlp.generateKShingles(doc, 2) for doc in authors]
        vocab = nlp.generateVocab(shingles)
        sparseVectors = [nlp.generateSparseVector(s, vocab) for s in shingles]
        sparseMatrix = nlp.generateSparseMatrix(sparseVectors)
        params = nlp.generateKHashParameters(150, 2**31 - 1)
        return nlp.generateSignatureMatrix(sparseMatrix, vocab, params)

    # hard coded edge cases
    def _edgeCases(self, data):
        match data["display_name"]: # Catch Special Cases
            case "Entertainment Desk":
                data["first_name"] = "A&E Desk"
                data["last_name"] = None
            case "The Triangle Sports Desk":
                data["first_name"] = "The Triangle Sports Desk"
                data["last_name"] = None  
            case "The Triangle Alumni":
                data["first_name"] = "The Triangle Alumni"
                data["last_name"] = None
            case "The Editorial Board":
                data["first_name"] = "The Editorial Board"
                data["last_name"] = None
            case "Drexel for PILOTS":
                data["first_name"] = "Drexel for PILOTS"
                data["last_name"] = None
            case "St. Christopher's Hospital for Children":
                data["first_name"] = "St. Christopher's Hospital for Children"
                data["last_name"] = None
            case "Granny &amp; Eloise":
                data["display_name"] = "Granny & Eloise"
                data["first_name"] = "Granny & Eloise"
                data["last_name"] = None        
        return data
    


    def _normalizeData(self):
        multipleAuthorIndicators = ["-and-", " and ", " &amp; ", ","]

        for author in list(self.data):
            author.data = self._edgeCases(author.data)
            if author.data["display_name"] != None:
                # multiple authors case
                if any(indicator in author.data["display_name"] for indicator in multipleAuthorIndicators):
                    authors = nlp.cleanDocument(author.data["display_name"], "author_multiple")
                    for name in authors:
                        cleanedName = nlp.cleanDocument(name, "author_single")
                        firstName, lastName = self._splitDisplayName(cleanedName)
                        self.lastAuid += 1
                        newAuthor = Author(int(self.lastAuid), cleanedName, firstName, lastName, None, None)
                        self.data.append(newAuthor)
                        self._logSplitChange(author, newAuthor)
                    self.data.remove(author)
                    continue
                author.data["display_name"] = nlp.cleanDocument(author.data["display_name"], "author_single")

                # missing first/last name
                if author.data["first_name"] is None or author.data["last_name"] is None:
                    firstName, lastName = self._splitDisplayName(author.data["display_name"])
                    if firstName or lastName:
                        author.data["first_name"] = firstName
                        author.data["last_name"] = lastName

    def _mergeAuthors(a: Author, b: Author, auto: bool):
        # merges into a and deletes b, favors lengthier names by default, 
        # failure to resolve will return an error to be handled by authors into a manual resolve queue
        if auto is True:
            for field in a.data:
                if a.data[field] == b.data[field]:
                    pass

    def _logSplitChange(self, a: Author, b: Author):
        if a.data.get("id") == b.data.get("id"):
            return
        self.changes.append([a, b])

    def _autoResolve(self):
        authors = [nlp.cleanDocument(a.data["display_name"],"similarity") for a in self.data if a.data["display_name"] is not None]
        sigMatrix = self._generateSigMatrix(authors)

        # Similarity Checking
        print('Checking Similarities...')
        # print('\033[?25l')
        # for i in range(len(authors)):
        #     for j in range(i+1, len(authors)):
        #         sim = nlp.checkJaccardSignatureSimilarity(sigMatrix[:, i], sigMatrix[:, j])
        #         if (sim > 0.5):
        #             print("\x1b[1A\x1b[2K"*3)
        #             print(f"{authors[i]} vs {authors[j]}")
        #             print(f"Similarity: {round(sim, 4):.4f}")               
        # print('\033[?25h')

    def _loadConflicts(self):
        if self.conflictsCache is not None:
            return self.conflictsCache
        conflictsPath = Path("logs") / f"{self.type}_conflicts.json"
        if not conflictsPath.exists():
            self.conflictsCache = []
            return self.conflictsCache
        try:
            with conflictsPath.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            self.conflictsCache = []
            return self.conflictsCache
        conflicts = payload.get("conflicts", payload) if isinstance(payload, dict) else payload
        self.conflictsCache = conflicts if isinstance(conflicts, list) else []
        return self.conflictsCache

    def sanitize(self, manualStart=None, manualEnd=None, clear: bool = True):
        self._normalizeData()
        self.policies.conflicts = self._loadConflicts()
        flaggedAuthors = self.policies._autoResolve()
        self.data = self.policies.data
        if flaggedAuthors and manualStart:
            manualStart()
        self.policies._manualResolve(flaggedAuthors, clear=clear)
        self.data = self.policies.data
        if flaggedAuthors and manualEnd:
            manualEnd()
        self.policies._autoResolve()
        self.data = self.policies.data
        self.changes = self.policies.changes
        self.conflicts = self.policies.conflicts
        self._log(f"{self.type}_mappings", f"{self.type}_conflicts")
        return self.data
