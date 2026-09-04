from pathlib import Path

import argparse
import json
import os
import sys


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


def write_json_file(path, payload):
    outputPath = Path(path)
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    with outputPath.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
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
        # Must match the CMS embedding sidecar's EMBED_MODEL. A distance between
        # vectors from two different models is meaningless, so a mismatch here
        # degrades search ranking and "related articles" silently rather than
        # failing. Was paraphrase-MiniLM-L3-v2, a symmetric paraphrase model;
        # bge-small-en-v1.5 is trained for query-to-document retrieval, which is
        # what search actually does. Both are 384-dimensional, so VECTOR(384) is
        # unchanged.
        default=os.getenv("WP_EMBED_MODEL", "BAAI/bge-small-en-v1.5"),
        help="SentenceTransformer model name; must match the CMS sidecar's EMBED_MODEL",
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
        "--headless",
        action="store_true",
        help="Run without the TUI, logging steps to stdout. Requires --best-guess, since nothing can answer a prompt",
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
    from Formatter.PollFormatter import PollFormatter
    from Formatter.PollOptionFormatter import PollOptionFormatter
    from Utils.CommentSpam import mark_spam, summarize
    from Utils.MediaInventory import write_media_reports
    from Utils.WPComments import load_wordpress_comments
    from Utils.WPPolls import load_wordpress_polls, poll_options
    from Utils.Utility import Utility
    from Utils.Constants import POLLS_ANSWERS_FILE, POLLS_QUESTIONS_FILE
    from Utils.SiteProfile import id_offset

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

    sanitizedArticles = pipeline.sanitizeArticleAuthors(translators, allAuthors, best_guess=args.best_guess)
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
            # WordPress's exporter already removed everything it had labelled
            # spam, so every row here arrived "approved" -- including the spam
            # its own filter missed. Re-status rather than drop, so a moderator
            # can reverse a false positive from the CMS.
            flagged = mark_spam(comments)
            if flagged:
                write_json_file("logs/comment_spam_report.json", flagged)
                tui.step_done(
                    f"Flagged {len(flagged)} of {len(comments)} comments as spam "
                    f"({dict(summarize(flagged))})"
                )
            outputs.append(("logs/sql/comments.sql", CommentFormatter(comments).iter_format("comments")))

        # Polls come from their own tables rather than the export, so they are
        # present only when someone has run scripts/dump_wp_polls.sh. Without
        # the dumps the rest of the run is unaffected -- but nothing else
        # re-seeds the archive, so a reseed without them empties it.
        if POLLS_QUESTIONS_FILE.is_file() and POLLS_ANSWERS_FILE.is_file():
            polls = load_wordpress_polls(
                POLLS_QUESTIONS_FILE,
                POLLS_ANSWERS_FILE,
                id_offset=id_offset(),
            )
            if polls:
                options = poll_options(polls)
                tui.step_done(f"Loaded {len(polls)} polls with {len(options)} options")
                outputs.append(("logs/sql/polls.sql", PollFormatter(polls).iter_format("cms_polls")))
                outputs.append((
                    "logs/sql/poll_options.sql",
                    PollOptionFormatter(options).iter_format("cms_poll_options"),
                ))
        else:
            tui.step_done("No poll dumps in Data/; skipping polls (see scripts/dump_wp_polls.sh)")

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


class HeadlessTUI:
    """Stand-in for the Textual app so a run can go in a script or CI job.

    The prompting callbacks raise rather than block. Reaching one means the run
    needed a human, which unattended is a failure to report, not a hang to wait
    on -- and with --best-guess neither should be reachable.
    """

    def step_start(self, msg):
        print(f"... {msg}", flush=True)

    def step_done(self, msg):
        print(f"  > {msg}", flush=True)

    def step_error(self, msg):
        print(f"!!! {msg}", file=sys.stderr, flush=True)

    def show_conflict(self, diffs, left, right, index, total):
        raise SystemExit(
            f"Headless run hit an author conflict needing a decision "
            f"({index + 1}/{total}): {left.get('display_name')!r} vs "
            f"{right.get('display_name')!r}. Re-run with the TUI to resolve it."
        )

    def show_select(self, prompt, options, fmt=None):
        raise SystemExit(f"Headless run hit an author prompt: {prompt}")


if __name__ == "__main__":
    args = parse_args()

    # Resolve the per-site settings up front: this validates every one of them,
    # and puts the profile the run actually used in the log next to its output.
    from Utils.SiteProfile import describe as _describe_profile

    print(_describe_profile())

    if args.headless:
        if not args.best_guess:
            raise SystemExit("--headless requires --best-guess: nothing can answer a prompt")
        _run_pipeline(HeadlessTUI(), args)
    else:
        from TUI import ETLApp

        ETLApp(lambda tui: _run_pipeline(tui, args)).run()
