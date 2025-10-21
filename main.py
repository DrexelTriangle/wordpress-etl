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

'''
FORMAT OF EXTRACTED DATA
{
  auth: ...
  guestAuth: ...
  art: ...
}
'''

translators = {
  "articles": ArticleTranslator(extracted["art"]),
  "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
  "auth": AuthorTranslator(extracted["auth"])
}



translators["gAuth"].translate()
translators["gAuth"]._log()









