import json
import os
from pathlib import Path
from Animator import Animator
from Extractor import Extractor
from Sanitizer.GuestAuthorPolicy import GuestAuthorPolicy
from Sanitizer.AuthorPolicy import AuthorPolicy
from Sanitizer.AuthorSanitizer import AuthorSanitizer
from Translator.ArticleTranslator import ArticleTranslator
from Translator.AuthorTranslator import AuthorTranslator
from Translator.GuestAuthorTranslator import GuestAuthorTranslator
from Utils.Constants import UNZIPPED_FILES, ZIP_FILE
from Utils.Utility import Utility

from App import App 


app = App()

# EXTRACTION
Utility.unzip(ZIP_FILE)
extractor = Extractor(*UNZIPPED_FILES)
extracted = app.run("Extracting...", "Extracted", extractor.getData)



# TRANSLATION
translators = {
    "articles": ArticleTranslator(extracted["art"]),
    "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
    "auth": AuthorTranslator(extracted["auth"]),
}
app.run("Translating...", "Translated", lambda: [translators[key].translate() for key in translators])



# LOGGING
logTargets = [
    ("Logging articles...", "Logged articles", translators["articles"]._log, Path("logs") / "articles"),
    ("Logging guest authors...", "Logged guest authors", translators["gAuth"]._log, Path("logs") / "gAuth.json"),
    ("Logging authors...", "Logged authors", translators["auth"]._log, Path("logs") / "auth.json"),
]
for onLoad, onDone, func, path in logTargets:
    app.run(onLoad, onDone, func, path)



# SANITATION
key = "auth"
name = "authors"
authors = translators[key].listAuthors()
authSanitizer = AuthorSanitizer(authors, AuthorPolicy(authors)) if key == "auth" else AuthorSanitizer(authors, GuestAuthorPolicy(authors))
authSpinner = app.animator.startSpinner(f"Sanitizing {name}...", f"Sanitized {name}", showDone=False)
def onManualStart():
    authSpinner.pause()

authors = authSanitizer.sanitize(
   manualStart=onManualStart,
   manualEnd=authSpinner.resume,
)

authSpinner.stop()
app.completedSteps.append(f"Sanitized {name}")



# OUTPUT
def outputAuthors():
    Path(path).write_text(
      json.dumps({str(i): authors[i].data for i in range(len(authors))}, indent=4),
      encoding="utf-8",
    )

app.run(f"Writing {name} output...", f"Wrote {name} output", outputAuthors)
app.printChecklist()

