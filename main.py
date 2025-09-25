from Extractor import Extractor
from Utility import *
from Constants import *

Utility.unzip(ZIP_FILE)
extractor = Extractor(POSTS_FILE, GUEST_AUTH_FILE)
result = extractor.getData()