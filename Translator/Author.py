import json

class Author:

    def __init__(self, auid, login=None, email=None, display_name=None, first_name=None, last_name=None):
        self.data = {
                "auid": auid,
                "login": login,
                "email": email,
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
        }

    def __str__(self):
        log = json.dump(self.objDataDict, file, indent=4)
        print(log)
