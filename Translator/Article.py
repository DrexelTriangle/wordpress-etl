from Utils.Utility import Utility as U
from Translator.WPObject import WPObject as WPO

class Article(WPO):  
  # Constructor - blank object
  defaultValue = "None"
  def __init__(
    self, 
    authorIDs, authors, authorCleanNames,
    breakingNews, commentStatus, description,
    featuredImgID, id, priority, modDate, 
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
      "priority": priority,
      "modDate": modDate,
      "photoURL": photoURL,
      "pubDate": pubDate,
      "tags": tags,
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
    try:
      for i in range(len(self.data["tags"])):
        # Grab tag data [KEYS-> author name: "@nicename" tag data: "@domain"]
        tagData = self["tags"][i]
        nicename = tagData.get("@nicename", Article.defaultValue)
        domain = tagData.get("@domain", Article.defaultValue)
        text = tagData.get("#text", Article.defaultValue)

        # Check whether or not we're dealing with crossowrd/comics post
        # TODO: implement handling these later, for now just flag for 
        #       skipping, along with any empty posts
        isCrosswordOrComics = nicename in {"crossword", "comics"}
        isNoTags = self["tags"] == "None" 
        isNoText = self["text"] == "None"
        if (isCrosswordOrComics or isNoTags or isNoText):
          self.data["tags"] = -1
          return
        
        if (domain == "post_tag"):
          resultTags.append(text)
        elif (domain == "author"):
          cleanName = text.translate(str.maketrans('', '', '.-_ ')).lower()
          self["authorCleanNames"].append(cleanName)
          self["authors"].append(text)

    # Handle invalid key access and other NoneType-related errors 
    except (KeyError, TypeError):
      resultTags.append('NO_TAGS')

    resultTags.sort(reverse=True)
    self["tags"] = resultTags




  




