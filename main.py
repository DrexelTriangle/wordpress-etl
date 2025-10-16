from Extractor import Extractor
from Translator.Translator import *
from Utility import *
from Constants import *
from Translator.ArticleTranslator import *

# TODO: python library dependency checks

# unzip export data
Utility.unzip(ZIP_FILE)

# STEP 1: Extraction
extractor = Extractor(POSTS_FILE, GUEST_AUTH_FILE)
extracted = extractor.getData() 

translatedData = {
  "articles": ArticleTranslator.translate(extracted["art"])
}

# ArticleTranslator._visualize()
print(ArticleTranslator.byteSize)