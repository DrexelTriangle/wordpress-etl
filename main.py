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
from Sanitizer.TempArticleSanitizer import *

# TODO: python library dependency checks

# unzip export data
Utility.unzip(ZIP_FILE)

# STEP 1: Extraction
extractor = Extractor(*UNZIPPED_FILES)
extracted = extractor.getData() 


# Step 2: Translation
articleTranslator = ArticleTranslator(extracted["art"])
authTranslator = AuthorTranslator(extracted["auth"])
gAuthTranslator = GuestAuthorTranslator(extracted["guestAuth"])

articleTranslator.translate()
authTranslator.translate()
gAuthTranslator.translate()


# DEBUG: logging
articleTranslator._log('log\\articles')
authTranslator._log('log\\gAuth.json')
gAuthTranslator._log('log\\auth.json')


# Step 3: Sanitation
authorSanitizer = AuthorSanitizer(authTranslator.getObjList(), {})
articleSanitizer = TempArticleSanitizer(articleTranslator.getObjDataDict(), {})
# authorSanitizer.sanitize()
articleSanitizer._checkForImgTags()

# Step 4: Formatting
formatters = {
  "articles": ArticleFormatter(articleTranslator),
  "gAuth": GuestAuthorFormatter(authTranslator),
  "auth": AuthorFormatter(gAuthTranslator),
}

for key in formatters:
  formatters[key].format()





