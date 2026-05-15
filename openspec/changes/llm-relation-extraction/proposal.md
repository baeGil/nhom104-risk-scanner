## Why

The current regex-based extraction pipeline is highly error-prone when dealing with complex, passive, or nested legal references (e.g. distinguishing an active modification from a historical mention). It lacks the semantic understanding required for legal text. By switching to an LLM-based extraction using Graph-based context merging (waterfall context), we can achieve near 100% precision in relationship mapping, properly capturing "sua_doi", "bai_bo", "bo_sung" along with handling enumerations and implicit context.

## What Changes

- Implement a Neo4j Cypher query module to extract "waterfall context" directly from the database, utilizing the inherently structured `clean_text` properties of Article, Clause, and Point nodes.
- Build a Python module to batch these nodes based on word count/token length.
- Implement an LLM prompting layer designed for OpenAI API (GPT-4o-mini / GPT-5 Nano) that strictly enforces a JSON output schema covering legal relationship types.
- Develop a test suite to validate the Cypher context queries, the batching logic, and the final LLM JSON response locally before running a massive pipeline execution.

## Capabilities

### New Capabilities
- `llm-extraction-pipeline`: Logic to pull waterfall context via Cypher, batch it by size, and send it to an LLM for structured relationship extraction.
- `llm-test-suite`: Utilities to independently test the LLM extraction process on a single document or set of specific nodes to debug prompts and parsing.

### Modified Capabilities
- `cross-reference-extractor`: Update or replace the existing regex extraction module with the new LLM-based module for relationship generation.

## Impact

- **Database**: The extraction logic now heavily relies on the Neo4j Graph as the source of truth for context, rather than raw text files.
- **Cost/Performance**: Processing will be slower and incur API costs compared to Regex, but will yield exceptionally higher data quality.
- **Dependencies**: Requires OpenAI SDK or an HTTP client to communicate with the LLM.
