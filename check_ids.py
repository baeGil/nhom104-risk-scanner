import pandas as pd
meta_df = pd.read_parquet("data/metadata_deduped.parquet")
content_df = pd.read_parquet("data/content_clean.parquet")
print("Kiểu id trong meta:", meta_df['id'].dtype)
print("Kiểu id trong content:", content_df['id'].dtype)
print("Mẫu content ids:", content_df['id'].head(5).tolist())

# Lấy ID nằm trong cả 2 bảng, loại Luật
core_types = ['Luật', 'Nghị định']
valid_ids = set(meta_df[meta_df['loai_van_ban'].isin(core_types)]['id'].astype(str))
content_ids = set(content_df['id'].astype(str))
common = valid_ids & content_ids
print("Một vài ID hợp lệ:", list(common)[:5])
