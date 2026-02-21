from xmltodict import *
from Utils.Utility import Utility as U
from Utils.Constants import EXPORT_DIR

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
    U._delete_dir(EXPORT_DIR)
    return self.data

  def _setData(self, key, value):
    self.data[key] = value

  # METHODS
  def _eparse(self, xmlFile):
    with open(xmlFile, "r", encoding="utf-8") as file:
      content = file.read()
    parsedDict = parse(content)
    return parsedDict
  
  def _equery(self, sourceDict, queryList):
    result = sourceDict
    failsafe = "ERROR"
    for query in queryList:
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
    
    self._setData('auth', self._equery(postsDict, ['wp:author']))
    self._setData('art', self._equery(postsDict, ['item']))
    self._setData('guestAuth', self._equery(guestAuthDict, ['rss', 'channel', 'item']))

    # with open('./investigation.txt', 'w+') as file:
    #   json.dump(postsDict, file, indent=4)
    #   file.close()



  
  
