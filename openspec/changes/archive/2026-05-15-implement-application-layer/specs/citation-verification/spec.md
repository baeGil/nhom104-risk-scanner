## ADDED Requirements

### Requirement: Parse citation format from text
The system SHALL parse citations from LLM output in the Vietnamese legal format: "Điều {N} khoản {K} {Loại_văn_bản} {so_ky_hieu}". The parser SHALL extract: article number (integer), clause number (integer, optional), point letter (string, optional), document type (Luật/Nghị định/Thông tư), and so_ky_hieu (normalized document identifier).

#### Scenario: Parse full citation with clause
- **WHEN** input is "Điều 301 khoản 2 Luật Thương mại 2005"
- **THEN** parser extracts article=301, clause=2, type="Luật", so_ky_hieu="LT-059-2005"

#### Scenario: Parse citation without clause
- **WHEN** input is "Điều 17 Luật Doanh nghiệp 2020"
- **THEN** parser extracts article=17, clause=null, type="Luật", so_ky_hieu="LT-068-2020"

#### Scenario: Parse multiple citations
- **WHEN** input contains multiple citations
- **THEN** each citation is parsed separately

### Requirement: Verify citations against Neo4j graph
For each parsed citation, the system SHALL query Neo4j to verify: the Article exists with the specified index, the parent Document exists with the normalized so_ky_hieu, the Clause exists if specified, and the is_current flag status. Each citation SHALL be marked as VERIFIED or UNVERIFIED with a reason.

#### Scenario: Verify existing article
- **WHEN** citation references an Article that exists in Neo4j
- **THEN** citation is marked VERIFIED with is_current status

#### Scenario: Verify non-existent article
- **WHEN** citation references an Article that does not exist
- **THEN** citation is marked UNVERIFIED with reason "Article not found"

#### Scenario: Verify with clause specificity
- **WHEN** citation specifies a clause number
- **THEN** system verifies the Clause node exists under the Article

#### Scenario: Batch verification
- **WHEN** multiple citations need verification
- **THEN** system processes all citations and returns results for each
