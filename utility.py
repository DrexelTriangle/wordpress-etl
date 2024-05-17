from datetime import datetime
from pytz import timezone

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
        return [name, 'PARSE_FAIL']

def generateUsername(first, last):
    if (first is None):
        return None
    if (last is None):
        return None
    return first.lower() + '.' + last.lower()


def GMT_to_EST(gmtDate):
    now_time = datetime.now(timezone('US/Eastern'))
    return now_time.strftime(gmtDate)

def processArticleTags(lst):
    result = []
    
    # temp = [item.get("#text") if (item.get('@domain') == 'post_tag') else '' for item in lst]
    # temp.sort(reverse=True)
    # return list(filter(lambda x: x != '', temp)) 

    for i in range(len(lst)):
        if (lst[i].get('@domain') == 'post_tag'):
            result.append(lst[i].get('#text'))
    result.sort(reverse=True)
    return result 

    