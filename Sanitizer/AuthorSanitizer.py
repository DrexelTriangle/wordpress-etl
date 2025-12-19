from Utils import NLP as nlp
import re
from Translator.Author import Author
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.PolicyDict import PolicyDict
from Sanitizer.DiffChecker import DiffChecker

class AuthorSanitizer(Sanitizer):
    def __init__(self, data: list, policies: PolicyDict, logDir: str = "./log"):
        super().__init__(data, policies, logDir)
        self.lastAuid = int(data[-1].data["id"])

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
                        newAuthor = Author(int(self.lastAuid), None, None, name, None, None)
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

    def _merge(self, a: Author, b: Author, sim):
        print(f"{a.data["display_name"]}, {b.data["display_name"]}, {sim}")

    def _flag(self, a: Author, b: Author, sim):
        print(f"{a.data["display_name"]}, {b.data["display_name"]}", {sim})

    def _autoResolve(self):
        banList = [ # Removed to bolster similarity checking
            "Editorial Board",
            "Campus Election Engagement Project",
            "Entertainment Desk",
            "Op-Ed",
            "The Triangle Sports Desk",
            "The Triangle News Desk",
            "Sadie Says",
            "The Pretentious Film Majors",
            "Granny  Eloise",
            "St. Christopher's Hospital For Children",
            "The Editorial Board",
            "Drexel For PILOTS",
            "The Triangle Alumni",
            "Campus Election Engagement Project",
            "Tadmin",
            "None",
        ]

        banListNormalized = {nlp.cleanDocument(name, "similarity") for name in banList}
        filteredAuthors = []
        bannedAuthors = []
        for author in self.data:
            name = author.data["display_name"]
            if name is None:
                bannedAuthors.append(author)
                continue
            nameNormalized = nlp.cleanDocument(name, "similarity")
            if nameNormalized in banListNormalized:
                bannedAuthors.append(author)
                continue
            filteredAuthors.append(author)

        authors = [nlp.cleanDocument(a.data["display_name"], "similarity") for a in filteredAuthors]
        authorsMeta = filteredAuthors

        diffChecker = DiffChecker(authors)
        for i in range(len(authors)):
            for j in range(i+1, len(authors)):
                sim = diffChecker.compare(i, j)
                if sim >= .9:
                    self._merge(authorsMeta[i], authorsMeta[j], sim)
                elif sim >= .8:
                    self._flag(authorsMeta[i], authorsMeta[j], sim)
                else:
                    self._flag(authorsMeta[i], authorsMeta[j], sim)

        self.data = filteredAuthors + bannedAuthors

    def _manualResolve(self):
        pass

    def sanitize(self):
        self._normalizeData()
        self._autoResolve()
