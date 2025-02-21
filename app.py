from xmltodict import *
from newUtility import *
from Author import *
from Article import *
from json import *
import os as OS 
from Controller import XmlSetup
from Menu import *
from UtilMenu import Menu
import sys
from temp import *

if (not OS.path.exists('./classes')):
  OS.mkdir('./classes') 
if (not OS.path.exists('./dumps')):
  OS.mkdir('./dumps') 
if (not OS.path.exists('./output')):
  OS.mkdir('./output') 
if (not OS.path.exists('./rawdata')):
  OS.mkdir('./rawdata') 
if (not OS.path.exists('./stats')):
  OS.mkdir('./stats') 
if (not OS.path.exists('./visualizations')):
  OS.mkdir('./visualizations') 


options = ['Load Data ', 'Exit']
app = Menu(options, 'Wordpress Data Tool')
file1 = ".\\rawdata\\tri-wpdump_4-1-24.xml"
file2 = ".\\rawdata\\thetriangle.WordPress.2024-07-10.xml"
authorData, articleData, guestAuthorData = [], [], []
existing, mustReplace, unmapped = [], [], []
authorData, articleData, guestAuthorData = [], [], []

def refreshOptions(optionsLst:list, conditions:list):
  optionsLst.remove('Exit')
  for newOption in conditions:
    if (newOption[0] in optionsLst):
      continue
    elif (newOption[1] == True):
      optionsLst.append(newOption[0])
  optionsLst.append('Exit')
  return optionsLst

def process():
  print('Processing...')
  Author.processAuthors(authorData)
  Author.processGuestAuthors(guestAuthorData)
  Article.processArticles(articleData)




processedData = False
unmappedLen = 1
while True:
  choice = app.awaitChoice()
  isExit = choice == len(options) - 1
  

  if (isExit):
    break
  else:
    match(choice):
      case 0:
        app.clearMenu()
        if (len(authorData) + len(articleData) + len(guestAuthorData) != 0):
          continue
        authorData, articleData, guestAuthorData = XmlSetup(file1, file2)
        processedData = False
      case 1:
        app.clearMenu()
        if (not processedData):
          process()
          processedData = True
      case 2:
        app.clearMenu()
        existing, mustReplace = checkForMending()
        unmapped = mapping(mustReplace)
        unmappedLen = len(unmapped)
        if (unmappedLen != 0):
          beginMapping(unmapped)
      case 3:
        exit(7)
    
    noXML = (len(authorData) + len(articleData) + len(guestAuthorData) != 0)
    notProcessed = processedData 
    processXmlOption = ['Process XML', noXML]
    checkForMendOption = ['Check Mending', notProcessed]
    generateSqlOption = ['Generate SQL', unmappedLen == 0]
    options = refreshOptions(options, [processXmlOption, checkForMendOption, generateSqlOption])
    app.clearOptions()
    app.setOptions(options)


