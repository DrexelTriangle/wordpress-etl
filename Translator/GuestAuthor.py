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
        result = ''
        result += f'Guest Author\n'
        result += f'\tdisplay_name: {self.data["display_name"]}\n'
        result += f'\tfirst_name: {self.data["first_name"]}\n'
        result += f'\tlast_name: {self.data["last_name"]}\n'
        result += f'\temail: {self.data["email"]}\n'
        result += f'\tlogin: {self.data["login"]}\n'
        result += f'\tid: {self.data["id"]}\n'
        return result
