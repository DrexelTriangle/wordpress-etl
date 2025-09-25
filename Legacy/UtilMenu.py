# Construct a Menu object, because you run into Menus too much
import keyboard
import re
import sys
from time import sleep


class Menu:
  HIDE_CURSOR = '\033[?25l'
  SHOW_CURSOR = '\033[?25h'
  GREEN = '\033[0;32m'
  DARK_GRAY = '\033[0;30m'
  END = '\033[0m'


  # MUTATORS
  def __init__(self, options:list, title:str = 'Select an option'):
    self.title = title
    self.options: list[Option] = []
    self.titleBlock = "○"
    self.currentTab = 0
    self.animCount = 0
    

    for i in range(len(options)):
      menuOption = self.detectOptionType(options[i], len(options), self.title, self.titleBlock)
      self.options.append(menuOption)
  
  def setOptions(self, value):
    self.options = []
    for i in range(len(value)):
      menuOption = self.detectOptionType(value[i], len(value), self.title, self.titleBlock)
      self.options.append(menuOption)


  def detectOptionType(self, optObj, menuLen, title, titleBlock):
    # Text class (mainItm, self.action() = none)
    if isinstance(optObj, str):
      return Option(optObj, menuLen, title, titleBlock)
    
    # Trigger Class
    if isinstance(optObj, list):
      confirmationCheck = re.search(r"(.+)\*", optObj[0])
      newOptObj = optObj[0] if (confirmationCheck == None) else confirmationCheck.group(1)
      checkForInput = re.search(r"(?<=->).*$", newOptObj)
      addConfirmMenu = (confirmationCheck != None)
      isInput = (checkForInput != None)

      mainTxt = checkForInput.group() if (checkForInput != None) else optObj[0]
      action = optObj[1] if (len(optObj) >= 2) else None 
      actionArgs = optObj[2] if (len(optObj) == 3) else None
      
      return Trigger(mainTxt, menuLen, title, titleBlock, action, actionArgs, addConfirmMenu, isInput)
    
    # Submenu class
    if isinstance(optObj, Menu):
      animSpd = 0.04
      menu = optObj
      return SubMenu(self, menu, animSpd)

  def __str__(self):
    result = ''
    for i in range(len(self.options)):
      optionItm = self.options[i]
      result += (f'{i + 1}. {optionItm.mainItm}\n')
    return result
  
  def awaitChoice(self, animSpd=-1):
    count = 0
    choice = 0
    direction = ''

    sys.stdout.flush()
    print(f'\r{Menu.HIDE_CURSOR} {self.titleBlock} {self.title}')
    while True:
      self.printOptions(choice, tab=len(self.titleBlock) + 2, animSpd=animSpd)
      direction = Menu.dir_keys()

      if (direction == "up" or direction == "down"):
        choice = self.changeTargetOption(direction, choice)
      match(direction):
        case "skip":
          self.clearOptions()
          continue
        case "enter":
          choice = self.options[choice].receiveAction(choice)
          break
          
      self.clearOptions()
    print('\n' + Menu.SHOW_CURSOR, end="")
    return choice
  
  # UTILITY FUNCTTIONS
  def changeTargetOption(self, direction:str, currOpt: int):
    buffer = currOpt + (-1 if direction == "up" else 1)
    menuLen = len(self.options)
        
    if (0 < buffer < menuLen):
      currOpt = buffer 
    else:
      currOpt = (menuLen - 1) if (buffer == -1) else 0
   
    return currOpt

  def printOptions(self, target:int=0, tab:int=0, animSpd=-1):
    currSelect = f'{Menu.GREEN}>{Menu.END}'
    unSelect = f'{Menu.DARK_GRAY}-'
    
    for i in range(len(self.options)):
      menuOption = self.options[i]
      leadingChar = (currSelect) if (i == target) else (unSelect)
      print(f'{' ' * tab}{leadingChar} {menuOption.mainItm}{Menu.END}')
      sys.stdout.flush()
      if (animSpd > 0 and self.animCount <= 0):
        sleep(animSpd)
      self.animCount += 1
  
  def clearOptions(self, lineNum=-1):
    if (lineNum < 0):
      lineNum = len(self.options)

    for i in range(lineNum):
      sys.stdout.write("\x1b[1A\x1b[2K")
  
  def clearMenu(self):
    self.clearOptions(len(self.options) + 2)

  def dir_keys():   
    while True:
      key = keyboard.read_event(suppress=True)
      if key.event_type == "up":
        return "skip"
      return key.name    

