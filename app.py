import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Cấu hình trang
st.set_page_config(page_title="Vietnamese Legal KG - Admin Portal", layout="wide")
load_dotenv()

# --- Sidebar: Cấu hình kết nối ---
st.sidebar.title("⚙️ Infrastructure Status")

# Neo4j Status
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "")

try:
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    with driver.session() as session:
        session.run("RETURN 1")
    st.sidebar.success("✅ Neo4j: Connected")
except Exception as e:
    st.sidebar.error(f"❌ Neo4j: Disconnected\n{e}")

# Data Files Status
st.sidebar.markdown("---")
st.sidebar.subheader("📂 Data Files")
files = {
    "Metadata": "data/metadata_deduped.parquet",
    "Content Clean": "data/content_clean.parquet",
    "Lookup": "output/so_ky_hieu_lookup.json"
}
for name, path in files.items():
    if Path(path).exists():
        st.sidebar.write(f"✅ {name}")
    else:
        st.sidebar.write(f"❌ {name}")

# --- Main UI ---
st.title("⚖️ Vietnamese Legal Knowledge Graph")
st.markdown("### Hệ thống thực nghiệm Data & Infrastructure (Người A)")

tabs = st.tabs(["🔍 Tra cứu văn bản", "🕸️ Đồ thị quan hệ", "📊 Thống kê dữ liệu"])

# --- Tab 1: Tra cứu ---
with tabs[0]:
    st.subheader("Tra cứu nội dung văn bản")
    search_query = st.text_input("Nhập số hiệu văn bản (ví dụ: 46/2014/NĐ-CP)", "")
    
    if search_query:
        # Load metadata để tìm ID
        try:
            with st.spinner("Đang tìm kiếm..."):
                df_meta = pd.read_parquet("data/metadata_deduped.parquet")
                doc = df_meta[df_meta['so_ky_hieu'].str.contains(search_query, case=False, na=False)]
                
                if not doc.empty:
                    doc_id = doc.iloc[0]['id']
                    st.success(f"Tìm thấy văn bản ID: {doc_id}")
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.write("**Thông tin chi tiết:**")
                        st.json(doc.iloc[0].to_dict())
                    
                    with col2:
                        st.write("**Nội dung (Clean HTML):**")
                        if Path("data/content_clean.parquet").exists():
                            import pyarrow.parquet as pq
                            target_id = str(doc_id)
                            found_html = None
                            pf = pq.ParquetFile("data/content_clean.parquet")
                            for batch in pf.iter_batches(batch_size=5000, columns=["id", "clean_html"]):
                                df_b = batch.to_pandas()
                                df_b["id"] = df_b["id"].astype(str)
                                match = df_b[df_b["id"] == target_id]
                                if not match.empty:
                                    found_html = match.iloc[0]["clean_html"]
                                    break
                            if found_html:
                                # Bọc vào khung trắng Paper Style để dễ đọc nhất
                                styled_html = f"""
                                <div style="background-color: white; color: black; padding: 30px; font-family: 'Times New Roman', Times, serif; line-height: 1.6; border-radius: 5px;">
                                    {found_html}
                                </div>
                                """
                                st.components.v1.html(styled_html, height=600, scrolling=True)
                            else:
                                st.warning(f"Chưa có nội dung sạch cho văn bản ID={doc_id}.")
                        else:
                            st.info("File content_clean.parquet chưa tồn tại. Hãy chạy T0.4.")
                else:
                    st.error("Không tìm thấy văn bản này trong database.")
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- Tab 2: Đồ thị ---
with tabs[1]:
    st.subheader("Quan hệ văn bản trong Neo4j")
    if search_query:
        try:
            with driver.session() as session:
                query = """
                MATCH (d:Document {id: $doc_id})-[r]->(other)
                RETURN type(r) as rel_type, other.so_ky_hieu as other_skh, other.title as other_title
                LIMIT 20
                """
                # Lưu ý: doc_id ở đây cần map từ so_ky_hieu
                # Tạm thời query theo so_ky_hieu nếu neo4j đã ingest
                res = session.run("MATCH (d:Document) WHERE d.so_ky_hieu CONTAINS $skh RETURN d.id as id LIMIT 1", skh=search_query)
                record = res.single()
                if record:
                    real_id = record['id']
                    rels = session.run(query, doc_id=real_id)
                    data = [dict(r) for r in rels]
                    if data:
                        st.table(pd.DataFrame(data))
                    else:
                        st.info("Văn bản này chưa có quan hệ nào được ghi nhận.")
                else:
                    st.info("Chưa tìm thấy node Document trong Neo4j. Hãy chạy T1.7 Ingest.")
        except Exception as e:
            st.error(f"Lỗi truy vấn Neo4j: {e}")

# --- Tab 3: Thống kê ---
with tabs[2]:
    st.subheader("Tổng quan dữ liệu")
    if Path("data/metadata_deduped.parquet").exists():
        df_meta = pd.read_parquet("data/metadata_deduped.parquet")
        st.metric("Tổng số văn bản (duy nhất)", len(df_meta))
        
        st.write("**Phân bổ theo loại văn bản:**")
        type_counts = df_meta['loai_van_ban'].value_counts()
        st.bar_chart(type_counts)
    else:
        st.info("Hãy hoàn thành T0.2 Deduplicate để xem thống kê.")

driver.close()
