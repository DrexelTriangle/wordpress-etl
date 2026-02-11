from App import App 

app = App()

# MASS IMPORT/EXPORT
def build():
    extracted = app.extractData()
    translators = app.translateData(extracted)
    app.logOutputs(translators)
    authors = app.sanitizeAuthors(translators, "auth", "authors")
    app.writeAuthorOutput(authors, "logs/auth_output.json", "author")
    guestAuthors = app.sanitizeAuthors(translators, "gAuth", "guest authors")
    app.writeAuthorOutput(guestAuthors, "logs/gauth_output.json", "guest author")
    app.printChecklist()

build()