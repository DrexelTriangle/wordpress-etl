from time import sleep
from pathlib import Path
from Extractor import Extractor
from Animator import Animator
from Sanitizer.GuestAuthorSanitizer import GuestAuthorSanitizer
from Translator.Translator import *
from Utils.Utility import *
from Utils.Constants import *
from Translator.ArticleTranslator import *
from Translator.GuestAuthorTranslator import *
from Translator.AuthorTranslator import *
from Sanitizer.AuthorSanitizer import *

# TODO: python library dependency checks

animator = Animator()

# unzip export data
Utility.unzip(ZIP_FILE)

completed_steps = []

def run_step(on_load, on_done, func, *args, show_done: bool = True):
  result = animator.Spinner(on_load, on_done, func, *args, show_done=show_done)
  completed_steps.append(on_done)
  return result

# STEP 1: Extraction
extractor = Extractor(*UNZIPPED_FILES)
extracted = run_step("Extracting...", "Extracted", extractor.getData)

# Step 2: Translation
translators = {
  "articles": ArticleTranslator(extracted["art"]),
  "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
  "auth": AuthorTranslator(extracted["auth"])
}

translate = lambda: [translators[key].translate() for key in translators]
run_step("Translating...", "Translated", translate)

# DEBUG: logging
run_step("Logging articles...", "Logged articles", translators["articles"]._log, 'logs/articles/.')
run_step("Logging guest authors...", "Logged guest authors", translators["gAuth"]._log, 'logs/gAuth.json')
run_step("Logging authors...", "Logged authors", translators["auth"]._log, 'logs/auth.json')

# Step 3: Sanitizing
authors = translators["auth"].listAuthors()
authSanitizer = AuthorSanitizer(authors, {})

auth_spinner = animator.start_spinner("Sanitizing authors...", "Sanitized authors", show_done=False)
manual_state = {"used": False}

def on_manual_start():
  manual_state["used"] = True
  auth_spinner.pause()

authors = authSanitizer.sanitize(
  on_manual_start=on_manual_start,
  on_manual_end=auth_spinner.resume,
)
auth_spinner.stop()
completed_steps.append("Sanitized authors")

outputAuthors = lambda: Path("logs/auth_output.json").write_text(
  json.dumps({str(i): authors[i].data for i in range(len(authors))}, indent=4),
  encoding="utf-8",
)

run_step(
  "Writing author output...",
  "Wrote author output",
  outputAuthors,
  show_done=not manual_state["used"],
)

if manual_state["used"]:
  checkmark = Animator.color_wrap('\033[32m', '✓')
  for step in completed_steps:
    text = Animator.color_wrap('\033[90m', step)
    print(f"{checkmark} {text}")
