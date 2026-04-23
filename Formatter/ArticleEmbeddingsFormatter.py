from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from Formatter.Formatter import Formatter


class EmbeddingsDependencyError(RuntimeError):
    """Raised when sentence-transformers is unavailable."""


class ArticleEmbeddingsFormatter(Formatter):
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
        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

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

            title = str(row.get("title") or "").strip()
            description = str(row.get("description") or "").strip()
            text = str(row.get("text") or "").strip()
            blob = "\n\n".join(part for part in (title, description, self._strip_html(text)) if part)
            if not blob:
                continue

            normalized.append({"id": article_id, "text": blob})

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
            out_sql.write_text(
                "DROP TABLE IF EXISTS article_embeddings;\n-- No articles to embed.\n",
                encoding="utf-8",
            )
            return

        model_obj = SentenceTransformer(self.model, device="cpu")
        corpus = [row["text"][: self.max_chars] for row in articles]
        vectors = model_obj.encode(
            corpus,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=True,
        )
        dim = int(vectors.shape[1])

        with out_sql.open("w", encoding="utf-8") as handle:
            handle.write(f"DROP TABLE IF EXISTS {table};\n")
            handle.write(
                f"CREATE TABLE {table} (\n"
                f"  article_id BIGINT PRIMARY KEY,\n"
                f"  embedding VECTOR({dim}) NOT NULL,\n"
                f"  VECTOR INDEX (embedding) DISTANCE=euclidean\n"
                f");\n"
            )
            for row, vec in zip(articles, vectors, strict=True):
                vector_text = self._vec_to_text(vec.tolist())
                handle.write(
                    f"INSERT INTO {table} (article_id, embedding) VALUES "
                    f"({row['id']}, VEC_FromText('{vector_text}'));\n"
                )
