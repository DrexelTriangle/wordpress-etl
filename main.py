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


# for t in translators:
#   translators[t].translate()
#   translators[t]._log()

translators["gAuth"].translate()
translators["gAuth"]._log()

# names = sorted(list(translators["articles"].uniqueAuthorCleanNames))
# longestName = len(max(names, key=len))


# for i in range(len(names)):
#   authorName = names[i]
#   spaces = longestName - len(authorName)
#   buf = (' ' * spaces) + authorName
#   print(buf, end=' ')
#   if (i + 1) % 4 == 0:
#     print()







