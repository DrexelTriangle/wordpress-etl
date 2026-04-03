from App import App
from pathlib import Path
from Formatter.ArticleFormatter import ArticleFormatter
from Formatter.SeoFormatter import SeoFormatter
from Formatter.AuthorFormatter import AuthorFormatter
from Formatter.ArtAuthFormatter import ArtAuthFormatter

app = App()

def write_sql_file(path, commands):
    outputPath = Path(path)
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    sqlText = "\n".join(commands) + "\n"
    outputPath.write_text(sqlText, encoding="utf-8")

def build():
    try:
        extracted = app.extractData()
    except:
      exit(0)

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

    # SQL formatting outputs
    sqlOutputs = [
        ("logs/sql/articles.sql", ArticleFormatter(sanitizedArticles).format("articles")),
        ("logs/sql/seo.sql", SeoFormatter(sanitizedArticles).format("seo")),
        ("logs/sql/authors.sql", AuthorFormatter(allAuthors).format("authors")),
        ("logs/sql/articles_authors.sql", ArtAuthFormatter(sanitizedArticles).format("articles_authors")),
    ]
    for path, commands in sqlOutputs:
        write_sql_file(path, commands)
    
    app.printChecklist()

build()
