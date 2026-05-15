## ADDED Requirements

### Requirement: Analyze contract clause compliance
For each contract clause with its matched legal provisions, the system SHALL use the LLM to generate a structured compliance report containing: violations (specific provisions the clause contradicts), risks (provisions that create risk if the clause is unclear or silent), suggestions (specific text changes to ensure compliance), and citations (precise Điều X khoản Y Luật/ND/TT format).

#### Scenario: Detect legal violation
- **WHEN** clause states "Phạt 30% giá trị hợp đồng" but law limits to 8%
- **THEN** system reports violation with citation to Luật Thương mại Điều 301

#### Scenario: Identify legal risk
- **WHEN** clause is silent on dispute resolution
- **THEN** system flags risk and suggests adding dispute resolution clause

#### Scenario: Suggest compliance fix
- **WHEN** clause violates a provision
- **THEN** system suggests specific text changes to ensure compliance

### Requirement: Include amendment history in analysis
The LLM input SHALL include the matched legal provisions' EffectiveArticle text, amendment history (which documents modified the provision), parent Document metadata (validity, scope, issuing authority), and detailing regulations (Nghị định/Thông tư via DETAILS relationship) when available.

#### Scenario: Include amendment context
- **WHEN** a provision has been modified by a newer document
- **THEN** the amendment history is included in the analysis context

### Requirement: Structured output format
The compliance analysis output SHALL be a JSON object with: violations (array of {clause, description, citation, severity}), risks (array of strings), suggestions (array of strings), and citations (array of {document, article, clause, text, verified}).

#### Scenario: Output matches expected format
- **WHEN** analysis completes
- **THEN** output contains violations, risks, suggestions, and citations arrays
