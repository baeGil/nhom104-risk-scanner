import pandas as pd
import json

df = pd.read_parquet("data/metadata_deduped.parquet")
mapping = {}
for _, row in df.iterrows():
    title = str(row.get('title', '')).strip()
    skh = str(row.get('so_ky_hieu', '')).strip()
    doc_type = str(row.get('loai_van_ban', '')).strip()
    
    if title and skh and doc_type:
        # Prepend doc_type if not present in title
        if not title.lower().startswith(doc_type.lower()):
            short_title = f"{doc_type} {title}"
        else:
            short_title = title
            
        # Optional: remove "năm YYYY" from the end if it exists?
        # Let's keep it exact first, then add a variant without year.
        import re
        short_title_no_year = re.sub(r'\s+năm\s+\d{4}$', '', short_title, flags=re.IGNORECASE)
        
        mapping[short_title] = skh
        if short_title_no_year != short_title:
            mapping[short_title_no_year] = skh

with open("data/short_title_mapping.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Generated {len(mapping)} short titles.")
