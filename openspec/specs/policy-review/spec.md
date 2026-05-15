## ADDED Requirements

### Requirement: Policy compliance classification
The system SHALL analyze policy documents using the same pipeline as contract review (matching + compliance analysis) and additionally classify each policy provision into one of three categories: "compliant_and_efficient" (meets legal requirements, no excess restrictions), "compliant_but_restrictive" (exceeds legal requirements, potentially costly), or "non_compliant" (violates legal requirements).

#### Scenario: Classify compliant and efficient policy
- **WHEN** policy provision matches legal requirements exactly
- **THEN** classification is "compliant_and_efficient"

#### Scenario: Classify compliant but restrictive policy
- **WHEN** policy provision is more restrictive than law requires
- **THEN** classification is "compliant_but_restrictive" with explanation of excess

#### Scenario: Classify non-compliant policy
- **WHEN** policy provision contradicts legal requirements
- **THEN** classification is "non_compliant" with violation details

### Requirement: Flag overly restrictive provisions
The system SHALL identify and flag policy provisions that are more restrictive than the law requires, explaining what the legal minimum is and how the policy exceeds it.

#### Scenario: Flag excessive restriction
- **WHEN** law requires 8-hour rest but policy requires 12-hour rest
- **THEN** system flags the policy as more restrictive than necessary
