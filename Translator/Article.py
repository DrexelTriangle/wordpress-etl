from Utils.Utility import Utility as U
from Translator.WPObject import WPObject as WPO
import re

class Article(WPO):  
  # Constructor - blank object
  defaultValue = "None"
  def __init__(
    self, 
    authorIDs, authors, authorCleanNames,
    breakingNews, commentStatus, description,
    featuredImgID, id, slug, priority, modDate, 
    photoURL, pubDate, tags, metadata, text, title
  ):
    self.data = {
      "authorIDs": authorIDs,
      "authors": authors,
      "authorCleanNames": authorCleanNames,
      "breakingNews": breakingNews,
      "commentStatus": commentStatus,
      "description": description,
      "featuredImgID": featuredImgID,
      "id": id,
      "slug": slug,
      "priority": priority,
      "modDate": modDate,
      "photoURL": photoURL,
      "pubDate": pubDate,
      "tags": tags,
      "categories": [],
      "metadata": metadata,
      "text": text,
      "title": title,
    }
  
  
  # dictionary overloads (convenience)
  def __getitem__(self, key):
    return self.data[key]
  def __setitem__(self, key, value):
    self.data[key] = value
  def __delitem__(self, key):
    del self.data[key]
  def __str__(self):
    return self.data
  

  def dataSanityCheck(self, debugMode=False):
    text = self["text"] 
    title = self["title"]

    lengthCheck = 4 if debugMode else 100 
    isTextNotNull = text != Article.defaultValue and len(text) >= lengthCheck 
    isTitleNotNull = title != Article.defaultValue 
    isTextNotSudoku = isTextNotNull and ('sudoku' not in text)
    isTitleNotUnderscore = isTitleNotNull and ('_' not in title) 

    return isTextNotSudoku and isTitleNotUnderscore


  # processTags: tags are stored in the 'category' WP key where its value should be a list of dict objects
  def processTags(self):
    resultTags = []
    resultCategories = []
    try:
      terms = self.data["tags"]
      if terms is None or terms == Article.defaultValue:
        terms = []
      elif isinstance(terms, dict):
        terms = [terms]
      elif not isinstance(terms, list):
        terms = []

      for tagData in terms:
        if not isinstance(tagData, dict):
          continue

        # Grab tag data [KEYS-> author name: "@nicename" tag data: "@domain"]
        nicename = tagData.get("@nicename", Article.defaultValue)
        domain = tagData.get("@domain", Article.defaultValue)
        text = U._html_text_norm(tagData.get("#text", Article.defaultValue))

        # Check whether or not we're dealing with crossword/comics post
        # TODO: implement handling these later, for now just flag for 
        #       skipping, along with any empty posts
        isCrosswordOrComics = nicename in {"crossword", "comics"}
        isNoTags = self["tags"] is None or self["tags"] == Article.defaultValue
        isNoText = self["text"] is None or self["text"] == Article.defaultValue
        if (isCrosswordOrComics or isNoTags or isNoText):
          self.data["tags"] = -1
          self.data["categories"] = -1
          return

        if (domain == "post_tag" and text is not None and text != Article.defaultValue):
          resultTags.append(text)
        elif (domain == "category" and text is not None and text != Article.defaultValue):
          resultCategories.append(text)
        elif (domain == "author"):
          cleanName = text.translate(str.maketrans('', '', '.-_ ')).lower()
          self["authorCleanNames"].append(cleanName)
          self["authors"].append(text)

    # Handle invalid key access and other NoneType-related errors 
    except (KeyError, TypeError):
      resultTags.append('NO_TAGS')

    resultTags.sort(reverse=True)
    resultCategories.sort(reverse=True)
    self["tags"] = resultTags
    self["categories"] = resultCategories
  
  def processMetadata(self):
    collection = {}
    metadata = self.data.get('metadata')
    if metadata is None or metadata == Article.defaultValue:
      self.data['metadata'] = collection
      return

    if isinstance(metadata, dict):
      metadata = [metadata]
    elif not isinstance(metadata, list):
      metadata = []

    for itm in metadata:
      if isinstance(itm, dict):
        key, value = itm.get('wp:meta_key'), itm.get('wp:meta_value')
        if isinstance(key, str) and ('yoast' in key):
          collection.update({key: value})
        

    self.data['metadata'] = collection
