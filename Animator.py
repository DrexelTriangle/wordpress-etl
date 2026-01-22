import sys 
import time
import threading

class Animator:
  def __init__(self):
    self.animations = {
      "spin": ...
    }

  
  def color_wrap(ansi_color, text):
    return f"{ansi_color}{text}\033[0m"


  def spinning_animation(chars, text, onLoad, onDone, e):
    idx = 0
    while not e.is_set():
      char = Animator.color_wrap('\033[90m', chars[idx % len(chars)])
      sys.stdout.write(f"\r{char} {onLoad}")
      sys.stdout.flush()
      idx += 1
      time.sleep(0.075)
    checkmark = Animator.color_wrap('\033[32m', '✓')
    text = Animator.color_wrap('\033[90m', onDone)
    sys.stdout.write(f"\r{checkmark} {text}    \n")


  def Spinner(self, onLoad, onDone, func, *args):
    chars = "⣾⣽⣻⢿⡿⣟⣯⣷"
    text = " Extracting..."
    stopEvent = threading.Event()
    animThread = threading.Thread(
      target=Animator.spinning_animation, 
      args=(chars, text, onLoad, onDone, stopEvent)
    )
    animThread.start()
    result = func() if (len(args) == 0) else func(*args) 
    stopEvent.set()
    animThread.join()

    return result