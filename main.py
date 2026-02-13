from App import App
import traceback

app = App()

def build():
    try:
        extracted = app.extractData()

        translators = app.translateData(extracted)
        app.logOutputs(translators)
        
        authors = app.sanitizeAuthors(translators, "auth", "authors")
        guestAuthors = app.sanitizeAuthors(translators, "gAuth", "guest authors")
        app.writeAuthorOutput(authors, "logs/auth_output.json", "author")
        app.writeAuthorOutput(guestAuthors, "logs/gauth_output.json", "guest author")
        
        allAuthors = app.combineAndReindexAuthors(authors, guestAuthors)
        del guestAuthors
        app.writeAuthorOutput(allAuthors, "logs/merged_auth_output.json", "merged authors")
        
        sanitizedArticles = app.sanitizeArticleAuthors(translators, allAuthors)
        sanitizedArticles = app.sanitizeArticleContent(sanitizedArticles)
        app.writeArticleOutput(sanitizedArticles)
        
        app.printChecklist()
    except Exception:
        app.shutdown()
        traceback.print_exc()

build()
