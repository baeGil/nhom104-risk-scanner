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
]
