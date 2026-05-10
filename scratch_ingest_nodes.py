import pandas as pd
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'thinhtran')

print('--- Ingesting 21k Document Nodes to Neo4j ---')
df = pd.read_parquet('data/metadata_deduped.parquet')
driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    for i in range(0, len(df), 5000):
        batch = df.iloc[i:i+5000].to_dict('records')
        session.run('''
            UNWIND $batch AS row
            MERGE (d:Document {id: toString(row.id)})
            SET d.so_ky_hieu = row.so_ky_hieu,
                d.title = row.title,
                d.ngay_ban_anh = row.ngay_ban_hanh,
                d.loai_van_ban = row.loai_van_ban
        ''', batch=batch)
        print(f'Done {i+len(batch)} nodes...')

driver.close()
print('✅ Hoàn tất nạp Node! Hãy kiểm tra lại Tab Đồ thị trên Streamlit.')
