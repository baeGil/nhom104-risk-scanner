import pandas as pd
df = pd.read_parquet("data/content_clean.parquet")
df['id'] = df['id'].astype(str)
content = df[df['id'] == '151086']['clean_html'].iloc[0]
with open("scratch/doc_151086.html", "w") as f:
    f.write(content)
print("Saved to scratch/doc_151086.html")
