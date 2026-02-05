import time
import threading
import os
import shutil
from dataclasses import dataclass
from itertools import cycle

ANSI_RESET = "\033[0m"
ANSI_WHITE = "\033[37m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_GRAY = "\033[90m"
ANSI_INVERT = "\033[7m"
SPINNER_CHARS = "⣾⣽⣻⢿⡿⣟⣯⣷"
CHECKMARK_CHAR = "✓"
LEFT_MARKER = ">>>>>>>>>>"
RIGHT_MARKER = "<<<<<<<<<<"
LEFT_ARROW = "\u2190"
RIGHT_ARROW = "\u2192"
CLEAR_LINE_WIDTH = 80
PAUSE_SLEEP_SECONDS = 0.05
SPINNER_SLEEP_SECONDS = 0.075

def _padValue(value, width):
  text = "" if value is None else str(value)
  return text[:width].ljust(width)

def _centerColored(text, width, color):
  if not text:
    return " " * width
  if len(text) >= width:
    return f"{color}{text[:width]}{ANSI_RESET}"
  leftPad = (width - len(text)) // 2
  rightPad = width - len(text) - leftPad
  return (" " * leftPad) + f"{color}{text}{ANSI_RESET}" + (" " * rightPad)

def _clearLine():
  print("\r" + (" " * CLEAR_LINE_WIDTH) + "\r", end="", flush=True)

class Animator:
  @dataclass
  class _ColumnWidths:
    fieldWidth: int
    markerWidth: int
    colWidth: int

  @staticmethod
  def colorWrap(ansiColor, text):
    return f"{ansiColor}{text}{ANSI_RESET}"

  @staticmethod
  def _renderTable(activeKey, diffs, authorParams, left, right, clear, conflictIndex, conflictTotal):
    def _clearAndGetTermWidth():
      if clear:
        os.system('cls' if os.name == 'nt' else 'clear')
      try:
        return shutil.get_terminal_size((120, 20)).columns
      except Exception:
        return 120

    termWidth = _clearAndGetTermWidth()
    minCol = 10
    maxCol = 40
    widths = Animator._ColumnWidths(fieldWidth=14, markerWidth=16, colWidth=minCol)
    maxLeft = max((len(str(lval)) for _, lval, _ in diffs), default=len("LEFT"))
    maxRight = max((len(str(rval)) for _, _, rval in diffs), default=len("RIGHT"))
    maxChosen = max((len(str(authorParams.get(key, ""))) for key, _, _ in diffs), default=len("CHOSEN"))
    baseWidth = max(len("CHOSEN"), maxLeft, maxRight, maxChosen, minCol)
    widths.colWidth = max(minCol, min(baseWidth, maxCol))
    totalWidth = widths.fieldWidth + (widths.markerWidth * 2) + (widths.colWidth * 3) + 5
    while totalWidth > termWidth and widths.colWidth > minCol:
      widths.colWidth -= 1
      totalWidth = widths.fieldWidth + (widths.markerWidth * 2) + (widths.colWidth * 3) + 5
    fieldLabel = _padValue("FIELD", widths.fieldWidth)
    leftLabel = _padValue("LEFT", widths.colWidth)
    chosenLabel = _padValue("CHOSEN", widths.colWidth)
    rightLabel = _padValue("RIGHT", widths.colWidth)
    leftMarkerLabel = _padValue("", widths.colWidth)
    rightMarkerLabel = _padValue("", widths.colWidth)
    print(
      f"{ANSI_WHITE}{fieldLabel}{ANSI_RESET} "
      f"{ANSI_CYAN}{leftLabel}{ANSI_RESET} "
      f"{leftMarkerLabel} "
      f"{ANSI_GREEN}{chosenLabel}{ANSI_RESET} "
      f"{rightMarkerLabel} "
      f"{ANSI_YELLOW}{rightLabel}{ANSI_RESET}"
    )
    print()
    chosenMap = {key: authorParams.get(key, "") for key, _, _ in diffs}
    for key, lval, rval in diffs:
      ltxt = f"{ANSI_CYAN}{_padValue(lval, widths.colWidth)}{ANSI_RESET}"
      rtxt = f"{ANSI_YELLOW}{_padValue(rval, widths.colWidth)}{ANSI_RESET}"
      chosenRaw = chosenMap.get(key, "")
      chosen = _padValue(chosenRaw, widths.colWidth) if chosenRaw else (" " * widths.colWidth)
      ctxt = f"{ANSI_GREEN}{chosen}{ANSI_RESET}"
      prefix = "> " if key == activeKey else "  "
      keyTxt = _padValue(f"{prefix}{key}", widths.fieldWidth)
      leftMarker = LEFT_MARKER if key in authorParams and authorParams.get(key) == left.get(key) else ""
      rightMarker = RIGHT_MARKER if key in authorParams and authorParams.get(key) == right.get(key) else ""
      leftMarkerTxt = _centerColored(leftMarker, widths.colWidth, ANSI_CYAN)
      rightMarkerTxt = _centerColored(rightMarker, widths.colWidth, ANSI_YELLOW)
      row = f"{keyTxt} {ltxt} {leftMarkerTxt} {ctxt} {rightMarkerTxt} {rtxt}"
      print(row)
    count = f"CONFLICT {conflictIndex + 1}/{conflictTotal}"
    countText = f"{ANSI_CYAN}{ANSI_INVERT}{count}{ANSI_RESET}"
    instructions = f"Use {RIGHT_ARROW} for left, {LEFT_ARROW} for right, or E to edit."
    pad = max(0, termWidth - len(count) - len(instructions) - 1)
    print()
    print(f"{instructions}{' ' * pad}{countText}")

  @staticmethod
  def _spinningAnimation(chars, onLoad, onDone, stopEvent, pauseEvent, showDone):
    for char in cycle(chars):
      if stopEvent.is_set():
        break
      if pauseEvent.is_set():
        time.sleep(PAUSE_SLEEP_SECONDS)
        continue
      wrappedChar = Animator.colorWrap(ANSI_GRAY, char)
      print(f"\r{wrappedChar} {onLoad}", end="", flush=True)
      time.sleep(SPINNER_SLEEP_SECONDS)
    if showDone and onDone is not None:
      checkmark = Animator.colorWrap(ANSI_GREEN, CHECKMARK_CHAR)
      text = Animator.colorWrap(ANSI_GRAY, onDone)
      print(f"\r{checkmark} {text}    ")
    else:
      _clearLine()


  @staticmethod
  def spinner(onLoad, onDone, func, *args, showDone: bool = True):
    stopEvent = threading.Event()
    pauseEvent = threading.Event()
    animThread = threading.Thread(
      target=Animator._spinningAnimation, 
      args=(SPINNER_CHARS, onLoad, onDone, stopEvent, pauseEvent, showDone)
    )
    animThread.start()
    result = func() if (len(args) == 0) else func(*args) 
    stopEvent.set()
    animThread.join()

    return result

  @staticmethod
  def startSpinner(onLoad, onDone, showDone: bool = True):
    stopEvent = threading.Event()
    pauseEvent = threading.Event()
    animThread = threading.Thread(
      target=Animator._spinningAnimation,
      args=(SPINNER_CHARS, onLoad, onDone, stopEvent, pauseEvent, showDone)
    )
    animThread.start()
    return SpinnerHandle(stopEvent, pauseEvent, animThread)


class SpinnerHandle:
  def __init__(self, stopEvent, pauseEvent, thread):
    self._stopEvent = stopEvent
    self._pauseEvent = pauseEvent
    self._thread = thread

  def pause(self):
    self._pauseEvent.set()
    _clearLine()

  def resume(self):
    self._pauseEvent.clear()

  def stop(self):
    self._stopEvent.set()
    self._thread.join()
