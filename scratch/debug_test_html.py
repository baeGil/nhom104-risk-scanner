import pandas as pd
from src.segmentation.parser import LegalDocumentParser
from bs4 import BeautifulSoup
import os

def debug_parse_parquet():
    content_path = "data/content_clean.parquet"
    if not os.path.exists(content_path):
        print(f"File {content_path} not found")
        return

    df = pd.read_parquet(content_path)
    row = df[df['id'] == '179095']
    if row.empty:
        print("ID 179095 not found in parquet")
        return
        
    html_content = row['clean_html'].values[0]
    print(f"Content length: {len(html_content)}")

    parser = LegalDocumentParser()
    
    # Let's inspect what BeautifulSoup sees first
    soup = BeautifulSoup(html_content, 'html.parser')
    block_tags_list = ['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    elements = soup.find_all(block_tags_list)
    
    leaf_elements = []
    for el in elements:
        has_block_child = el.find(block_tags_list) is not None
        if not has_block_child:
            leaf_elements.append(el)
            
    print(f"Total leaf elements found: {len(leaf_elements)}")
    for i, el in enumerate(leaf_elements[:30]):
        text = el.get_text(separator=' ', strip=True)
        print(f"  {i}: [{el.name}] -> {text[:100]}")

    result = parser.parse(doc_id="179095", clean_html=html_content, loai_van_ban="Luật")
    print(f"\nParse result: {len(result.segments)} segments")
    print(f"  Articles: {result.article_count}")
    print(f"  Clauses: {result.clause_count}")
    print(f"  Points: {result.point_count}")

if __name__ == "__main__":
    debug_parse_parquet()
