from pathlib import Path
import json
from Translator.Translator import Translator
from Translator.Article import Article
from Utils.Utility import Utility as U
import re

_IMG_UPLOAD_PATTERN = re.compile(r"wp-content\/uploads\/(.*?)\\")

class ArticleTranslator(Translator):
  # Constructor
  def __init__(self, incomingData):
    super().__init__(incomingData)
    # {guest author term slug -> real display name}, supplied by the Extractor.
    # Empty is valid: resolution then falls back to the term's own text.
    self.guestAuthorNames = {}

  def _getArticleData(self, data):
    text = str(U._html_text_norm(data.get('content:encoded', Article.defaultValue))).replace('"', '\\"')
    return {
      "authorIDs": [],
      "authors": [],
      "authorCleanNames": [],
      "breakingNews": False,
      "commentStatus": self._normalizeCommentStatus(data.get('wp:comment_status')),
      "description": U._html_text_norm(data.get('description')),
      "featuredImgID": -1,
      "id": self.objCount,
      "slug": data.get('wp:post_name', Article.defaultValue),
      "wpPostID": self._normalizeInt(data.get('wp:post_id')),
      "priority": False,
      "modDate": data.get('wp:post_modified_gmt', Article.defaultValue),
      "photoURL": self._checkForImg(text),
      "pubDate": data.get('wp:post_date_gmt', Article.defaultValue),
      "tags": data.get('category'),
      "categories": [],
      "metadata": data.get('wp:postmeta'),
      "text": text,
      "excerpt": "",
      "title": self._normalizeTitle(U._html_text_norm(data.get('title', Article.defaultValue))),
    }


  # NOTE: using to only load 9k of the article data
  def _shouldSkip(self, obj, debugMode):
    title = obj["title"]
    if (title is None or not self._dataSanityCheck(obj, debugMode) or obj["tags"] == -1):
      return True 
    return False

  def _dataSanityCheck(self, obj, debugMode=False):
    text = obj["text"]
    title = obj["title"]

    lengthCheck = 4 if debugMode else 100
    isTextNotNull = text != Article.defaultValue and len(text) >= lengthCheck
    isTitleNotNull = title != Article.defaultValue
    isTextNotSudoku = isTextNotNull and ('sudoku' not in text)
    isTitleNotUnderscore = isTitleNotNull and ('_' not in title)

    return isTextNotSudoku and isTitleNotUnderscore

  def _normalizeCommentStatus(self, value):
    # WordPress exports carry inconsistent casing/whitespace for comment_status
    # ("open", "Open", " closed"). Force a uniform enum here so downstream
    # consumers (and the CMS dropdown) never see variants. Anything that isn't
    # an explicit "closed" defaults to "open", matching the WordPress default.
    if isinstance(value, str) and value.strip().lower() == "closed":
      return "closed"
    return "open"

  def _normalizeTitle(self, title):
    if title is None:
      return None
    if not isinstance(title, str):
      return title
    # WP export payloads sometimes carry slashed quotes in title text.
    return title.replace('\\"', '"').replace("\\'", "'")

  def _normalizeInt(self, value):
    if value in (None, ""):
      return None
    try:
      return int(str(value).strip())
    except (TypeError, ValueError):
      return None
  
  def _checkForImg(self, text:str):
    matchObj = _IMG_UPLOAD_PATTERN.search(text) 
    if matchObj:
      return matchObj.group(0).replace('\\', '')

  def _processTags(self, obj):
    resultTags = []
    resultCategories = []
    try:
      terms = obj["tags"]
      if terms is None or terms == Article.defaultValue:
        terms = []
      elif isinstance(terms, dict):
        terms = [terms]
      elif not isinstance(terms, list):
        terms = []

      for tagData in terms:
        if not isinstance(tagData, dict):
          continue

        nicename = tagData.get("@nicename", Article.defaultValue)
        domain = tagData.get("@domain", Article.defaultValue)
        text = U._html_text_norm(tagData.get("#text", Article.defaultValue))

        isNoTags = obj["tags"] is None or obj["tags"] == Article.defaultValue
        isNoText = obj["text"] is None or obj["text"] == Article.defaultValue
        if (isNoTags or isNoText):
          obj["tags"] = -1
          obj["categories"] = -1
          return

        if (domain == "post_tag" and text is not None and text != Article.defaultValue):
          resultTags.append(text)
        elif (domain == "category" and text is not None and text != Article.defaultValue):
          resultCategories.append(text)
        elif (domain == "author"):
          # The term's text is the slug ("beeboop"), not the byline. Resolve it
          # through the guest author export, which holds the real name.
          resolved = self.guestAuthorNames.get(nicename, text)
          cleanName = resolved.translate(str.maketrans('', '', '.-_ ')).lower()
          obj["authorCleanNames"].append(cleanName)
          obj["authors"].append(resolved)

    except (KeyError, TypeError):
      resultTags.append('NO_TAGS')

    resultTags.sort(reverse=True)
    resultCategories.sort(reverse=True)
    obj["tags"] = resultTags
    obj["categories"] = resultCategories

  def _processMetadata(self, obj):
    collection = {}
    metadata = obj.get('metadata')
    if metadata is None or metadata == Article.defaultValue:
      obj['metadata'] = collection
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

    obj['metadata'] = collection


  def translate(self, on_progress=None):
    debugMode = False
    if on_progress:
      on_progress(f"translating {len(self.source)} articles")
    for itm in self.source:
      self.translateItem(itm, debugMode)

  def translateItem(self, itm, debugMode=False):
    obj = self._getArticleData(itm)
    self._processTags(obj)
    self._processMetadata(obj)
    # NOTE: using to only load 9k of the article data
    if self._shouldSkip(obj, debugMode):
      return None
    self.addObject(obj)
    return obj

  def _log(self, fileDestination):                      
    fileBuckets = []
    dictLen = len(self.objDataDict)
    remainder = dictLen % 1000
    bucketNum = (dictLen // 1000) + (1 if (remainder > 0) else 0)
    fileDir = Path(fileDestination)
    fileDir.mkdir(parents=True, exist_ok=True)

    for i in range(bucketNum):
      fileBuckets.append({})
    
    for i, itm in enumerate(self.objDataDict):
      bucket = i // 1000
      fileBuckets[bucket].update({i: self.objDataDict[i]})
    
    for i in range(len(fileBuckets)):
      bucket = fileBuckets[i]
      filePath = fileDir / f"{i}.json"
      with filePath.open('w+', encoding='utf-8') as file:
        json.dump(bucket, file, indent=4)


 


  
