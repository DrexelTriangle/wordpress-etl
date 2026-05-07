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
ANSI_RED = "\033[31m"
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
  _activeHandles = set()
  _activeLock = threading.Lock()

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

    # Column sizing — no marker columns
    fieldWidth = 14
    minCol, maxCol = 10, 40
    maxLeft   = max((len(str(lval)) for _, lval, _ in diffs), default=len("LEFT"))
    maxRight  = max((len(str(rval)) for _, _, rval in diffs), default=len("RIGHT"))
    maxChosen = max((len(str(authorParams.get(k, ""))) for k, _, _ in diffs), default=len("CHOSEN"))
    colWidth  = max(minCol, min(max(maxLeft, maxRight, maxChosen, len("CHOSEN")), maxCol))
    tableWidth = 2 + fieldWidth + 3 * colWidth + 3
    while tableWidth > termWidth and colWidth > minCol:
      colWidth -= 1
      tableWidth = 2 + fieldWidth + 3 * colWidth + 3

    # Box header
    title    = f"CONFLICT {conflictIndex + 1}/{conflictTotal}"
    subtitle = "Duplicate author entries — pick a value for each field"
    boxInner = f"  {title}  │  {subtitle}  "
    boxWidth = max(len(boxInner), tableWidth)
    boxInner = boxInner.ljust(boxWidth)
    print(f"{ANSI_CYAN}╔{'═' * boxWidth}╗{ANSI_RESET}")
    print(f"{ANSI_CYAN}║{ANSI_RESET}{ANSI_WHITE}{boxInner}{ANSI_RESET}{ANSI_CYAN}║{ANSI_RESET}")
    print(f"{ANSI_CYAN}╚{'═' * boxWidth}╝{ANSI_RESET}")
    print()

    # Column headers + top separator
    sep = "─" * tableWidth
    print(f"  {ANSI_GRAY}{_padValue('FIELD', fieldWidth)} {_padValue('LEFT', colWidth)} {_padValue('CHOSEN', colWidth)} {_padValue('RIGHT', colWidth)}{ANSI_RESET}")
    print(f"  {ANSI_GRAY}{sep}{ANSI_RESET}")
    print()

    # Rows
    chosenMap = {key: authorParams.get(key, "") for key, _, _ in diffs}
    for key, lval, rval in diffs:
      isActive  = key == activeKey
      chosenRaw = chosenMap.get(key, "")
      keyTxt    = _padValue(key, fieldWidth)
      ltxt      = _padValue(lval, colWidth)
      rtxt      = _padValue(rval, colWidth)
      chosen    = _padValue(chosenRaw, colWidth) if chosenRaw else " " * colWidth
      marker    = "▶ " if isActive else "  "

      if isActive:
        print(f"{ANSI_GREEN}{marker}{keyTxt} {ltxt} {chosen} {rtxt}{ANSI_RESET}")
      else:
        chosenColored = f"{ANSI_GREEN}{chosen}{ANSI_RESET}" if chosenRaw else " " * colWidth
        print(f"  {ANSI_GRAY}{keyTxt}{ANSI_RESET} {ANSI_CYAN}{ltxt}{ANSI_RESET} {chosenColored} {ANSI_YELLOW}{rtxt}{ANSI_RESET}")

    # Footer separator + instructions
    print()
    print(f"  {ANSI_GRAY}{sep}{ANSI_RESET}")
    print(f"  {LEFT_ARROW} left  │  {RIGHT_ARROW} right  │  E to edit")

  @staticmethod
  def _spinningAnimation(chars, onLoad, onDone, stopEvent, pauseEvent, showDone, getSubStep=None):
    for char in cycle(chars):
      if stopEvent.is_set():
        break
      if pauseEvent.is_set():
        time.sleep(PAUSE_SLEEP_SECONDS)
        continue
      wrappedChar = Animator.colorWrap(ANSI_GRAY, char)
      subStep = getSubStep() if getSubStep else ""
      subStepText = f"  {ANSI_GRAY}→ {subStep}{ANSI_RESET}" if subStep else ""
      print(f"\r\033[2K{wrappedChar} {onLoad}{subStepText}", end="", flush=True)
      time.sleep(SPINNER_SLEEP_SECONDS)
    if showDone and onDone is not None:
      checkmark = Animator.colorWrap(ANSI_GREEN, CHECKMARK_CHAR)
      text = Animator.colorWrap(ANSI_GRAY, onDone)
      print(f"\r\033[2K{checkmark} {text}")
    else:
      _clearLine()


  @staticmethod
  def spinner(onLoad, onDone, func, *args, showDone: bool = True):
    spinnerHandle = Animator.startSpinner(onLoad, onDone, showDone=False)
    try:
      result = func() if (len(args) == 0) else func(*args)
    except Exception:
      spinnerHandle.stop()
      errorMark = Animator.colorWrap(ANSI_RED, "✗")
      errorText = Animator.colorWrap(ANSI_GRAY, f"Error occurred: {onLoad}")
      print(f"\r{errorMark} {errorText}    ")
      raise
    spinnerHandle.stop()
    if showDone and onDone is not None:
      checkmark = Animator.colorWrap(ANSI_GREEN, CHECKMARK_CHAR)
      text = Animator.colorWrap(ANSI_GRAY, onDone)
      print(f"\r{checkmark} {text}    ")
    return result

  @staticmethod
  def startSpinner(onLoad, onDone, showDone: bool = True):
    stopEvent = threading.Event()
    pauseEvent = threading.Event()
    subStepContainer = [""]
    animThread = threading.Thread(
      target=Animator._spinningAnimation,
      args=(SPINNER_CHARS, onLoad, onDone, stopEvent, pauseEvent, showDone, lambda: subStepContainer[0])
    )
    spinnerHandle = SpinnerHandle(stopEvent, pauseEvent, animThread, Animator._onHandleStopped, subStepContainer)
    Animator._registerHandle(spinnerHandle)
    animThread.start()
    return spinnerHandle

  @staticmethod
  def stopAllSpinners():
    with Animator._activeLock:
      handles = list(Animator._activeHandles)
    for handle in handles:
      handle.stop()

  @staticmethod
  def _registerHandle(handle):
    with Animator._activeLock:
      Animator._activeHandles.add(handle)

  @staticmethod
  def _onHandleStopped(handle):
    with Animator._activeLock:
      Animator._activeHandles.discard(handle)


class SpinnerHandle:
  def __init__(self, stopEvent, pauseEvent, thread, onStop, subStepContainer=None):
    self._stopEvent = stopEvent
    self._pauseEvent = pauseEvent
    self._thread = thread
    self._onStop = onStop
    self._isStopped = threading.Event()
    self._subStepContainer = subStepContainer if subStepContainer is not None else [""]

  def report(self, msg):
    if not self._isStopped.is_set():
      self._subStepContainer[0] = msg

  def pause(self):
    if self._isStopped.is_set():
      return
    self._pauseEvent.set()
    _clearLine()

  def resume(self):
    if self._isStopped.is_set():
      return
    self._pauseEvent.clear()

  def stop(self):
    if self._isStopped.is_set():
      return
    self._isStopped.set()
    self._stopEvent.set()
    if self._thread.is_alive() and threading.current_thread() is not self._thread:
      self._thread.join()
    self._onStop(self)
