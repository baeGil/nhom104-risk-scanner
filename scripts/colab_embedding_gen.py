# --- COPY NỘI DUNG NÀY VÀO GOOGLE COLAB ---
# !pip install pandas pyarrow sentence-transformers

import pandas as pd
from sentence_transformers import SentenceTransformer
import torch
import os

# 1. Cấu hình
INPUT_FILE = 'legal_segments_for_colab.parquet'  # Tên file bạn vừa upload lên Colab
OUTPUT_FILE = 'legal_embeddings_results.parquet'
MODEL_NAME = 'mainguyen9/vietlegal-harrier-0.6b' # Model bạn đã chọn

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Không tìm thấy file {INPUT_FILE}. Hãy upload file lên Colab trước.")
        return

    # 2. Đọc dữ liệu
    print("Đang đọc dữ liệu từ Parquet...")
    df = pd.read_parquet(INPUT_FILE)
    print(f"Tổng số đoạn văn bản: {len(df)}")

    # 3. Load Model lên GPU
    print(f"Đang tải model {MODEL_NAME}...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = SentenceTransformer(MODEL_NAME, device=device)
    print(f"Đang sử dụng thiết bị: {device.upper()}")

    # 4. Tạo Embedding
    print("Bắt đầu tạo embedding (quá trình này có thể mất vài phút)...")
    # Chúng ta chỉ lấy cột 'text' để embed
    sentences = df['text'].tolist()
    embeddings = model.encode(sentences, show_progress_bar=True, batch_size=64)

    # 5. Đóng gói kết quả
    # Chỉ giữ lại UID và Embedding để giảm dung lượng file
    output_df = pd.DataFrame({
        'uid': df['uid'],
        'embedding': embeddings.tolist()
    })

    # 6. Lưu kết quả
    print(f"Đang lưu kết quả ra {OUTPUT_FILE}...")
    output_df.to_parquet(OUTPUT_FILE, index=False)
    print("=== HOÀN THÀNH! Hãy tải file legal_embeddings_results.parquet về máy cục bộ. ===")

if __name__ == "__main__":
    main()
