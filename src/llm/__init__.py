"""
Unified LLM Module — T5.1 (Người C)
====================================
Unified LLM gateway serving both Contract Review and Legal QA pipelines.
Provides intent analysis, clause extraction, compliance analysis, and answer generation.

Owner: Người C
Dependencies: OpenAI SDK (configurable provider)
"""

from .models import (
    IntentClassification,
    SubIntent,
    SubQuery,
    ConversationContext,
)
from .client import LLMClient, OpenAIClient, create_client
from .intent import IntentAnalyzer
from .context import ConversationManager
from .prompts import PromptTemplate
from .qa_models import (
    QACitation,
    QARetrievedProvision,
    QARetrievalResult,
    QAAnswer,
    QAResponse,
    QAValidity,
)


def __getattr__(name: str):
    if name in {"LegalQAPipeline", "answer_legal_question"}:
        from .qa_pipeline import LegalQAPipeline, answer_legal_question

        return {
            "LegalQAPipeline": LegalQAPipeline,
            "answer_legal_question": answer_legal_question,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "IntentClassification",
    "SubIntent",
    "SubQuery",
    "ConversationContext",
    "LLMClient",
    "OpenAIClient",
    "create_client",
    "IntentAnalyzer",
    "ConversationManager",
    "PromptTemplate",
    "QACitation",
    "QARetrievedProvision",
    "QARetrievalResult",
    "QAAnswer",
    "QAResponse",
    "QAValidity",
    "LegalQAPipeline",
    "answer_legal_question",
]
