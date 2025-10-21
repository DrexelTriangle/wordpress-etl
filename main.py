from Extractor import Extractor
from Translator.Translator import *
from Utility import *
from Constants import *
from Translator.ArticleTranslator import *
from Translator.GuestAuthorTranslator import *
from Translator.AuthorTranslator import *

# TODO: python library dependency checks

# unzip export data
Utility.unzip(ZIP_FILE)

# STEP 1: Extraction
extractor = Extractor(POSTS_FILE, GUEST_AUTH_FILE)
extracted = extractor.getData() 


# Step 2: Translation
translators = {
  "articles": ArticleTranslator(extracted["art"]),
  "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
  "auth": AuthorTranslator(extracted["auth"])
}

for key in translators:
  translators[key].translate()


# DEBUG: logging
translators["articles"]._log('log\\articles.json')
translators["gAuth"]._log('log\\gAuth.json')











