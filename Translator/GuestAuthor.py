from Translator.WPObject import WPObject as WPO

class GuestAuthor(WPO):
    def __init__(self, display_name, first_name, last_name, email, login, count):
        self.data = {
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "login": login,
                "id": count
        } 

