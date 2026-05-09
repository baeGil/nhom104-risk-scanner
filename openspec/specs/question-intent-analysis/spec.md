## ADDED Requirements

### Requirement: Classify query domain
The system SHALL classify user input into one of five domains: QA (legal question), CONTRACT_REVIEW (review uploaded contract), CONTRACT_QA (question about previously reviewed contract), EXPLAIN (request for explanation/clarification), or CHITCHAT (unrelated). Domain classification SHALL consider conversation context and presence of uploaded files.

#### Scenario: Classify QA query
- **WHEN** user asks "Điều 17 Luật Doanh nghiệp quy định gì?"
- **THEN** domain is classified as "QA"

#### Scenario: Classify contract review query
- **WHEN** user says "Review hợp đồng này" with uploaded PDF
- **THEN** domain is classified as "CONTRACT_REVIEW"

#### Scenario: Classify contract QA query
- **WHEN** user asks "Tại sao điều khoản phạt trong hợp đồng vừa review không hợp pháp?"
- **THEN** domain is classified as "CONTRACT_QA"

#### Scenario: Classify chitchat
- **WHEN** user says "Xin chào, bạn khỏe không?"
- **THEN** domain is classified as "CHITCHAT"

### Requirement: Classify query intent within QA domain
For QA domain queries, the system SHALL classify the intent into one of: LOOKUP (tra cứu), TOPIC (chủ đề), VALIDITY (hiệu lực), COMPARISON (so sánh), CHECKLIST (danh sách yêu cầu), NUMERIC (con số/giới hạn), SCENARIO (tình huống), or SEARCH (tìm kiếm).

#### Scenario: Classify LOOKUP intent
- **WHEN** user asks "Điều 17 Luật Doanh nghiệp 2020 nói gì?"
- **THEN** intent is classified as "LOOKUP" with granularity "article"

#### Scenario: Classify TOPIC intent
- **WHEN** user asks "Quy định về bảo hiểm xã hội như thế nào?"
- **THEN** intent is classified as "TOPIC"

#### Scenario: Classify VALIDITY intent
- **WHEN** user asks "Luật Đất đai 2013 còn hiệu lực không?"
- **THEN** intent is classified as "VALIDITY"

#### Scenario: Classify COMPARISON intent
- **WHEN** user asks "So sánh Luật Doanh nghiệp 2014 và 2020"
- **THEN** intent is classified as "COMPARISON"

### Requirement: Extract granularity for LOOKUP queries
For LOOKUP intent, the system SHALL extract the granularity level: "chapter" (Chương), "article" (Điều), "clause" (Khoản), "point" (Điểm), or "document" (văn bản). The system SHALL extract corresponding identifiers (chapter number, article number, clause number, point letter).

#### Scenario: Extract article granularity
- **WHEN** user asks "Điều 17 Luật Doanh nghiệp"
- **THEN** granularity is "article" and article_number is 17

#### Scenario: Extract clause granularity
- **WHEN** user asks "Khoản 3 Điều 17 Luật Doanh nghiệp"
- **THEN** granularity is "clause", article_number is 17, clause_number is 3

#### Scenario: Extract point granularity
- **WHEN** user asks "Điểm b khoản 2 Điều 5 Nghị định 46"
- **THEN** granularity is "point", article_number is 5, clause_number is 2, point_label is "b"

#### Scenario: Extract chapter granularity
- **WHEN** user asks "Chương III Luật Đất đai"
- **THEN** granularity is "chapter" and chapter_identifier is "III"

### Requirement: Resolve so_ky_hieu
The system SHALL resolve document references to normalized so_ky_hieu using the lookup table from T0.1. Resolution SHALL support: exact match on normalized so_ky_hieu, fuzzy match (Levenshtein ≤ 2), and year + type + title substring fallback. Unresolved references SHALL be flagged for user clarification.

#### Scenario: Resolve exact so_ky_hieu
- **WHEN** user mentions "Luật Doanh nghiệp 2020"
- **THEN** so_ky_hieu is resolved to "LT-068-2020"

#### Scenario: Resolve abbreviated reference
- **WHEN** user mentions "ND 46"
- **THEN** so_ky_hieu is resolved via fuzzy match to "ND-046-2014"

#### Scenario: Flag unresolved reference
- **WHEN** so_ky_hieu cannot be resolved
- **THEN** the system flags it for user clarification

### Requirement: Decompose multi-intent queries
The system SHALL decompose complex queries containing multiple intents into sub-queries. Each sub-query SHALL include: intent type, natural language query, retrieval strategy, and required context. Sub-queries SHALL be processable in parallel.

#### Scenario: Decompose mixed validity + comparison
- **WHEN** user asks "Điều 17 Luật DN 2020 còn hiệu lực không, và khác gì Luật 2014?"
- **THEN** query is decomposed into 3 sub-queries: LOOKUP, VALIDITY, COMPARISON

#### Scenario: Decompose topic + checklist
- **WHEN** user asks "Thủ tục thành lập công ty cần những gì và quy định ở đâu?"
- **THEN** query is decomposed into 2 sub-queries: TOPIC, CHECKLIST

### Requirement: Handle confidence thresholds
The system SHALL apply confidence thresholds: >= 0.7 → proceed normally, 0.4-0.7 → ask clarification, < 0.4 → fallback to general response. The system SHALL provide a suggested clarification question when confidence is medium.

#### Scenario: High confidence proceeds
- **WHEN** intent confidence is 0.92
- **THEN** query proceeds to retrieval

#### Scenario: Medium confidence asks clarification
- **WHEN** intent confidence is 0.55
- **THEN** system asks "Bạn có thể nói rõ hơn không?"

#### Scenario: Low confidence falls back
- **WHEN** intent confidence is 0.25
- **THEN** system responds with general fallback message

### Requirement: Track conversation context
The system SHALL maintain conversation context including: conversation_id, turn_number, previous intents, referenced contracts, and extracted entities. Context SHALL be used to resolve follow-up references (e.g., "điều khoản đó" → previously discussed clause).

#### Scenario: Resolve follow-up reference
- **WHEN** previous turn discussed clause 5 of contract_xyz, and user asks "tại sao điều khoản đó sai?"
- **THEN** system resolves "điều khoản đó" to clause 5 of contract_xyz

#### Scenario: Track contract references
- **WHEN** user uploads and reviews a contract
- **THEN** contract_id is stored in conversation context for follow-up questions
