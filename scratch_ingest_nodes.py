import pandas as pd
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'password')

print('--- Ingesting Document Nodes to Neo4j ---')
df = pd.read_parquet('data/metadata_deduped.parquet')
print(f'Total documents: {len(df)}')

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    for i in range(0, len(df), 5000):
        batch = df.iloc[i:i+5000].to_dict('records')
        session.run('''
            UNWIND $batch AS row
            MERGE (d:Document {id: toString(row.id)})
            SET d.so_ky_hieu = row.so_ky_hieu,
                d.title = row.title,
                d.ngay_ban_hanh = row.ngay_ban_hanh,
                d.loai_van_ban = row.loai_van_ban,
                d.tinh_trang_hieu_luc = row.tinh_trang_hieu_luc,
                d.co_quan_ban_hanh = row.co_quan_ban_hanh,
                d.nganh = row.nganh,
                d.linh_vuc = row.linh_vuc
        ''', batch=batch)
        print(f'Done {min(i+5000, len(df))} / {len(df)} nodes...')

driver.close()
print('✅ Hoàn tất nạp Document nodes!')
