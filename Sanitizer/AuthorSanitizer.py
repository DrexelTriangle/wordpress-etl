import json
from Utils import NLP as nlp
import re
from pathlib import Path
from Translator.Author import Author
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.Policy import Policy

class AuthorSanitizer(Sanitizer):
    def __init__(self, data: list, policies: Policy):
        super().__init__(data, policies)
        self.lastAuid = int(data[-1].data["id"])
        self.conflictsCache = None
        self.priorityId = set()
        self.type = "auth" if policies.isAuthor else "gauth"

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
            updates = self.policies.specialEdits.get(author.data["display_name"])
            if updates:
                author.data.update(updates)
                special = True
            elif author.data["display_name"] in self.policies.specialFlags:
                special = True
            if special:
                self.priorityId.add(str(author.data.get("id")))
            if author.data["display_name"] is not None:
                if any(indicator in author.data["display_name"] for indicator in self.policies.multipleAuthorIndicators):
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