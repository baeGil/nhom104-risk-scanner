"""
Prompt Templates for LLM operations.

Templates for:
- Intent analysis (Vietnamese legal domain)
- Clause extraction (T4.2)
- Compliance analysis (T4.4)
- Answer generation (T5.3)
"""
from __future__ import annotations

import re
from typing import Any


class PromptTemplate:
    """
    Prompt template with variable substitution.

    Usage:
        template = PromptTemplate("intent_analysis")
        prompt = template.render(user_input="Điều 17 Luật DN", conversation_history=[])
    """

    # All templates
    TEMPLATES: dict[str, str] = {}

    def __init__(self, name: str) -> None:
        self.name = name
        self._template = self.TEMPLATES.get(name, "")
        if not self._template:
            raise ValueError(f"Unknown template: {name}")

    def render(self, **variables: Any) -> str:
        """Render template with variable substitution."""
        result = self._template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    @classmethod
    def register(cls, name: str, template: str) -> None:
        """Register a new template."""
        cls.TEMPLATES[name] = template


# ---------------------------------------------------------------------------
# Intent Analysis Template
# ---------------------------------------------------------------------------

PromptTemplate.register("intent_analysis", """Bạn là hệ thống phân tích intent cho câu hỏi pháp lý tiếng Việt.

Câu hỏi: {{user_input}}
Lịch sử hội thoại: {{conversation_history}}

Phân tích và trả về JSON với cấu trúc sau:
- conversation_id: string
- turn_number: số nguyên
- domain: một trong QA, CONTRACT_REVIEW, CONTRACT_QA, EXPLAIN, CHITCHAT
- confidence: số 0-1
- intents: mảng, mỗi phần tử có type (LOOKUP/VALIDITY/COMPARISON/CHECKLIST/NUMERIC/TOPIC/SCENARIO/SEARCH), confidence, query_span [start, end], extracted (object chứa thông tin rút trích như document_name, article_number, year...)
- sub_queries: mảng, mỗi phần tử có intent, query, retrieval_strategy, requires
  - retrieval_strategy chỉ được dùng một trong: direct_lookup, hybrid_search, validity_check, comparison
  - requires chỉ được dùng các token chuẩn: legal_provision, effective_text, document_metadata, conversation_context, contract_context, citation_validation, amendment_history
- context_references: object
- routing: object với primary_pipeline, fallback_pipeline, context_needed

Quy tắc chọn retrieval_strategy:
- Dùng direct_lookup chỉ khi câu hỏi nêu rõ căn cứ cụ thể có thể tra cứu trực tiếp, ví dụ Điều/Khoản/Điểm và tên hoặc số hiệu văn bản: "Điều 17 Luật Doanh nghiệp 2020", "khoản 2 Điều 5 Nghị định 12/2022/NĐ-CP".
- Dùng hybrid_search cho câu hỏi tra cứu quy định chung theo chủ đề, nghĩa vụ, điều kiện, chế độ, mức phạt, thủ tục, quyền lợi, dù intent là LOOKUP. Ví dụ: "quy định về nghĩa vụ đóng bảo hiểm y tế khi ký hợp đồng lao động".
- Dùng validity_check cho câu hỏi hỏi tính hợp pháp/hiệu lực/vi phạm/đúng luật hay không.
- Dùng comparison cho câu hỏi so sánh hai hoặc nhiều quy định/văn bản.

Chỉ trả về JSON, không giải thích.""")


PromptTemplate.register("direct_reference_rewrite", """Bạn là hệ thống chuẩn hóa trích dẫn pháp luật Việt Nam cho truy hồi Neo4j.

Input:
{{query}}

Nhiệm vụ:
- Nếu input có thể quy về một căn cứ cụ thể, chuẩn hóa thành citation dạng: "điểm a khoản 1 Điều 1 Luật Lao động 2019" hoặc "khoản 2 Điều 5 Nghị định 12/2022/NĐ-CP".
- Chỉ trích xuất căn cứ có trong input; không tự bịa số điều/khoản/điểm/văn bản.
- Nếu input chỉ hỏi chủ đề chung và không nêu điều/khoản/điểm cụ thể, trả article=null và confidence thấp.

Trả về duy nhất một JSON object:
{
  "canonical_citation": "citation đã chuẩn hóa hoặc chuỗi rỗng",
  "article": 1,
  "clause": "1",
  "point": "a",
  "document_hint": "Luật Lao động",
  "so_ky_hieu": "45/2019/QH14",
  "year": "2019",
  "confidence": 0.0
}

Quy tắc:
- article là số Điều hoặc null.
- clause là số Khoản dạng string hoặc null.
- point là chữ cái Điểm dạng lowercase hoặc null.
- document_hint là tên văn bản ngắn, ví dụ "Luật Lao động", "Bộ luật Lao động", "Nghị định 12/2022/NĐ-CP".
- so_ky_hieu chỉ điền khi input có số hiệu văn bản rõ ràng.
- Không trả markdown, không giải thích ngoài JSON.
""")

# ---------------------------------------------------------------------------
# Clause Extraction Template (T4.2)
# ---------------------------------------------------------------------------

