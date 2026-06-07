import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor

from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.ArticlePolicy import ArticlePolicy
from Sanitizer.content_worker import process_article as _process_article
from Utils.WPContentSanitization import (
    log_shortcodes,
    log_inline_styles,
    log_problematic_chars,
    write_detailed_logs
)


class ArticleContentSanitizer(Sanitizer):
    # Below this many articles the process-pool overhead isn't worth it.
    _PARALLEL_MIN = 500

    def __init__(self, data: list, detailed_logs: bool | None = None,
                 parallel: bool | None = None, workers: int | None = None):
        super().__init__(data, policies=ArticlePolicy([]))
        # Building and writing the per-article shortcode/inline-style/problematic-
        # character logs costs ~1s and is purely diagnostic, so it's off unless
        # explicitly requested via arg or the WP_SANITIZER_DETAILED_LOGS env var.
        if detailed_logs is None:
            detailed_logs = os.getenv("WP_SANITIZER_DETAILED_LOGS", "").strip().lower() in ("1", "true", "yes", "on")
        self.detailed_logs = detailed_logs

        if parallel is None:
            parallel = os.getenv("WP_SANITIZER_PARALLEL", "1").strip().lower() not in ("0", "false", "no", "off")
        self.parallel = parallel

        if workers is None:
            env_workers = os.getenv("WP_SANITIZER_WORKERS")
            if env_workers:
                try:
                    workers = int(env_workers)
                except ValueError:
                    workers = None
        # Returns plateau around 8 workers (result IPC dominates beyond that), so
        # the auto-default is capped; an explicit arg/env value is respected as-is.
        self.workers = workers if workers else min(os.cpu_count() or 1, 8)

        self.shortcode_log = []
        self.inline_style_log = []
        self.problematic_chars_log = {}

    def _logChange(self, article_id, change_type, details):
        self.changes.append({
            "article_id": article_id,
            "change_type": change_type,
            "details": details
        })

    def _logConflict(self, article_id, issue_type, details):
        self.conflicts.append({
            "article_id": article_id,
            "issue_type": issue_type,
            "details": details
        })

    def _normalizeData(self):
        """Ensure all articles include a text field."""
        for article in self.data:
            if 'text' not in article:
                article['text'] = ""

    def _processAll(self, payloads):
        """Run the per-article transform, in parallel when worthwhile.

        Falls back to sequential execution for small inputs, a single worker,
        or if the process pool fails to start/run for any reason.
        """
        if not self.parallel or self.workers <= 1 or len(payloads) < self._PARALLEL_MIN:
            return [_process_article(p) for p in payloads]
        chunksize = max(1, len(payloads) // (self.workers * 4))
        for ctx in self._pool_contexts():
            try:
                with ProcessPoolExecutor(max_workers=self.workers, mp_context=ctx) as executor:
                    return list(executor.map(_process_article, payloads, chunksize=chunksize))
            except Exception:
                continue
        # Graceful fallback: pickling/OS/pool failure -> identical sequential result.
        return [_process_article(p) for p in payloads]

    @staticmethod
    def _pool_contexts():
        """Yield thread-safe start methods in preferred fallback order.

        The pipeline runs on a Textual worker thread, so plain ``fork`` is unsafe
        (forking a multithreaded process can deadlock). Prefer ``spawn`` because
        it is reliable across threaded/sandboxed runners; keep ``forkserver`` as
        a fallback for platforms where spawn is unavailable or fails.
        """
        preferred = os.getenv("WP_SANITIZER_START_METHOD", "").strip().lower()
        methods = (preferred,) if preferred in ("spawn", "forkserver") else ("spawn", "forkserver")
        for method in methods:
            try:
                ctx = multiprocessing.get_context(method)
                if method == "forkserver":
                    try:
                        ctx.set_forkserver_preload(["Sanitizer.content_worker"])
                    except (AttributeError, RuntimeError):
                        pass
                yield ctx
            except ValueError:
                continue

    def sanitize(self):
        self._normalizeData()

        payloads = [
            (idx, article.get("text", ""), article.get("categories", []))
            for idx, article in enumerate(self.data)
        ]

        for idx, sanitized, fixes, excerpt in self._processAll(payloads):
            article = self.data[idx]
            article["excerpt"] = excerpt
            if sanitized is not None:
                article["text"] = sanitized
                self._logChange(article.get("id", "unknown"), "content_sanitized", "; ".join(fixes))

        # Detailed logs are accumulated in a single sequential pass over the now
        # sanitized text. Keeping it out of the parallel workers avoids shared
        # mutable state, so enabling detailed logs degrades gracefully to one
        # extra sequential scan rather than breaking parallelism.
        if self.detailed_logs:
            self._collectDetailedLogs()
            self._write_detailed_logs()

        self._log("article-sanitizer/article_content_changes", "article-sanitizer/article_content_conflicts")
        return self.data

    def _collectDetailedLogs(self):
        for article in self.data:
            text = article.get("text", "")
            if not text:
                continue
            article_id = article.get("id", "unknown")

            problematic_chars = log_problematic_chars(text, article_id, self.policies.problematic_char_patterns)
            for char_type, data in problematic_chars.items():
                if char_type not in self.problematic_chars_log:
                    self.problematic_chars_log[char_type] = data
                else:
                    self.problematic_chars_log[char_type]["unicodes"].update(data["unicodes"])
                    self.problematic_chars_log[char_type]["occurrences"].extend(data["occurrences"])

            self.shortcode_log.extend(log_shortcodes(text, article_id, self.policies.shortcode_pattern))
            self.inline_style_log.extend(log_inline_styles(text, article_id, self.policies.inline_style_pattern))

    def _write_detailed_logs(self):
        if not self.detailed_logs:
            return
        write_detailed_logs(self.shortcode_log, self.inline_style_log, self.problematic_chars_log)
