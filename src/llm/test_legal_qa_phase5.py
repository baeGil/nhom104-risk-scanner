from __future__ import annotations

import asyncio

from src.contract.hybrid_retriever import LegalCandidate, ScoreFactors
from src.llm.answer_generator import QAAnswerGenerator
from src.llm.citation_verifier import CitationVerifier, ParsedCitation, VerificationResult
from src.llm.intent import IntentAnalyzer
from src.llm.models import IntentClassification, SubIntent, SubQuery
from src.llm.qa_models import QACitation, QAAnswer, QARetrievalResult, QARetrievedProvision, QAValidity
from src.llm.qa_pipeline import LegalQAPipeline
from src.llm.qa_planner import plan_qa_sub_queries
from src.llm.qa_retrieval import QARetrievalService, parse_legal_reference, _normalize_so_ky_hieu


def test_qa_planner_maps_topic_to_hybrid_search():
    classification = IntentClassification(
        conversation_id="c1",
        turn_number=1,
        domain="QA",
        confidence=0.9,
        intents=[
            SubIntent(
                type="TOPIC",
                confidence=0.9,
                extracted={"topic": "bảo hiểm xã hội"},
            )
        ],
    )

    planned = plan_qa_sub_queries(classification, "Quy định về bảo hiểm xã hội")

    assert len(planned) == 1
    assert planned[0].intent == "TOPIC"
    assert planned[0].retrieval_strategy == "hybrid_search"
    assert "legal_provision" in planned[0].requires


def test_qa_planner_normalizes_vector_search_to_hybrid_search():
    classification = IntentClassification(
        conversation_id="c1",
        turn_number=1,
        domain="QA",
        confidence=0.9,
        sub_queries=[
            SubQuery(
                intent="TOPIC",
                query="Quy định về bảo hiểm xã hội",
                retrieval_strategy="vector_search",
                requires=[],
            )
        ],
    )

    planned = plan_qa_sub_queries(classification)

    assert planned[0].retrieval_strategy == "hybrid_search"
    assert "effective_text" in planned[0].requires


def test_qa_planner_converts_broad_lookup_to_hybrid_search():
    classification = IntentClassification(
        conversation_id="c1",
        turn_number=1,
        domain="QA",
        confidence=0.9,
        sub_queries=[
            SubQuery(
                intent="LOOKUP",
                query="Quy định pháp luật Việt Nam về nghĩa vụ đóng bảo hiểm y tế khi ký hợp đồng lao động",
                retrieval_strategy="direct_lookup",
                requires=["legal_provision"],
            )
        ],
    )

    planned = plan_qa_sub_queries(classification)

    assert planned[0].retrieval_strategy == "hybrid_search"
    assert "effective_text" in planned[0].requires


def test_qa_planner_keeps_article_lookup_as_direct_lookup():
    classification = IntentClassification(
        conversation_id="c1",
        turn_number=1,
        domain="QA",
        confidence=0.9,
        sub_queries=[
            SubQuery(
                intent="LOOKUP",
                query="Điều 17 Luật Doanh nghiệp 2020",
                retrieval_strategy="direct_lookup",
                requires=["legal_provision"],
            )
        ],
    )

    planned = plan_qa_sub_queries(classification)

    assert planned[0].retrieval_strategy == "direct_lookup"


def test_qa_planner_fallback_lookup_without_article_uses_hybrid_search():
    classification = IntentClassification(
        conversation_id="c1",
        turn_number=1,
        domain="QA",
        confidence=0.9,
        intents=[
            SubIntent(
                type="LOOKUP",
                confidence=0.9,
                extracted={"topic": "nghĩa vụ đóng bảo hiểm y tế khi ký hợp đồng lao động"},
            )
        ],
    )

    planned = plan_qa_sub_queries(classification)

    assert planned[0].retrieval_strategy == "hybrid_search"


def test_intent_analyzer_normalizes_llm_sub_query_schema():
    llm = FakeLLM(
        [
            {
                "conversation_id": "c1",
                "turn_number": 1,
                "domain": "QA",
                "confidence": 0.98,
                "intents": [
                    {
                        "type": "VALIDITY",
                        "confidence": 0.97,
                        "query_span": [0, 12],
                        "extracted": {},
                    }
                ],
                "sub_queries": [
                    {
                        "intent": "VALIDITY",
                        "query": "Ký hợp đồng lao động mà không đóng BHYT có vi phạm không",
                        "retrieval_strategy": "tra cứu quy định về trách nhiệm đóng BHYT và chế tài",
                        "requires": [
                            "quy định về người lao động thuộc diện tham gia BHYT bắt buộc",
                            "mức xử phạt/biện pháp khắc phục",
                        ],
                    }
                ],
                "context_references": {},
                "routing": {},
            }
        ]
    )
    analyzer = IntentAnalyzer(llm_client=llm)

    classification = asyncio.run(analyzer.analyze("Ký hợp đồng lao động mà không đóng BHYT có vi phạm không"))

    assert classification.sub_queries[0].retrieval_strategy == "validity_check"
    assert classification.sub_queries[0].requires == [
        "legal_provision",
        "document_metadata",
        "effective_text",
    ]


