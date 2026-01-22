import sys 
import time
import threading

class Animator:
  def color_wrap(ansi_color, text):
    return f"{ansi_color}{text}\033[0m"


  def spinning_animation(chars, onLoad, onDone, e, pause_event, show_done):
    idx = 0
    while not e.is_set():
      if pause_event.is_set():
        time.sleep(0.05)
        continue
      char = Animator.color_wrap('\033[90m', chars[idx % len(chars)])
      sys.stdout.write(f"\r{char} {onLoad}")
      sys.stdout.flush()
      idx += 1
      time.sleep(0.075)
    if show_done and onDone is not None:
      checkmark = Animator.color_wrap('\033[32m', '✓')
      text = Animator.color_wrap('\033[90m', onDone)
      sys.stdout.write(f"\r{checkmark} {text}    \n")
    else:
      sys.stdout.write("\r" + (" " * 80) + "\r")
      sys.stdout.flush()


  def Spinner(self, onLoad, onDone, func, *args, show_done: bool = True):
    chars = "⣾⣽⣻⢿⡿⣟⣯⣷"
    stopEvent = threading.Event()
    pauseEvent = threading.Event()
    animThread = threading.Thread(
      target=Animator.spinning_animation, 
      args=(chars, onLoad, onDone, stopEvent, pauseEvent, show_done)
    )
    animThread.start()
    result = func() if (len(args) == 0) else func(*args) 
    stopEvent.set()
    animThread.join()

    return result

  def start_spinner(self, onLoad, onDone, show_done: bool = True):
    chars = "⣾⣽⣻⢿⡿⣟⣯⣷"
    stopEvent = threading.Event()
    pauseEvent = threading.Event()
    animThread = threading.Thread(
      target=Animator.spinning_animation,
      args=(chars, onLoad, onDone, stopEvent, pauseEvent, show_done)
    )
    animThread.start()
    return SpinnerHandle(stopEvent, pauseEvent, animThread)


class SpinnerHandle:
  def __init__(self, stop_event, pause_event, thread):
    self._stop_event = stop_event
    self._pause_event = pause_event
    self._thread = thread

  def pause(self):
    self._pause_event.set()
    sys.stdout.write("\r" + (" " * 80) + "\r")
    sys.stdout.flush()

  def resume(self):
    self._pause_event.clear()

  def stop(self):
    self._stop_event.set()
    self._thread.join()