PromptTemplate.register("clause_extraction", """Trích xuất các điều khoản từ hợp đồng sau.

Với mỗi điều khoản, xác định:
- clause_type: "thanh_toán" | "bảo_hành" | "phạt" | "chấm_dứt" | "bồi_thường" | "bảo_mật" | "giải_quyết_tranh_chấp" | "force_majeure" | "khác"
- text_content: Nội dung điều khoản
- parties_involved: ["Bên A", "Bên B"] (nếu có)
- obligations: Danh sách nghĩa vụ (nếu có)
- amount: Số tiền (nếu có)
- deadline: Thời hạn (nếu có)

Contract text:
{{contract_text}}

Trả về JSON array.
""")

# ---------------------------------------------------------------------------
# Legal Query Rewrite Template (Task 4 Hybrid Retrieval)
# ---------------------------------------------------------------------------

PromptTemplate.register("legal_query_rewrite", """Bạn là hệ thống rewrite query pháp lý cho rà soát hợp đồng.

Nhiệm vụ: chuyển điều khoản hợp đồng thành kế hoạch tìm kiếm pháp luật.

Clause type:
{{clause_type}}

Contract clause:
{{clause_text}}

Trả về duy nhất một JSON object với schema:
{
  "original_text": "điều khoản gốc",
  "legal_issue": "vấn đề pháp lý ngắn gọn",
  "search_queries": ["các truy vấn pháp lý tự nhiên"],
  "keywords": ["cụm từ pháp lý quan trọng"],
  "expected_domains": ["tên luật/nghị định/bộ luật có khả năng liên quan"],
  "title_hints": ["tên văn bản hoặc chủ đề cần boost"],
  "risk_type": "penalty_cap | termination | wage_benefits | confidentiality | dispute_resolution | general",
  "filters": {"document_types": ["Luật", "Bộ luật", "Nghị định", "Thông tư"]},
  "confidence": 0.0
}

Yêu cầu:
- Không phân tích tuân thủ ở bước này.
- Không bịa citation cụ thể.
- Ưu tiên thuật ngữ pháp lý Việt Nam ngắn, dễ search.
- Chỉ trả về JSON, không giải thích.
""")

# ---------------------------------------------------------------------------
# Compliance Analysis Template (T4.4)
# ---------------------------------------------------------------------------

PromptTemplate.register("compliance_analysis", """Phân tích tuân thủ pháp luật cho điều khoản hợp đồng sau.

Contract clause:
{{clause_text}}

Matched legal provisions:
{{legal_provisions}}

Amendment history:
{{amendment_history}}

Trả về duy nhất một JSON object với schema:
{
  "violations": [
    {
      "clause": "tên hoặc loại điều khoản",
      "description": "mô tả vi phạm hoặc điểm chưa phù hợp",
      "citation": "trích dẫn pháp lý dạng dễ đọc",
      "severity": "low | medium | high"
    }
  ],
  "risks": ["rủi ro pháp lý"],
  "suggestions": ["đề xuất sửa đổi"],
  "citations": [
    {
      "display_text": "Điều/Khoản/Điểm + tên văn bản",
      "uid": "uid của matched provision",
      "document_title": "tên văn bản",
      "article": "số điều hoặc null",
      "clause": "số khoản hoặc null",
      "point": "ký hiệu điểm hoặc null"
    }
  ]
}

Quy tắc citation:
- Chỉ dùng uid xuất hiện trong Matched legal provisions.
- display_text phải là trích dẫn dễ đọc: Điều/Khoản/Điểm + tên văn bản.
- Nếu validity_signal không phải latest_known, nêu rõ rủi ro văn bản có thể đã bị sửa đổi.
- Nếu không có vi phạm, trả về "violations": [].
- Không trả về mảng string cho violations. Mỗi violation phải là một object đúng schema.

Chỉ trả về JSON object, không giải thích, không markdown.
""")

# ---------------------------------------------------------------------------
# Answer Generation Template (T5.3)
# ---------------------------------------------------------------------------

PromptTemplate.register("answer_generation", """Trả lời câu hỏi pháp lý sau dựa trên thông tin đã truy xuất.

Question:
{{question}}

Retrieved provisions:
{{retrieved_provisions}}

Effective text:
{{effective_text}}

Amendment history:
{{amendment_history}}

Trả lời bằng tiếng Việt, kèm trích dẫn chính xác (Điều X khoản Y Luật Z).
Trả về duy nhất một JSON object với schema:
{
  "answer": "câu trả lời tiếng Việt",
  "citations": [
    {
      "display_text": "Điều/Khoản/Điểm + tên văn bản",
      "uid": "uid lấy từ retrieved provisions",
      "document_title": "tên văn bản",
      "article": "số điều hoặc null",
      "clause": "số khoản hoặc null",
      "point": "ký hiệu điểm hoặc null",
      "text": "đoạn căn cứ ngắn"
    }
  ],
  "retrieval_status": "ok",
  "confidence": 0.0,
  "validity": {
    "status": "verified | likely_current | unknown",
    "reason": "lý do ngắn gọn",
    "evidence": []
  }
}

Quy tắc:
- Chỉ dùng citation uid xuất hiện trong Retrieved provisions.
- Nếu validity không chắc chắn, nói rõ là dữ liệu quan hệ chưa đủ để kết luận chắc chắn.
- Không trả về markdown hoặc giải thích ngoài JSON.
""")
