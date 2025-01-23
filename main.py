from xmltodict import *
from newUtility import *
from Author import *
from Article import *
from json import *
import os as OS 
from Controller import XmlSetup
from Menu import *

# Setup
file1 = ".\\rawdata\\tri-wpdump_4-1-24.xml"
file2 = ".\\rawdata\\thetriangle.WordPress.2024-07-10.xml"
authorData, articleData, guestAuthorData = [], [], []
existing, mustReplace, unmapped = [], [], []
authorData, articleData, guestAuthorData = XmlSetup(file1, file2)

# Process Authors
Author.processAuthors(authorData)
Author.processGuestAuthors(guestAuthorData)

# Process Articles
Article.processArticles(articleData)

# Mending
existing, mustReplace = checkForMending()
unmapped = mapping(mustReplace)
beginMapping(unmapped)
count = binding(existing, mustReplace)


if (count == 0):
  print(f'> [main] All article authors have been locally mapped. Everything is accounted for!')
  Author.SQLifiy()
  Article.SQLifiy()
