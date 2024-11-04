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


def GMT_to_EST(gmtDate):
    now_time = datetime.now(timezone('US/Eastern'))
    return now_time.strftime(gmtDate)


