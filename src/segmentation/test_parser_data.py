from pandas.io import html
from email import charset
import pandas as pd
from segmentation.parser import LegalDocumentParser
from segmentation.confidence import ConfidenceScorer
from segmentation.writer import SegmentWriter
from segmentation.embedder import ArticleEmbedder
from neo4j import GraphDatabase

def test_parser_with_real_data():
    # 1. Đọc dữ liệu từ file Parquet
    print("Đang đọc dữ liệu metadata và content...")
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    metadata_path = os.path.join(base_dir, "data", "metadata.parquet")
    content_path = os.path.join(base_dir, "data", "content.parquet")
    
    metadata_df = pd.read_parquet(metadata_path)
    content_df = pd.read_parquet(content_path)
    
    # Giả sử cột khóa chính là 'id' (hoặc 'doc_id')
    doc_id_col = 'id' if 'id' in metadata_df.columns else 'doc_id'
    content_id_col = 'id' if 'id' in content_df.columns else 'doc_id'
    
    metadata_df[doc_id_col] = metadata_df[doc_id_col].astype(str)
    content_df[content_id_col] = content_df[content_id_col].astype(str)
    
    # 2. Lọc mỗi loại văn bản 1 sample
    html_col = 'clean_html' if 'clean_html' in content_df.columns else 'content_html'
    
    # Kết hợp metadata và content để dễ filter
    merged_df = pd.merge(
        content_df[content_df[html_col].notna()],
        metadata_df,
        left_on=content_id_col,
        right_on=doc_id_col,
        how='inner'
    )
    
    target_types = ["Luật", "Bộ luật", "Nghị định", "Thông tư"]
    filtered_df = merged_df[merged_df['loai_van_ban'].isin(target_types)].copy()
    
    if 'ngay_ban_hanh' in filtered_df.columns:
        years = pd.to_datetime(filtered_df['ngay_ban_hanh'], errors='coerce').dt.year
        filtered_df = filtered_df[years > 2000]
    
    # Lấy 1 văn bản cho mỗi loại
    sample_contents = filtered_df.groupby('loai_van_ban').head(1)
    
    # 3. Khởi tạo Parser và Scorer
    parser = LegalDocumentParser()
    scorer = ConfidenceScorer()
    
    results_to_write = []
    doc_ids_to_mock = []
    
    for _, row in sample_contents.iterrows():
        doc_id = str(row[content_id_col])
        html_content = row[html_col]
        loai_van_ban = row.get('loai_van_ban', '')
        
        # Nếu file metadata có trường article_count (số điều dự kiến)
        expected_articles = row.get('article_count', None)
        
        print("-" * 60)
        print(f"Đang parse Văn bản ID: {doc_id} | Loại VB: {loai_van_ban}")
        
        # 4. Thực thi parse
        result = parser.parse(
            doc_id=doc_id,
            clean_html=html_content,
            loai_van_ban=loai_van_ban
        )
        
        # 5. Thực thi Score
        result = scorer.score(result, expected_article_count=expected_articles)
        
        # 6. In kết quả
        print(f"Kết quả Parse:")
        print(f"  - Độ tin cậy (Confidence): {result.confidence_score*100:.1f}% ({result.confidence_level.value})")
        print(f"  - Ghi chú: {result.confidence_notes}")
        print(f"  - Số Chương: {result.chapter_count}")
        print(f"  - Số Điều:   {result.article_count}")
        print(f"  - Số Khoản:  {result.clause_count}")
        print(f"  - Số Điểm:   {result.point_count}")
        print("Cấu trúc (10 segment đầu tiên):")
        for seg in result.segments[:10]:
            print(f"  [{seg.hierarchy_type.value}] {seg.path} (Mục: {seg.section})")
            print(f"      Text: {seg.clean_text[:80]}...")
            
        results_to_write.append(result)
        doc_ids_to_mock.append(doc_id)
        
    # 7. Test Writer và Embedder
    print("\n" + "=" * 60)
    print("Bắt đầu test SegmentWriter và ArticleEmbedder...")
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
    EMBED_URL = os.environ.get("EMBED_SERVICE_URL", "http://localhost:8001")
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # 7.1 Tạo Mock Document Node (Bắt buộc phải có để SegmentWriter liên kết)
        with driver.session() as session:
            for d_id in doc_ids_to_mock:
                session.run("MERGE (d:Document {id: $id}) SET d.title = 'Mock Document ' + $id", id=d_id)
                
        # 7.2 Test Writer
        print("Đang ghi cấu trúc vào Neo4j...")
        writer = SegmentWriter(driver)
        counts = writer.write_batch(results_to_write)
        print(f"  -> Kết quả ghi: {counts}")
        
        # 7.3 Test Embedder
        print("Đang tạo Embedding (1024-dim)...")
        embedder = ArticleEmbedder(driver, embed_service_url=EMBED_URL)
        embed_stats = embedder.embed_all(overwrite=True)
        print(f"  -> Kết quả Embedder: {embed_stats}")
        
        driver.close()
        print("Test Writer và Embedder thành công!")
    except Exception as e:
        print(f"Lỗi khi chạy Writer hoặc Embedder: {e}")
        print("Hãy đảm bảo bạn đang chạy Neo4j ở cổng 7687 và Embedding Service ở cổng 8001.")

if __name__ == "__main__":
    test_parser_with_real_data()
