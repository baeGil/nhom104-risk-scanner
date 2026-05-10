import pandas as pd
import pyarrow.parquet as pq
import json
import re
import os
from bs4 import BeautifulSoup
from tqdm import tqdm

def main():
    print("--- 1. Filtering Metadata ---")
    meta_df = pd.read_parquet('data/metadata_deduped.parquet')
    
    # Lấy năm từ ngay_ban_hanh
    meta_df['year'] = meta_df['ngay_ban_hanh'].str[-4:]
    meta_df['year'] = pd.to_numeric(meta_df['year'], errors='coerce')
    
    # Filter điều kiện của Cường
    target_types = ['Nghị định', 'Thông tư', 'Luật', 'Bộ luật']
    filtered_df = meta_df[
        (meta_df['year'] >= 2000) & 
        (meta_df['loai_van_ban'].isin(target_types))
    ]
    
    valid_ids = set(filtered_df['id'].astype(str))
    print(f"Filtered {len(valid_ids)} documents (>=2000 & types: {target_types})")

    print("\n--- 2. Loading Lookup Table ---")
    with open('output/final_lookup_ui.json', 'r') as f:
        lookup = json.load(f)

    print("\n--- 3. Extracting Relationships ---")
    # Pattern tìm số hiệu văn bản (vd: 46/2014/NĐ-CP, 10/2012/QH13) và 30 ký tự trước đó
    pattern = re.compile(r'(?P<context>.{0,35})(?P<skh>\d+/\d+/[A-ZĐ]+-[A-ZĐ]+|\d+/\d+/[A-Z0-9]+|\d+/[A-ZĐ]+)')
    
    relationships = []
    pf = pq.ParquetFile('data/content_clean.parquet')
    
    for batch in pf.iter_batches(batch_size=2000, columns=['id', 'clean_html']):
        df_b = batch.to_pandas()
        for _, row in df_b.iterrows():
            source_id = str(row['id'])
            if source_id not in valid_ids:
                continue
                
            html = str(row['clean_html'])
            if not html or html == 'None': continue
            
            # Xoá thẻ HTML lấy text thô
            text = BeautifulSoup(html, "lxml").get_text(separator=" ", strip=True)
            
            seen_targets = set()
            for match in pattern.finditer(text):
                ctx = match.group('context').lower()
                skh = match.group('skh').lower()
                
                # Bỏ qua nếu tham chiếu chính nó
                target_id = lookup.get(skh)
                if not target_id or target_id == source_id or target_id in seen_targets:
                    continue
                    
                seen_targets.add(target_id)
                
                # Phân loại quan hệ dựa vào Context (35 ký tự trước số hiệu)
                rel_type = 'LIEN_QUAN'
                if any(k in ctx for k in ['căn cứ', 'theo', 'chiếu']):
                    rel_type = 'CAN_CU'
                elif any(k in ctx for k in ['sửa đổi', 'bổ sung']):
                    rel_type = 'SUA_DOI'
                elif any(k in ctx for k in ['hướng dẫn', 'thi hành', 'quy định chi tiết']):
                    rel_type = 'HUONG_DAN'
                elif any(k in ctx for k in ['thay thế', 'hủy bỏ', 'bãi bỏ']):
                    rel_type = 'THAY_THE'
                    
                relationships.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'rel_type': rel_type,
                    'context': ctx.strip() + " " + skh
                })

    rel_df = pd.DataFrame(relationships)
    print(f"\nExtracted {len(rel_df)} relationships!")
    
    # Lưu ra file cho T1.7
    os.makedirs('data', exist_ok=True)
    rel_df.to_parquet('data/relationships.parquet', index=False)
    print("✅ Saved to data/relationships.parquet")
    print("🎯 Bạn đã gánh xong phần của Người B! Bây giờ chỉ cần chạy lại Pipeline (T1.7) để nạp vào Neo4j.")

if __name__ == "__main__":
    main()
