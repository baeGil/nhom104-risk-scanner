from __future__ import annotations

from typing import Any, Optional

from src.config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
from src.contract.citations import LegalCitation
from src.embeddings.retriever import EmbeddingRetriever


class LegalContextAssembler:
    """Assembles Document -> Article -> Clause -> Point context for legal segment uids."""

    def __init__(self, retriever: Optional[EmbeddingRetriever] = None) -> None:
        self._retriever = retriever or EmbeddingRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    def close(self) -> None:
        self._retriever.close()

    def assemble(self, uid: str) -> Optional[dict[str, Any]]:
        return self._retriever.get_segment_context(uid)

    def citation_for(self, uid: str) -> Optional[LegalCitation]:
        context = self.assemble(uid)
        return LegalCitation.from_context(context) if context else None
