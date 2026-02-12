from App import App

app = App()

# MASS IMPORT/EXPORT
def build():
    # EXTRACTION
    extracted = app.extractData()

    # TRANSLATION
    translators = app.translateData(extracted)
    app.logOutputs(translators)
    
    # SANITATION
    authors = app.sanitizeAuthors(translators, "auth", "authors")
    guestAuthors = app.sanitizeAuthors(translators, "gAuth", "guest authors")
    app.writeAuthorOutput(authors, "logs/auth_output.json", "author")
    app.writeAuthorOutput(guestAuthors, "logs/gauth_output.json", "guest author")
    authors = app.mergeAuthLists(authors, guestAuthors)
    sanitizedArticles = app.sanitizeArticleAuthors(translators, authors, guestAuthors)
    sanitizedArticles = app.sanitizeArticleContent(sanitizedArticles)
    app.writeArticleOutput(sanitizedArticles)
    
    
    app.printChecklist()

build()
