from pathlib import Path

import argparse
import os


# WordPress ids start at 0, and the generated tables declare AUTO_INCREMENT
# primary keys. Without this, MariaDB reads an explicit 0 as "assign the next
# value", which then collides with the real row holding id 1 and rejects the
# whole multi-row INSERT -- so one id-0 row leaves the entire table empty.
# mysqldump emits the same setting for the same reason.
_SQL_PREAMBLE = "SET sql_mode = CONCAT(@@sql_mode, ',NO_AUTO_VALUE_ON_ZERO');"


def write_sql_file(path, commands):
    outputPath = Path(path)
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    with outputPath.open("w", encoding="utf-8") as file:
        file.write(_SQL_PREAMBLE)
        file.write("\n")
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
    parser.add_argument(
        "--skip-media-reports",
        action="store_true",
        help="Skip logs/media attachment inventory, reference, reconciliation, and copy-manifest reports",
    )
    return parser.parse_args()


def _run_pipeline(tui, args) -> None:
    from App import Pipeline
    from Formatter.ArticleFormatter import ArticleFormatter
    from Formatter.CommentFormatter import CommentFormatter
    from Formatter.SeoFormatter import SeoFormatter
    from Formatter.AuthorFormatter import AuthorFormatter
    from Formatter.ArtAuthFormatter import ArtAuthFormatter
    from Formatter.ArticleEmbeddingsFormatter import (
        ArticleEmbeddingsFormatter,
        EmbeddingsDependencyError,
    )
    from Utils.MediaInventory import write_media_reports
    from Utils.WPComments import load_wordpress_comments
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

    if not args.skip_media_reports:
        pipeline.runStep(
            "Writing media inventory reports...",
            "Wrote media inventory reports",
            lambda: write_media_reports(sanitizedArticles),
        )

    def write_sql_outputs():
        outputs = [
            ("logs/sql/articles.sql", ArticleFormatter(sanitizedArticles).iter_format("articles")),
            ("logs/sql/seo.sql", SeoFormatter(sanitizedArticles).iter_format("seo")),
            ("logs/sql/authors.sql", AuthorFormatter(allAuthors).iter_format("authors")),
            ("logs/sql/articles_authors.sql", ArtAuthFormatter(sanitizedArticles).iter_format("articles_authors")),
        ]
        comments = load_wordpress_comments(
            Utility.resolveExportZipMembers()[0],
            sanitizedArticles,
        )
        if comments:
            outputs.append(("logs/sql/comments.sql", CommentFormatter(comments).iter_format("comments")))

        for path, commands in outputs:
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
    args = parse_args()

    from TUI import ETLApp

    ETLApp(lambda tui: _run_pipeline(tui, args)).run()
