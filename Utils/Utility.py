from pathlib import Path
from Utils.Constants import *
import zipfile
import shutil
import os

class Utility:
  def unzip(zipPath):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zipPath, 'r') as zip_ref:
      zip_ref.extractall(DATA_DIR)


  def _delete_dir(dir):
    path = Path(dir)
    if not path.exists():
      return
    if path.is_dir():
      shutil.rmtree(path, ignore_errors=True)
      return
    path.unlink(missing_ok=True)

  
  def _html_text_norm(text):
    result = ''
    
    if (text is None):
      return None 
    result = text.replace('&amp;', '&')
    result = result.replace('&nbsp;', ' ')
    return result

  def _readChoice():
      try:
          if os.name == "nt":
              import msvcrt
              while True:
                  ch = msvcrt.getch()
                  if ch in (b"\x00", b"\xe0"):
                      code = msvcrt.getch()
                      if code == b"K":
                          return "RIGHT"
                      if code == b"M":
                          return "LEFT"
                  elif ch in (b"e", b"E"):
                      return "E"
                  elif ch in (b"l", b"L", b"\r", b"\n"):
                      return "LEFT"
                  elif ch in (b"r", b"R"):
                      return "RIGHT"
          else:
              import sys
              import termios
              import tty
              fd = sys.stdin.fileno()
              old = termios.tcgetattr(fd)
              try:
                  tty.setraw(fd)
                  ch = sys.stdin.read(1)
                  if ch == "\x1b":
                      seq = sys.stdin.read(2)
                      if seq == "[D":
                          return "RIGHT"
                      if seq == "[C":
                          return "LEFT"
                  elif ch in ("e", "E"):
                      return "E"
                  elif ch in ("l", "L", "\r", "\n"):
                      return "LEFT"
                  elif ch in ("r", "R"):
                      return "RIGHT"
              finally:
                  termios.tcsetattr(fd, termios.TCSADRAIN, old)
      except Exception:
          pass
