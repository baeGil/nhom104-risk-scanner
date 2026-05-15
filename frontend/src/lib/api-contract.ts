import { apiRequest } from "./api-client";

export interface UploadResponse {
  jobId: string;
}

export interface ContractJob {
  id: string;
  filename: string;
  status: "uploading" | "parsing" | "extracting" | "retrieving" | "analyzing" | "verifying" | "completed" | "failed";
  progress: number;
  createdAt: string;
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

export interface ComplianceResult {
  violations: ComplianceViolation[];
  risks: string[];
  suggestions: string[];
  citations?: CitationResult[];
}

export interface ComplianceViolation {
  clause: string;
  description: string;
  citation: string;
  verified: boolean;
}

export interface JobStatusResponse {
  jobId: string;
  status: ContractJob["status"];
  progress: number;
  filename: string;
  createdAt: string;
  clauses?: ContractClause[];
  matches?: LegalMatch[];
  compliance?: ComplianceResult;
  citations?: CitationResult[];
  error?: string;
}

export async function uploadContract(file: File): Promise<{ jobId: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout for uploads

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/contracts/upload`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
      headers: {
        // Don't set Content-Type — browser sets it with boundary for FormData
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || `Upload failed: ${response.status}`);
    }

    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getJobStatus(jobId: string): Promise<ContractJob> {
  const status = await apiRequest<JobStatusResponse>(`/api/contracts/${jobId}/status`);

  return {
    id: status.jobId,
    filename: status.filename,
    status: status.status,
    progress: status.progress,
    createdAt: status.createdAt,
    clauses: status.clauses,
    matches: status.matches,
    compliance: status.compliance,
    citations: status.citations,
    error: status.error,
  };
}

export async function getJobHistory(): Promise<ContractJob[]> {
  const jobs = await apiRequest<JobStatusResponse[]>("/api/contracts/history");

  return jobs.map((job) => ({
    id: job.jobId,
    filename: job.filename,
    status: job.status,
    progress: job.progress,
    createdAt: job.createdAt,
    clauses: job.clauses,
    matches: job.matches,
    compliance: job.compliance,
    citations: job.citations,
    error: job.error,
  }));
}

export const contractApi = {
  uploadContract,
  getJobStatus,
  getJobHistory,
};
