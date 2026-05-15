import json
import pandas as pd
import re

def normalize_so_hieu(so_hieu):
    so_hieu = str(so_hieu).strip().upper()
    # Tìm kiếm cấu trúc chuẩn <số>/<năm>/<mã chữ> (VD: 51/2024/QH15)
    # Bỏ qua các chữ như "Luật số", hoặc dấu ngoặc thừa ở cuối
    match = re.search(r'(\d+/\d+/[A-ZĐ0-9\-]+)', so_hieu)
    if match:
        core_skh = match.group(1)
    else:
        # Fallback về lấy từ đầu tiên nếu không tìm thấy cấu trúc chuẩn
        match_fallback = re.search(r'^([^\s\(\)]+)', so_hieu)
        if match_fallback:
            core_skh = match_fallback.group(1)
        else:
            core_skh = so_hieu
            
    # Bỏ các số 0 ở đầu các thành phần để đồng nhất (VD: 08/2022/QH15 -> 8/2022/QH15)
    parts = core_skh.split('/')
    stripped_parts = [re.sub(r'^0+', '', p) if re.match(r'^0+\d+', p) else p for p in parts]
    return '/'.join(stripped_parts)

def main():
    print("Đang đọc file parquet metadata...")
    df = pd.read_parquet("data/metadata.parquet")
    df['id'] = df['id'].astype(str)
    
    # Tạo từ điển tra cứu: Chuẩn hóa cả số ký hiệu trong Parquet
    lookup_exact = {}
    for _, row in df.iterrows():
        skh_raw = str(row.get('so_ky_hieu', ''))
        doc_id = str(row.get('id', ''))
        if skh_raw and skh_raw.lower() != 'nan':
            skh_clean = normalize_so_hieu(skh_raw)
            lookup_exact[skh_clean] = doc_id
            
    print("Đang đọc file JSON...")
    with open("luat_lao_dong_schema.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    matched_count = 0
    total_count = 0
    
    for category in data:
        for doc in category.get("van_ban", []):
            total_count += 1
            so_hieu_raw = doc.get("so_hieu", "")
            
            if "Cần xác nhận" in so_hieu_raw:
                print(f"Bỏ qua (chưa có số hiệu): {doc.get('ten')}")
                continue
                
            skh_clean = normalize_so_hieu(so_hieu_raw)
            
            # Match 1-1 vì cả 2 bên đều đã được chuẩn hóa về một format duy nhất
            doc_id = lookup_exact.get(skh_clean)
            
            if doc_id:
                doc["doc_id"] = doc_id
                matched_count += 1
            else:
                print(f"CẢNH BÁO: Không tìm thấy ID cho văn bản '{doc.get('ten')}' - Số hiệu: {so_hieu_raw} (Clean: {skh_clean})")
                    
    print(f"Tổng kết: Match thành công {matched_count}/{total_count} văn bản.")
    
    output_file = "data_updated_with_ids.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Đã lưu kết quả ra file: {output_file}")

if __name__ == "__main__":
    main()
