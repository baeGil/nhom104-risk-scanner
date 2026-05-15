import os
import logging
import json
from dotenv import load_dotenv
from src.cross_reference.llm_extractor import LLMExtractor

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def test_hardcoded_node():
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is not set!")
        return

    # Text của Điều 87 (Hiệu lực thi hành) - Ví dụ "khó nhằn" mà user đưa ra
    art_87_text = """
Điều 87. Hiệu lực thi hành
1. Thông tư này có hiệu lực thi hành kể từ ngày 01 tháng 01 năm 2022.
3. Thông tư này bãi bỏ:
a) Thông tư số 156/2013/TT-BTC ngày 06/11/2013 của Bộ Tài chính hướng dẫn thi hành một số điều của Luật quản lý thuế; Luật sửa đổi, bổ sung một số điều của Luật quản lý thuế và Nghị định số 83/2013/NĐ-CP ngày 22/7/2013 của Chính phủ;
c) Thông tư số 31/2017/TT-BTC ngày 18/4/2017 sửa đổi bổ sung một số điều của Thông tư số 99/2016/TT-BTC ngày 29/6/2016 của Bộ Tài chính hướng dẫn về quản lý hoàn thuế giá trị gia tăng;
e) Thông tư số 06/2017/TT-BTC ngày 20/01/2017 của Bộ Tài chính sửa đổi, bổ sung khoản 1 Điều 34a Thông tư số 156/2013/TT-BTC ngày 06/11/2013 của Bộ Tài chính hướng dẫn thi hành một số điều của Luật Quản lý thuế (đã được bổ sung tại Khoản 10 Điều 2 Thông tư 26/2015/TT-BTC);
4. Thông tư này bãi bỏ nội dung tại các Thông tư sau:
b) Điều 14, Điều 15, Điều 16, Điều 17, Điều 18, Điều 19, Điều 20, Điều 21 Chương IV Thông tư số 151/2014/TT-BTC ngày 10/10/2014 của Bộ Tài chính hướng dẫn thi hành nghị định số 91/2014/NĐ-CP ngày 01 tháng 10 năm 2014 của Chính phủ về việc sửa đổi, bổ sung một số điều tại các Nghị định quy định về thuế;
"""

    extractor = LLMExtractor("", "", "") # No Neo4j needed for hardcoded test
    try:
        mock_batch = [
            {"uid": "manual_test_article_87", "text": art_87_text}
        ]
        
        logger.info("Đang gọi LLM cho đoạn text cứng (Điều 87)...")
        result = extractor.extract_batch(mock_batch)
        
        print("\n=== KẾT QUẢ TRÍCH XUẤT LLM (MANUAL TEST) ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    finally:
        # Don't call close() because we didn't connect to driver
        pass

if __name__ == "__main__":
    test_hardcoded_node()
