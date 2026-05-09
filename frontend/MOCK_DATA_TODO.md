# Mock Data - TODO: Replace with Real API

## Contract Review
- `src/lib/mock-api-contract.ts` — mock jobs, clauses, compliance results
- `src/app/(app)/contract-review/page.tsx:30-56` — `mockAnalysis` hardcoded clauses & compliance
- `src/app/(app)/contract-review/page.tsx:140-160` — `handleAnalyze()` fake 4s progress bar

**Replace with:**
```
POST /api/contracts/upload → { jobId }
GET  /api/contracts/jobs/:id → { progress, step, status, clauses, compliance }
SSE  /api/contracts/jobs/:id/stream → real-time progress updates
```

## Legal QA
- `src/lib/mock-api-qa.ts` — mock responses, streaming simulation
- `src/app/(app)/legal-qa/page.tsx` — uses mock sendMessage with fake token-by-token delay

**Replace with:**
```
POST /api/qa/chat → SSE stream of tokens
GET  /api/qa/conversations → conversation history
```

## Dashboard Stats
- `src/app/(app)/dashboard/page.tsx:6-23` — hardcoded mockStats, mockContracts, mockQuestions

**Replace with:**
```
GET /api/dashboard/stats → { contractsReviewed, questionsAsked, systemHealth, kgCoverage }
GET /api/dashboard/recent → { contracts[], questions[] }
```

## Settings
- `src/app/(app)/settings/page.tsx:11-14` — hardcoded user profile, API key

**Replace with:**
```
GET  /api/user/profile → { name, email, apiKey }
PUT  /api/user/profile → update profile
POST /api/user/api-key → generate new key
```

## PDF Worker
- `public/pdf.worker.min.mjs` — copied from node_modules, may need update on pdfjs-dist version change
