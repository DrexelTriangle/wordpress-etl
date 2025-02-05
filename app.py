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

options = ['Exit']
app = Menu(options, 'Wordpress Data Tool')

while True:
  choice = app.awaitChoice()
  isExit = choice == len(options) - 1

  if (isExit):
    break 
  else:
    app.clearOptions()
    break


