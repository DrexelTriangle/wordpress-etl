import json
import os
from pathlib import Path

from Animator import Animator
from Extractor import Extractor
from Sanitizer.AuthorSanitizer import AuthorSanitizer
from Translator.ArticleTranslator import ArticleTranslator
from Translator.AuthorTranslator import AuthorTranslator
from Translator.GuestAuthorTranslator import GuestAuthorTranslator
from Utils.Constants import UNZIPPED_FILES, ZIP_FILE
from Utils.Utility import Utility

animator = Animator()
completedSteps = []

def runStep(onLoad, onDone, func, *args, showDone: bool = True):
  result = animator.spinner(onLoad, onDone, func, *args, showDone=showDone)
  completedSteps.append(onDone)
  return result

def extractData():
  Utility.unzip(ZIP_FILE)
  extractor = Extractor(*UNZIPPED_FILES)
  return runStep("Extracting...", "Extracted", extractor.getData)

def translateData(extracted):
  translators = {
    "articles": ArticleTranslator(extracted["art"]),
    "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
    "auth": AuthorTranslator(extracted["auth"]),
  }
  runStep("Translating...", "Translated", lambda: [translators[key].translate() for key in translators])
  return translators

def logOutputs(translators):
  logTargets = [
    ("Logging articles...", "Logged articles", translators["articles"]._log, Path("logs") / "articles"),
    ("Logging guest authors...", "Logged guest authors", translators["gAuth"]._log, Path("logs") / "gAuth.json"),
    ("Logging authors...", "Logged authors", translators["auth"]._log, Path("logs") / "auth.json"),
  ]
  for onLoad, onDone, func, path in logTargets:
    runStep(onLoad, onDone, func, path)

def sanitizeAuthors(translators):
  authors = translators["auth"].listAuthors()
  authSanitizer = AuthorSanitizer(authors, {})
  authSpinner = animator.startSpinner("Sanitizing authors...", "Sanitized authors", showDone=False)
  def onManualStart():
    authSpinner.pause()

  authors = authSanitizer.sanitize(
    manualStart=onManualStart,
    manualEnd=authSpinner.resume,
  )
  authSpinner.stop()
  completedSteps.append("Sanitized authors")
  return authors

def writeAuthorOutput(authors):
  def outputAuthors():
    Path("logs/auth_output.json").write_text(
      json.dumps({str(i): authors[i].data for i in range(len(authors))}, indent=4),
      encoding="utf-8",
    )
  runStep("Writing author output...", "Wrote author output", outputAuthors)

def printChecklist():
  os.system('cls' if os.name == 'nt' else 'clear')
  checkmark = Animator.colorWrap('\033[32m', '✓')
  for step in completedSteps:
    text = Animator.colorWrap('\033[90m', step)
    print(f"{checkmark} {text}")

extracted = extractData()
translators = translateData(extracted)
logOutputs(translators)
authors = sanitizeAuthors(translators)
writeAuthorOutput(authors)
printChecklist()
