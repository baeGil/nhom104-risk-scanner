import asyncio
import json
import os
import pandas as pd
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm
from src.config import OPENAI_API_KEY

MODEL = "gpt-5.4-nano"
PROCESSED_CHECKPOINT_PATH = "data/extracted_relations_batched_processed_uids.json"

# Prompt template for batch processing
SYSTEM_PROMPT = """Bạn là chuyên gia phân tích văn bản pháp luật Việt Nam. Nhiệm vụ của bạn là trích xuất quan hệ pháp luật từ DANH SÁCH các đoạn văn bản được cung cấp.

Bạn phải phân loại mỗi quan hệ vào đúng 1 trong 3 nhóm:

1. internal
- Dẫn chiếu đến điểm, khoản, điều hoặc toàn bộ văn bản trong CÙNG văn bản nguồn.
- Dấu hiệu thường gặp: "Điều này", "Khoản này", "Điểm này", "Luật này", "Bộ luật này", "Nghị định này", "Thông tư này", "Điều 1 của Luật này", "điểm a khoản 1 Điều 37a của Luật này".
- target_doc phải là một trong các cụm nội bộ xuất hiện hoặc được suy ra: "luật này", "bộ luật này", "nghị định này", "thông tư này", "văn bản này".
- target_article là số/ký hiệu điều, ví dụ "1", "37a". Nếu chỉ nói "Điều này" và source_uid có dạng doc_X_dieu_37a... thì target_article là "37a".
- target_clause là số khoản, ví dụ "1", "2". Nếu không có khoản thì null.
- target_diem là chữ điểm, ví dụ "a", "b", "đ". Nếu không có điểm thì null.
- Không bao giờ ghi "luật này", "nghị định này", "thông tư này" vào target_clause hoặc target_diem.

2. external
- Dẫn chiếu đến văn bản KHÁC.
- target_doc có thể là số hiệu hoặc tên văn bản, ví dụ "12/2022/NĐ-CP", "Bộ luật Lao động", "Luật Xử lý vi phạm hành chính", "Nghị định 46/2016/NĐ-CP".
- Nếu câu chỉ nêu tên văn bản mà không có số hiệu, vẫn phải trích xuất. Ví dụ "theo Bộ luật Lao động" => target_doc là "Bộ luật Lao động".
- Nếu có điều/khoản/điểm của văn bản ngoài thì điền target_article, target_clause, target_diem; nếu không có thì để null.

3. modify
- Quan hệ mà đoạn nguồn CHỦ ĐỘNG sửa đổi, bổ sung, thay thế, bãi bỏ, đình chỉ, ngưng hiệu lực hoặc làm hết hiệu lực một phần/toàn bộ văn bản khác.
- relationship_type luôn là "modify".
- modify_action phải là một trong:
  "sua_doi" cho sửa đổi;
  "bo_sung" cho bổ sung;
  "thay_the" cho thay thế;
  "bai_bo" cho bãi bỏ;
  "dinh_chi" cho đình chỉ;
  "ngung_hieu_luc" cho ngưng hiệu lực;
  "het_hieu_luc" cho hết hiệu lực.
- Chỉ lấy quan hệ chủ động. Ví dụ: "Sửa đổi Điều 5 của Nghị định 12/2022/NĐ-CP" thì lấy. "Điều 5 được sửa đổi bởi Nghị định 99/2024/NĐ-CP" thì không lấy nếu đoạn nguồn chỉ đang mô tả văn bản bị sửa.
- Với internal và external, modify_action luôn là null.

QUY TẮC TÁCH NHIỀU ĐỐI TƯỢNG:
- Nếu một câu dẫn chiếu đến nhiều đối tượng, phải tạo nhiều object riêng biệt.
- Ví dụ "khoản 1, khoản 2 Điều 10" => 2 object: khoản 1 Điều 10 và khoản 2 Điều 10.
- Ví dụ "các điểm a, b, c, đ, e, h, i, k, l, m và n khoản 1 Điều 37a của Luật này" => tạo từng object riêng:
  điểm a khoản 1 Điều 37a;
  điểm b khoản 1 Điều 37a;
  điểm c khoản 1 Điều 37a;
  điểm đ khoản 1 Điều 37a;
  tiếp tục cho từng điểm còn lại.
- Khi nhiều điểm/khoản dùng chung điều hoặc văn bản phía sau, phải copy phần chung đó vào từng object.

QUY TẮC SUY LUẬN TỪ source_uid:
- source_uid có thể chứa vị trí nguồn, ví dụ "doc_123_dieu_37a_khoan_1_diem_a".
- Nếu văn bản nói "Điều này", dùng điều trong source_uid làm target_article.
- Nếu văn bản nói "Khoản này", dùng khoản trong source_uid làm target_clause và điều trong source_uid làm target_article.
- Nếu văn bản nói "Điểm này", dùng điểm/khoản/điều trong source_uid làm target_diem, target_clause, target_article.
- Nếu không thể suy luận chắc chắn thì để field tương ứng là null, không bịa.

Mỗi object trong mảng JSON phải có đúng cấu trúc:
{
  "source_uid": "ID của đoạn văn bản chứa quan hệ này",
  "target_doc": "tên/số hiệu văn bản hoặc 'luật này'/'nghị định này'/...",
  "target_article": "số điều hoặc null",
  "target_clause": "số khoản hoặc null",
  "target_diem": "tên điểm hoặc null",
  "relationship_type": "internal" | "external" | "modify",
  "modify_action": "sua_doi" | "bo_sung" | "thay_the" | "bai_bo" | "dinh_chi" | "ngung_hieu_luc" | "het_hieu_luc" | null
}

QUY TẮC BATCH:
- Tôi cung cấp danh sách đoạn văn bản, mỗi đoạn có một source_uid.
- Trả về một MẢNG JSON duy nhất chứa tất cả quan hệ tìm thấy trong tất cả đoạn.
- Mỗi object phải dùng đúng source_uid của đoạn chứa quan hệ.
- Nếu không tìm thấy quan hệ nào, trả về [].
- Chỉ trả về JSON array hợp lệ, không giải thích, không markdown, không code fence."""

