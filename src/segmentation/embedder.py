"""
Article embedding generator — T1.6 (Người B)

Calls embedding service provided by Người A (T6.2).
Writes embeddings back to Neo4j Article nodes.

Interface contract with Người A (T6.2)
---------------------------------------
API format:
  POST {EMBED_SERVICE_URL}/embed
  Body: {"texts": ["text1", "text2", ...]}
  Response: {"embeddings": [[float, ...], ...]}  # 1024-dim each

Interface contract with cross_reference / application layer (Người C)
----------------------------------------------------------------------
After T1.6 completes:
  - Article.embedding property exists (1024-dim float array)
  - Neo4j vector index "article_embeddings" is created and populated
  - Người C queries this index via:
      CALL db.index.vector.queryNodes("article_embeddings", 20, $query_vector)
"""
from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)

# Batch sizes from spec
EMBED_BATCH_SIZE = 512    # articles per embedding API call
NEO4J_BATCH_SIZE = 1_000  # articles per Neo4j write transaction

EMBED_DIM = 1024          # harrier-0.6b (updated) output dimension
VECTOR_INDEX_NAME = "article_embeddings"  # used by Người C's queries

# Retry configuration for embedding service
EMBED_MAX_RETRIES = 3
EMBED_RETRY_DELAY = 2.0  # seconds


class ArticleEmbedder:
    """
    Generates embeddings for all Article nodes and stores them in Neo4j.

    Usage
    -----
        embedder = ArticleEmbedder(
            driver=neo4j_driver,
            embed_service_url=os.getenv("EMBED_SERVICE_URL"),
        )
        stats = embedder.embed_all()
        # {"total": N, "embedded": N, "errors": N}
    """

    def __init__(
        self,
        driver: "Driver",
        embed_service_url: Optional[str] = None,
        *,
        embed_batch_size: int = EMBED_BATCH_SIZE,
        neo4j_batch_size: int = NEO4J_BATCH_SIZE,
    ) -> None:
        self._driver = driver
        self._url = embed_service_url or os.getenv("EMBED_SERVICE_URL", "http://localhost:8001")
        self._embed_batch = embed_batch_size
        self._neo4j_batch = neo4j_batch_size

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_all(self, *, overwrite: bool = False) -> dict[str, int]:
        """
        Embed all Article nodes that don't yet have an embedding.

        Parameters
        ----------
        overwrite : bool
            If True, re-embed all articles (even those with existing embeddings).
            Default False for idempotent re-runs.

        Returns
        -------
        dict with keys: total, embedded, errors
        """

        stats = {"total": 0, "embedded": 0, "errors": 0}
        
        where_clause = "WHERE a.embedding IS NULL" if not overwrite else ""
        query = f"""
        MATCH (a:Article) {where_clause}
        OPTIONAL MATCH (d:Document)-[:HAS_ARTICLE]->(a)
        OPTIONAL MATCH (d2:Document)-[:HAS_CHAPTER]->(ch:Chapter)-[:HAS_ARTICLE]->(a)
        WITH a, coalesce(d.title, d2.title, "Văn bản") AS doc_title, coalesce(ch.title, "") AS ch_title
        RETURN a.uid AS uid,
               doc_title + " - " + ch_title + " - " + coalesce(a.title, "") + " - " + coalesce(a.clean_text, "") AS rich_text
        """
        
        with self._driver.session() as session:
            records = session.run(query).data()
            
        stats["total"] = len(records)
        
        for i in range(0, len(records), self._embed_batch):
            batch = records[i : i + self._embed_batch]
            uids = [r["uid"] for r in batch]
            texts = [r["rich_text"] for r in batch]
            
            try:
                embeddings = self._call_embed_service(texts)
                update_query = """
                UNWIND $batch AS row
                MATCH (a:Article {uid: row.uid})
                SET a.embedding = row.embedding
                """
                batch_data = [{"uid": uid, "embedding": emb} for uid, emb in zip(uids, embeddings)]
                with self._driver.session() as session:
                    session.run(update_query, batch=batch_data)
                stats["embedded"] += len(batch)
            except Exception as exc:
                logger.error("Failed to embed batch: %s", exc)
                stats["errors"] += len(batch)
                
        try:
            self._ensure_vector_index()
        except Exception as exc:
            logger.error("Failed to ensure vector index: %s", exc)
            
        return stats

    def embed_article(self, uid: str, text: str) -> Optional[list[float]]:
        """
        Embed a single article and write to Neo4j. Returns the embedding vector.
        Useful for incremental updates or testing.
        """

        try:
            emb = self._call_embed_service([text])[0]
            query = "MATCH (a:Article {uid: $uid}) SET a.embedding = $embedding"
            with self._driver.session() as session:
                session.run(query, uid=uid, embedding=emb)
            return emb
        except Exception as exc:
            logger.error("Failed to embed article %s: %s", uid, exc)
            return None

    def verify_embeddings(self) -> dict[str, int]:
        """
        Check that all Article nodes have a 1024-dim embedding.

        Returns: {"total_articles": N, "with_embedding": N, "missing": N, "wrong_dim": N}
        """

        query = f"""
        MATCH (a:Article)
        RETURN
          count(a) AS total_articles,
          count(a.embedding) AS with_embedding,
          count(CASE WHEN size(a.embedding) <> {EMBED_DIM} THEN 1 END) AS wrong_dim
        """
        with self._driver.session() as session:
            res = session.run(query).single()
            return dict(res) if res else {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_embed_service(self, texts: list[str]) -> list[list[float]]:
        """
        Call Người A's embedding API with retry logic.
        """
        import requests

        last_error = None
        for attempt in range(EMBED_MAX_RETRIES):
            try:
                resp = requests.post(
                    self._url + "/embed",
                    json={"texts": texts},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                embeddings = data.get("embeddings", [])
                if len(embeddings) != len(texts):
                    raise RuntimeError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")
                if embeddings and len(embeddings[0]) != EMBED_DIM:
                    raise RuntimeError(f"Expected {EMBED_DIM} dims, got {len(embeddings[0])}")
                return embeddings

            except Exception as e:
                last_error = e
                if attempt < EMBED_MAX_RETRIES - 1:
                    delay = EMBED_RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Embedding service failed (attempt {attempt + 1}/{EMBED_MAX_RETRIES}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)

        raise last_error  # type: ignore[misc]

    def _ensure_vector_index(self) -> None:
        """
        Create the Neo4j vector index if it doesn't exist.
        Safe to call multiple times (IF NOT EXISTS).

        Cypher:
        CREATE VECTOR INDEX article_embeddings IF NOT EXISTS
        FOR (a:Article) ON (a.embedding)
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1024,
          `vector.similarity_function`: 'cosine'
        }}
        """

        query = f"""
        CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
        FOR (a:Article) ON (a.embedding)
        OPTIONS {{indexConfig: {{
          `vector.dimensions`: {EMBED_DIM},
          `vector.similarity_function`: 'cosine'
        }}}}
        """
        with self._driver.session() as session:
            session.run(query)
