import json
import os
from pathlib import Path
from Extractor import Extractor
from Sanitizer.GuestAuthorPolicy import GuestAuthorPolicy
from Sanitizer.AuthorPolicy import AuthorPolicy
from Sanitizer.AuthorSanitizer import AuthorSanitizer
from Sanitizer.ArticleAuthorMatcher import ArticleAuthorMatcher
from Sanitizer.ArticleContentSanitizer import ArticleContentSanitizer
from Translator.ArticleTranslator import ArticleTranslator
from Translator.AuthorTranslator import AuthorTranslator
from Translator.GuestAuthorTranslator import GuestAuthorTranslator
from Utils.Constants import ZIP_FILE
from Utils.Utility import Utility


class Pipeline:
    def __init__(self, on_start, on_done, on_error, resolve_conflict, select_author):
        self.on_start = on_start
        self.on_done = on_done
        self.on_error = on_error
        self.resolve_conflict = resolve_conflict
        self.select_author = select_author

    def runStep(self, onLoad, onDone, func, *args):
        self.on_start(onLoad)
        try:
            result = func(*args) if args else func()
        except Exception:
            self.on_error(f"Error: {onLoad}")
            raise
        self.on_done(onDone)
        return result

    def extractData(self):
        self.on_start("Extracting...")
        try:
            self.on_start("Extracting... (opening wp-export.zip)")
            extractor = Extractor(*Utility.resolveExportZipMembers(ZIP_FILE))
            result = extractor.getData(on_progress=self.on_start)
        except Exception:
            self.on_error("Error: Extracting...")
            raise
        self.on_done("Extracted")
        return result

    def translateData(self, extracted):
        translators = {
            "articles": ArticleTranslator(extracted["art"]),
            "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
            "auth": AuthorTranslator(extracted["auth"]),
        }
        # The same resolution the fused path performs, so the two cannot
        # disagree about who wrote an article.
        translators["articles"].guestAuthorNames = Extractor.buildGuestAuthorNameMap(
            Utility.resolveExportZipMembers(ZIP_FILE)[1]
        )
        self.on_start("Translating...")
        try:
            translators["auth"].translate(on_progress=self.on_start)
            translators["gAuth"].translate(on_progress=self.on_start)
            translators["articles"].translate(on_progress=self.on_start)
        except Exception:
            self.on_error("Error: Translating...")
            raise
        self.on_done("Translated")
        return translators

    def extractAndTranslateData(self):
        translators = {
            "articles": ArticleTranslator([]),
            "gAuth": GuestAuthorTranslator([]),
            "auth": AuthorTranslator([]),
        }
        self.on_start("Extracting and translating...")
        try:
            self.on_start("Extracting and translating... (opening wp-export.zip)")
            extractor = Extractor(*Utility.resolveExportZipMembers(ZIP_FILE))
            extractor.translateData(translators, on_progress=self.on_start)
        except Exception:
            self.on_error("Error: Extracting and translating...")
            raise
        self.on_done("Extracted and translated")
        return translators

    def logOutputs(self, translators):
        if os.getenv("WP_TRANSLATOR_LOGS", "").strip().lower() not in ("1", "true", "yes", "on"):
            return

        logTargets = [
            ("Logging articles...", "Logged articles", translators["articles"]._log, Path("logs") / "articles"),
            ("Logging guest authors...", "Logged guest authors", translators["gAuth"]._log, Path("logs") / "gAuth.json"),
            ("Logging authors...", "Logged authors", translators["auth"]._log, Path("logs") / "auth.json"),
        ]
        for onLoad, onDone, func, path in logTargets:
            self.runStep(onLoad, onDone, func, path)

    def sanitizeAuthors(self, translators, key, name):
        authors = translators[key].listAuthors()
        policy = AuthorPolicy(authors) if key == "auth" else GuestAuthorPolicy(authors)
        authSanitizer = AuthorSanitizer(authors, policy)
        self.on_start(f"Sanitizing {name}...")
        authors = authSanitizer.sanitize(resolve_conflict=self.resolve_conflict, on_progress=self.on_start)
        self.on_done(f"Sanitized {name}")
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
        for gAuth in guestAuthors:
            gAuthName = gAuth.data["display_name"]
            if gAuthName not in authNames:
                while nextId in usedIds:
                    nextId += 1
                gAuth.data["id"] = nextId
                usedIds.add(nextId)
                nextId += 1
                authNames.add(gAuthName)
                combined.append(gAuth)
        return combined

    def sanitizeArticleAuthors(self, translators, allAuthors, best_guess=False):
        articles = translators["articles"].getObjList()
        articleSanitizer = ArticleAuthorMatcher(articles, allAuthors, best_guess=best_guess)
        self.on_start("Sanitizing article authors...")
        sanitizedArticles = articleSanitizer.sanitize(select_author=self.select_author)
        self.on_done("Sanitized article authors")
        return sanitizedArticles

    def sanitizeArticleContent(self, sanitizedArticles):
        # ArticleContentSanitizer.sanitize now also builds excerpts as part of its
        # (parallelized) per-article pass, so no separate excerpt loop is needed.
        contentSanitizer = ArticleContentSanitizer(sanitizedArticles)
        self.runStep("Sanitizing article content...", "Sanitized article content", contentSanitizer.sanitize)
        return sanitizedArticles

    def writeArticleOutput(self, sanitizedArticles):
        if os.getenv("WP_ARTICLE_OUTPUT_LOGS", "").strip().lower() not in ("1", "true", "yes", "on"):
            return

        def outputArticles():
            output_path = Path("logs/article_output.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(
                    {str(i): (sanitizedArticles[i].data if hasattr(sanitizedArticles[i], "data") else sanitizedArticles[i])
                     for i in range(len(sanitizedArticles))},
                    indent=4,
                ),
                encoding="utf-8",
            )
        self.runStep("Writing article output...", "Wrote article output", outputArticles)
