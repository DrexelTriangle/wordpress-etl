import json
import os
from pathlib import Path

from Animator import Animator
from Extractor import Extractor
from Sanitizer.AuthorSanitizer import AuthorSanitizer
from Translator.ArticleTranslator import ArticleTranslator
from Translator.AuthorTranslator import AuthorTranslator
from Translator.GuestAuthorTranslator import GuestAuthorTranslator
from Utils.Constants import UNZIPPED_FILES, ZIP_FILE
from Utils.Utility import Utility