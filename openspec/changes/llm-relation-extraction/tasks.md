## 1. Context Extraction Infrastructure

- [x] 1.1 Create `src/cross_reference/llm_extractor.py` and set up the `LLMExtractor` class with Neo4j driver initialization.
- [x] 1.2 Implement the Cypher query method `get_waterfall_context` to retrieve leaf nodes and their hierarchical text concatenation.

## 2. LLM Integration and Batching

- [x] 2.1 Implement the batching logic to group leaf nodes by a maximum word/character count (e.g. 1500 words).
- [x] 2.2 Construct the LLM System Prompt enforcing the JSON schema and the 4 Legal Precision Rules (Title, Passive History, Enumeration, Context Override).
- [x] 2.3 Implement the OpenAI API call to process a batch and parse the structured JSON output.

## 3. Testing Suite

- [x] 3.1 Create `scratch/test_llm_pipeline.py` to execute the pipeline on a single document (e.g., `doc_153913`) and print the parsed relationships.
- [x] 3.2 Create `scratch/test_llm_node.py` to allow manual injection of hardcoded text (like Article 87) directly into the prompt for isolated debugging and fine-tuning.
