class GuestAuthor:

    def __init__(self, display_name, first_name, last_name):
        self.data = {
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
        } 

    def __str__(self):
        result = ''
        result += f'Guest Author\n'
        result += f'\tdisplay_name: {self.data["display_name"]}\n'
        result += f'\tfirst_name: {self.data["first_name"]}\n'
        result += f'\tlast_name: {self.data["last_name"]}\n'
        return result
