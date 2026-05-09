Dựa trên thông tin bạn đã chia sẻ (đang build AI trợ lý pháp luật **Việt Nam** với chức năng **rà soát hợp đồng**, dùng **GraphRAG**, **model local** qua LM Studio), đây là khuyến nghị:

***

## ✅ **KHÔNG nên dùng skill nào (gốc)**

| Skill | Tại sao KHÔNG phù hợp |
|-------|------------------------|
| **claude-legal-skill** | ❌ US law focus (Delaware/NY/CA benchmarks) — không có luật Việt Nam  [github](https://github.com/evolsb/claude-legal-skill)<br>❌ 41 CUAD categories không áp dụng được cho BVDS, Luật Dân sự VN<br>❌ Không có tiếng Việt |
| **legal-document-analyzer** | ❌ Compliance EU (GDPR, SOC2, ISO) — không có DPA Việt Nam<br>❌ Thiếu knowledge base luật VN (Bộ luật Dân sự, Luật Doanh nghiệp, Luật Thuế)  [playbooks](https://playbooks.com/skills/qodex-ai/ai-agent-skills/legal-document-analyzer)<br>❌ Không có 37 lĩnh vực pháp luật VN  [perplexity](https://www.perplexity.ai/search/5ac6ce55-9158-4db5-bc59-7b760829add6) |
| **Contract Risk Analyzer (FindSkill Pro)** | ❌ Cần subscription trả phí (~$945 skills)<br>❌ US-centric |

***

## 🎯 **NÊN TẬN DỤNG: Điều gì từ các skill này?**

### 1. **Lấy TEMPLATE (cấu trúc SKILL.md)** — UPGRADE thành **vietnamese-law-analyzer**

| Từ skill gốc | Đổi thành cho VN |
|--------------|------------------|
| **CUAD risk categories** (41 US contract types)  [github](https://github.com/evolsb/claude-legal-skill) | → **Risk categories VN**: uncapped penalty, auto-renewal bí mật, bounded liability thấp, transfers without notice  [perplexity](https://www.perplexity.ai/search/d04e9b69-6915-4396-afa2-566050f50598) |
| **Liability cap benchmarks** (12 tháng = standard US)  [github](https://github.com/evolsb/claude-legal-skill) | → **Điều chỉnh VN**: 6 tháng = standard cho doanh nghiệp VN; 12 tháng cho B2B lớn |
| **Position-aware** (customer/vendor)  [github](https://github.com/evolsb/claude-legal-skill) | → **Giữ lại!** Rất hữu ích: flag rủi ro cho phía A/B |
| **Legal redlines + tracked changes Word**  [github](https://github.com/evolsb/claude-legal-skill) | → **Giữ lại!** Output PDF/Word với đề xuất edit cụ thể |

***

### 2. **Lấy CHECKLIST rủi ro cho hợp đồng VN (từ autoanalyzing)**

Từ các nguồn bạn đã nghiên cứu trước đó: [perplexity](https://www.perplexity.ai/search/d041a215-3179-477f-b89d-bc01dec47e87)

| Rủi ro cần flag trong hợp đồng VN | Mô tả  [perplexity](https://www.perplexity.ai/search/d04e9b69-6915-4396-afa2-566050f50598) |
|-----------------------------------|-------------------|
| **Phạt vi phạm quá cao** | >10% giá trị hợp đồng = rủi ro (Luật Dân sự 2015) |
| **Bất khả kháng mơ hồ** | Không định nghĩa rõ (thiên tai, dịch bệnh, chiến tranh) → bên A fraud |
| **Tạm ứng/thanh toán bất lợi** | 50% tạm ứng, 50% còn lại sau xong = rủi ro cho người nhận |
| **Trách nhiệm bán không rõ ràng** | Không có penalty nếu hàng lỗi → rủi ro mua |
| **Hợp đồng tự động gia hạn** | Không có notice 60-90 ngày → trap |
| **Thẩm quyền giải quyết tranh chấp** | Tòa án nước ngoài → khó thực thi tại VN |

***

### 3. **Lấy KNOWLEDGE BASE PATTERN** — Upload luật VN [perplexity](https://www.perplexity.ai/search/9a5e5272-253e-4534-a9d2-9863d12dd179)

Từ **legal-document-analyzer**, học cách dùng knowledge base. Nhưng thay vì GDPR, upload:

| Type | Source | Link |
|------|--------|------|
| **Bộ luật Dân sự 2015** | Legal.Dien / vbpl.vn |  [perplexity](https://www.perplexity.ai/search/b05ed36f-a128-4263-876b-020efa82c1d7) |
| **Luật Doanh nghiệp 2020** | toantc1024/vietlaw |  [perplexity](https://www.perplexity.ai/search/b05ed36f-a128-4263-876b-020efa82c1d7) |
| **Luật Đầu tư 2020** | Để liên kết chéo Doanh nghiệp - Đầu tư |  [perplexity](https://www.perplexity.ai/search/15b509ca-d2f3-4856-a789-529e5cb9d687) |
| **Luật Đất đai 2024** | Luật Nhà ở cross-reference |  [perplexity](https://www.perplexity.ai/search/0a34a94d-fa90-41e4-bce5-984cc31408b3) |
| **Nghị định 47/2021/NĐ-CP** | Cross-reference Luật DN 2020 Điều 195 |  [perplexity](https://www.perplexity.ai/search/5ac6ce55-9158-4db5-bc59-7b760829add6) |
| **518K văn bản QPPL** | Vietnamese Curated Dataset (content 3.6GB) |  [perplexity](https://www.perplexity.ai/search/c0adf30b-9ebe-4d94-ab32-67e660d61975) |
| **Án lệ + hợp đồng mẫu** | Caselaw.vn |  [perplexity](https://www.perplexity.ai/search/c0adf30b-9ebe-4d94-ab32-67e660d61975) |
| **Hợp đồng có trap** | maudong.vn, saigondaitin.com |  [perplexity](https://www.perplexity.ai/search/d04e9b69-6915-4396-afa2-566050f50598) |

***

## 🔨 **KIẾN TRÚC ĐỀ XUẤT: Rà soát hợp đồng AI của bạn**

```
┌─────────────────────────────────────────────────────────────┐
│                   1. INPUT: Hợp đồng (PDF/Word/Text)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. LAYERS: Bạn sẽ code 3 phần chính (KHÔNG dùng skill)     │
├─────────────────┬───────────────────┬───────────────────────┤
│ A. Clause       │ B. RAG Lookup     │ C. Risk Scoring       │
│ Extraction      │ (Luật VN)         │ & Compliance Check    │
│                 │                   │                       │
│ • Parse PDF/    │ • Query GraphRAG  │ • Rule-based:         │
│   DocX          │   vào knowledge   │   - Nếu penalty > 10% │
│   [cite:105]    │     base:         │     → flag 🔴         │
│                 │     - Điều 408 BV │   - Nếu auto-renewal  │
│ • Extract:      │     (Nghĩa vụ &   │     notice < 60 ngày  │
│   - Parties     │     trách nhiệm)  │     → flag 🟡         │
│   - Amount,     │   • GraphRAG:     │   - Nếu jurisdiction  │
│     Dates       │     - Cross-ref   │     nước ngoài        │
│   - Penalty     │     Luật DN-Đầu   │     → flag 🟡         │
│     clauses     │     tư [cite:106] │   • LLM reasoning:    │
│   - Termination │     - Án lệ       │     - So sánh market  │
│     rights      │     [cite:103]    │     standard VN       │
│                 │                   │     [cite:99]         │
└────────┬────────┴────────┬──────────┴───────────┬───────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. OUTPUT: Báo cáo rà soát (Tiếng Việt)                    │
│  • 🔴 Critical: Uncleared risk, vi phạm luật VN             │
│  • 🟡 Important: Rủi ro cần đàm phán lại                    │
│  • 🟢 Acceptable: OK, nằm trong standard                    │
│  • Điều khoản đề xuất thay thế (redlines)                   │
│  • Trích dẫn điều luật: "Điều 408 BVDS 2015"                │
└─────────────────────────────────────────────────────────────┘
```

***

## 📋 **Template SKILL.md cho AI của bạn**

```markdown
# SKILL.md - VietLaw Contract Analyzer

## Role
Trợ lý pháp lý AI chuyên rà soát hợp đồng theo luật Việt Nam

## Phạm vi [cite:102][cite:106]
- Bộ luật Dân sự 2015 (Nghĩa vụ & trách nhiệm)
- Luật Doanh nghiệp 2020
- Luật Đầu tư 2020
- Luật Đất đai 2024
- 518K văn bản QPPL [cite:103]

## Rủi ro chính (từ template claude-legal-skill + điều chỉnh VN)

### 1. Phạt vi phạm [cite:104]
- ❌ Phạt > 10% giá trị → Flag 🔴
- ✅ Standard: 8-10% cho doanh nghiệp VN

### 2. Bất khả kháng [cite:104]
- ❌ Không định nghĩa rõ → Flag 🟡
- ✅ Seasonal typhoons, COVID-19, market crashes

### 3. Thanh toán [cite:104]
- ❌ 100% tạm ứng → Flag 🟡 (rủi ro bên nhận)
- ❌ 100% khi xong → Flag 🔴 (rủi ro bên trả)
- ✅ 50/50 hoặc 30/40/10 (deposit/milestone/retain)

### 4. Trách nhiệm [cite:104]
- ❌ Uncapped liability → Flag 🔴 cho vendor
- ✅ Standard: 12 tháng doanh thu (B2B VN)

### 5. Gia hạn tự động [cite:104]
- ❌ Notice < 60 ngày → Flag 🔴
- ✅ Standard: 90 ngày

### 6. Thẩm quyền tranh chấp
- ❌ Tòa nước ngoài (Singapore, NY) → Flag 🟡 cho VN
- ✅ Tòa VN, Trọng tài VN (VIAC)

### 7. Transfers without notice
- ❌ Cho transfer rights mà không cần consent → Flag 🟡

## Output [web:34][web:64]
1. Risk score tổng (🔴/🟡/🟢)
2. Clause-level assessment với section references
3. Đề xuất redlines (replacement text)
4. Trích dẫn điều luật VN (số hiệu, điều, khoản)
5. Action plan đàm phán

## Knowledge Base
- Upload: Bodylaws VN, Án lệ, Hợp đồng trap [cite:104]
- Use GraphRAG cho cross-reference [cite:112]
```

***

## 🎯 **Tóm lại: AI bạn code nên tận dụng gì?**

| Từ skill | Dùng gì | Không dùng gì |
|----------|---------|---------------|
| **claude-legal-skill** | ✅ Template cấu trúc SKILL.md<br>✅ Checklists risk categories<br>✅ Redline formatting (Word/PDF) | ❌ Benchmark US (liability cap 12 tháng)<br>❌ Jurisdiction (Delaware/NY)<br>❌ English-only |
| **legal-document-analyzer** | ✅ Knowledge base pattern<br>✅ Compliance check workflow | ❌ EU regs (GDPR)<br>❌ ISO/SOC2<br>❌ Compliance không áp dụng VN |
| **Contract Risk Analyzer** | ✅ Red flags mẫu | ❌ Subscription<br>❌ US markets |

### ❗ **Không dùng skill nào để chạy**

Vì bạn đang **code AI riêng** (không dùng Claude Code/ChatGPT/Cursor):
- ❌ Không cần Toolkit `SKILL.md` — **tự code logic** trong AI của bạn
- ✅ **Chỉ dùng template/các checklist** để build module kiểm tra hợp đồng

***

## 🔥 **Gợi ý cụ thể cho bạn**

1. **Lấy dataset hợp đồng trap** từ  (mauhopdong.vn, saigondaitin.com) — annotate 200-500 mẫu [perplexity](https://www.perplexity.ai/search/d04e9b69-6915-4396-afa2-566050f50598)
2. **Fine-tune model local** (Qwen2.5 9B hoặc GLM-4 9B cho tiếng Việt)  với dữ liệu này [perplexity](https://www.perplexity.ai/search/e7194419-7e51-493f-8ed4-2646eb025179)
3. **Dùng GraphRAG** để liên kết Luật DN, Luật Đầu tư, Nghị định 47 [perplexity](https://www.perplexity.ai/search/c6fff4c9-d374-46fe-a420-e57517c721eb)
4. **Code module risk scoring** theo checklist **đã điều chỉnh VN** ở trên

Bạn có muốn mình viết ngay **mẫu code Python** cho 1 trong các phần sau không?
- A. Clause extraction từ PDF/Word (British, primary)
- B. GraphRAG cross-reference Luật DN <-> Luật Đầu tư
- C. Rule-based risk scorer (phạt > 10%, auto-renewal < 60 ngày)