export type JobState =
  | "queued"
  | "analyzing"
  | "extracting"
  | "ocr"
  | "building"
  | "previewing"
  | "completed"
  | "failed";

export interface JobCreateResponse {
  job_id: string;
  filename: string;
  status: JobState;
}

export interface BatchJobCreateResponse {
  jobs: JobCreateResponse[];
}

export interface JobProgressResponse {
  job_id: string;
  filename: string;
  status: JobState;
  progress: number;
  stage_message: string;
  mode?: string | null;
  error_message?: string | null;
  download_url?: string | null;
  preview_url?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface HistoryRecordResponse {
  job_id: string;
  original_filename: string;
  status: string;
  processing_mode: string;
  total_pages: number;
  input_size_bytes: number;
  output_size_bytes: number;
  created_at: string;
  completed_at?: string | null;
  download_url?: string | null;
  preview_url?: string | null;
}

export interface UserResponse {
  id: number;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export type SummaryMode = "extractive" | "abstractive" | "bullet";
export type SummaryLength = "short" | "medium" | "long";
export type SummarySource = "pdf" | "docx";

export interface SummaryResponse {
  job_id: string;
  source_type: SummarySource;
  mode: SummaryMode;
  length: SummaryLength;
  summary_text: string;
  bullets: string[];
  language: string;
  model_used: string;
  used_fallback: boolean;
}

export interface InsightResponse {
  job_id: string;
  source_type: SummarySource;
  keywords: string[];
  topics: string[];
  sentiment_label: string;
  sentiment_score: number;
  classification_label: string;
  classification_score: number;
  generated_at: string;
  model_used: string;
  used_fallback: boolean;
}

export interface DashboardStatsResponse {
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  queued_jobs: number;
  total_pages_processed: number;
  average_output_size_bytes: number;
  latest_job_filename?: string | null;
}
