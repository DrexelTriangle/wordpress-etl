import json
import os
from pathlib import Path
from Animator import Animator
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
from Formatter.ArticleFormatter import ArticleFormatter
from Formatter.ArtAuthFormatter import ArtAuthFormatter
from Formatter.AuthorFormatter import AuthorFormatter
from Formatter.Formatter import Formatter


class App:
    def __init__(self):
        self.animator = Animator()
        self.completedSteps = []
    
    def runStep(self, onLoad, onDone, func, *args, showDone: bool = True):
        result = self.animator.spinner(onLoad, onDone, func, *args, showDone=showDone)
        self.completedSteps.append(onDone)
        return result

    def extractData(self):
        Utility.unzip(ZIP_FILE)
        extractor = Extractor(*UNZIPPED_FILES)
        return self.runStep("Extracting...", "Extracted", extractor.getData)

    def translateData(self, extracted):
        translators = {
            "articles": ArticleTranslator(extracted["art"]),
            "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
            "auth": AuthorTranslator(extracted["auth"]),
        }
        self.runStep("Translating...", "Translated", lambda: [translators[key].translate() for key in translators])
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
        authSpinner = self.animator.startSpinner(f"Sanitizing {name}...", f"Sanitized {name}", showDone=False)
        def onManualStart():
            authSpinner.pause()

        authors = authSanitizer.sanitize(
            manualStart=onManualStart,
            manualEnd=authSpinner.resume,
        )
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

    def sanitizeArticleAuthors(self, translators, authors, guestAuthors):
        articles = translators["articles"].getObjList()
        articleSanitizer = ArticleAuthorMatcher(articles, authors, guestAuthors)
        articleSpinner = self.animator.startSpinner("Sanitizing article authors...", "Sanitized article authors", showDone=False)
        def onManualStart():
            articleSpinner.pause()

        sanitizedArticles = articleSanitizer.sanitize(
            manualStart=onManualStart,
            manualEnd=articleSpinner.resume,
        )
        articleSpinner.stop()
        self.completedSteps.append("Sanitized article authors")
        return sanitizedArticles

    def sanitizeArticleContent(self, sanitizedArticles):
        contentSanitizer = ArticleContentSanitizer(sanitizedArticles)
        self.runStep("Sanitizing article content...", "Sanitized article content", contentSanitizer.sanitize)
        return sanitizedArticles

    def writeArticleOutput(self, sanitizedArticles):
        def outputArticles():
            Path("logs/article_output.json").write_text(
                json.dumps({str(i): (sanitizedArticles[i].data if hasattr(sanitizedArticles[i], "data") else sanitizedArticles[i]) for i in range(len(sanitizedArticles))}, indent=4),
                encoding="utf-8",
            )
        self.runStep("Writing article output...", "Wrote article output", outputArticles)
    

    def formatSqlTables(self, sanitizedArticles, authors):
        formatters = {
            'articles': ArticleFormatter(sanitizedArticles),
            'authors': AuthorFormatter(authors),
            'articles_authors': ArtAuthFormatter(sanitizedArticles)
        }

        commands = [formatters[key].format() for key in formatters]
        Formatter.fileDump(commands)

        return True

    def mergeAuthLists(self, auths:list, gAuths:list):
        for auth in gAuths:
            newId = len(auths)
            auth.data['id'] = newId
            auths.append(auth)
        return auths


    def printChecklist(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        checkmark = Animator.colorWrap('\033[32m', '✓')
        for step in self.completedSteps:
            text = Animator.colorWrap('\033[90m', step)
            print(f"{checkmark} {text}")