from Utils import NLP as nlp
import re
from Translator.Author import Author
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.PolicyDict import PolicyDict

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
                        self.lastAuid += 1
                        newAuthor = Author(int(self.lastAuid+1), None, None, name, None, None)
                        self.data.append(newAuthor)
                    self.data.remove(author)
                    continue
                else:
                    author.data["display_name"] = nlp.cleanDocument(author.data["display_name"], "author_single")

                # missing first/last name
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

    def _manualResolve(self):
        pass

    def sanitize(self):
        self._normalizeData()
        self._autoResolve()