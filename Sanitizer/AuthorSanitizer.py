import Utils.NLP as nlp
import re
from Translator.Author import Author
from Sanitizer import Sanitizer

class AuthorSanitizer(Sanitizer):
    def __init__(self, data: list, policies: dict, logDir: str, lastAuid: int):
        super().__init__(data, policies, logDir)
        self.lastAuid = lastAuid

    def normalizeData(self):
        multipleAuthorIndicators = ["-and-", " and ", " &amp; ", ","]
        for author in self.data[:]: # self.data[:] guards against editing list during iteration
            match author.data["display_name"]: # Catch Special Cases
                case "Jenna.M.Doka":
                    author.data["display_name"] = "Jenna M. Doka"
                    author.data["first_name"] = "Jenna M."
                    author.data["last_name"] = "Doka"
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

            if any(indicator in author.data["display_name"] for indicator in multipleAuthorIndicators):
                authors = nlp.cleanDocument(author.data["display_name"], "author_multiple")
                for name in authors:
                    newAuthor = Author(str(self.lastAuid+1), None, None, name, None, None)
                    self.data.append(newAuthor)
                    self.lastAuid += 1
                self.data.remove(author)
                continue
            else:
                author.data["display_name"] = nlp.cleanDocument(author.data["display_name"], "author_single")

            if author.data["first_name"] or author.data["last_name"] == None:
                name = re.split(" (?!.* )", author.data["display_name"])
                author.data["first_name"] = name[0]
                author.data["last_name"] = name[1]

        def autoResolve(self):
            authors = [nlp.cleanDocument(a.data["display_name"],"similarity") for a in self.data]
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