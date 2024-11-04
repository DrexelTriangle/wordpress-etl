from datetime import datetime
from pytz import timezone
from difflib import SequenceMatcher
import pprint

def grabTags(tagObjectList):
    result = []
    # print(tagObjectList)
    for i in range(0, len(tagObjectList)):
        # print(tagObjectList[i].get('#text')) #.get('@domain'))
        if (tagObjectList[i].get('@domain') == 'category'):
            result.append(tagObjectList[i].get('#text'))
    return result

def charMorph(myStr):
    
    if (myStr == None):
        return None
    else:
        result = myStr
        result = result.replace('&amp;', '&')
        result = result.replace('&nbsp;', ' ')
        return result
    

# Return a list of first name and last name
def parseName(name):
    result = None

    try:
        # if email -> attempt to split on condition of email = 'first.last@...'
        if "@" in name:
            result = name.split('@')[0].split('.')
        
        # if not email -> attempt to split on convention of email = 'first last'
        else:
            result = name.split(' ')
            

        if (len(result) == 1):
            return [result[0], None]    
        else:
            return result
    except:
        if (name is None):
            return ['PARSE_FAIL', 'PARSE_FAIL']
        else:
          return [name, 'PARSE_FAIL']

def generateUsername(first, last): 
    result = ''
    
    if (not (first is None)):
        result += first.replace(' ', "").replace('-', "").replace('.', '').replace("'", '').lower() 
    if (not (last is None)):
        result += '.' + last.replace(' ', "").replace('-', "").replace('.', '').replace("'", '').lower()
    return result


def GMT_to_EST(gmtDate):
    now_time = datetime.now(timezone('US/Eastern'))
    return now_time.strftime(gmtDate)

def processArticleTags(myLst):
    startColorCode = f"\033[38;2;255;234;0m"
    endColorCode = f"\033[0m"
    # print(f"{startColorCode}Error, no tags given{endColorCode}")
    result = []
    tags = []
    articleAuthors = []
    # for item in myLst:
    #     temp = [item.get("#text") if (item.get('@domain') == 'post_tag') else '' for item in myLst]
    #     temp.sort(reverse=True)
    #     return list(filter(lambda x: x != '', temp)) 
 

    for i in range(len(myLst)):
        try:
            if (myLst[i].get('@domain') == 'post_tag'):
                tags.append(myLst[i].get('#text'))            
                tags.sort(reverse=True)
            if (myLst[i].get('@domain') == 'author'):
                nicename = myLst[i].get('@nicename')
                articleAuthors.append(nicename.replace('cap-', '').replace('_', '-'))            
                articleAuthors.sort(reverse=True)
        except KeyError:
            tags.append(f"Error, no tags given")
            
    result.append(tags)
    result.append(articleAuthors)
    return result

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def visualizeDictionary(dict, fileName):
    result = pprint.pformat(dict)
    with open(fileName, 'w+') as file:
        file.write(result)
        file.close()
