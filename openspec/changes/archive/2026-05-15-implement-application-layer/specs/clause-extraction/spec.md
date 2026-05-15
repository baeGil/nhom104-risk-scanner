## ADDED Requirements

### Requirement: Extract clauses from contract text
The system SHALL use the LLM to identify and structure individual clauses from contract Markdown text. For each clause, the system SHALL extract: clause index (sequential number), clause_type (thanh_toán, bảo_hành, phạt, chấm_dứt, bồi_thường, bảo_mật, giải_quyết_tranh_chấp, force_majeure, etc.), text_content (the full clause text), parties_involved (list of party names), obligations (list of obligations described), amount (monetary values if present), and deadline (dates/deadlines if present).

#### Scenario: Extract payment clause
- **WHEN** contract contains "Bên A thanh toán cho Bên B số tiền 50 triệu đồng/tháng"
- **THEN** system extracts clause with type="thanh_toán", amount="50 triệu đồng/tháng"

#### Scenario: Extract penalty clause
- **WHEN** contract contains "Phạt 30% giá trị hợp đồng khi vi phạm"
- **THEN** system extracts clause with type="phạt", obligations include penalty terms

#### Scenario: Extract multiple clauses
- **WHEN** contract has 10+ clauses
- **THEN** all clauses are extracted with correct types and content

### Requirement: Generate embeddings for extracted clauses
For each extracted ContractClause, the system SHALL generate an embedding using the vietlegal-harrier-0.6b model (1024 dimensions) and store it in the ContractClause.embedding property. The embedding SHALL be generated from the clause text_content.

#### Scenario: Embed single clause
- **WHEN** a clause is extracted
- **THEN** its embedding is generated and stored

#### Scenario: Batch embed all clauses
- **WHEN** multiple clauses are extracted from a contract
- **THEN** all embeddings are generated in a batch request

### Requirement: Target extraction accuracy
The system SHALL achieve ≥90% clause extraction accuracy on test contracts, measured by human evaluation of clause boundary detection, type classification, and content completeness.

#### Scenario: Meet accuracy target
- **WHEN** evaluated on test contracts
- **THEN** ≥90% of clauses are correctly extracted with proper type and content
