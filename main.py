from Extractor import Extractor
from Translator.Translator import *
from Utils.Utility import *
from Utils.Constants import *
from Translator.ArticleTranslator import *
from Translator.GuestAuthorTranslator import *
from Translator.AuthorTranslator import *
from Formatter.ArticleFormatter import *
from Formatter.AuthorFormatter import *
from Formatter.GuestAuthorFormatter import *
from Sanitizer.AuthorSanitizer import *

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


# # DEBUG: logging
# translators["articles"]._log('log\\articles')
# translators["gAuth"]._log('log\\gAuth.json')
# translators["auth"]._log('log\\auth.json')


# Step 3: Sanitation
authorSanitizer = AuthorSanitizer(translators["auth"].getObjList(), {})
authorSanitizer.sanitize()


# Step 4: Formatting
formatters = {
  "articles": ArticleFormatter(translators["articles"]),
  "gAuth": GuestAuthorFormatter(translators["auth"]),
  "auth": AuthorFormatter(translators["gAuth"]),
}

for key in formatters:
  formatters[key].format()





