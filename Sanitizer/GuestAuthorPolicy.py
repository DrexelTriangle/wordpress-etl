from Sanitizer.Policy import Policy

class GuestAuthorPolicy(Policy):
    def __init__(self, data):
        specialEdits = {
            "evoPhilly": {"first_name": "evoPhilly"},
            "Anonymous Author": {"first_name": "Anonymous Author", "last_name": None},
            "myDoc": {"first_name": "myDoc"},
            "Triangle News Desk": {"first_name": "Triangle News Desk"},
            "Editorial Board": {"first_name": "Editorial Board", "last_name": None},
            "Triangle Staff": {"first_name": "Triangle Staff"},
            "Drexel Sport Management Council": {"first_name": "Drexel Sport Management Council"},
            "Center for Sport Management": {"first_name": "Center for Sport Management"},
            "Arts and Entertainment Staff": {"first_name": "Arts and Entertainment Staff", "last_name": None},
            "Dac Pack Alumni": {"first_name": "Dac Pack Alumni", "last_name": None},
            "Comics Board": {"first_name": "Comics Board", "last_name": None},
            "Guest Author": {"first_name": "Guest Author", "last_name": None},
            "Drexel for Justice": {"first_name": "Drexel for Justice"},
            "Triangle Ed-Board": {"first_name": "Triangle Ed-Board", "last_name": None},
        }
        specialFlags = {
            "Steve \"Spag\" Spagnolo",
            "Miss Connections"
        }
        banList = [
            "evoPhilly",
            "Anonymous Author",
            "myDoc",
            "Triangle News Desk",
            "Editorial Board",
            "Drexel Sport Management Council"
            "Triangle Staff",
            "Center for Sport Management",
            "Arts and Entertainment Staff",
            "Dac Pack Alumni",
            "Comics Board",
            "Miss Connections",
            "Guest Author",
            "Triangle Ed-Board"
        ]
        super().__init__(specialEdits, specialFlags, banList, data, False)
        