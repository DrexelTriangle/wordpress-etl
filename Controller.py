from xmltodict import *
from newUtility import *
from Author import *
from Article import *
from json import *
import os as OS 
import pprint
import re
from difflib import SequenceMatcher
from datetime import datetime
from pytz import timezone

def dataDumping(data, filename):
  print(f"> [data-dump] mending <{filename}>...")
  with open(f'.\\visualizations\\{filename}', 'w+', encoding='utf-8') as file:
    dump(data, file, ensure_ascii=False, indent=2)
    
def XmlSetup(wp_postsExportFile, wp_guestAuthorsExportFile):
  wpPostsDict, wpGuestAuthorsDict, authorData, articleData = {}, {}, {}, {}

  # Grab XML Content, convert to dictionary, grab author & article data  
  print("Converting Posts XML to Dictionary...")
  
  wpPostsDict = parseDictionary(wp_postsExportFile)
  wpGuestAuthorsDict = parseDictionary(wp_guestAuthorsExportFile)

  authorData = dictQuery(wpPostsDict, ['rss', 'channel', 'wp:author'])
  articleData = dictQuery(wpPostsDict, ['rss', 'channel', 'item'])
  guestAuthorData = dictQuery(wpGuestAuthorsDict, ['rss', 'channel', 'item'])

  print("> [xml-setup] Visualizing author dictionary...")
  visualizeDictionary(authorData, '.\\visualizations\\author-data.json')
  
  dataDumping(authorData, 'author-data.json')
  dataDumping(authorData, 'guest-author-data.json')
  dataDumping(authorData, 'article-data.json')

  print("> [xml-setup]: done.")
  return [authorData, articleData, guestAuthorData]


# UTILITY #########################################################################

def getDictValue(myDict, key):
  result = ''
  if (myDict.get('wp:meta_key') == key):
      if not(myDict.get('wp:meta_value') is None):
          result = myDict.get('wp:meta_value')
  return result

def parseDictionary(xml_file):
  content = None 
  print("Converting XML to Dictionary...")
  with open(xml_file, "+r", encoding='utf-8') as file:
      content = file.read()
      file.close()
  parsedDict = parse(content)
  return parsedDict

def dictQuery(myDict, queryLst):
  result = myDict
  failsafe = "ERROR"
  for query in queryLst:
    if (result == failsafe):
      return None
    else:
      result = result.get(query, failsafe)
  return result