def test_parse_legal_reference_extracts_article_clause_point():
    ref = parse_legal_reference("Điều 17 khoản 2 điểm a Luật Doanh nghiệp 2020")

    assert ref.article == 17
    assert ref.clause == "2"
    assert ref.point == "a"
    assert ref.document_hint == "Luật Doanh nghiệp"
    assert ref.year == "2020"


def test_parse_legal_reference_extracts_common_so_ky_hieu():
    ref = parse_legal_reference("khoản 1 Điều 3 Nghị định 12/2022/NĐ-CP")

    assert ref.article == 3
    assert ref.clause == "1"
    assert ref.so_ky_hieu == "12/2022/NĐ-CP"


def test_normalize_so_ky_hieu_matches_lookup_key():
    assert _normalize_so_ky_hieu("135/2020/NĐ-CP", "Nghị định") == "ND-135-2020"
    assert _normalize_so_ky_hieu("45/2019/QH14", "Bộ luật Lao động") == "LT-045-2019"


def test_direct_lookup_rewrites_natural_reference_before_parsing():
    llm = FakeLLM(
        [
            {
                "canonical_citation": "điểm a khoản 1 Điều 1 Bộ luật Lao động 2019",
                "article": 1,
                "clause": "1",
                "point": "a",
                "document_hint": "Bộ luật Lao động",
                "so_ky_hieu": "45/2019/QH14",
                "year": "2019",
                "confidence": 0.9,
            }
        ]
    )
    service = QARetrievalService(hybrid_retriever=FakeHybridRetriever([]), llm_client=llm)

    ref = asyncio.run(service._resolve_direct_reference("tìm điểm a khoản đầu điều đầu luật lao động"))

    assert ref.article == 1
    assert ref.clause == "1"
    assert ref.point == "a"
    assert ref.document_hint == "Bộ luật Lao động"
    assert ref.so_ky_hieu == "45/2019/QH14"


def test_direct_lookup_resolves_doc_id_from_lookup():
    service = QARetrievalService(hybrid_retriever=FakeHybridRetriever([]))
    service._doc_lookup = {"ND-135-2020": "152734"}
    ref = parse_legal_reference("Nội dung Điều 8 Nghị định 135/2020/NĐ-CP")

    doc_id = service._resolve_doc_id(ref)

    assert ref.article == 8
    assert doc_id == "152734"


def test_direct_lookup_without_article_returns_no_results():
    service = QARetrievalService(hybrid_retriever=FakeHybridRetriever([]))
    query = SubQuery(intent="LOOKUP", query="Luật Doanh nghiệp 2020", retrieval_strategy="direct_lookup")

    result, debug = asyncio.run(service.retrieve_sub_query(query))

    assert result == []
    assert debug["rewritten_query"] == "Luật Doanh nghiệp 2020"


def test_topic_retrieval_normalizes_phase4_candidate():
    candidate = LegalCandidate(
        uid="doc_1_dieu_17_khoan_2",
        segment_type="Clause",
        text="Doanh nghiệp có quyền kinh doanh ngành nghề luật không cấm.",
        document_title="Luật Doanh nghiệp 2020",
        document_so_ky_hieu="LT-068-2020",
        document_type="Luật",
        article_uid="doc_1_dieu_17",
        article_index=17,
        clause_index=2,
        combined_score=2.5,
        score_factors=ScoreFactors(vector=0.8, authority=3.0),
    )
    service = QARetrievalService(hybrid_retriever=FakeHybridRetriever([candidate]))
    classification = IntentClassification(
        conversation_id="c1",
        turn_number=1,
        domain="QA",
        confidence=0.9,
        sub_queries=[SubQuery(intent="TOPIC", query="quyền doanh nghiệp", retrieval_strategy="hybrid_search")],
    )

    result = asyncio.run(service.retrieve("quyền doanh nghiệp", classification))

    assert result.retrieval_status == "ok"
    assert result.provisions[0].uid == "doc_1_dieu_17_khoan_2"
    assert result.provisions[0].display_citation == "Điều 17 khoản 2 Luật Doanh nghiệp 2020"


