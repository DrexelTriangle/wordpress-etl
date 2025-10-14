from xmltodict import *
from Utility import *
from Constants import EXPORT_DIR

class Extractor:
  def __init__(self, posts, guestAuths):
    self.value = 0
    self.postsFile = posts
    self.guestAuthsFile = guestAuths
    self.data = {
      'auth': None,
      'guestAuth': None,
      'art': None 
    }

  # GETTERS/SETTERS
  def getData(self):
    self._xml2Dict(self.postsFile, self.guestAuthsFile)
    Utility._delete_dir(EXPORT_DIR)
    return self.data

  def _setData(self, key, value):
    self.data[key] = value

  # METHODS
  def _eparse(self, xmlFile):
    content = None 
    with open(xmlFile, "+r", encoding='utf-8') as file:
      content = file.read()
      file.close()
    parsedDict = parse(content)
    return parsedDict
  
  def _equery(self, myDict, queryLst):
    result = myDict
    failsafe = "ERROR"
    for query in queryLst:
      if (result == failsafe):
        return None
      else:
        result = result.get(query, failsafe)
    return result
  
  def _xml2Dict(self, posts, guestAuths):
    postsDict, guestAuthDict = {}, {}

    postsDict = self._eparse(posts)
    guestAuthDict = self._eparse(guestAuths)
    postsDict = self._equery(postsDict, ['rss', 'channel'])

    # OG, kept just in case
    # self._setData('auth', self._equery(postsDict, ['wp:author']))
    # self._setData('guestAuth', self._equery(postsDict, ['item']))
    # self._setData('art', self._equery(guestAuthDict, ['rss', 'channel', 'item']))
    
    self._setData('auth', self._equery(postsDict, ['wp:author']))
    self._setData('art', self._equery(postsDict, ['item']))
    self._setData('guestAuth', self._equery(guestAuthDict, ['rss', 'channel', 'item']))



  
  
