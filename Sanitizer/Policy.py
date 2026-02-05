import re
from Utils import NLP as nlp
from Utils.Utility import Utility
from Translator.Author import Author
from Translator.GuestAuthor import GuestAuthor
from Animator import Animator
from Sanitizer.DiffChecker import DiffChecker

class Policy():
    def __init__(self,
                 specialEdits: dict[str, dict[str, str]],
                 specialFlags: dict[str],
                 banList: list[str],
                 data: list,
                 isAuthor: bool,
                 multipleAuthorIndicators: list[str] = ["-and-", " and ", " &amp; ", ","]
                ):
        self.specialEdits = specialEdits
        self.specialFlags = specialFlags
        self.banList = banList
        self.data = data
        self.isAuthor = isAuthor
        self.multipleAuthorIndicators = multipleAuthorIndicators
        
        self.changes = []
        self.conflicts = []
        self.priorityId = set()

    @staticmethod
    def _buildDisplayName(firstName, lastName):
        nameParts = list(filter(None, (firstName, lastName)))
        return " ".join(nameParts) if nameParts else None
    
    @staticmethod
    def _splitDisplayName(displayName):
        try:
            firstName, lastName = re.split(" (?!.* )", displayName)
            return firstName, lastName
        except ValueError:
            return None, None
        
    def _merge(self, a, b):

        aPriority = str(a.data.get("id")) in self.priorityId
        bPriority = str(b.data.get("id")) in self.priorityId

        primary, secondary = (a, b) if aPriority else (b, a) if bPriority else (a, b)

        if aPriority or bPriority:
            id = primary.data.get("id")
            displayName = primary.data.get("display_name") or secondary.data.get("display_name")
            firstName = primary.data.get("first_name") or secondary.data.get("first_name") or None
            lastName = primary.data.get("last_name") or secondary.data.get("last_name") or None
            email = primary.data.get("email") or secondary.data.get("email")
            login = primary.data.get("login") or secondary.data.get("login")
        else:
            email = a.data["email"] or b.data["email"]
            id = min(a.data["id"], b.data["id"])
            aHasFullName = bool(a.data["first_name"]) and bool(a.data["last_name"])
            bHasFullName = bool(b.data["first_name"]) and bool(b.data["last_name"])
            
            if aHasFullName or bHasFullName:
                preferA = aHasFullName and (not bHasFullName or a.data["id"] <= b.data["id"])
                source = a if preferA else b
                firstName = source.data["first_name"]
                lastName = source.data["last_name"]
            else:
                firstName = a.data["first_name"] or b.data["first_name"] or None
                lastName = a.data["last_name"] or b.data["last_name"] or None

            displayName = a.data["display_name"] or b.data["display_name"]
            login = a.data["login"] or b.data["login"]

        if self.isAuthor:
            return Author(id, displayName, firstName, lastName, email, login)
        else:
            return GuestAuthor(id, displayName, firstName, lastName, email, login)
        
    def _resolveFromConflicts(self, a, b):

        for entry in self.conflicts:
            if not entry:
                continue
            entryFirst = entry[0]
            entryFirstId = entryFirst.get("id") if isinstance(entryFirst, dict) else entryFirst.data.get("id")
            if entryFirstId not in {a.data.get("id"), b.data.get("id")}:
                continue
            canonical = entry[-1]
            if isinstance(canonical, dict):
                if self.isAuthor:
                    return Author(canonical.get("id"),
                        canonical.get("display_name"),
                        canonical.get("first_name"),
                        canonical.get("last_name"),
                        canonical.get("email"),
                        canonical.get("login"),
                    )
                else:
                    return GuestAuthor(canonical.get("id"),
                        canonical.get("display_name"),
                        canonical.get("first_name"),
                        canonical.get("last_name"),
                        canonical.get("email"),
                        canonical.get("login"),
                    )
            return canonical
        return None
    
    def _autoResolve(self):
        banListNormalized = {nlp.cleanDocument(name, "similarity") for name in self.banList}
        filteredAuthors, bannedAuthors, flaggedAuthors = [], [], []
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
        authorsMeta = list(filteredAuthors)

        diffChecker = DiffChecker(authors)
        keep = [True] * len(authorsMeta)
        canonicals = []
        for i in range(len(authors)):
            if not keep[i]:
                continue
            canonical = authorsMeta[i]
            mergedAny = False
            for j in range(i+1, len(authors)):
                if not keep[j]:
                    continue
                sim = diffChecker.compare(i, j)
                if sim >= .9:
                    canonical = self._merge(canonical, authorsMeta[j])
                    self._logChange(authorsMeta[j], canonical)
                    keep[j] = False
                    mergedAny = True
                elif sim >= .8:
                    flaggedAuthors.append((authorsMeta[i], authorsMeta[j]))
            if mergedAny:
                keep[i] = False
                canonicals.append(canonical)

        filteredAuthors = [authorsMeta[i] for i in range(len(authorsMeta)) if keep[i]]
        self.data = filteredAuthors + canonicals + bannedAuthors
        return flaggedAuthors
    
    def _manualResolve(self, disputes: list, clear: bool = True):
        authors, toRemove = [], []

        for i, dispute in enumerate(disputes):
            authorParams = {}
            leftAuthor = dispute[0]
            rightAuthor = dispute[1]
            toRemove.extend([leftAuthor, rightAuthor])
            canonical = self._resolveFromConflicts(leftAuthor, rightAuthor)
            if canonical:
                authors.append(canonical)
                self._logChange(leftAuthor, canonical)
                self._logChange(rightAuthor, canonical)
                continue
            left = leftAuthor.data
            right = rightAuthor.data
            keys = ["id", "display_name", "first_name", "last_name", "email", "login"]

            diffs = []
            for key in keys:
                lval = "" if left.get(key) is None else str(left.get(key))
                rval = "" if right.get(key) is None else str(right.get(key))
                if lval == rval:
                    authorParams[key] = left.get(key)
                else:
                    diffs.append((key, lval, rval))

            for key, lval, rval in diffs:
                Animator._renderTable(
                    key,
                    diffs,
                    authorParams,
                    left,
                    right,
                    clear,
                    i,
                    len(disputes),
                )
                while True:
                    choice = Utility._readChoice()
                    if choice in {"RIGHT", "LEFT"}:
                        authorParams[key] = right.get(key) if choice == "RIGHT" else left.get(key)
                        break
                    if choice == "E":
                        authorParams[key] = input("Value: ")
                        break
                    print("Input not recognized -- try again")

            canonical = Author(*(authorParams[key] for key in keys)) if self.isAuthor else GuestAuthor(*(authorParams[key] for key in keys))
            self.priorityId.add(str(canonical.data.get("id")))
            authors.append(canonical)
            self._logChange(leftAuthor, canonical)
            self._logChange(rightAuthor, canonical)
            self._logConflict(leftAuthor, canonical)
            self._logConflict(rightAuthor, canonical)
        if toRemove:
            self.data = [author for author in self.data if author not in toRemove]
        self.data.extend(authors) 

    def _logChange(self, a, b):
        for change in self.changes:
            if change and change[-1].data.get("id") == a.data.get("id"):
                if change[-1].data.get("id") == b.data.get("id"):
                    return
                change.append(b)
                return
        if a.data.get("id") == b.data.get("id"):
            return
        self.changes.append([a, b])

    def _logConflict(self, a, b):
        self.conflicts.append([a, b])