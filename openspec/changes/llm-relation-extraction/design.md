## Context

Currently, the Legal Risk Scanner uses Regex to extract legal relationships (e.g. amend, replace, repeal) from the raw text of legal documents. However, Vietnamese legal text frequently employs complex grammatical structures, enumerations, and historical context references (e.g., "Thông tư X sửa đổi Điều Y của Luật Z (đã được sửa đổi bởi Luật W)") that cause Regex-based extraction to fail or produce false positives. We have already ingested document structures (Article -> Clause -> Point) into Neo4j. By pulling the context hierarchically from the graph (waterfall context), we can provide a complete context block to an LLM to reliably extract structural actions.

## Goals / Non-Goals

**Goals:**
- Provide a scalable architecture to batch Neo4j leaf nodes and send them to an LLM for structured relationship extraction.
- Formulate a robust LLM prompt and JSON schema that strictly forces the model to categorize relationships properly.
- Develop an isolated test module to verify extraction logic before massive ingestion.

**Non-Goals:**
- Completely replacing the existing `cross_reference/extractor.py` immediately. The LLM extraction should be an alternative strategy that can be switched on or tested in isolation first.
- Modifying the existing Neo4j parsing or segmenting logic. We rely on the existing graph.

## Decisions

**1. Source of Context: Neo4j Graph Query**
- *Rationale*: Instead of parsing text recursively, we leverage the existing `clean_text` properties in Neo4j. Since `clean_text` at the Article level only contains text before the first Clause, it effectively functions as the preamble. By concatenating `a.clean_text + c.clean_text + p.clean_text`, we organically build the waterfall context.

**2. LLM Batching Strategy**
- *Rationale*: Sending one node per API call is too slow and expensive. We will batch nodes. A batch will be constructed by accumulating text until a target character count or token limit (e.g., 1000-1500 words) is reached to ensure the context window remains small enough for strict instruction adherence.

**3. Output JSON Schema**
- *Rationale*: The LLM will be prompted to return a JSON array of objects. Keys will be the node `uid`, and values will be an array of relationships: `[{action_type, target: {document_name, dieu, khoan, diem}, quote_context}]`. This maps cleanly to our Neo4j ingestion code.

**4. Prompt Rules for Legal Precision**
- *Rule of Title*: Do not extract relationships from documents listed as part of another document's title.
- *Rule of Passive History*: Ignore passive statements ("đã được bãi bỏ", "theo quy định... đã sửa đổi").
- *Rule of Enumeration*: Split "Điều 1, 2 và 3" into three distinct target actions.
- *Rule of Context Override*: Do not split enumerations if they are part of a title.

## Risks / Trade-offs

- **[Risk] High API Cost and Latency:** LLM inference is slow. Processing 4000+ documents will take significant time.
  - *Mitigation*: Develop the system with robust error handling and batching. Consider a hybrid approach in the future where only nodes containing modifying keywords are sent to the LLM.
- **[Risk] Hallucinations on target resolution:** LLM might hallucinate a slightly incorrect `document_name`.
  - *Mitigation*: We will pass the LLM output's `document_name` through the existing Regex/Lookup Table canonicalization (e.g., fuzzy matching `so_ky_hieu_lookup.json`) to map it securely to an actual `doc_id`.
