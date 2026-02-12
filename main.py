from App import App
from Formatter.Formatter import Formatter
from Formatter.AuthorFormatter import AuthorFormatter
from Formatter.ArticleFormatter import ArticleFormatter
from Formatter.ArtAuthFormatter import ArtAuthFormatter

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

    # FORMATTING
    formatters = {
        'articles': ArticleFormatter(sanitizedArticles),
        'authors': AuthorFormatter(authors),
        'articles_authors': ArtAuthFormatter(sanitizedArticles)
    }
    commands = {k: v.format() for k, v in formatters.items()}
    print(commands['authors'])
    exit(9)
    for key, commandSequence in commands.items():
        for command in commandSequence:
            with open(f"./{key}_commands.txt", "a") as file:
                file.write(command.strip())
                file.close()
    
    
    app.printChecklist()

build()
