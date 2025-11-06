from Extractor import Extractor
from Translator.Translator import *
from Utils.Utility import *
from Utils.Constants import *
from Translator.ArticleTranslator import *
from Translator.GuestAuthorTranslator import *
from Translator.AuthorTranslator import *
from Formatter.Formatter import *
from Formatter.ArticleFormatter import *
from Formatter.AuthorFormatter import *
from Formatter.GuestAuthorFormatter import *

# TODO: python library dependency checks

# unzip export data
Utility.unzip(ZIP_FILE)

# STEP 1: Extraction
extractor = Extractor(*UNZIPPED_FILES)
extracted = extractor.getData() 


# Step 2: Translation
translators = {
  "articles": ArticleTranslator(extracted["art"]),
  "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
  "auth": AuthorTranslator(extracted["auth"])
}

for key in translators:
  translators[key].translate()


# Step 3: Formatter
formatters = {
    "articles": ArticleFormatter(translators["articles"]),
    "gAuth": GuestAuthorFormatter(translators["gAuth"]),
    "auth": AuthorFormatter(translators["auth"])
}

for key in formatters:
    formatters[key].SQLify()
    
# DEBUG: logging
formatters["articles"]._logCommands('log\\sql-articles.json')
formatters["gAuth"]._logCommands('log\\sql-gAuth.json')
formatters["auth"]._logCommands('log\\sql-auth.json')

