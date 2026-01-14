import json
from Utils import NLP as nlp
import re
import os
from Translator.Author import Author
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.PolicyDict import PolicyDict
from Sanitizer.DiffChecker import DiffChecker

class AuthorSanitizer(Sanitizer):
    def __init__(self, data: list, policies: PolicyDict):
        super().__init__(data, policies)
        self.lastAuid = int(data[-1].data["id"])
        self._conflicts_cache = None
        self._manual_ids = set()
        self._sticky_ids = set()

    def _normalizeData(self):
        multipleAuthorIndicators = ["-and-", " and ", " &amp; ", ","]
        for author in list(self.data):
            if author.data["display_name"] is None:
                name_parts = [part for part in [author.data["first_name"], author.data["last_name"]] if part]
                if name_parts:
                    author.data["display_name"] = " ".join(name_parts)
            special_case_matched = False
            match author.data["display_name"]: # Catch Special Cases
                case "Jena.M.Doka":
                    author.data["display_name"] = "Jenna M. Doka"
                    special_case_matched = True
                case "Campus Election Engagement Project":
                    special_case_matched = True
                case "Op-Ed":
                    special_case_matched = True
                case "Entertainment Desk":
                    author.data["first_name"] = "A&E Desk"
                    author.data["last_name"] = None
                    special_case_matched = True
                case "The Triangle Sports Desk":
                    author.data["first_name"] = "The Triangle Sports Desk"
                    author.data["last_name"] = None
                    special_case_matched = True
                case "The Triangle News Desk":
                    special_case_matched = True
                case "The Triangle Alumni":
                    author.data["first_name"] = "The Triangle Alumni"
                    author.data["last_name"] = None
                    special_case_matched = True
                case "The Editorial Board":
                    author.data["first_name"] = "The Editorial Board"
                    author.data["last_name"] = None
                    special_case_matched = True
                case "Drexel for PILOTS":
                    author.data["first_name"] = "Drexel for PILOTS"
                    author.data["last_name"] = None
                    special_case_matched = True
                case "St. Christopher's Hospital for Children":
                    author.data["first_name"] = "St. Christopher's Hospital for Children"
                    author.data["last_name"] = None
                    special_case_matched = True
                case "tadmin":
                    pass
                case "Granny &amp; Eloise":
                    author.data["display_name"] = "Granny & Eloise"
                    author.data["first_name"] = "Granny & Eloise"
                    author.data["last_name"] = None
                    special_case_matched = True
                case "Granny  Eloise":
                    author.data["display_name"] = "Granny & Eloise"
                    author.data["first_name"] = "Granny & Eloise"
                    author.data["last_name"] = None
                    special_case_matched = True
            if special_case_matched:
                self._sticky_ids.add(str(author.data.get("id")))
            if author.data["display_name"] != None:
                if any(indicator in author.data["display_name"] for indicator in multipleAuthorIndicators):
                    authors = nlp.cleanDocument(author.data["display_name"], "author_multiple")
                    for name in authors:
                        cleanedName = nlp.cleanDocument(name, "author_single")
                        firstName = None
                        lastName = None
                        try:
                            splitName = re.split(" (?!.* )", cleanedName)
                            firstName = splitName[0]
                            lastName = splitName[1]
                        except:
                            pass
                        self.lastAuid += 1
                        newAuthor = Author(int(self.lastAuid), cleanedName, firstName, lastName, None, None)
                        self.data.append(newAuthor)
                        self._logSplitChange(author, newAuthor)
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

    def _merge(self, a: Author, b: Author):
        a_id = str(a.data.get("id"))
        b_id = str(b.data.get("id"))
        a_manual = a_id in self._manual_ids
        b_manual = b_id in self._manual_ids
        a_sticky = a_id in self._sticky_ids
        b_sticky = b_id in self._sticky_ids

        if (a_manual or a_sticky) and not (b_manual or b_sticky):
            primary = a
            secondary = b
        elif (b_manual or b_sticky) and not (a_manual or a_sticky):
            primary = b
            secondary = a
        else:
            primary = a
            secondary = b

        if a_manual or b_manual or a_sticky or b_sticky:
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
            
            if aHasFullName and bHasFullName:
                useA = a.data["id"] <= b.data["id"]
                firstName = a.data["first_name"] if useA else b.data["first_name"]
                lastName = a.data["last_name"] if useA else b.data["last_name"]
            elif aHasFullName and (not bHasFullName):
                firstName = a.data["first_name"]
                lastName = a.data["last_name"]
            elif bHasFullName and (not aHasFullName):
                firstName = b.data["first_name"]
                lastName = b.data["last_name"]
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

    def _loadConflictsFromFile(self):
        if self._conflicts_cache is not None:
            return self._conflicts_cache
        log_dir = "./logs"
        conflicts_path = os.path.join(log_dir, "conflicts.json")
        if not os.path.exists(conflicts_path):
            self._conflicts_cache = []
            return self._conflicts_cache
        try:
            with open(conflicts_path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            self._conflicts_cache = []
            return self._conflicts_cache
        conflicts = payload.get("conflicts", payload) if isinstance(payload, dict) else payload
        self._conflicts_cache = conflicts if isinstance(conflicts, list) else []
        return self._conflicts_cache

    def _resolveFromConflicts(self, a: Author, b: Author):
        a_id = a.data.get("id")
        b_id = b.data.get("id")
        for entry in self._loadConflictsFromFile():
            if not entry:
                continue
            entry_first = entry[0]
            entry_first_id = entry_first.get("id") if isinstance(entry_first, dict) else entry_first.data.get("id")
            if entry_first_id not in {a_id, b_id}:
                continue
            canonical = entry[-1]
            if isinstance(canonical, dict):
                return Author(
                    canonical.get("id"),
                    canonical.get("display_name"),
                    canonical.get("first_name"),
                    canonical.get("last_name"),
                    canonical.get("email"),
                    canonical.get("login"),
                )
            return canonical
        return None
        
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
            "Tadmin",
            "None",
        ]

        banListNormalized = {nlp.cleanDocument(name, "similarity") for name in banList}
        filteredAuthors = []
        bannedAuthors = []
        flaggedAuthors = []
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
                else:
                    pass
            if mergedAny:
                keep[i] = False
                canonicals.append(canonical)

        filteredAuthors = [authorsMeta[i] for i in range(len(authorsMeta)) if keep[i]]
        self.data = filteredAuthors + canonicals + bannedAuthors
        return flaggedAuthors

    def _manualResolve(self, disputes: list[tuple[Author, Author]]):
        authors = []
        to_remove = []
        for dispute in disputes:
            authorParams = []
            leftAuthor = dispute[0]
            rightAuthor = dispute[1]
            to_remove.extend([leftAuthor, rightAuthor])
            canonical = self._resolveFromConflicts(leftAuthor, rightAuthor)
            if canonical:
                authors.append(canonical)
                self._logChange(leftAuthor, canonical)
                self._logChange(rightAuthor, canonical)
                continue
            left = leftAuthor.data
            right = rightAuthor.data
            keys = ["id", "display_name", "first_name", "last_name", "email", "login"]

            table = ""
            for key in keys:
                lval = "" if left.get(key) is None else str(left.get(key))
                rval = "" if right.get(key) is None else str(right.get(key))
                table += f"{key:<14} {lval:<50} {rval}\n"

            for key in keys:
                print(f"{'field':<14} {'left':<50} {'right'}\n")
                print(table)
                lval = "" if left.get(key) is None else str(left.get(key))
                rval = "" if right.get(key) is None else str(right.get(key))
                print(f"{key:<14} {lval:<50} {rval}")
                choice = input("Type L or R to select left or right. Type E to manually enter a value.\n")
                if choice == "R" or choice == "r":
                    authorParams.append(right.get(key))
                elif choice == "L" or choice == "l":
                    authorParams.append(left.get(key))
                elif choice == "E" or choice == "e":
                    field = input("Value: ")
                    authorParams.append(field)
                else:
                    print("Input not recognized -- try again")
                os.system('cls' if os.name == 'nt' else 'clear')
            canonical = Author(*authorParams)
            self._manual_ids.add(str(canonical.data.get("id")))
            authors.append(canonical)
            self._logChange(leftAuthor, canonical)
            self._logChange(rightAuthor, canonical)
            self._logConflict(leftAuthor, canonical)
            self._logConflict(rightAuthor, canonical)
        if to_remove:
            self.data = [author for author in self.data if author not in to_remove]
        self.data.extend(authors) 

    def sanitize(self):
        self._normalizeData()
        flaggedAuthors = self._autoResolve()
        self._manualResolve(flaggedAuthors)
        self._autoResolve()
        self._log()
        return self.data
