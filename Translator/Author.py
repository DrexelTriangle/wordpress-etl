from Translator.WPObject import WPObject as WPO

class Author(WPO):
    def __init__(self, auid, display_name=None, first_name=None, last_name=None, email=None, login=None):
        if isinstance(auid, str):
            stripped = auid.strip()
            if stripped:
                try:
                    auid = int(stripped)
                except ValueError:
                    pass
        self.data = {
                "id": auid,
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "login": login
        }