def test_answer_generator_parses_json_and_filters_unknown_uid():
    provision = QARetrievedProvision(
        uid="doc_1_dieu_17",
        text="Nội dung Điều 17",
        display_citation="Điều 17 Luật Doanh nghiệp 2020",
        article_index=17,
        document_title="Luật Doanh nghiệp 2020",
    )
    retrieval = QARetrievalResult(query="q", provisions=[provision])
    classification = IntentClassification("c1", 1, "QA", 0.9)
    llm = FakeLLM(
        [
            {
                "answer": "Câu trả lời",
                "citations": [
                    {"display_text": "bad", "uid": "missing"},
                    {"display_text": "Điều 17 Luật Doanh nghiệp 2020", "uid": "doc_1_dieu_17"},
                ],
                "confidence": 0.8,
            }
        ]
    )

    answer = asyncio.run(QAAnswerGenerator(llm).generate("q", classification, retrieval))

    assert answer.answer == "Câu trả lời"
    assert [c.uid for c in answer.citations] == ["doc_1_dieu_17"]
    assert answer.warnings


def test_answer_generator_retries_malformed_json():
    provision = QARetrievedProvision(uid="doc_1_dieu_17", text="Nội dung")
    retrieval = QARetrievalResult(query="q", provisions=[provision])
    classification = IntentClassification("c1", 1, "QA", 0.9)
    llm = FakeLLM(["not json", {"answer": "Sau retry", "citations": []}])

    answer = asyncio.run(QAAnswerGenerator(llm).generate("q", classification, retrieval))

    assert answer.answer == "Sau retry"
    assert len(llm.calls) == 2


def test_answer_generator_no_result_answer():
    retrieval = QARetrievalResult(query="q", provisions=[], retrieval_status="no_results")
    classification = IntentClassification("c1", 1, "QA", 0.9)

    answer = QAAnswerGenerator(FakeLLM([])).no_result_answer(classification, retrieval)

    assert answer.retrieval_status == "no_results"
    assert answer.citations == []


def test_citation_verifier_accepts_qa_citation_objects():
    verifier = FakeCitationVerifier()
    citations = [QACitation(display_text="Điều 17 Luật Doanh nghiệp 2020", uid="doc_1_dieu_17")]

    results = asyncio.run(verifier.verify_qa_citations(citations))

    assert results[0].verified is True
    assert results[0].segment_uid == "doc_1_dieu_17"


def test_pipeline_smoke_with_mocks():
    classification = IntentClassification(
        conversation_id="c1",
        turn_number=1,
        domain="QA",
        confidence=0.9,
        sub_queries=[SubQuery(intent="TOPIC", query="q", retrieval_strategy="hybrid_search")],
    )
    provision = QARetrievedProvision(
        uid="doc_1_dieu_17",
        text="Nội dung",
        display_citation="Điều 17 Luật Doanh nghiệp 2020",
        validity=QAValidity(status="unknown", reason="mock"),
    )
    answer = QAAnswer(
        answer="Câu trả lời",
        citations=[QACitation(display_text="Điều 17 Luật Doanh nghiệp 2020", uid="doc_1_dieu_17")],
        retrieved_provisions=[provision],
    )
    pipeline = LegalQAPipeline(
        intent_analyzer=FakeIntentAnalyzer(classification),
        retrieval_service=FakeRetrievalService(QARetrievalResult(query="q", provisions=[provision])),
        answer_generator=FakeAnswerGenerator(answer),
        citation_verifier=FakeCitationVerifier(),
    )

    response = asyncio.run(pipeline.ask("q"))
    data = response.to_dict()

    assert data["answer"] == "Câu trả lời"
    assert data["citations_verified"] is True
    assert data["citation_verifications"][0]["verified"] is True


class FakeHybridRetriever:
    def __init__(self, candidates):
        self.candidates = candidates

    async def retrieve(self, plan):
        return self.candidates


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def chat(self, prompt, schema=None, temperature=0.0):
        self.calls.append(prompt)
        if not self.responses:
            return {"answer": "", "citations": []}
        return self.responses.pop(0)

    async def extract(self, text, schema):
        return {}

    async def classify(self, text, categories):
        return {}


class FakeCitationVerifier(CitationVerifier):
    def __init__(self):
        pass

    async def verify_qa_citations(self, citations):
        results = []
        for citation in citations:
            results.append(
                VerificationResult(
                    citation=ParsedCitation(raw_text=citation.display_text),
                    verified=True,
                    is_current=True,
                    article_uid=citation.uid,
                    segment_uid=citation.uid,
                    document_title=citation.document_title,
                )
            )
        return results


class FakeIntentAnalyzer(IntentAnalyzer):
    def __init__(self, classification):
        self.classification = classification

    async def analyze(self, query, context=None):
        return self.classification


class FakeRetrievalService:
    def __init__(self, result):
        self.result = result

    async def retrieve(self, question, classification):
        return self.result


class FakeAnswerGenerator:
    def __init__(self, answer):
        self.answer = answer

    async def generate(self, question, classification, retrieval):
        return self.answer
