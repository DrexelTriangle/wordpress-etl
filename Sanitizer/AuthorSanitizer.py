from Utils import NLP as nlp
import re
from Translator.Author import Author
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.PolicyDict import PolicyDict

class AuthorSanitizer(Sanitizer):
    def __init__(self, data: list, policies: PolicyDict, logDir: str = "./log"):
        super().__init__(data, policies, logDir)
        self.lastAuid = len(data) - 1

    def _normalizeData(self):
        multipleAuthorIndicators = ["-and-", " and ", " &amp; ", ","]

        for author in list(self.data):
            match author.data["display_name"]: # Catch Special Cases
                case "Jena.M.Doka":
                    author.data["display_name"] = "Jenna M. Doka"
                    continue
                case "Campus Election Engagement Project":
                    continue
                case "Op-Ed":
                    continue
                case "Entertainment Desk":
                    author.data["first_name"] = "A&E Desk"
                    author.data["last_name"] = None
                case "The Triangle Sports Desk":
                    author.data["first_name"] = "The Triangle Sports Desk"
                    author.data["last_name"] = None
                case "The Triangle News Desk":
                    continue
                case "The Triangle Alumni":
                    author.data["first_name"] = "The Triangle Alumni"
                    author.data["last_name"] = None
                case "The Editorial Board":
                    author.data["first_name"] = "The Editorial Board"
                    author.data["last_name"] = None
                case "Drexel for PILOTS":
                    author.data["first_name"] = "Drexel for PILOTS"
                    author.data["last_name"] = None
                case "St. Christopher's Hospital for Children":
                    author.data["first_name"] = "St. Christopher's Hospital for Children"
                    author.data["last_name"] = None
                case "tadmin":
                    pass
                case "Granny &amp; Eloise":
                    author.data["display_name"] = "Granny & Eloise"
                    author.data["first_name"] = "Granny & Eloise"
                    author.data["last_name"] = None
            if author.data["display_name"] != None:
                if any(indicator in author.data["display_name"] for indicator in multipleAuthorIndicators):
                    authors = nlp.cleanDocument(author.data["display_name"], "author_multiple")
                    for name in authors:
                        self.lastAuid += 1
                        newAuthor = Author(int(self.lastAuid+1), None, None, name, None, None)
                        self.data.append(newAuthor)
                    self.data.remove(author)
                    continue
                else:
                    author.data["display_name"] = nlp.cleanDocument(author.data["display_name"], "author_single")

                if author.data["first_name"] is None or author.data["last_name"] is None:
                    try:
                        name = re.split(" (?!.* )", author.data["display_name"])
                        author.data["first_name"] = name[0]
                        author.data["last_name"] = name[1]
                    except:
                        pass
            else:
                pass

    def _mergeAuthors(a: Author, b: Author, auto: bool):
        # merges into a and deletes b, favors lengthier names by default, 
        # failure to resolve will return an error to be handled by authors into a manual resolve queue
        if auto is True:
            for field in a.data:
                if a.data[field] == b.data[field]:
                    pass


    def _autoResolve(self):
        authors = [nlp.cleanDocument(a.data["display_name"],"similarity") for a in self.data if a.data["display_name"] is not None]
        shingles = [nlp.generateKShingles(doc, 2) for doc in authors]
        vocab = nlp.generateVocab(shingles)
        sparseVectors = [nlp.generateSparseVector(s, vocab) for s in shingles]
        sparseMatrix = nlp.generateSparseMatrix(sparseVectors)
        params = nlp.generateKHashParameters(150, 2**31 - 1)
        sigMatrix = nlp.generateSignatureMatrix(sparseMatrix, vocab, params)
        for i in range(len(authors)):
            for j in range(i+1, len(authors)):
                sim = nlp.checkJaccardSignatureSimilarity(sigMatrix[:, i], sigMatrix[:, j])
                print(f"{authors[i]} vs {authors[j]}")
                print("Similarity:", round(sim, 4))

    def _manualResolve(self):
        pass

    def sanitize(self):
        self._normalizeData()
        self._autoResolve()