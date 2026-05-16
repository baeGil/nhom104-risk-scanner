"""End-to-end orchestration for the Phase 5 legal QA pipeline."""
from __future__ import annotations

import logging
import sys
from time import perf_counter
from typing import Optional

from src.llm.answer_generator import QAAnswerGenerator
from src.llm.citation_verifier import CitationVerifier, VerificationResult
from src.llm.context import ConversationManager
from src.llm.intent import IntentAnalyzer
from src.llm.models import ConversationContext, IntentClassification
from src.llm.qa_display import QARenderer
from src.llm.qa_models import QAAnswer, QAResponse, QAValidity, VALIDITY_UNKNOWN
from src.llm.qa_planner import is_supported_qa_domain
from src.llm.qa_retrieval import QARetrievalService

logger = logging.getLogger(__name__)


class LegalQAPipeline:
    def __init__(
        self,
        intent_analyzer: Optional[IntentAnalyzer] = None,
        retrieval_service: Optional[QARetrievalService] = None,
        answer_generator: Optional[QAAnswerGenerator] = None,
        citation_verifier: Optional[CitationVerifier] = None,
        conversation_manager: Optional[ConversationManager] = None,
        verify_citations: bool = True,
        pretty_output: Optional[bool] = None,
    ) -> None:
        self._intent_analyzer = intent_analyzer or IntentAnalyzer()
        self._retrieval = retrieval_service or QARetrievalService()
        self._answer_generator = answer_generator or QAAnswerGenerator()
        self._citation_verifier = citation_verifier or CitationVerifier()
        self._conversation_manager = conversation_manager or ConversationManager()
        self._verify_citations = verify_citations
        self._pretty_output = sys.stdout.isatty() if pretty_output is None else pretty_output
        self._renderer = QARenderer() if self._pretty_output else None

    async def ask(self, message: str, conversation_id: Optional[str] = None) -> QAResponse:
        started = perf_counter()
        logger.info(
            "QA pipeline start conversation_id=%s message_chars=%d verify_citations=%s",
            conversation_id or "",
            len(message),
            self._verify_citations,
        )
        context = self._get_context(conversation_id)
        classification = await self._intent_analyzer.analyze(message, context)
        logger.info(
            "QA intent analyzed conversation_id=%s domain=%s confidence=%.2f intents=%s sub_queries=%d",
            classification.conversation_id,
            classification.domain,
            classification.confidence,
            [intent.type for intent in classification.intents],
            len(classification.sub_queries),
        )

        if not is_supported_qa_domain(classification):
            response = self._unsupported_response(classification)
            self._record_turn(message, classification)
            logger.info(
                "QA pipeline unsupported conversation_id=%s elapsed_ms=%.1f",
                classification.conversation_id,
                (perf_counter() - started) * 1000.0,
            )
            return response

        retrieval = await self._retrieval.retrieve(message, classification)
        logger.info(
            "QA retrieval complete conversation_id=%s status=%s provisions=%d errors=%d",
            classification.conversation_id,
            retrieval.retrieval_status,
            len(retrieval.provisions),
            len(retrieval.errors),
        )
        answer = await self._answer_generator.generate(message, classification, retrieval)
        logger.info(
            "QA answer generated conversation_id=%s answer_chars=%d citations=%d status=%s",
            classification.conversation_id,
            len(answer.answer),
            len(answer.citations),
            answer.retrieval_status,
        )
        verifications = await self._verify(answer) if self._verify_citations else []
        logger.info(
            "QA citation verification complete conversation_id=%s verified=%d total=%d",
            classification.conversation_id,
            sum(1 for result in verifications if result.verified),
            len(verifications),
        )
        self._apply_verifications(answer, verifications)
        if self._renderer:
            self._renderer.render(message, classification, retrieval, answer)
        self._record_turn(message, classification)

        response = QAResponse(
            answer=answer,
            citation_verifications=[CitationVerifier.result_to_dict(result) for result in verifications],
            citations_verified=bool(answer.citations) and all(result.verified for result in verifications),
            conversation_id=classification.conversation_id,
            domain=classification.domain,
            unsupported=False,
        )
        logger.info(
            "QA pipeline complete conversation_id=%s elapsed_ms=%.1f citations_verified=%s",
            classification.conversation_id,
            (perf_counter() - started) * 1000.0,
            response.citations_verified,
        )
        return response

    def _get_context(self, conversation_id: Optional[str]) -> Optional[ConversationContext]:
        if not conversation_id:
            return None
        return self._conversation_manager.get_context(conversation_id)

    async def _verify(self, answer: QAAnswer) -> list[VerificationResult]:
        if not answer.citations:
            return []
        return await self._citation_verifier.verify_qa_citations(answer.citations)

    def _apply_verifications(self, answer: QAAnswer, verifications: list[VerificationResult]) -> None:
        by_uid = {result.segment_uid or result.article_uid: result for result in verifications}
        for citation in answer.citations:
            result = by_uid.get(citation.uid)
            if not result and len(verifications) == 1 and len(answer.citations) == 1:
                result = verifications[0]
            if result:
                citation.verified = result.verified
                citation.reason = result.reason

    def _record_turn(self, message: str, classification: IntentClassification) -> None:
        self._conversation_manager.add_turn(classification.conversation_id, message, classification)

    def _unsupported_response(self, classification: IntentClassification) -> QAResponse:
        answer = QAAnswer(
            answer="Luồng hiện tại chỉ hỗ trợ câu hỏi pháp luật thuần. CONTRACT_QA và CONTRACT_REVIEW chưa nằm trong Phase 5 ban đầu.",
            citations=[],
            retrieved_provisions=[],
            intent={
                "domain": classification.domain,
                "intents": [intent.type for intent in classification.intents],
            },
            confidence=classification.confidence,
            validity=QAValidity(
                status=VALIDITY_UNKNOWN,
                reason="Unsupported domain for the pure legal QA pipeline.",
            ),
            retrieval_status="unsupported_domain",
        )
        return QAResponse(
            answer=answer,
            citation_verifications=[],
            citations_verified=False,
            conversation_id=classification.conversation_id,
            domain=classification.domain,
            unsupported=True,
        )


async def answer_legal_question(message: str, conversation_id: Optional[str] = None) -> dict:
    """Convenience entrypoint for future backend routes."""
    pipeline = LegalQAPipeline()
    response = await pipeline.ask(message, conversation_id=conversation_id)
    return response.to_dict()
