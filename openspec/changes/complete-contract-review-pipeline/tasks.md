## 1. Graph Retrieval Surface

- [x] 1.1 Add a Neo4j migration/script to label embedded Article, Clause, and Point nodes as `LegalSegment`.
- [x] 1.2 Create or document the `legal_segment_embeddings` vector index over `LegalSegment.embedding`.
- [x] 1.3 Create or document full-text indexes for legal segment text and document/title search.
- [x] 1.4 Add an index validation utility that reports missing labels, missing vector/full-text indexes, embedding counts by label, and sample dimensions.
- [x] 1.5 Update reference ingestion or migration so `REFERENCES` relationships preserve `ref_type` or `raw_type` for internal and external references.

## 2. Query Rewrite

- [x] 2.1 Define a structured `LegalRetrievalPlan` model containing original text, legal_issue, search_queries, keywords, expected_domains, title_hints, risk_type, and filters.
- [x] 2.2 Add an LLM prompt and parser for rewriting contract clauses into `LegalRetrievalPlan`.
- [x] 2.3 Add fallback rewrite behavior that uses raw clause text and extracted keywords when LLM rewrite fails.
- [x] 2.4 Add unit tests for rewrite output on penalty, termination, wage, confidentiality, and dispute-resolution clauses.

## 3. Hybrid Legal Retrieval

- [x] 3.1 Replace Article-only matcher logic with a `LegalHybridRetriever` that searches Article, Clause, and Point nodes.
- [x] 3.2 Implement vector candidate retrieval from `legal_segment_embeddings`.
- [x] 3.3 Implement lexical/full-text candidate retrieval over legal segment text and title/document metadata.
- [x] 3.4 Implement exact keyword, title hint, and citation-like boosts from the retrieval plan.
- [x] 3.5 Merge candidate sets by uid while preserving vector, lexical, exact, graph, authority, and validity score factors.
- [x] 3.6 Add graph expansion over `REFERENCES` and `MODIFIES` relationships for high-confidence candidates.
- [x] 3.7 Implement reranking and return top-5 legal matches per contract clause with transparent score factors.

## 4. Context Assembly and Citation Verification

- [x] 4.1 Build a context assembler that returns Document title plus Article, Clause, and Point context for any matched uid.
- [x] 4.2 Reuse or extend `src/embeddings/retriever.py` hierarchy logic so matched leaf nodes include parent context.
- [x] 4.3 Define citation objects with display text, uid, document title, article, clause, point, and verification fields.
- [x] 4.4 Update citation verification to verify by graph uid first and display text consistency second.
- [x] 4.5 Add tests for verified uid citations, missing uid citations, and display-text mismatch citations.

## 5. Contract Parsing and OCR

- [x] 5.1 Add GPT-4o-mini OCR support for scanned PDFs or image-based contract pages.
- [x] 5.2 Keep direct text extraction for TXT, MD, and text-layer PDFs before OCR fallback.
- [x] 5.3 Normalize OCR/parser output into Markdown or plain text suitable for clause extraction.
- [x] 5.4 Add parser tests for TXT/MD, text-layer PDF behavior, and OCR fallback using mocked LLM responses.

## 6. Real Contract Review Pipeline

- [x] 6.1 Create an orchestration service for parse → clause extraction → query rewrite → hybrid retrieval → compliance analysis → citation verification.
- [x] 6.2 Update compliance analysis prompts to consume matched segment context, REFERENCES context, MODIFIES validity signals, and structured citation requirements.
- [x] 6.3 Ensure policy review can reuse the same retrieval, analysis, and citation verification pipeline.
- [x] 6.4 Add robust stage-level error handling so failed jobs record the failing stage and error message.

## 7. Persistence and API Integration

- [x] 7.1 Choose and document the first durable storage backend for contract jobs and review outputs.
- [x] 7.2 Add persistence models/tables or repositories for jobs, clauses, matches, compliance results, and citation verification records.
- [x] 7.3 Replace in-memory/mock-only contract job processing in `infra/api/contract_routes.py` with the real pipeline.
- [x] 7.4 Extend API response models to include statuses `extracting`, `retrieving`, `verifying`, matches, citations, and errors.
- [x] 7.5 Keep a development fixture path only behind an explicit non-production configuration flag.

## 8. Frontend Integration

- [x] 8.1 Update frontend contract API types to match real job status, clauses, matches, compliance, and citation response shapes.
- [x] 8.2 Render legal matches for each clause with document title and Article/Clause/Point path.
- [x] 8.3 Render citation verification badges using backend verification status and reason.
- [x] 8.4 Update job history and result loading to use persisted backend results instead of mock-only data shapes.
- [x] 8.5 Add frontend fixtures or tests for completed, failed, and in-progress real job responses.

## 9. Production Tests and Evaluation

- [x] 9.1 Create golden contract fixtures with expected clauses, risk categories, and expected legal segment uids or document titles.
- [x] 9.2 Add retrieval evaluation tests that report hit@5 or precision@5 for hybrid retrieval.
- [x] 9.3 Add contract API smoke tests for upload, polling, completion, and history.
- [x] 9.4 Add integration test markers for live Neo4j, live LLM, OCR, and slow end-to-end tests.
- [x] 9.5 Run and document the final verification commands for backend tests, frontend checks, OpenSpec validation, and a manual end-to-end demo.
