import os
import logging
import json
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMExtractor:
    """
    Handles LLM-based extraction of legal relationships using waterfall context from Neo4j.
    """
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        if uri:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        else:
            self.driver = None

        # Khởi tạo OpenAI client 1 lần duy nhất để tái dùng connection pool
        from openai import OpenAI

        _raw_base_url = os.environ.get("OPENAI_BASE_URL", "")
        base_url = _raw_base_url.strip() if _raw_base_url.strip() else None

        # Xóa biến môi trường rỗng để tránh SDK tự đọc và dùng URL không hợp lệ
        if not base_url and "OPENAI_BASE_URL" in os.environ:
            del os.environ["OPENAI_BASE_URL"]

        client_kwargs: Dict[str, Any] = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "timeout": 120.0,   # Tăng lên 120s để chịu được server chậm / rate limit
            "max_retries": 2,
        }
        if base_url:
            client_kwargs["base_url"] = base_url

        self._model = os.getenv("OPENAI_MODEL", "gpt-5-nano").strip()
        self._client = OpenAI(**client_kwargs)
        logger.info(f"LLMExtractor: model={self._model}, base_url={base_url or '(OpenAI default)'}")

    def close(self):
        if self.driver:
            self.driver.close()

    def get_waterfall_context(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves hierarchical context for all leaf nodes (Article/Clause/Point) in a document.
        Leaf nodes are the lowest available level in the hierarchy.
        """
        if not self.driver:
            logger.error("Neo4j driver is not initialized. Cannot fetch waterfall context.")
            return []
        query = """
        MATCH (d:Document {id: $doc_id})
        MATCH (d)-[:HAS_CHAPTER|HAS_SECTION|HAS_ARTICLE*..3]->(a:Article)
        OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(c:Clause)
        OPTIONAL MATCH (c)-[:HAS_POINT]->(p:Point)
        RETURN 
            a.uid AS a_uid, a.clean_text AS a_txt, toInteger(a.index) AS a_idx,
            c.uid AS c_uid, c.clean_text AS c_txt, toInteger(c.index) AS c_idx,
            p.uid AS p_uid, p.clean_text AS p_txt, p.letter AS p_letter
        ORDER BY a_idx, c_idx, p_letter
        """
        
        leaf_contexts = []
        with self.driver.session() as session:
            result = session.run(query, doc_id=str(doc_id))
            for record in result:
                # Determine the leaf node and build context
                a_txt = (record["a_txt"] or "").strip()
                c_txt = (record["c_txt"] or "").strip()
                p_txt = (record["p_txt"] or "").strip()
                
                # Combine waterfall context: Article -> Clause -> Point
                context_parts = [a_txt]
                if c_txt:
                    context_parts.append(c_txt)
                if p_txt:
                    context_parts.append(p_txt)
                
                full_context = "\n".join(context_parts)
                
                # The leaf node is the most specific one available
                leaf_uid = record["p_uid"] or record["c_uid"] or record["a_uid"]
                
                # Avoid duplicates if a Clause has multiple Points (Cypher returns a row per Point)
                # We only want to process the actual leaf nodes.
                # If p_uid exists, it's the leaf. If not, c_uid is the leaf.
                leaf_contexts.append({
                    "uid": leaf_uid,
                    "text": full_context
                })
        
        # Deduplicate leaf_contexts based on UID (just in case, though Cypher logic above is mostly fine)
        seen_uids = set()
        unique_contexts = []
        for ctx in leaf_contexts:
            if ctx["uid"] not in seen_uids:
                unique_contexts.append(ctx)
                seen_uids.add(ctx["uid"])
                
        return unique_contexts
    def extract_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sends a batch of contexts to the LLM and returns the structured relationships.
        """
        llm_input = {ctx["uid"]: ctx["text"] for ctx in batch}

        system_prompt = """Bạn là chuyên gia pháp luật Việt Nam, chuyên về phân tích và bóc tách các mối quan hệ giữa các văn bản quy phạm pháp luật.
Nhiệm vụ của bạn là đọc các đoạn văn bản (context) được cung cấp và trích xuất các quan hệ pháp lý dưới dạng JSON.

HƯỚNG DẪN TRÍCH XUẤT:
1. Phân loại quan hệ (action_type):
   - sua_doi: Sửa đổi nội dung điều/khoản/điểm hiện có.
   - bo_sung: Bổ sung thêm điều/khoản/điểm mới.
   - bai_bo: Bãi bỏ, hủy bỏ hiệu lực một phần hoặc toàn bộ.
   - thay_the: Thay thế nội dung, cụm từ hoặc toàn bộ văn bản.
   - internal_ref: Dẫn chiếu tới các phần khác trong CÙNG văn bản.
   - external_ref: Dẫn chiếu tới các văn bản quy phạm pháp luật khác.
    - exception: Các trường hợp ngoại lệ (thường có từ "trừ", "ngoại trừ").

2. Quy tắc chính xác pháp lý (QUAN TRỌNG):
   - Rule of Explicit Citation: CHỈ trích xuất quan hệ khi văn bản có dẫn chiếu ĐÍCH DANH tên văn bản hoặc số Điều/Khoản/Điểm cụ thể. Nếu một đoạn văn chỉ nêu nội dung quy định, nghĩa vụ, hoặc hình phạt mà không nhắc đến một thực thể pháp lý khác, bạn phải trả về danh sách rỗng `[]` cho UID đó.
   - Rule of Internal Content: Tuyệt đối KHÔNG trích xuất các nội dung định nghĩa nội tại của chính văn bản làm quan hệ `bo_sung`. Ví dụ: "Điều 4. Biện pháp khắc phục..." chỉ là nội dung của Điều 4, nó KHÔNG phải là hành động bổ sung cho Điều 4.
   - Rule of Verbatim: Trong trường `quote_context`, bạn PHẢI trích dẫn NGUYÊN VĂN toàn bộ câu hoặc đoạn văn chứa quan hệ đó từ context. KHÔNG được tóm tắt, KHÔNG được dùng dấu "..." để lược bớt, KHÔNG được sửa đổi dù chỉ một dấu phẩy.
   - Rule of Title: KHÔNG trích xuất quan hệ từ các văn bản được nhắc đến chỉ như một phần của TÊN (Tiêu đề) của văn bản đang xét.
   - Rule of Passive History: BỎ QUA các hành động mang tính chất liệt kê lịch sử bị động (ví dụ: "đã được sửa đổi bởi...", "theo quy định đã được sửa đổi tại..."). Chỉ trích xuất các hành động CHỦ ĐỘNG do văn bản hiện tại thực hiện.
    - Rule of Enumeration: Nếu câu văn liệt kê nhiều đối tượng (ví dụ: "Điều 1, 2 và 3" hoặc "khoản 1, 2, 3 Điều 9"), bạn PHẢI tách chúng thành các object riêng biệt. Ví dụ: "khoản 1 và 2 Điều 5" phải được tách thành 2 object: một cái cho khoản 1 Điều 5, một cái cho khoản 2 Điều 5.
   - Rule of Context Override: KHÔNG tách liệt kê nếu danh sách đó nằm trong tiêu đề của một văn bản khác.

3. Định dạng đầu ra: Trả về một JSON object duy nhất có khóa là `results`. Mỗi phần tử trong `results` phải tương ứng với một `uid` được cung cấp trong input. Nếu một UID không chứa dẫn chiếu pháp lý nào, kết quả phải là mảng rỗng: `"uid": []`.

Ví dụ Output (Minh họa Rule of Enumeration):
{
  "results": {
    "doc_123_dieu_1": [
      {
        "action_type": "external_ref",
        "target": {"document_name": "Luật A", "dieu": "9", "khoan": "1", "diem": null},
        "quote_context": "Đình chỉ các hoạt động quy định tại khoản 1, 2 Điều 9 của Luật A"
      },
      {
        "action_type": "external_ref",
        "target": {"document_name": "Luật A", "dieu": "9", "khoan": "2", "diem": null},
        "quote_context": "Đình chỉ các hoạt động quy định tại khoản 1, 2 Điều 9 của Luật A"
      }
    ]
  }
}
"""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(llm_input, ensure_ascii=False)}
                ],
                response_format={"type": "json_object"}
            )

            usage = response.usage
            logger.info(
                f"LLM done — in={usage.prompt_tokens} tok, out={usage.completion_tokens} tok"
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return {"results": {uid: [] for uid in llm_input.keys()}, "error": str(e)}

    def batch_by_word_count(self, contexts: List[Dict[str, Any]], max_words: int = 1500) -> List[List[Dict[str, Any]]]:
        """
        Groups context nodes into batches based on total word count.
        """
        batches = []
        current_batch = []
        current_word_count = 0
        
        for ctx in contexts:
            word_count = len(ctx["text"].split())
            if current_word_count + word_count > max_words and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_word_count = 0
            
            current_batch.append(ctx)
            current_word_count += word_count
            
        if current_batch:
            batches.append(current_batch)
            
        return batches
