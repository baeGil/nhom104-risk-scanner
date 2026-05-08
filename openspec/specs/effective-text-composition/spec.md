# Spec: Effective Text Composition

## Overview

Traverse amendment chains in the Neo4j graph, compose effective text for each Article by merging original text with all applicable amendments, and create EffectiveArticle nodes representing the current version of each provision.

## Capabilities

### Traverse amendment chains

For each Article that has incoming [:MODIFIES] edges, collect and order all modifications.

- Query Neo4j: find all Articles with incoming MODIFIES relationships
- Order modifications by modifying_doc.ngay_ban_hanh ASC (chronological order)
- For each modification, retrieve: action type, target clause/point, source Article text (the new/replacement text)
- Build a chronologically ordered list of modifications per Article
- Handle modification chains where Document A modifies Document B which was itself modified by Document C (transitive)
- Handle documents with 3+ modification levels (1,643 docs identified with complex chains)
- Output: ordered amendment chain per Article, ready for text merge

### Rule-based text merge

Apply modification actions to compose effective text from original + amendments.

- **"sửa đổi"** (modify): Replace the text of the specified Khoản/Điểm with the new text from the modifying document. Pattern: `"Sửa đổi khoản X như sau: {new_text}"`
- **"bổ sung"** (supplement): Insert a new Điểm after existing points in the specified Khoản. Pattern: `"Bổ sung điểm X khoản Y như sau: {new_text}"`
- **"thay thế"** (replace): Replace entire Khoản or Đoạn with new text. Pattern: `"Thay thế khoản X Điều Y bằng: {new_text}"`
- **"bãi bỏ"** (revoke): Mark the specified Khoản/Điểm as voided. Pattern: `"Bãi bỏ khoản X Điều Y"`
- **"hết hiệu lực một phần"** (partially invalidate): Mark specified provisions as no longer in effect
- Handle multi-action modifications: "Sửa đổi, bổ sung một số khoản của Điều X"
- Handle cascading amendments: if Amendment 1 modifies Khoản 2, and Amendment 2 also modifies Khoản 2, apply Amendment 1 first, then Amendment 2
- For each EffectiveArticle, store the composed text and the ordered amendment_chain

### Create EffectiveArticle nodes

Store composed text with versioning metadata in Neo4j.

- Create EffectiveArticle node for each Article that has amendments (and optionally for all Articles as base version)
- Properties: uid (`eff_{article_uid}_{date}`), as_of_date, effective_text, amendment_chain (ordered list), is_current, changes_count
- Create COMPOSED_FROM relationship from EffectiveArticle to original Article
- Create AMENDED_BY relationships from EffectiveArticle to each modifying Article (with order property)
- For Articles without any amendments: create EffectiveArticle with is_current=true, effective_text identical to original Article text, changes_count=0
- For Articles with amendments: is_current=true on the EffectiveArticle with the most recent as_of_date
- Handle validity: if the entire Document is "Hết hiệu lực toàn bộ", mark all its Articles' EffectiveArticle as is_current=false
- Handle partial invalidation: if "Hết hiệu lực một phần", only mark specifically voided provisions

### Validate against VB hợp nhất

Compare composed EffectiveArticle text against 35 available Văn bản hợp nhất documents as ground truth.

- For each of the 35 VB hợp nhất documents that exist in the dataset:
  - Parse its content to extract the merged text for each Điều
  - Find the corresponding original Document and all its amendments
  - Compose EffectiveArticle text using our pipeline
  - Compare our composed text against VB hợp nhất text
  - Compute: character-level similarity, structural equivalence (same Khoản/Điểm structure), semantic equivalence
- Compute overall agreement rate: percentage of Điều where composed text matches VB hợp nhất
- Flag any mismatches with details: original text, composed text, VB hợp nhất text, specific differences
- Target: ≥90% agreement with VB hợp nhất ground truth
- Use mismatches as training data for future LLM-assisted composition

### Compute is_current for all Articles

Determine whether each Article is still in effect based on document-level and article-level validity.

- Check Document.tinh_trang_hieu_luc:
  - "Còn hiệu lực" → Articles default to is_current=true (unless specifically invalidated)
  - "Hết hiệu lực toàn bộ" → all Articles is_current=false
  - "Hết hiệu lực một phần" → Articles default to is_current=true, check specific invalidations
  - "Ngưng hiệu lực" → all Articles is_current=false
- Check incoming PARTIALLY_SUPERSEDES relationships: specific Khoản/Điểm may be voided
- Check incoming MODIFIES relationships with action "bãi bỏ" or "hết hiệu lực một phần"
- Propagate: if a Điều has no EffectiveArticle with is_current=true, the Điều is considered voided
- Update is_current and effective_date on all Article and EffectiveArticle nodes
- Generate validity report: count of is_current=true/false by loai_van_ban