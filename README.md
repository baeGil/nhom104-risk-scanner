uvicorn infra.api.app:app --port 8000 --log-level info
python -m uvicorn infra.embedding_service.app:app --host 0.0.0.0 --port 8080
python -m src.data_pipeline.legal_segment_index apply
python -m src.data_pipeline.full_ingets_neo4j
python scratch/import_embedding_to_neo4j.py