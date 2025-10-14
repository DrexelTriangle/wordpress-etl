from Extractor import Extractor
from Translator import *
from Utility import *
from Constants import *

# TODO: python library dependency checks

# unzip export data
Utility.unzip(ZIP_FILE)

# STEP 1: Extraction
extractor = Extractor(POSTS_FILE, GUEST_AUTH_FILE)
result = extractor.getData()
print(result["auth"])
#for auth in result["auth"]:
#    print(auth["wp:author_email"])
