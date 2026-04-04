from pathlib import Path
from Utils.Constants import *
import zipfile
import shutil
import os
import re
import html

# Precompiled regex patterns to avoid recompilation overhead on hot paths.
_AMP_PATTERN = re.compile("&amp;")
_DOT_PATTERN = re.compile("\\.(?=\\w\\w)")
_AUTHOR_CLEAN_PATTERN = re.compile("^by-|^By-|^By |^by |[^\\w ^'^\\.^-]|_|\\d")
_AUTHOR_SPLIT_PATTERN = re.compile(r",|&|&amp;|\band\b")
_SIMILARITY_PATTERN = re.compile("[^\\w]| |\\d|_")
_FIGURE_PATTERN = re.compile(r"<figure\b[^>]*>.*?</figure>", re.IGNORECASE | re.DOTALL)
_IMG_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")

class Utility:
  def cleanDocument(document: str, type: str):
    def uppercaseMatch(match):
      return match.group(0).upper()

    match type:
      case "author_single":
        document = document.split("@")
        document = _AMP_PATTERN.sub("&", document[0])
        document = _DOT_PATTERN.sub(" ", document)
        document = _AUTHOR_CLEAN_PATTERN.sub("", document).strip()
        document = re.sub("^\\w| \\w", uppercaseMatch, document)
        return document
      case "author_multiple":
        documents = _AUTHOR_SPLIT_PATTERN.split(document)
        return [_AUTHOR_CLEAN_PATTERN.sub("", doc).strip() for doc in documents]
      case "similarity":
        return _SIMILARITY_PATTERN.sub("", document).lower()
      case "article":
        return document
    return document

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

  def _build_excerpt(text, max_words=100):
    if text is None:
      return ""

    text_without_media = _FIGURE_PATTERN.sub(" ", str(text))
    text_without_media = _IMG_PATTERN.sub(" ", text_without_media)

    plain = html.unescape(text_without_media)
    plain = _TAG_PATTERN.sub(" ", plain)
    plain = _WHITESPACE_PATTERN.sub(" ", plain).strip()

    if not plain:
      return ""

    words = plain.split(" ")
    if len(words) <= max_words:
      return plain
    return " ".join(words[:max_words])

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
