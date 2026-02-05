from Sanitizer.Policy import Policy

class AuthorPolicy(Policy):
    def __init__(self, data):
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
        super().__init__(specialEdits, specialFlags, banList, data, True)
