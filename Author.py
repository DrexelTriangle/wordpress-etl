class Author:

    def __init__(self, auid, login=None, email=None, display_name=None, first_name=None, last_name=None):
        self._auid = auid
        self._login = login
        self._email = email
        self._display_name = display_name
        self._first_name = first_name
        self._last_name = last_name

    @property
    def auid(self):
        return self._auid

    @auid.setter
    def auid(self, new_auid):
        if not isinstance(new_auid, string):
            raise ValueError("Author ID must be an int")
        self._auid = new_auid

    @property
    def login(self)
        return self._login

    @login.setter
    def login(self, new_login):
        if not isinstance(new_login, string):
            raise ValueError("Author Login must be a string")
        self._login = new_login

    @property
    def email(self)
        return self._email

    @email.setter
    def email(self, new_email):
        if not isinstance(new_email, string):
            raise ValueError("Author Email must be a string")
        self._email = new_email

    @property
    def email(self)
        return self._email

    @display_name.setter
    def display_name(self, new_display_name):
        if not isinstance(new_display_name, string):
            raise ValueError("Author Display Name must be a string")
        self._display_name = new_display_name

    @property
    def first_name(self)
        return self._first_name

    @first_name.setter
    def first_name(self, new_first_name):
        if not isinstance(new_first_name, string):
            raise ValueError("Author First Name must be a string")
        self._first_name = new_first_name

    @property
    def last_name(self)
        return self._last_name

    @last_name.setter
    def last_name(self, new_last_name):
        if not isinstance(new_login, string):
            raise ValueError("Author Last Name must be a string")
        self._last_name = new_last_name

