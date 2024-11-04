from xmltodict import *
from newUtility import *
from Author import *
from Article import *
from json import *
import os as OS 


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
    


def XmlSetup(wp_postsExportFile, wp_guestAuthorsExportFile):
    wp_xmlPostContent, wp_xmlGuestAuthors = None, None
    wpPostsDict, wpGuestAuthorsDict, authorData, articleData = {}, {}, {}, {}

    # Grab XML Content, convert to dictionary, grab author & article data  
    print("Converting Posts XML to Dictionary...")
    with open(wp_postsExportFile, "+r", encoding='utf-8') as file:
      wp_xmlPostContent = file.read()
      file.close()

    with open(wp_guestAuthorsExportFile, "+r", encoding='utf-8') as file:
      wp_xmlGuestAuthors = file.read()
      file.close()
    
    print("> [xml-setup] Parsing wordpress posts and guest authors...")
    wpPostsDict = parse(wp_xmlPostContent)
    wpGuestAuthorsDict = parse(wp_xmlGuestAuthors)

    authorData = wpPostsDict.get('rss').get('channel').get('wp:author')
    articleData = wpPostsDict.get('rss').get('channel').get('item')
    guestAuthorData = wpGuestAuthorsDict.get('rss').get('channel').get('item')

    print("> [xml-setup] Visualizing author dictionary...")
    visualizeDictionary(authorData, '.\\visualizations\\author-data.json')
    newlines = []
    # FIXME: Manual ass file mending
    print("> [xml-setup] mending <author-data.json>...")
    with open('.\\visualizations\\author-data.json', 'w+', encoding='utf-8') as file:
      dump(authorData, file, ensure_ascii=False, indent=2)

    print("> [xml-setup] mending <guest-author-data.json>...")
    with open('.\\visualizations\\guest-author-data.json', 'w+', encoding='utf-8') as file:
      dump(guestAuthorData, file, ensure_ascii=False, indent=2)

    print("> [xml-setup] mending <article-data.json>...")
    with open('.\\visualizations\\article-data.json', 'w+', encoding='utf-8') as file:
      dump(articleData, file, ensure_ascii=False, indent=2)

    print("> [xml-setup]: done.")
    return [authorData, articleData, guestAuthorData]



