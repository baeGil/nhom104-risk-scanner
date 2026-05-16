"""
Mock Bridge Layer — Enables parallel development before data is ready.

Provides mock implementations of:
- EmbeddingService: Returns deterministic 1024-dim vectors
- GraphTraversal: Returns empty result lists (no relationships in new data)
- EffectiveTextService: Falls back to Article.clean_text

Configuration via src/config.py:
  EMBEDDING_SERVICE_MODE: "mock" | "real"
  GRAPH_REPOSITORY_MODE: "mock" | "neo4j"
  EFFECTIVE_TEXT_SERVICE_MODE: "mock" | "real"

Usage:
    from src.contract.mock_bridge import create_embedding_service
    embedder = create_embedding_service()
    vector = await embedder.embed("some text")
"""
from __future__ import annotations

import hashlib
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.config import (
    EMBEDDING_SERVICE_MODE,
    GRAPH_REPOSITORY_MODE,
    EFFECTIVE_TEXT_SERVICE_MODE,
    EMBED_DIMENSIONS,
    EMBED_QUERY_INSTRUCTION,
    EMBED_SERVICE_URL,
)


# ── Embedding Service ───────────────────────────────────────────────────────

class EmbeddingService(ABC):
    """Abstract interface for embedding generation."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...


class MockEmbeddingService(EmbeddingService):
    """
    Mock embedding service returning deterministic pseudo-random vectors.

    Same input → same output (deterministic via hash).
    Simulates 10-50ms processing delay per text.
    """

    def __init__(self, dimensions: int = 1024):
        self.dimensions = dimensions

    def _generate_vector(self, text: str) -> list[float]:
        """Generate deterministic vector from text hash."""
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        # Generate normalized vector (unit length for cosine similarity)
        vector = [rng.gauss(0, 1) for _ in range(self.dimensions)]
        magnitude = sum(v * v for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        return vector

    async def embed(self, text: str) -> list[float]:
        """Generate embedding with simulated delay."""
        delay = 0.01 + random.random() * 0.04  # 10-50ms
        time.sleep(delay)
        return self._generate_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [self._generate_vector(t) for t in texts]


class RealEmbeddingService(EmbeddingService):
    """HTTP adapter for the embedding service used by contract retrieval."""

    def __init__(
        self,
        url: str = EMBED_SERVICE_URL,
        dimensions: int = EMBED_DIMENSIONS,
        query_instruction: str = EMBED_QUERY_INSTRUCTION,
    ):
        self._url = url.rstrip("/")
        self._dimensions = dimensions
        self._query_instruction = query_instruction

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([self._format_query(text)]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        import requests

        def _request() -> list[list[float]]:
            response = requests.post(
                f"{self._url}/embed",
                json={"texts": texts},
                timeout=60,
            )
            response.raise_for_status()
            embeddings = response.json().get("embeddings", [])
            if len(embeddings) != len(texts):
                raise RuntimeError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")
            if embeddings and len(embeddings[0]) != self._dimensions:
                raise RuntimeError(f"Expected {self._dimensions} dims, got {len(embeddings[0])}")
            return embeddings

        return await asyncio.to_thread(_request)

    def _format_query(self, text: str) -> str:
        if text.lstrip().startswith("Instruct:"):
            return text
        return f"Instruct: {self._query_instruction}\nQuery: {text}"


class LocalEmbeddingService(EmbeddingService):
    """
    Local SentenceTransformer embedding service.

    Query embeddings use Harrier's instruction format:
    Instruct: ...
    Query: ...
    """

    _model: Any = None

    def __init__(
        self,
        model_name: str | None = None,
        dimensions: int = EMBED_DIMENSIONS,
        batch_size: int = 32,
        query_instruction: str = EMBED_QUERY_INSTRUCTION,
    ) -> None:
        from src.config import EMBED_MODEL

        self._model_name = model_name or EMBED_MODEL
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._query_instruction = query_instruction

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([self._format_query(text)]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import asyncio

        return await asyncio.to_thread(self._embed_batch_sync, texts)

    def _ensure_model_loaded(self) -> None:
        if self.__class__._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Local embedding mode requires sentence-transformers. "
                "Install project dependencies or use EMBEDDING_SERVICE_MODE=real."
            ) from exc

        self.__class__._model = SentenceTransformer(self._model_name)

    def _embed_batch_sync(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        self._ensure_model_loaded()

        model = self.__class__._model
        encoded = model.encode(
            texts,
            batch_size=self._batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        embeddings = encoded.tolist()

        for embedding in embeddings:
            if len(embedding) != self._dimensions:
                raise RuntimeError(f"Expected {self._dimensions} dims, got {len(embedding)}")

        return embeddings

    def _format_query(self, text: str) -> str:
        if text.lstrip().startswith("Instruct:"):
            return text
        return f"Instruct: {self._query_instruction}\nQuery: {text}"


# ── Graph Traversal ─────────────────────────────────────────────────────────

class GraphRepository(ABC):
    """Abstract interface for Neo4j graph operations."""

    @abstractmethod
    async def query(self, cypher: str, params: Optional[dict] = None) -> list[dict]:
        """Execute a Cypher query."""
        ...

    @abstractmethod
    async def traverse_references(self, article_uid: str) -> list[dict]:
        """Traverse REFERENCES_INTERNAL, REFERENCES_EXTERNAL from an Article."""
        ...

    @abstractmethod
    async def traverse_modifications(self, article_uid: str) -> list[dict]:
        """Traverse incoming MODIFIES edges to get EffectiveArticle."""
        ...

    @abstractmethod
    async def traverse_details(self, doc_so_ky_hieu: str) -> list[dict]:
        """Traverse DETAILS relationships to find implementing regulations."""
        ...


class MockGraphRepository(GraphRepository):
    """
    Mock graph repository returning empty results.

    Logs all queries for debugging purposes.
    """

    def __init__(self):
        self.query_log: list[dict] = []

    async def query(self, cypher: str, params: Optional[dict] = None) -> list[dict]:
        """Log query and return empty result."""
        self.query_log.append({"cypher": cypher, "params": params})
        return []

    async def traverse_references(self, article_uid: str) -> list[dict]:
        """Return empty list — no cross-references in new data."""
        self.query_log.append({"operation": "traverse_references", "article_uid": article_uid})
        return []

    async def traverse_modifications(self, article_uid: str) -> list[dict]:
        """Return empty list — no modifications in new data."""
        self.query_log.append({"operation": "traverse_modifications", "article_uid": article_uid})
        return []

    async def traverse_details(self, doc_so_ky_hieu: str) -> list[dict]:
        """Return empty list — no DETAILS relationships in new data."""
        self.query_log.append({"operation": "traverse_details", "so_ky_hieu": doc_so_ky_hieu})
        return []


# ── Effective Text Service ──────────────────────────────────────────────────

class EffectiveTextService(ABC):
    """Abstract interface for effective text retrieval."""

    @abstractmethod
    async def get_effective_text(self, article_uid: str) -> Optional[dict]:
        """Get EffectiveArticle for an Article."""
        ...


class MockEffectiveTextService(EffectiveTextService):
    """
    Mock effective text service.

    Returns Article.clean_text as effective_text when EffectiveArticle is not available.
    Sets is_current=true and amendment_chain=[].
    """

    def __init__(self):
        self._cache: dict[str, dict] = {}

    async def get_effective_text(self, article_uid: str, clean_text: str = "") -> Optional[dict]:
        """Return mock effective text based on Article.clean_text."""
        if article_uid in self._cache:
            return self._cache[article_uid]

        result = {
            "uid": f"eff_{article_uid}_mock",
            "article_uid": article_uid,
            "as_of_date": None,
            "effective_text": clean_text,
            "amendment_chain": [],
            "is_current": True,
            "changes_count": 0,
        }
        self._cache[article_uid] = result
        return result


# ── Factory Functions ───────────────────────────────────────────────────────

def create_embedding_service() -> EmbeddingService:
    """Create embedding service based on config."""
    if EMBEDDING_SERVICE_MODE == "real":
        return RealEmbeddingService()
    if EMBEDDING_SERVICE_MODE == "local":
        return LocalEmbeddingService()
    return MockEmbeddingService(dimensions=EMBED_DIMENSIONS)


def create_graph_repository() -> GraphRepository:
    """Create graph repository based on config."""
    if GRAPH_REPOSITORY_MODE == "neo4j":
        from neo4j import GraphDatabase
        from src.config import NEO4J_URI, neo4j_auth

        class Neo4jGraphRepository(GraphRepository):
            def __init__(self):
                self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())

            async def query(self, cypher: str, params: Optional[dict] = None) -> list[dict]:
                with self._driver.session() as session:
                    result = session.run(cypher, params or {})
                    return [dict(r) for r in result]

            async def traverse_references(self, article_uid: str) -> list[dict]:
                cypher = """
                MATCH (a:Article {uid: $uid})-[:REFERENCES_INTERNAL|REFERENCES_EXTERNAL]->(target)
                RETURN target, type(relationship) as rel_type
                """
                return await self.query(cypher, {"uid": article_uid})

            async def traverse_modifications(self, article_uid: str) -> list[dict]:
                cypher = """
                MATCH (a:Article {uid: $uid})<-[:MODIFIES]-(m:Article)
                RETURN m ORDER BY m.effective_date
                """
                return await self.query(cypher, {"uid": article_uid})

            async def traverse_details(self, doc_so_ky_hieu: str) -> list[dict]:
                cypher = """
                MATCH (d:Document {so_ky_hieu: $skh})-[:DETAILS]->(detail)
                RETURN detail
                """
                return await self.query(cypher, {"skh": doc_so_ky_hieu})

        return Neo4jGraphRepository()
    return MockGraphRepository()


def create_effective_text_service() -> EffectiveTextService:
    """Create effective text service based on config."""
    if EFFECTIVE_TEXT_SERVICE_MODE == "real":
        # Real implementation would query Neo4j for EffectiveArticle nodes
        return MockEffectiveTextService()  # Fallback until T3.3 is implemented
    return MockEffectiveTextService()
