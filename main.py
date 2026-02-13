from App import App

app = App()

# MASS IMPORT/EXPORT
def build():
    # Extract and translate
    extracted = app.extractData()

    # TRANSLATION
    translators = app.translateData(extracted)
    app.logOutputs(translators)
    
    # Sanitize authors
    authors = app.sanitizeAuthors(translators, "auth", "authors")
    guestAuthors = app.sanitizeAuthors(translators, "gAuth", "guest authors")
    app.writeAuthorOutput(authors, "logs/auth_output.json", "author")
    app.writeAuthorOutput(guestAuthors, "logs/gauth_output.json", "guest author")
    
    # Combine auth
    allAuthors = app.combineAndReindexAuthors(authors, guestAuthors)
    del guestAuthors
    app.writeAuthorOutput(allAuthors, "logs/merged_auth_output.json", "merged authors")
    
    # Sanitize article
    sanitizedArticles = app.sanitizeArticleAuthors(translators, allAuthors)
    sanitizedArticles = app.sanitizeArticleContent(sanitizedArticles)
    app.writeArticleOutput(sanitizedArticles)    
    
    app.printChecklist()

build()