class Option:
  # MUTATOR
  def __init__(self, itm, totalOptions:int=-1, title:str=None, titleBlock:str=None):
    # subtext? 
    self.action = None
    self.totalOptions = totalOptions
    self.parentTitle = title
    self.parentTitleBlock = titleBlock

    self.mainItm = itm
    self.type = 'text'
    

  
  def receiveAction(self, optionNum:int):
    return optionNum

  # UTILITY FUNCTIONS
  def clearOptions(lineNum=1, animSpd=-1):
    for i in range(lineNum):
      sys.stdout.write("\x1b[1A\x1b[2K")
      sys.stdout.flush()
      if (animSpd > 0):
        sleep(animSpd)


class SubMenu(Menu):
  def __init__(self, parentMenu, currMenu, animSpd=0.04):
    Menu.__init__(self, currMenu.options, currMenu.title)
    self.animSpd = animSpd
    self.animCount = 0
    self.type = 'subMenu'
    self.action = self.awaitChoice
    self.parentMenu = parentMenu

    self.mainItm = currMenu.title
    self.action = currMenu.awaitChoice
    self.totalOptions = len(currMenu.options)
    self.parentTitle = parentMenu.title
    self.parentTitleBlock = parentMenu.titleBlock
    self.type = 'subMenu'

  def clearOptions(self, lineNum=1):
    for i in range(lineNum):
      sys.stdout.write("\x1b[1A\x1b[2K")
      sys.stdout.flush()
      if (self.animSpd > 0):
        sleep(self.animSpd)
  
  def receiveAction(self, optionNum):
    self.clearOptions(len(self.parentMenu.options) + 1)
    self.animCount += 1
    return self.action(self.animSpd) if (self.animCount <= 1) else self.action()


class Trigger(Option):
  def __init__(self, mainText, menuLen, title, titleBlock, action, actionArgs, addConfirmMenu, isInput):
    Option.__init__(self, mainText, menuLen, title, titleBlock)
    self.action = action 
    self.args = actionArgs
    self.confirmMenu = addConfirmMenu
    self.isInput = isInput
    self.type = "trigger"
  
  def receiveAction(self, optionNum):
    if (self.isInput):
      inputValue = self.getInput()
      return inputValue
    else:
      return self.action(*self.args) if (self.args != None) else (self.action() if self.action != None else None)
    
  def getInput(self):
    Option.clearOptions(self.totalOptions + 1)
    activeTitle = f' {self.parentTitleBlock} {self.parentTitle}: {Menu.DARK_GRAY}{self.mainItm}{Menu.END}'
    print(activeTitle)
    print(Menu.SHOW_CURSOR, end="")
    choice = input(f'{ ' ' * (len(self.parentTitleBlock) + 2)}{Menu.DARK_GRAY}- [Enter value]>{Menu.END} ')
    print(Menu.HIDE_CURSOR, end="")
    Option.clearOptions()
    print()
    
    confirmAction = self.confirmAction(selectedOption=choice, title=activeTitle, lineNum=2)

    if (confirmAction == 0 or confirmAction == -1):
      return choice 
    elif (confirmAction == 1):
      exit(7)

  def confirmAction(self, selectedOption=None, title=None, lineNum:int=1):
    # -1 = don't load menu
    # 0 = yes
    # 1 = no
    def handleToggle(direction, currentSelection):
      buffer = currentSelection + (-1 if direction == "left" else 1)
      menuLen = 2
      if (0 < buffer < menuLen):
        currOpt = buffer 
      else:
        currOpt = (menuLen - 1) if (buffer == -1) else 0
    
      return currOpt
    
    
    
    if (self.confirmMenu == False): 
      return -1
    if (self.confirmMenu):
      selected = f'{Menu.GREEN}●{Menu.END}'
      if (title != None):
        Option.clearOptions(2)
        print(f'{title} {Menu.DARK_GRAY}> "{selectedOption}"{Menu.END}')
      print(f'{' ' * (len(self.parentTitleBlock) + 2)}Are you sure?')

      choice = 0
      direction = ''
      while True:
        print(f'{' ' * (len(self.parentTitleBlock) + 2)}{selected if choice == 0 else "○"} Yes  {selected if choice == 1 else "○"} No')
        direction = Menu.dir_keys()
        if (direction == "left" or direction == "right"):
          choice = handleToggle(direction, choice)
        match(direction):
          case "skip":
            Option.clearOptions()
            continue
          case "enter":
            Option.clearOptions()
            result = f'{' ' * (len(self.parentTitleBlock) + 2)}{Menu.DARK_GRAY}{"No" if choice == 1 else "Yes"}{Menu.END}'
            print(result)
            break
        Option.clearOptions()
      return choice


