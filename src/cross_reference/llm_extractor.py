import asyncio
import json
import os
import pandas as pd
import httpx
from tqdm.asyncio import tqdm
from src.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

# Prompt template for batch processing
SYSTEM_PROMPT = """Bạn là chuyên gia phân tích văn bản pháp luật Việt Nam. Nhiệm vụ của bạn là trích xuất các mối quan hệ pháp luật từ DANH SÁCH các đoạn văn bản được cung cấp bên dưới.

Có 3 loại quan hệ cần trích xuất:
1. internal: Dẫn chiếu nội bộ trong cùng một văn bản (ví dụ: "Điều 10 Luật này", "Khoản 1 Điều này", "Nghị định này"). 
   - target_doc: Ghi là "luật này", "nghị định này", hoặc "thông tư này".
2. external: Dẫn chiếu đến văn bản khác (ví dụ: "Điều 10 Luật Xử lý vi phạm hành chính", "Nghị định số 46/2016/NĐ-CP").
   - target_doc: Ghi tên hoặc số hiệu văn bản cụ thể.
3. modify: Các quan hệ sửa đổi, bổ sung, thay thế hoặc bãi bỏ văn bản khác. 
   - Chỉ lấy quan hệ CHỦ ĐỘNG (ví dụ: "Điều 1 bổ sung Điều 2" -> lấy; "Điều 1 được bổ sung bởi Điều 2" -> KHÔNG lấy).
   - relationship_type: Ghi là "modify".

QUY TẮC TÁCH: 
Nếu một câu dẫn chiếu đến nhiều đối tượng (ví dụ: "Khoản 1, Khoản 2 Điều 10"), bạn PHẢI tách thành các block riêng biệt.

QUY TẮC BATCH:
Tôi sẽ cung cấp danh sách các đoạn văn bản, mỗi đoạn có một ID (source_uid).
Bạn phải trả về một MẢNG JSON duy nhất chứa tất cả các quan hệ tìm thấy trong tất cả các đoạn.
Mỗi object trong mảng phải có cấu trúc:
{
  "source_uid": "ID của đoạn văn bản chứa quan hệ này",
  "target_doc": "tên/số hiệu văn bản hoặc 'luật này'...",
  "target_article": "số điều",
  "target_clause": "số khoản",
  "target_diem": "tên điểm",
  "relationship_type": "internal" | "external" | "modify"
}

Chỉ trả về JSON array, không giải thích gì thêm."""

async def process_batch(http_client, batch_segments):
    """Xử lý một batch các đoạn văn bản."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Ghép các đoạn văn bản lại thành 1 prompt
    formatted_texts = []
    for i, seg in enumerate(batch_segments):
        formatted_texts.append(f"[{i+1}] ID: {seg['uid']}\nNội dung: {seg['text']}")
    
    combined_text = "\n\n".join(formatted_texts)
    
    data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "Bạn là chuyên gia pháp luật. Trả về duy nhất 1 JSON array chứa các quan hệ trích xuất được. Mỗi quan hệ phải có source_uid chính xác."},
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\nDANH SÁCH VĂN BẢN:\n{combined_text}"}
        ],
        "temperature": 0.0
    }
    
    url = f"{OPENAI_BASE_URL}/chat/completions" if OPENAI_BASE_URL else "https://api.openai.com/v1/chat/completions"

    for attempt in range(3):
        try:
            response = await http_client.post(url, headers=headers, json=data, timeout=60.0)
            response.raise_for_status()
            
            resp_json = response.json()
            content = resp_json['choices'][0]['message']['content'].strip()
            usage = resp_json.get('usage', {})
            
            # Log tokens
            in_tokens = usage.get('prompt_tokens', 0)
            out_tokens = usage.get('completion_tokens', 0)
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
    input_path = 'scratch/legal_segments_for_colab.parquet'
    if not os.path.exists(input_path):
        input_path = '../../scratch/legal_segments_for_colab.parquet'
    
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} not found.")
        return

    df = pd.read_parquet(input_path)
    all_segments = df.to_dict('records')
    
    # --- Checkpoint / Resume Logic ---
    output_dir = 'scratch' if os.path.exists('scratch') else '../../data'
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
    
    # Lọc những segments chưa được xử lý
    segments_to_process = [s for s in all_segments if s['uid'] not in processed_uids]
    
    # GIỚI HẠN XỬ LÝ CHO MỖI LẦN CHẠY (Ví dụ chia làm 3 lần cho 7000 segment)
    CHUNK_SIZE = 2350
    
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
    
    async with httpx.AsyncClient() as http_client:
        MAX_CONCURRENT = 3
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def batch_task(batch):
            async with sem:
                res, in_t, out_t = await process_batch(http_client, batch)
                return res, in_t, out_t

        tasks = [batch_task(b) for b in batches]
        
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            batch_res, in_t, out_t = await f
            new_results.extend(batch_res)
            total_in_tokens += in_t
            total_out_tokens += out_t

    # Gộp kết quả mới vào kết quả cũ
    all_results.extend(new_results)
    
    # Lưu lại
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Chunk complete!")
    print(f"New relationships found: {len(new_results)}")
    print(f"Total input tokens: {total_in_tokens}")
    print(f"Total output tokens: {total_out_tokens}")
    print(f"Final total relationships in file: {len(all_results)}")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
