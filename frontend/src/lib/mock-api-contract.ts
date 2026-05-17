export interface ContractJob {
  id: string;
  documentId?: string;
  versionId?: string;
  filename: string;
  status: "uploading" | "parsing" | "extracting" | "retrieving" | "analyzing" | "verifying" | "completed" | "failed";
  progress: number;
  createdAt: string;
  fileUrl?: string;
  previewText?: string;
  sourceFormat?: string;
  clauses?: ContractClause[];
  matches?: LegalMatch[];
  compliance?: ComplianceResult;
  citations?: CitationResult[];
  error?: string;
}

export interface ContractClause {
  id: string;
  type: string;
  text: string;
  riskLevel: "low" | "medium" | "high";
}

export interface ComplianceResult {
  violations: ComplianceViolation[];
  risks: string[];
  suggestions: string[];
  citations?: CitationResult[];
}

export interface LegalMatch {
  clauseId: string;
  uid: string;
  citation: string;
  documentTitle: string;
  segmentType: string;
  score: number;
  validitySignal: string;
  scoreFactors: Record<string, number>;
}

export interface CitationResult {
  displayText: string;
  uid: string;
  verified: boolean;
  reason?: string;
  documentTitle?: string;
}

export interface ComplianceViolation {
  clause: string;
  description: string;
  citation: string;
  verified: boolean;
  contractClauseId?: string;
  contractClauseType?: string;
}

const mockJobs: ContractJob[] = [
  {
    id: "job_001",
    documentId: "doc_001",
    versionId: "ver_001",
    filename: "Hợp đồng thuê VP.pdf",
    status: "completed",
    progress: 100,
    createdAt: "2026-05-08",
    sourceFormat: "pdf",
    clauses: [
      { id: "c1", type: "Thanh toán", text: "Bên A thanh toán cho Bên B số tiền 50 triệu đồng/tháng", riskLevel: "low" },
      { id: "c2", type: "Phạt vi phạm", text: "Phạt 30% giá trị hợp đồng khi vi phạm", riskLevel: "high" },
      { id: "c3", type: "Bảo hành", text: "Thời hạn bảo hành 12 tháng", riskLevel: "medium" },
    ],
    matches: [
      {
        clauseId: "c2",
        uid: "doc_legal_dieu_301",
        citation: "Điều 301 Luật Thương mại",
        documentTitle: "Luật Thương mại",
        segmentType: "Article",
        score: 0.92,
        validitySignal: "latest_known",
        scoreFactors: { vector: 0.8, lexical: 0.6, exact: 0.2 },
      },
    ],
    compliance: {
      violations: [
        { clause: "Phạt vi phạm", description: "Mức phạt 30% vượt quá 8% theo Luật Thương mại", citation: "Điều 301 Luật Thương mại 2005", verified: true },
      ],
      risks: ["Mức phạt quá cao có thể bị tòa án tuyên vô hiệu"],
      suggestions: ["Giảm mức phạt xuống tối đa 8% giá trị phần nghĩa vụ bị vi phạm"],
      citations: [
        { displayText: "Điều 301 Luật Thương mại", uid: "doc_legal_dieu_301", verified: true, documentTitle: "Luật Thương mại" },
      ],
    },
    citations: [
      { displayText: "Điều 301 Luật Thương mại", uid: "doc_legal_dieu_301", verified: true, documentTitle: "Luật Thương mại" },
    ],
  },
  {
    id: "job_002",
    documentId: "doc_002",
    versionId: "ver_002",
    filename: "Hợp đồng lao động.docx",
    status: "completed",
    progress: 100,
    createdAt: "2026-05-07",
    previewText: "Điều 1. Lương cơ bản 15 triệu đồng/tháng",
    sourceFormat: "text",
    clauses: [
      { id: "c4", type: "Lương", text: "Lương cơ bản 15 triệu đồng/tháng", riskLevel: "low" },
    ],
    compliance: {
      violations: [],
      risks: [],
      suggestions: [],
    },
  },
];

export async function uploadContract(file: File): Promise<{ jobId: string; documentId: string; versionId: string }> {
  await new Promise((r) => setTimeout(r, 1000));
  const job = mockJobs[0];
  return { jobId: job.id, documentId: job.documentId || "doc_001", versionId: job.versionId || "ver_001" };
}

export async function getJobStatus(jobId: string): Promise<ContractJob> {
  await new Promise((r) => setTimeout(r, 500));
  return mockJobs.find((j) => j.id === jobId) || mockJobs[0];
}

export async function getJobHistory(): Promise<ContractJob[]> {
  await new Promise((r) => setTimeout(r, 300));
  return mockJobs;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await new Promise((r) => setTimeout(r, 150));
  const index = mockJobs.findIndex((job) => job.documentId === documentId);
  if (index >= 0) {
    mockJobs.splice(index, 1);
  }
}