async def process_batch(client, batch_segments):
    """Xử lý một batch các đoạn văn bản."""
    # Ghép các đoạn văn bản lại thành 1 prompt
    formatted_texts = []
    for i, seg in enumerate(batch_segments):
        formatted_texts.append(f"[{i+1}] ID: {seg['uid']}\nNội dung: {seg['text']}")
    
    combined_text = "\n\n".join(formatted_texts)
    
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia pháp luật. Trả về duy nhất 1 JSON array chứa các quan hệ trích xuất được. Mỗi quan hệ phải có source_uid chính xác.",
                    },
                    {
                        "role": "user",
                        "content": f"{SYSTEM_PROMPT}\n\nDANH SÁCH VĂN BẢN:\n{combined_text}",
                    },
                ],
                temperature=0.0,
                timeout=60.0,
            )

            content = response.choices[0].message.content.strip()
            usage = response.usage
            
            # Log tokens
            in_tokens = usage.prompt_tokens if usage else 0
            out_tokens = usage.completion_tokens if usage else 0
            # print(f"  [Batch] In: {in_tokens}, Out: {out_tokens}")
            
            # Xử lý markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:].strip()
            
            result = json.loads(content)
            
            if not isinstance(result, list):
                if isinstance(result, dict):
                    for key in ['results', 'relationships', 'data']:
                        if key in result and isinstance(result[key], list):
                            result = result[key]
                            break
                    else:
                        result = [result]
                else:
                    result = []
            
            return result, in_tokens, out_tokens
        except Exception as e:
            if attempt == 2:
                print(f"Error processing batch: {e}")
            await asyncio.sleep(2 * (attempt + 1))
    return [], 0, 0

