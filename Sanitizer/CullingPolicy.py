from Sanitizer.Policy import Policy
from Utils import NLP as nlp
from Translator.Author import Author
from Translator.GuestAuthor import GuestAuthor

class CullingPolicy(Policy):
    def __init__(self, data):
        specialEdits = {}
        specialFlags = {}
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
            "Drexel For PILOTS",
            "The Triangle Alumni",
            "Tadmin",
            "evoPhilly",
            "Anonymous Author",
            "myDoc",
            "Triangle News Desk",
            "Drexel Sport Management Council",
            "Triangle Staff",
            "Center for Sport Management",
            "Arts and Entertainment Staff",
            "Dac Pack Alumni",
            "Comics Board",
            "Miss Connections",
            "Guest Author",
            "Triangle Ed-Board",
            "None",
        ]
        super().__init__(specialEdits, specialFlags, banList, data, True)

    def _merge(self, a, b):
        aIsAuthor = isinstance(a, Author)
        bIsAuthor = isinstance(b, Author)

        if aIsAuthor and not bIsAuthor:
            return a
        if bIsAuthor and not aIsAuthor:
            return b
        else:
            return None

    def _autoResolve(self):
        flaggedAuthors = super()._autoResolve()

        # After base resolution, drop banned guest authors whose normalized name
        # already exists as an Author. Keep banned authors untouched.
        banListNormalized = {nlp.cleanDocument(name, "similarity") for name in self.banList}
        author_name_set = {
            nlp.cleanDocument(a.data["display_name"], "similarity")
            for a in self.data
            if isinstance(a, Author) and a.data.get("display_name") is not None
        }

        pruned = []
        for obj in self.data:
            name = obj.data.get("display_name")
            if name is None:
                pruned.append(obj)
                continue
            norm = nlp.cleanDocument(name, "similarity")
            if norm in banListNormalized and isinstance(obj, GuestAuthor) and norm in author_name_set:
                continue
            pruned.append(obj)

        self.data = pruned
        return flaggedAuthors
