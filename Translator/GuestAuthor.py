from Translator.WPObject import WPObject as WPO

class GuestAuthor(WPO):
    def __init__(self, gauid, display_name=None, first_name=None, last_name=None, email=None, login=None):
        self.data = {
                "id": gauid,
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "login": login
        } 

