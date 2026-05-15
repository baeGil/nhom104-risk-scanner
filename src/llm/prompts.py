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
- context_references: object
- routing: object với primary_pipeline, fallback_pipeline, context_needed

Chỉ trả về JSON, không giải thích.""")

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

Với mỗi điều khoản, trả về:
- violations: Vi phạm pháp luật cụ thể
- risks: Rủi ro pháp lý
- suggestions: Đề xuất sửa đổi
- citations: mảng citation object, mỗi object gồm display_text, uid, document_title, article, clause, point

Quy tắc citation:
- Chỉ dùng uid xuất hiện trong Matched legal provisions.
- display_text phải là trích dẫn dễ đọc: Điều/Khoản/Điểm + tên văn bản.
- Nếu validity_signal không phải latest_known, nêu rõ rủi ro văn bản có thể đã bị sửa đổi.

Trả về JSON.
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
Trả về JSON với keys: answer (string), citations (array).
""")
