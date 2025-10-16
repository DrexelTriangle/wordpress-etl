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
        result = ''
        result += f'Author\n'
        result += f'\tauid: {self.data["auid"]}\n'
        result += f'\tlogin: {self.data["login"]}\n'
        result += f'\temail: {self.data["email"]}\n'
        result += f'\tdisplay_name: {self.data["display_name"]}\n'
        result += f'\tfirst_name: {self.data["first_name"]}\n'
        result += f'\tlast_name: {self.data["last_name"]}\n'
        return result
