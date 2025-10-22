import json

class GuestAuthor:

    def __init__(self, display_name, first_name, last_name, email, login, count):
        self.data = {
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "login": login,
                "id": count
        } 

    def __str__(self):
        log = json.dump(self.objDataDict, file, indent=4)
        print(log)
