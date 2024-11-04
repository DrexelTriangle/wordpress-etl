from xmltodict import *
from newUtility import *
from Author import *
from Article import *
from json import *
import os as OS 


def parseDictionary(xml_file):
  content = None 
  print("Converting XML to Dictionary...")
  with open(xml_file, "+r", encoding='utf-8') as file:
      content = file.read()
      file.close()
  parsedDict = parse(content)
  return parsedDict

def dictQuery(myDict, queryLst):
  result = myDict
  failsafe = "ERROR"
  for query in queryLst:
    if (result == failsafe):
      return None
    else:
      result = result.get(query, failsafe)
  return result

def dataDumping(data, filename):
  print(f"> [data-dump] mending <{filename}>...")
  with open(f'.\\visualizations\\{filename}', 'w+', encoding='utf-8') as file:
    dump(data, file, ensure_ascii=False, indent=2)
    



