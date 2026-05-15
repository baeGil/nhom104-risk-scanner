import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMSegment:
    """Đại diện cho một đoạn text đã được gom đủ ngữ cảnh từ trên xuống dưới để đưa vào LLM."""
    doc_id: str
    article_uid: str
    clause_uid: Optional[str]
    point_uid: Optional[str]
    context_text: str  # Chuỗi text đã gộp (Preamble Điều + Khoản + Nội dung Điểm)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "article": self.article_uid,
            "clause": self.clause_uid,
            "point": self.point_uid,
            "text": self.context_text
        }

class ContextBuilder:
    """
    Xây dựng ngữ cảnh thác nước (Waterfall Context) cho LLM.
    Gộp Preamble của Điều -> Khoản -> Điểm thành một đoạn hội thoại duy nhất.
    """
    
    def __init__(self):
        pass

    def build_contexts(self, doc_id: str, parsed_doc: List[Dict[str, Any]]) -> List[LLMSegment]:
        """
        Duyệt qua danh sách các Điều (Articles) được Parser trả về và build context.
        """
        segments = []
        
        for article in parsed_doc:
            art_id = article.get('id', '')
            art_title = article.get('title', '')
            art_preamble = article.get('preamble', '').strip()
            
            # Ngữ cảnh cấp 1: Nội dung hoặc Preamble của Điều
            base_art_context = f"{art_title}. {art_preamble}".strip()
            
            clauses = article.get('children', [])
            if not clauses:
                # Nếu Điều không có Khoản, toàn bộ Điều là 1 đoạn
                if art_preamble:
                    segments.append(LLMSegment(doc_id, art_id, None, None, base_art_context))
                continue
                
            for clause in clauses:
                cl_id = clause.get('id', '')
                cl_title = clause.get('title', '')
                cl_preamble = clause.get('preamble', '').strip()
                
                # Ngữ cảnh cấp 2: Preamble Điều + Preamble Khoản
                cl_text = f"{cl_title} {cl_preamble}".strip()
                base_cl_context = f"{base_art_context}\n{cl_text}".strip()
                
                points = clause.get('children', [])
                if not points:
                    # Nếu Khoản không có Điểm
                    if cl_preamble:
                        segments.append(LLMSegment(doc_id, art_id, cl_id, None, base_cl_context))
                    continue
                    
                for point in points:
                    pt_id = point.get('id', '')
                    pt_title = point.get('title', '')
                    pt_content = point.get('content', '').strip()
                    
                    # Ngữ cảnh cấp 3: Preamble Điều + Preamble Khoản + Nội dung Điểm
                    pt_text = f"{pt_title} {pt_content}".strip()
                    full_context = f"{base_cl_context}\n{pt_text}".strip()
                    
                    segments.append(LLMSegment(doc_id, art_id, cl_id, pt_id, full_context))
                    
        return segments

    def batch_segments(self, segments: List[LLMSegment], batch_size: int = 5) -> List[List[LLMSegment]]:
        """
        Chia nhỏ danh sách segments thành các batch để đưa vào LLM (GPT-5 Nano).
        """
        return [segments[i:i + batch_size] for i in range(0, len(segments), batch_size)]

# Script test nhanh
if __name__ == "__main__":
    # Mô phỏng dữ liệu từ Parser
    mock_parsed = [
        {
            "id": "1",
            "title": "Điều 1",
            "preamble": "Sửa đổi, bổ sung một số điều của Luật Thuế:",
            "children": [
                {
                    "id": "1_1",
                    "title": "1.",
                    "preamble": "Sửa đổi khoản 2 Điều 3 như sau:",
                    "children": [
                        {
                            "id": "1_1_a",
                            "title": "a)",
                            "content": "Người nộp thuế phải nộp đúng hạn."
                        },
                        {
                            "id": "1_1_b",
                            "title": "b)",
                            "content": "Không áp dụng cho người tàn tật."
                        }
                    ]
                }
            ]
        }
    ]
    
    builder = ContextBuilder()
    segments = builder.build_contexts("DOC_001", mock_parsed)
    
    print("--- CÁC SEGMENTS SAU KHI GỘP NGỮ CẢNH ---")
    for i, seg in enumerate(segments):
        print(f"[{i+1}] Vị trí: Điều {seg.article_uid} > Khoản {seg.clause_uid} > Điểm {seg.point_uid}")
        print(f"Context Text:\n{seg.context_text}\n" + "-"*40)
