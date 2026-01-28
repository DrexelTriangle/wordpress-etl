import json
from Utils import NLP as nlp
import re
import os
from pathlib import Path
from Translator.Author import Author
from Animator import Animator
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.PolicyDict import PolicyDict
from Sanitizer.DiffChecker import DiffChecker

class AuthorSanitizer(Sanitizer):
    multipleAuthorIndicators = ["-and-", " and ", " &amp; ", ","]
    specialEdits = {
        "Jena.M.Doka": {"display_name": "Jenna M. Doka"},
        "Entertainment Desk": {"first_name": "A&E Desk", "last_name": None},
        "The Triangle Sports Desk": {"first_name": "The Triangle Sports Desk", "last_name": None},
        "The Triangle Alumni": {"first_name": "The Triangle Alumni", "last_name": None},
        "The Editorial Board": {"first_name": "The Editorial Board", "last_name": None},
        "Drexel for PILOTS": {"first_name": "Drexel for PILOTS", "last_name": None},
        "St. Christopher's Hospital for Children": {
            "first_name": "St. Christopher's Hospital for Children",
            "last_name": None,
        },
        "Granny &amp; Eloise": {
            "display_name": "Granny & Eloise",
            "first_name": "Granny & Eloise",
            "last_name": None,
        },
        "Granny  Eloise": {
            "display_name": "Granny & Eloise",
            "first_name": "Granny & Eloise",
            "last_name": None,
        },
    }
    specialFlags = {
        "Campus Election Engagement Project",
        "Op-Ed",
        "The Triangle News Desk",
    }
    banList = [
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
        "Tadmin",
        "None",
    ]

    def __init__(self, data: list, policies: PolicyDict):
        super().__init__(data, policies)
        self.lastAuid = int(data[-1].data["id"])
        self.conflictsCache = None
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

    def _normalizeData(self):
        for author in list(self.data):
            if author.data["display_name"] is None:
                displayName = self._buildDisplayName(author.data["first_name"], author.data["last_name"])
                if displayName is not None:
                    author.data["display_name"] = displayName
            special = False

            # check for special editing edge case
            updates = self.specialEdits.get(author.data["display_name"])
            if updates:
                author.data.update(updates)
                special = True
            elif author.data["display_name"] in self.specialFlags:
                special = True
            
            if special:
                self.priorityId.add(str(author.data.get("id")))
            if author.data["display_name"] is not None:
                # Check if author actually represents 2 authors
                if any(indicator in author.data["display_name"] for indicator in self.multipleAuthorIndicators):
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

                if author.data["first_name"] is None or author.data["last_name"] is None:
                    firstName, lastName = self._splitDisplayName(author.data["display_name"])
                    if firstName or lastName:
                        author.data["first_name"] = firstName
                        author.data["last_name"] = lastName

    def _merge(self, a: Author, b: Author):
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

        return Author(id, displayName, firstName, lastName, email, login)

    def _logChange(self, a: Author, b: Author):
        for change in self.changes:
            if change and change[-1].data.get("id") == a.data.get("id"):
                if change[-1].data.get("id") == b.data.get("id"):
                    return
                change.append(b)
                return
        if a.data.get("id") == b.data.get("id"):
            return
        self.changes.append([a, b])

    def _logSplitChange(self, a: Author, b: Author):
        if a.data.get("id") == b.data.get("id"):
            return
        self.changes.append([a, b])

    def _logConflict(self, a: Author, b: Author):
        self.conflicts.append([a, b])

    def _loadConflicts(self):
        if self.conflictsCache is not None:
            return self.conflictsCache
        conflictsPath = Path("logs") / "auth_conflicts.json"
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

    def _resolveFromConflicts(self, a: Author, b: Author):
        for entry in self._loadConflicts():
            if not entry:
                continue
            entryFirst = entry[0]
            entryFirstId = entryFirst.get("id") if isinstance(entryFirst, dict) else entryFirst.data.get("id")
            if entryFirstId not in {a.data.get("id"), b.data.get("id")}:
                continue
            canonical = entry[-1]
            if isinstance(canonical, dict):
                return Author(canonical.get("id"),
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

    def _manualResolve(self, disputes: list[tuple[Author, Author]], clear: bool = True):
        def _readChoice():
            try:
                if (os.name == "nt"):
                    import msvcrt
                    while True:
                        ch = msvcrt.getch()
                        if ch in (b"\x00", b"\xe0"):
                            code = msvcrt.getch()
                            if code == b"K":
                                return "RIGHT"
                            if code == b"M":
                                return "LEFT"
                        elif ch in (b"e", b"E"):
                            return "E"
                        elif ch in (b"l", b"L", b"\r", b"\n"):
                            return "LEFT"
                        elif ch in (b"r", b"R"):
                            return "RIGHT"
                else:
                    import sys
                    import termios
                    import tty
                    fd = sys.stdin.fileno()
                    old = termios.tcgetattr(fd)
                    try:
                        tty.setraw(fd)
                        ch = sys.stdin.read(1)
                        if ch == "\x1b":
                            seq = sys.stdin.read(2)
                            if seq == "[D":
                                return "RIGHT"
                            if seq == "[C":
                                return "LEFT"
                        elif ch in ("e", "E"):
                            return "E"
                        elif ch in ("l", "L", "\r", "\n"):
                            return "LEFT"
                        elif ch in ("r", "R"):
                            return "RIGHT"
                        elif ch in ("q", "Q"):
                            return "EXIT"
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass

        authors = []
        toRemove = []
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
                    choice = _readChoice()
                    if choice == "EXIT":
                        exit(7)
                    if choice in {"RIGHT", "LEFT"}:
                        authorParams[key] = right.get(key) if choice == "RIGHT" else left.get(key)
                        break
                    if choice == "E":
                        authorParams[key] = input("Value: ")
                        break
                    print("Input not recognized -- try again")

            canonical = Author(*(authorParams[key] for key in keys))
            self.priorityId.add(str(canonical.data.get("id")))
            authors.append(canonical)
            self._logChange(leftAuthor, canonical)
            self._logChange(rightAuthor, canonical)
            self._logConflict(leftAuthor, canonical)
            self._logConflict(rightAuthor, canonical)
        if toRemove:
            self.data = [author for author in self.data if author not in toRemove]
        self.data.extend(authors) 


    def sanitize(self, manualStart=None, manualEnd=None, clear: bool = True):
        self._normalizeData()
        flaggedAuthors = self._autoResolve()
        if flaggedAuthors and manualStart:
            manualStart()
        self._manualResolve(flaggedAuthors, clear=clear)
        if flaggedAuthors and manualEnd:
            manualEnd()
        self._autoResolve()
        self._log("auth_mappings", "auth_conflicts")
        return self.data
