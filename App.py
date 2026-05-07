import json
import os
from pathlib import Path
from Animator import Animator, ANSI_GREEN, ANSI_GRAY, ANSI_RED, CHECKMARK_CHAR
from Extractor import Extractor
from Sanitizer.GuestAuthorPolicy import GuestAuthorPolicy
from Sanitizer.AuthorPolicy import AuthorPolicy
from Sanitizer.AuthorSanitizer import AuthorSanitizer
from Sanitizer.ArticleAuthorMatcher import ArticleAuthorMatcher
from Sanitizer.ArticleContentSanitizer import ArticleContentSanitizer
from Translator.ArticleTranslator import ArticleTranslator
from Translator.AuthorTranslator import AuthorTranslator
from Translator.GuestAuthorTranslator import GuestAuthorTranslator
from Utils.Constants import UNZIPPED_FILES, ZIP_FILE
from Utils.Utility import Utility

class App:
    def __init__(self):
        self.animator = Animator()
        self.completedSteps = []
        self.stepCount = 0

    def shutdown(self):
        self.animator.stopAllSpinners()

    def runStep(self, onLoad, onDone, func, *args, showDone: bool = True):
        self.stepCount += 1
        result = self.animator.spinner(f"[{self.stepCount}] {onLoad}", onDone, func, *args, showDone=showDone)
        self.completedSteps.append(onDone)
        return result

    def extractData(self):
        self.stepCount += 1
        spinner = self.animator.startSpinner(f"[{self.stepCount}] Extracting...", "Extracted", showDone=False)
        try:
            spinner.report("unzipping wp-export.zip")
            Utility.unzip(ZIP_FILE)
            extractor = Extractor(*UNZIPPED_FILES)
            result = extractor.getData(on_progress=spinner.report)
        except Exception:
            spinner.stop()
            errorMark = Animator.colorWrap(ANSI_RED, '✗')
            errorText = Animator.colorWrap(ANSI_GRAY, f"Error occurred: [{self.stepCount}] Extracting...")
            print(f"\r{errorMark} {errorText}    ")
            raise
        spinner.stop()
        checkmark = Animator.colorWrap(ANSI_GREEN, CHECKMARK_CHAR)
        print(f"\r{checkmark} {Animator.colorWrap(ANSI_GRAY, 'Extracted')}    ")
        self.completedSteps.append("Extracted")
        return result

    def translateData(self, extracted):
        translators = {
            "articles": ArticleTranslator(extracted["art"]),
            "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
            "auth": AuthorTranslator(extracted["auth"]),
        }
        self.stepCount += 1
        spinner = self.animator.startSpinner(f"[{self.stepCount}] Translating...", "Translated", showDone=False)
        try:
            translators["auth"].translate(on_progress=spinner.report)
            translators["gAuth"].translate(on_progress=spinner.report)
            translators["articles"].translate(on_progress=spinner.report)
        except Exception:
            spinner.stop()
            errorMark = Animator.colorWrap(ANSI_RED, '✗')
            errorText = Animator.colorWrap(ANSI_GRAY, f"Error occurred: [{self.stepCount}] Translating...")
            print(f"\r{errorMark} {errorText}    ")
            raise
        spinner.stop()
        checkmark = Animator.colorWrap(ANSI_GREEN, CHECKMARK_CHAR)
        print(f"\r{checkmark} {Animator.colorWrap(ANSI_GRAY, 'Translated')}    ")
        self.completedSteps.append("Translated")
        return translators

    def logOutputs(self, translators):
        logTargets = [
            ("Logging articles...", "Logged articles", translators["articles"]._log, Path("logs") / "articles"),
            ("Logging guest authors...", "Logged guest authors", translators["gAuth"]._log, Path("logs") / "gAuth.json"),
            ("Logging authors...", "Logged authors", translators["auth"]._log, Path("logs") / "auth.json"),
        ]
        for onLoad, onDone, func, path in logTargets:
            self.runStep(onLoad, onDone, func, path)

    def sanitizeAuthors(self, translators, key, name):
        authors = translators[key].listAuthors()
        authSanitizer = AuthorSanitizer(authors, AuthorPolicy(authors)) if key == "auth" else AuthorSanitizer(authors, GuestAuthorPolicy(authors))
        self.stepCount += 1
        authSpinner = self.animator.startSpinner(f"[{self.stepCount}] Sanitizing {name}...", f"Sanitized {name}", showDone=False)
        def onManualStart():
            authSpinner.pause()

        try:
            authors = authSanitizer.sanitize(
                manualStart=onManualStart,
                manualEnd=authSpinner.resume,
                on_progress=authSpinner.report,
            )
        finally:
            authSpinner.stop()
        self.completedSteps.append(f"Sanitized {name}")
        return authors

    def writeAuthorOutput(self, authors, path, name):
        def outputAuthors():
            Path(path).write_text(
            json.dumps({str(i): authors[i].data for i in range(len(authors))}, indent=4),
            encoding="utf-8",
            )
        self.runStep(f"Writing {name} output...", f"Wrote {name} output", outputAuthors)

    def combineAndReindexAuthors(self, authors, guestAuthors):
        combined = authors
        authNames = {auth.data["display_name"] for auth in authors}
        usedIds = {
            auth.data["id"]
            for auth in authors
            if auth.data.get("id") is not None
        }
        nextId = (max(usedIds) + 1) if usedIds else 0
        dupes = {}
        for idx, gAuth in enumerate(guestAuthors):
            # only merge in guest author if name doesn't exist within author list
            # TODO: 
            # correctness 
            # -> ~all~ first + last names correspond to unique name => every author has unique name
            # -> currently exists edge case where Jake Billman from 2004 is different than Jake Billman from 2024
            gAuthName = gAuth.data["display_name"]
            if gAuthName not in authNames:
                while nextId in usedIds:
                    nextId += 1
                gAuth.data["id"] = nextId
                usedIds.add(nextId)
                nextId += 1
                authNames.add(gAuthName)
                combined.append(gAuth)
            else:
                dupes.update({len(dupes):str(gAuth)})
        return combined

    def sanitizeArticleAuthors(self, translators, allAuthors, best_guess=False):
        articles = translators["articles"].getObjList()
        articleSanitizer = ArticleAuthorMatcher(articles, allAuthors, best_guess=best_guess)
        self.stepCount += 1
        articleSpinner = self.animator.startSpinner(f"[{self.stepCount}] Sanitizing article authors...", "Sanitized article authors", showDone=False)

        manualStart = None
        manualEnd = None
        if not best_guess:
            def manualStart():
                articleSpinner.pause()
            manualEnd = articleSpinner.resume

        try:
            sanitizedArticles = articleSanitizer.sanitize(
                manualStart=manualStart,
                manualEnd=manualEnd,
                on_progress=articleSpinner.report,
            )
        finally:
            articleSpinner.stop()
        self.completedSteps.append("Sanitized article authors")
        return sanitizedArticles

    def sanitizeArticleContent(self, sanitizedArticles):
        contentSanitizer = ArticleContentSanitizer(sanitizedArticles)
        self.runStep("Sanitizing article content...", "Sanitized article content", contentSanitizer.sanitize)
        for article in sanitizedArticles:
            text = article.get("text", "")
            categories = article.get("categories", [])
            normalized_categories = {
                str(category).strip().lower() for category in categories if category is not None
            }
            is_comics_or_puzzles = bool(
                normalized_categories
                & {
                    "comics",
                    "comic",
                    "comics & puzzles",
                    "puzzles",
                    "crossword",
                    "sudoku",
                }
            )
            has_puzzle_embed = "[puzzleme" in text.lower() or "pm-embed-div" in text.lower()
            if is_comics_or_puzzles or has_puzzle_embed:
                article["excerpt"] = ""
                continue

            article["excerpt"] = Utility._build_excerpt(text, max_words=100)
        return sanitizedArticles

    def writeArticleOutput(self, sanitizedArticles):
        def outputArticles():
            Path("logs/article_output.json").write_text(
                json.dumps({str(i): (sanitizedArticles[i].data if hasattr(sanitizedArticles[i], "data") else sanitizedArticles[i]) for i in range(len(sanitizedArticles))}, indent=4),
                encoding="utf-8",
            )
        self.runStep("Writing article output...", "Wrote article output", outputArticles)

    def printChecklist(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        checkmark = Animator.colorWrap('\033[32m', '✓')
        for step in self.completedSteps:
            text = Animator.colorWrap('\033[90m', step)
            print(f"{checkmark} {text}")
