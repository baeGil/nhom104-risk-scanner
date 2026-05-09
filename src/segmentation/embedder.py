"""
Article embedding generator — T1.6 (Người B)

Calls embedding service provided by Người A (T6.2).
Writes embeddings back to Neo4j Article nodes.

Interface contract with Người A (T6.2)
---------------------------------------
API format:
  POST {EMBED_SERVICE_URL}/embed
  Body: {"texts": ["text1", "text2", ...]}
  Response: {"embeddings": [[float, ...], ...]}  # 768-dim each

Interface contract with cross_reference / application layer (Người C)
----------------------------------------------------------------------
After T1.6 completes:
  - Article.embedding property exists (768-dim float array)
  - Neo4j vector index "article_embeddings" is created and populated
  - Người C queries this index via:
      CALL db.index.vector.queryNodes("article_embeddings", 20, $query_vector)
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)

# Batch sizes from spec
EMBED_BATCH_SIZE = 512    # articles per embedding API call
NEO4J_BATCH_SIZE = 1_000  # articles per Neo4j write transaction

EMBED_DIM = 768           # harrier-0.6b output dimension
VECTOR_INDEX_NAME = "article_embeddings"  # used by Người C's queries


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

        TODO (T1.6): implement this method.

        Suggested implementation:
        1. Query Neo4j: MATCH (a:Article) WHERE a.embedding IS NULL RETURN a.uid, a.clean_text
        2. Batch texts with self._embed_batch size
        3. Call self._call_embed_service(texts)
        4. Write embeddings back: MATCH (a:Article {uid: $uid}) SET a.embedding = $embedding
        5. After all done, call self._ensure_vector_index()
        """
        raise NotImplementedError("T1.6: implement embed_all()")

    def embed_article(self, uid: str, text: str) -> Optional[list[float]]:
        """
        Embed a single article and write to Neo4j. Returns the embedding vector.
        Useful for incremental updates or testing.

        TODO (T1.6): implement.
        """
        raise NotImplementedError("T1.6: implement embed_article()")

    def verify_embeddings(self) -> dict[str, int]:
        """
        Check that all Article nodes have a 768-dim embedding.

        Returns: {"total_articles": N, "with_embedding": N, "missing": N, "wrong_dim": N}

        TODO (T1.6): implement using Cypher:
            MATCH (a:Article)
            RETURN
              count(a) AS total,
              count(a.embedding) AS with_embedding,
              count(CASE WHEN size(a.embedding) <> 768 THEN 1 END) AS wrong_dim
        """
        raise NotImplementedError("T1.6: implement verify_embeddings()")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_embed_service(self, texts: list[str]) -> list[list[float]]:
        """
        Call Người A's embedding API.

        TODO (T1.6): implement.
        Use requests.post(self._url + "/embed", json={"texts": texts})
        Validate response: len(embeddings) == len(texts), len(embeddings[0]) == 768

        Raises: RuntimeError if service returns wrong shape.
        """
        raise NotImplementedError("T1.6: implement _call_embed_service()")

    def _ensure_vector_index(self) -> None:
        """
        Create the Neo4j vector index if it doesn't exist.
        Safe to call multiple times (IF NOT EXISTS).

        Cypher:
            CREATE VECTOR INDEX article_embeddings IF NOT EXISTS
            FOR (a:Article) ON (a.embedding)
            OPTIONS {indexConfig: {
              `vector.dimensions`: 768,
              `vector.similarity_function`: 'cosine'
            }}

        TODO (T1.6): implement.
        """
        raise NotImplementedError("T1.6: implement _ensure_vector_index()")
