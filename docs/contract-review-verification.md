# Contract Review Verification

Fast local checks:

```bash
.venv/bin/python -m compileall src/contract src/llm/citation_verifier.py infra/api
.venv/bin/python -m pytest src/contract/tests/test_query_rewriter.py src/contract/tests/test_citation_verifier.py src/contract/tests/test_parser_ocr.py src/contract/tests/test_contract_review_eval.py -q
cd frontend && ./node_modules/.bin/tsc --noEmit
openspec validate complete-contract-review-pipeline
```

Live Neo4j retrieval checks:

```bash
.venv/bin/python -m src.data_pipeline.legal_segment_index validate
RUN_LIVE_NEO4J=1 .venv/bin/python -m pytest src/contract/tests/test_contract_review_eval.py -q -m live_neo4j
```

API smoke test with mock processing:

```bash
RUN_CONTRACT_API_SMOKE=1 CONTRACT_REVIEW_USE_MOCK=true .venv/bin/python -m pytest src/contract/tests/test_contract_api_smoke.py -q
```

Manual end-to-end demo:

1. Ensure Neo4j is running and `legal_segment_embeddings`, `legal_segment_fulltext`, and `document_title_fulltext` are ONLINE.
2. Ensure `OPENAI_API_KEY` and LLM/OCR model env vars are configured for real processing.
3. Start backend API.
4. Start frontend.
5. Upload a TXT or PDF contract from the contract review page.
6. Confirm the completed job shows clauses, legal matches, compliance output, and citation verification badges.
