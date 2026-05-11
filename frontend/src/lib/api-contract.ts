import { apiRequest } from "./api-client";
import type { ContractJob, ContractClause, ComplianceResult } from "./mock-api-contract";

export interface UploadResponse {
  jobId: string;
}

export interface JobStatusResponse {
  jobId: string;
  status: "uploading" | "parsing" | "analyzing" | "completed" | "failed";
  progress: number;
  filename: string;
  createdAt: string;
  clauses?: ContractClause[];
  compliance?: ComplianceResult;
}

export async function uploadContract(file: File): Promise<{ jobId: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/contracts/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Upload failed");
  }

  return response.json();
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
    compliance: status.compliance,
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
    compliance: job.compliance,
  }));
}
