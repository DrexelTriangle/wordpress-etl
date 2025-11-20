import Utils.NLP as nlp
from Translator.Author import Author
from Sanitizer import Sanitizer

class AuthorSanitizer(Sanitizer):
    def __init__(self, data: list, policies: dict, logDir: str):
        super().__init__(self, data, policies, logDir)

    def normalizeText(self):

