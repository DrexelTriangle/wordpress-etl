from Utility import Utility as U
from Translator.Translator import Translator

class Article():  
  # Constructor - blank object
  defaultValue = "None"
  def __init__(self):
    self.data = {
      "authorIDs": [],
      "authors": [],
      "authorCleanNames": [],
      "breakingNews": False,
      "commentStatus": '',
      "description": '',
      "featuredImgID": -1,
      "id": -1,
      "priority": False,
      "modDate": '',
      "photoCred": '',
      "pubDate": '',
      "tags": [],
      "text": '',
      "title": '', 
    }
  
  # CLASS OVERLOADS
  # printing
  def __str__(self):
    result = ""
    for key, value in self.source.items():
      result += f"{key}: {value}\n"
    result += "\n"
    return result 
  
  # dictionary overloads (convenience)
  def __getitem__(self, key):
    return self.data[key]
  def __setitem__(self, key, value):
    self.data[key] = value
  def __delitem__(self, key):
    del self.data[key]
    
  
  
  def setData(self, count, data:dict):
    self.data.update({
      "authorIDs": [], # for author/article linking (author<->linking)
      "authors": [],
      "authorCleanNames": [],
      "breakingNews": False,
      "commentStatus": data.get('wp:comment_status', Article.defaultValue),
      "description": U._html_text_norm(data.get('description')),
      "featuredImgID": -1,
      "id": count,
      "priority": False,
      "modDate": data.get('wp:post_modified_gmt', Article.defaultValue),
      "photoCred": None,
      "pubDate": data.get('wp:post_date_gmt', Article.defaultValue),
      "tags": data.get('category'),
      "text": str(U._html_text_norm(data.get('content:encoded'))).replace('"', '\\"'),
      "title": U._html_text_norm(data.get('title')), 
    })

    
  

  def dataSanityCheck(self):
    text = self["text"]
    title = self["title"]
    isTextNotNull = text != Article.defaultValue and len(text) > 100 
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
        temp = self["tags"][i]
        nicename = temp.get("@nicename", Article.defaultValue)
        domain = temp.get("@domain", Article.defaultValue)
        text = temp.get("#text", Article.defaultValue)

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

    self["tags"] = resultTags.sort(reverse=True)




  



