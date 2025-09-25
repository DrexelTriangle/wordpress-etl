import pprint
import re
from difflib import SequenceMatcher
from datetime import datetime
from pytz import timezone

def charMorph(myStr):
  if (myStr == None):
    return None
  else:
    result = myStr
    result = result.replace('&amp;', '&')
    result = result.replace('&nbsp;', ' ')
    return result
    
def attemptNameParse(name):
  result = None

  try:
    # if email -> attempt to split on condition of email = 'first.last@...'
    if "@" in name:
      result = name.split('@')[0].split('.')
    
    # if not email -> attempt to split on convention of email = 'first last'
    elif " " in name:
      result = name.split(' ')
        
    if (len(result) == 1):
      return [result[0], None]
    else:
      return result
    
  except:
    if (name is None):
      return ['NO_FIRST', 'NO_LAST']
    else:
      return [name, 'NO_LAST']
    
def generateUsername(first, last): 
  result = ''
  if (last == 'NO_LAST'):
    return first
  
  if (not (first is None)):
    result += first.replace(' ', "").replace('-', "").replace('.', '').replace("'", '').lower() 
  if (not (last is None)):
    result += '.' + last.replace(' ', "").replace('-', "").replace('.', '').replace("'", '').lower()
  return result

def generateMeshname(first, last): 
  result = ''
  if (last == 'NO_LAST' or (last != None and 'NO_LAST' in last)):
    return first
  
  if (not (first is None)):
    result += first.replace(' ', "").replace('-', "").replace('.', '').replace("'", '').lower() 
  if (not (last is None)):
    result += last.replace(' ', "").replace('-', "").replace('.', '').replace("'", '').lower()
  return result

def visualizeDictionary(dict, fileName):
  result = pprint.pformat(dict)
  with open(fileName, 'w+', encoding='utf-8') as file:
    file.write(result)
    file.close()

def similar(a, b):
  return SequenceMatcher(None, a, b).ratio()

def GMT_to_EST(gmtDate):
  now_time = datetime.now(timezone('US/Eastern'))
  return now_time.strftime(gmtDate)

