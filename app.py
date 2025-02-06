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
    if (newOption[1] == True):
      optionsLst.append(newOption[0])
  optionsLst.append('Exit')
  return optionsLst

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
      case 1:
        exit(7)
    
    noXML = (len(authorData) + len(articleData) + len(guestAuthorData) != 0)
    processXmlOption = ['Process XML', noXML]
    options = refreshOptions(options, [processXmlOption])
    app.clearOptions()
    app.setOptions(options)


