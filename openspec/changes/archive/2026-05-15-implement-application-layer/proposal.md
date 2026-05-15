## Why

The application layer (Người C) is the bridge between the Neo4j knowledge graph and the frontend UI. Currently, only T4.1 (Contract Parser) and T5.1 (Intent Analysis) are complete. The remaining 14 tasks — clause extraction, legal provision matching, compliance analysis, retrieval pipeline, answer generation, citation verification, and the FastAPI backend — are all unimplemented. With the data scope reduced from 20K to 90 documents and a deadline approaching, this change implements the entire application layer in parallel with data ingestion, using mock bridges where dependencies are not yet ready, so that all components can be integrated immediately when data is available.

## What Changes

- **T4.2 Contract Clause Extractor**: LLM-based extraction of clauses from contract Markdown text, with embedding generation per clause
- **T4.3 Legal Provision Matching**: Vector search + graph traversal + reranking to match contract clauses against legal provisions in Neo4j, with fulltext fallback for demo
- **T4.4 Compliance Analysis**: LLM-powered compliance report generation with violations, risks, suggestions, and precise citations
- **T4.5 Citation Verification**: Automated verification of all citations against Neo4j graph nodes (VERIFIED/UNVERIFIED)
- **T4.6 Policy Review Extension**: Policy compliance checking with classification (compliant_and_efficient, compliant_but_restrictive, non_compliant)
- **T5.2 Retrieval Pipeline**: Multi-strategy retrieval engine (direct lookup, vector search, graph traversal, hybrid search, validity check, comparison) consuming SubQuery objects from T5.1
- **T5.3 Answer Generation**: LLM-based answer generation with retrieved provisions, effective text, and amendment history as context
- **T5.4 QA Citation Verification**: Same as T4.5, applied to QA answers
- **FastAPI Backend API**: 7 endpoints (QA chat with SSE, conversation CRUD, contract upload, job status, job history) connecting frontend to Python pipeline
- **Mock Bridge Layer**: Mock implementations for embeddings, graph traversal, and effective text to unblock development before data is ready
- **Bug Fixes**: Fix broken prompt template syntax (3 templates using `{var}` instead of `{{var}}`), fix frontend API switcher bypass, add mock LLM provider for offline development
- **Test Infrastructure**: conftest.py with shared fixtures, pytest.ini configuration, mock fixtures for Neo4j/LLM/embedding service

## Capabilities

### New Capabilities
- `retrieval-pipeline`: Multi-strategy retrieval engine consuming SubQuery objects from intent analysis, supporting direct lookup, vector search, graph traversal, hybrid search, validity check, and comparison strategies
- `answer-generation`: LLM-based answer generation with legal provisions, effective text, and amendment history as context, producing structured answers with citations
- `citation-verification`: Automated citation verification against Neo4j graph, marking citations as VERIFIED or UNVERIFIED with reasons
- `clause-extraction`: LLM-based extraction of contract clauses with type, parties, obligations, and embeddings
- `legal-matching`: Matching contract clauses to legal provisions via vector search + graph traversal + authority-weighted reranking
- `compliance-analysis`: LLM-powered compliance analysis producing violations, risks, suggestions, and precise legal citations
- `policy-review`: Policy document compliance checking with classification against legal requirements
- `backend-api`: FastAPI REST API with SSE streaming connecting frontend to Python pipeline (QA chat, conversations, contract upload, job status)
- `mock-bridge`: Mock implementations for embeddings, graph traversal, and effective text to enable parallel development
- `test-infrastructure`: Shared test fixtures, pytest configuration, and mock providers for offline development

### Modified Capabilities
- `contract-review-pipeline`: Add requirements for clause extraction (T4.2), legal matching (T4.3), compliance analysis (T4.4), citation verification (T4.5), and policy review (T4.6)
- `question-intent-analysis`: Add SubQuery consumption contract — T5.2 retrieves based on SubQuery.retrieval_strategy and SubQuery.requires

## Impact

- **New files**: ~15 Python modules (retriever, strategies, clause_extractor, matcher, compliance_analyzer, answer_generator, citation_verifier, policy_review, mock_bridge, mock_provider, API routes)
- **Modified files**: `src/llm/prompts.py` (fix template syntax), `frontend/src/app/(app)/legal-qa/page.tsx` (fix API switcher), `frontend/src/app/(app)/contract-review/page.tsx` (add API integration), `frontend/src/lib/api-contract.ts` (use apiRequest)
- **New infrastructure**: `infra/api/` directory with FastAPI app, routes, SSE utilities, middleware
- **Dependencies**: OpenAI API (LLM), Neo4j (graph queries), embedding service (vector search — mockable)
- **Frontend**: Existing UI components (chat bubbles, provision cards, intent badges) remain unchanged; only API integration layer is updated
- **Data**: Works with both old data (20K docs) and new data (90 docs); mock bridges enable development before data is ready
