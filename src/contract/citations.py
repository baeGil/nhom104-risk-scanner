from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LegalCitation:
    display_text: str
    uid: str
    document_title: str = ""
    article: Optional[str] = None
    clause: Optional[str] = None
    point: Optional[str] = None
    verified: bool = False
    reason: str = ""

    @classmethod
    def from_context(cls, context: dict[str, Any]) -> "LegalCitation":
        return cls(
            display_text=context.get("display_citation", "") or context.get("uid", ""),
            uid=context.get("uid", ""),
            document_title=context.get("document_title", ""),
            article=str(context["article_index"]) if context.get("article_index") is not None else None,
            clause=str(context["clause_index"]) if context.get("clause_index") is not None else None,
            point=str(context["point_letter"]) if context.get("point_letter") else None,
        )
