from pathlib import Path

import argparse
import os


def write_sql_file(path, commands):
    outputPath = Path(path)
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    with outputPath.open("w", encoding="utf-8") as file:
        for command in commands:
            file.write(command)
            file.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Run wordpress-etl pipeline and write SQL outputs.")
    parser.add_argument(
        "--generate-embeddings",
        action="store_true",
        help="Generate logs/sql/article_embeddings.sql from sanitized article content",
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
    parser.add_argument(
        "--best-guess",
        action="store_true",
        help="Resolve ambiguous author matches automatically using the highest similarity score instead of prompting",
    )
    return parser.parse_args()


def _run_pipeline(tui, args) -> None:
    from App import Pipeline
    from Formatter.ArticleFormatter import ArticleFormatter
    from Formatter.SeoFormatter import SeoFormatter
    from Formatter.AuthorFormatter import AuthorFormatter
    from Formatter.ArtAuthFormatter import ArtAuthFormatter
    from Formatter.ArticleEmbeddingsFormatter import (
        ArticleEmbeddingsFormatter,
        EmbeddingsDependencyError,
    )
    from Utils.Utility import Utility

    pipeline = Pipeline(
        on_start=tui.step_start,
        on_done=tui.step_done,
        on_error=tui.step_error,
        resolve_conflict=tui.show_conflict,
        select_author=tui.show_select,
    )

    if os.getenv("WP_FUSED_EXTRACT_TRANSLATE", "1").strip().lower() in ("0", "false", "no", "off"):
        try:
            extracted = pipeline.extractData()
        except Exception as exc:
            tui.step_error(f"Extraction failed: {exc}")
            raise SystemExit(1)
        translators = pipeline.translateData(extracted)
    else:
        try:
            translators = pipeline.extractAndTranslateData()
        except Exception as exc:
            tui.step_error(f"Extraction/translation failed: {exc}")
            raise SystemExit(1)
    pipeline.logOutputs(translators)

    authors = pipeline.sanitizeAuthors(translators, "auth", "authors")
    guestAuthors = pipeline.sanitizeAuthors(translators, "gAuth", "guest authors")
    Utility.canonicalizeAuthorLogins(authors)
    Utility.canonicalizeAuthorLogins(guestAuthors)
    pipeline.writeAuthorOutput(authors, "logs/auth_output.json", "author")
    pipeline.writeAuthorOutput(guestAuthors, "logs/gauth_output.json", "guest author")

    allAuthors = pipeline.combineAndReindexAuthors(authors, guestAuthors)
    Utility.canonicalizeAuthorLogins(allAuthors)
    del guestAuthors
    pipeline.writeAuthorOutput(allAuthors, "logs/merged_auth_output.json", "merged authors")

    sanitizedArticles = pipeline.sanitizeArticleAuthors(translators, allAuthors)
    sanitizedArticles = pipeline.sanitizeArticleContent(sanitizedArticles)
    Utility.canonicalizeArticleSlugs(sanitizedArticles)
    pipeline.writeArticleOutput(sanitizedArticles)

    def write_sql_outputs():
        for path, commands in [
            ("logs/sql/articles.sql", ArticleFormatter(sanitizedArticles).iter_format("articles")),
            ("logs/sql/seo.sql", SeoFormatter(sanitizedArticles).iter_format("seo")),
            ("logs/sql/authors.sql", AuthorFormatter(allAuthors).iter_format("authors")),
            ("logs/sql/articles_authors.sql", ArtAuthFormatter(sanitizedArticles).iter_format("articles_authors")),
        ]:
            write_sql_file(path, commands)

    pipeline.runStep("Formatting SQL...", "Wrote SQL", write_sql_outputs)

    if args.generate_embeddings:
        try:
            pipeline.runStep(
                "Generating embeddings...",
                "Generated embeddings",
                lambda: ArticleEmbeddingsFormatter(
                    sanitizedArticles,
                    model=args.embedding_model,
                    batch_size=args.embedding_batch_size,
                    max_chars=args.embedding_max_chars,
                ).write_sql(Path("logs/sql/article_embeddings.sql")),
            )
        except EmbeddingsDependencyError as exc:
            tui.step_error(str(exc))
            raise SystemExit(1)


if __name__ == "__main__":
    from TUI import ETLApp

    args = parse_args()
    ETLApp(lambda tui: _run_pipeline(tui, args)).run()
