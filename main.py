from Extractor import Extractor
from Translator.Translator import *
from Utils.Utility import *
from Utils.Constants import *
from Translator.ArticleTranslator import *
from Translator.GuestAuthorTranslator import *
from Translator.AuthorTranslator import *
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


# DEBUG: logging
translators["articles"]._log('logs/articles/.')
translators["gAuth"]._log('logs/gAuth.json')
translators["auth"]._log('logs/auth.json')
authors = translators["auth"].listAuthors()
sanitizer = AuthorSanitizer(authors, {})
authors = sanitizer.sanitize()
with open("output.json", 'w+', encoding='utf-8') as file:
  oAuthors = {}
  for i in range(len(authors)):
    oAuthors[str(i)] = authors[i].data
  json.dump(oAuthors, file, indent=4)
  file.close()