def create_batches_by_chars(segments, max_chars=4000):
    """Chia segments thành các batch dựa trên số lượng ký tự."""
    batches = []
    current_batch = []
    current_chars = 0
    
    for seg in segments:
        text_len = len(seg['text'])
        if current_chars + text_len > max_chars and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0
        
        current_batch.append(seg)
        current_chars += text_len
        
    if current_batch:
        batches.append(current_batch)
        
    return batches

async def main():
    # Load data
    input_path = 'data/legal_segments_for_colab.parquet'
    if not os.path.exists(input_path):
        input_path = '../../data/legal_segments_for_colab.parquet'
    
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} not found.")
        return

    df = pd.read_parquet(input_path)
    all_segments = df.to_dict('records')
    
    # --- Checkpoint / Resume Logic ---
    output_dir = 'data' if os.path.exists('data') else '../../data'
    output_path = os.path.join(output_dir, 'extracted_relations_batched.json')
    
    all_results = []
    processed_uids = set()
    
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
                processed_uids = {res.get('source_uid') for res in all_results if res.get('source_uid')}
            print(f"Loaded {len(all_results)} existing relations from {len(processed_uids)} processed segments.")
        except Exception as e:
            print(f"Warning: Could not load existing results: {e}")
            all_results = []

    if os.path.exists(PROCESSED_CHECKPOINT_PATH):
        try:
            with open(PROCESSED_CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                processed_checkpoint = json.load(f)
                if isinstance(processed_checkpoint, list):
                    processed_uids.update(str(uid) for uid in processed_checkpoint if uid)
                    print(f"Loaded checkpoint for {len(processed_checkpoint)} processed segments.")
        except Exception as e:
            print(f"Warning: Could not load processed checkpoint: {e}")
    
    # Lọc những segments chưa được xử lý
    segments_to_process = [s for s in all_segments if s['uid'] not in processed_uids]
    
    # GIỚI HẠN XỬ LÝ CHO MỖI LẦN CHẠY (Ví dụ chia làm 3 lần cho 7000 segment)
    CHUNK_SIZE = 2000
    
    if not segments_to_process:
        print("✅ All segments already processed!")
        return

    segments_current_run = segments_to_process[:CHUNK_SIZE]
    print(f"Processing chunk: {len(segments_current_run)} segments (Remaining total: {len(segments_to_process)})")
    
    # Chia batch theo ký tự
    batches = create_batches_by_chars(segments_current_run, max_chars=5000)
    print(f"Current run: {len(segments_current_run)} segments in {len(batches)} batches.")

    total_in_tokens = 0
    total_out_tokens = 0
    new_results = []
    newly_processed_uids = []
    
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    async with client:
        MAX_CONCURRENT = 3
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def batch_task(batch):
            async with sem:
                res, in_t, out_t = await process_batch(client, batch)
                batch_uids = [seg["uid"] for seg in batch if seg.get("uid")]
                return res, in_t, out_t, batch_uids

        tasks = [batch_task(b) for b in batches]
        
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            batch_res, in_t, out_t, batch_uids = await f
            new_results.extend(batch_res)
            total_in_tokens += in_t
            total_out_tokens += out_t
            newly_processed_uids.extend(batch_uids)

    # Gộp kết quả mới vào kết quả cũ
    all_results.extend(new_results)
    
    # Lưu lại
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Lưu checkpoint riêng để các segment không sinh ra relation cũng không bị chạy lại
    processed_uids.update(newly_processed_uids)
    with open(PROCESSED_CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(processed_uids), f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Chunk complete!")
    print(f"New relationships found: {len(new_results)}")
    print(f"Total input tokens: {total_in_tokens}")
    print(f"Total output tokens: {total_out_tokens}")
    print(f"Final total relationships in file: {len(all_results)}")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
