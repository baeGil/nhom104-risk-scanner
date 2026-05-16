uvicorn infra.api.app:app --port 8000 --log-level info
python -m uvicorn infra.embedding_service.app:app --host 0.0.0.0 --port 8080
