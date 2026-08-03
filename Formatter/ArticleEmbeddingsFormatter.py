from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path
from typing import Any

from Formatter.Formatter import Formatter


class EmbeddingsDependencyError(RuntimeError):
    """Raised when sentence-transformers is unavailable."""


class ArticleEmbeddingsFormatter(Formatter):
    """Bulk-loads vectors for the migrated archive.

    The CMS owns this table now: it creates it, and a background reconciler
    fills in anything missing or stale (see server/internal/embeddings). This
    formatter exists only because embedding ~30k archived articles in one batched
    process is far faster than draining them through the sidecar a batch at a
    time. It is an optimization, not the source of truth -- which is why it no
    longer drops the table, and why the CMS is correct without it.

    Two things here MUST match the CMS or the reconciler will fight this
    formatter, re-embedding the whole archive after every reseed:

      * ``_embedding_source`` must produce byte-identical text to
        ``BuildEmbeddingSource`` in server/internal/database/article_embeddings.go.
      * ``--embedding-model`` must be the sidecar's ``EMBED_MODEL``.
    """

    def __init__(self, articleData, model: str, batch_size: int, max_chars: int):
        super().__init__(articleData)
        self.model = model
        self.batch_size = batch_size
        self.max_chars = max_chars

    def _normalize_obj(self, item: Any) -> dict[str, Any] | None:
        obj = item.data if hasattr(item, "data") else item
        if isinstance(obj, dict):
            return obj
        return None

    @staticmethod
    def _strip_html(text: str) -> str:
        """Mirror of stripHTMLForEmbedding in the CMS.

        The order matters and is part of the contract: replace tags with a
        space, *then* unescape entities, *then* collapse whitespace. Unescaping
        first would let an escaped &lt;b&gt; become a tag and get stripped.
        """
        cleaned = re.sub(r"<[^>]*>", " ", text)
        cleaned = html.unescape(cleaned)
        return " ".join(cleaned.split())

    def _embedding_source(self, row: dict[str, Any]) -> str:
        """Mirror of BuildEmbeddingSource in the CMS. Keep the two in step."""
        parts = [
            str(row.get("title") or "").strip(),
            str(row.get("tags") or "").strip(),
            self._strip_html(str(row.get("text") or "")).strip(),
        ]
        blob = "\n\n".join(part for part in parts if part)
        # Truncate by character, matching the CMS's rune-wise cut.
        return blob[: self.max_chars]

    def _normalize_articles(self) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in self.data:
            row = self._normalize_obj(item)
            if row is None:
                continue

            article_id = row.get("id")
            if article_id is None:
                continue
            try:
                article_id = int(article_id)
            except (TypeError, ValueError):
                continue

            blob = self._embedding_source(row)
            if not blob:
                continue

            normalized.append(
                {
                    "id": article_id,
                    "text": blob,
                    "hash": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
                }
            )

        normalized.sort(key=lambda x: x["id"])
        return normalized

    @staticmethod
    def _vec_to_text(values: list[float]) -> str:
        return "[" + ",".join(f"{v:.8f}" for v in values) + "]"

    def write_sql(self, out_sql: Path, table: str = "article_embeddings") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:  # pragma: no cover - dependency availability is env-specific
            raise EmbeddingsDependencyError(
                "Missing dependency: sentence-transformers. Install with `pip install sentence-transformers`."
            ) from exc

        articles = self._normalize_articles()
        out_sql.parent.mkdir(parents=True, exist_ok=True)

        if not articles:
            out_sql.write_text("-- No articles to embed.\n", encoding="utf-8")
            return

        model_obj = SentenceTransformer(self.model, device="cpu")
        corpus = [row["text"] for row in articles]
        vectors = model_obj.encode(
            corpus,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            # MariaDB ranks these by euclidean distance, which only agrees with
            # cosine similarity on unit vectors. Left unnormalized, a long
            # article's larger magnitude skewed every ranking it appeared in.
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        dim = int(vectors.shape[1])

        with out_sql.open("w", encoding="utf-8") as handle:
            # No DROP. This table is CMS-owned (see
            # server/internal/database/schema/article_embeddings.sql); dropping it
            # here is what used to wipe every vector written since the last
            # reseed. CREATE IF NOT EXISTS covers loading this seed into an empty
            # database before the CMS has ever started.
            handle.write(
                f"CREATE TABLE IF NOT EXISTS {table} (\n"
                f"  article_id BIGINT NOT NULL PRIMARY KEY,\n"
                f"  embedding VECTOR({dim}) NOT NULL,\n"
                f"  source_hash CHAR(64) NOT NULL DEFAULT '',\n"
                f"  model VARCHAR(128) NOT NULL DEFAULT '',\n"
                f"  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
                f"  VECTOR INDEX (embedding) DISTANCE=euclidean\n"
                f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n"
            )
            model_sql = self.model.replace("\\", "\\\\").replace("'", "\\'")
            for row, vec in zip(articles, vectors, strict=True):
                vector_text = self._vec_to_text(vec.tolist())
                # The hash and model name are what let the CMS reconciler tell
                # "already embedded with the current model" from "needs work".
                # Without them every seeded row looks unattributed and the
                # archive gets re-embedded through the sidecar after each reseed.
                #
                # ON DUPLICATE KEY UPDATE, because a reseed now loads into a
                # table the CMS may already have populated.
                handle.write(
                    f"INSERT INTO {table} (article_id, embedding, source_hash, model) VALUES "
                    f"({row['id']}, VEC_FromText('{vector_text}'), '{row['hash']}', '{model_sql}') "
                    f"ON DUPLICATE KEY UPDATE embedding = VALUES(embedding), "
                    f"source_hash = VALUES(source_hash), model = VALUES(model), "
                    f"updated_at = CURRENT_TIMESTAMP;\n"
                )
