import argparse
import os
import sys

from App import App
from pathlib import Path
from Formatter.ArticleFormatter import ArticleFormatter
from Formatter.SeoFormatter import SeoFormatter
from Formatter.AuthorFormatter import AuthorFormatter
from Formatter.ArtAuthFormatter import ArtAuthFormatter
from Formatter.ArticleEmbeddingsFormatter import (
    ArticleEmbeddingsFormatter,
    EmbeddingsDependencyError,
)
from Utils.Utility import Utility

app = App()


def write_sql_file(path, commands):
    outputPath = Path(path)
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    sqlText = "\n".join(commands) + "\n"
    outputPath.write_text(sqlText, encoding="utf-8")

def parse_args():
    parser = argparse.ArgumentParser(description="Run wordpress-etl pipeline and write SQL outputs.")
    parser.add_argument(
        "--generate-embeddings",
        action="store_true",
        help="Generate logs/sql/article_embeddings.sql from logs/article_output.json",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("WP_EMBED_MODEL", "sentence-transformers/paraphrase-MiniLM-L3-v2"),
        help="SentenceTransformer model name",
    )
    parser.add_argument(
        "--embedding-batch-size",
        type=int,
        default=int(os.getenv("WP_EMBED_BATCH_SIZE", "64")),
        help="Embedding batch size",
    )
    parser.add_argument(
        "--embedding-max-chars",
        type=int,
        default=int(os.getenv("WP_EMBED_MAX_CHARS", "5000")),
        help="Maximum characters per article for embedding input",
    )
    return parser.parse_args()


def build(args):
    try:
        extracted = app.extractData()
    except Exception as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    # TRANSLATION
    translators = app.translateData(extracted)
    app.logOutputs(translators)
    
    # Sanitize authors
    authors = app.sanitizeAuthors(translators, "auth", "authors")
    guestAuthors = app.sanitizeAuthors(translators, "gAuth", "guest authors")
    Utility.canonicalizeAuthorLogins(authors)
    Utility.canonicalizeAuthorLogins(guestAuthors)
    app.writeAuthorOutput(authors, "logs/auth_output.json", "author")
    app.writeAuthorOutput(guestAuthors, "logs/gauth_output.json", "guest author")
    
    # Combine auth
    allAuthors = app.combineAndReindexAuthors(authors, guestAuthors)
    Utility.canonicalizeAuthorLogins(allAuthors)
    del guestAuthors
    app.writeAuthorOutput(allAuthors, "logs/merged_auth_output.json", "merged authors")
    
    # Sanitize article
    sanitizedArticles = app.sanitizeArticleAuthors(translators, allAuthors)
    sanitizedArticles = app.sanitizeArticleContent(sanitizedArticles)
    Utility.canonicalizeArticleSlugs(sanitizedArticles)
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

    if args.generate_embeddings:
        try:
            embeddings_formatter = ArticleEmbeddingsFormatter(
                sanitizedArticles,
                model=args.embedding_model,
                batch_size=args.embedding_batch_size,
                max_chars=args.embedding_max_chars,
            )
            embeddings_formatter.write_sql(Path("logs/sql/article_embeddings.sql"))
        except EmbeddingsDependencyError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(1)
    
    app.printChecklist()

if __name__ == "__main__":
    build(parse_args())
