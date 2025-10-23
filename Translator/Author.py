from Translator.WPObject import WPObject as WPO

class Author(WPO):
    def __init__(self, auid, login=None, email=None, display_name=None, first_name=None, last_name=None):
        self.data = {
                "id": auid,
                "login": login,
                "email": email,
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
        }
