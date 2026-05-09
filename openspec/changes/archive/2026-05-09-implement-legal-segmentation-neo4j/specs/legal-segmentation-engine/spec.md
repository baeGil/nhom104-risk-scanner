## ADDED Requirements

### Requirement: Hierarchical State Machine Parser
Hệ thống SHALL triển khai một bộ máy parser dựa trên trạng thái để phân bóc cấu trúc văn bản pháp luật Việt Nam.

#### Scenario: Phân bóc Chương và Điều
- **WHEN** Parser gặp dòng "Chương I" và dòng kế tiếp là "Điều 1"
- **THEN** Hệ thống tạo ra một phân đoạn Chương với tiêu đề tương ứng và gán các Điều tiếp theo vào Chương này.

#### Scenario: Reset trạng thái phân cấp
- **WHEN** Parser đang ở trong "Mục 2" của "Chương I" và gặp dòng "Chương II"
- **THEN** Hệ thống SHALL xóa bỏ trạng thái "Mục 2" hiện tại để các Điều thuộc Chương II không bị gán nhầm vào Mục của chương trước.

### Requirement: Rich Contextualization
Hệ thống SHALL ghép thông tin metadata của văn bản vào nội dung của từng phân đoạn trước khi thực hiện embedding.

#### Scenario: Ghép metadata vào Điều
- **WHEN** Thực hiện tạo segment cho "Điều 5" của "Nghị định 100/2019/NĐ-CP"
- **THEN** Nội dung văn bản gửi đi embedding SHALL có định dạng: "Nghị định 100/2019/NĐ-CP - Điều 5. [Nội dung Điều 5]"
