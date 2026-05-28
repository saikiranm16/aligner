import { useEffect, useMemo, useState } from "react";
import {
  createBatchJobs,
  createJob,
  downloadDocx,
  downloadFile,
  generateSummary,
  getAuthToken,
  getDashboard,
  getHistory,
  getMe,
  getInsights,
  getJob,
  login,
  register,
  retryJob,
  setAuthToken,
} from "./api/client";
import { AnalysisPanel } from "./components/analysis-panel";
import { AuthPanel } from "./components/auth-panel";
import { DashboardOverview } from "./components/dashboard-overview";
import { DownloadManager } from "./components/download-manager";
import { HistoryPanel } from "./components/history-panel";
import { PreviewPanel } from "./components/preview-panel";
import { ProgressCard } from "./components/progress-card";
import { ThemeToggle } from "./components/theme-toggle";
import { UploadDropzone } from "./components/upload-dropzone";
import {
  AuthResponse,
  DashboardStatsResponse,
  HistoryRecordResponse,
  InsightResponse,
  JobProgressResponse,
  SummaryLength,
  SummaryMode,
  SummaryResponse,
  SummarySource,
  UserResponse,
} from "./types";

const MAX_FILE_SIZE_MB = Number(import.meta.env.VITE_MAX_FILE_SIZE_MB ?? 50);
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export default function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [jobs, setJobs] = useState<Record<string, JobProgressResponse>>({});
  const [history, setHistory] = useState<HistoryRecordResponse[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dashboardStats, setDashboardStats] = useState<DashboardStatsResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [insights, setInsights] = useState<InsightResponse | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);

  const activeJobs = useMemo(() => Object.values(jobs).sort((a, b) => b.created_at.localeCompare(a.created_at)), [jobs]);

  const refreshDashboard = async () => {
    const stats = await getDashboard();
    setDashboardStats(stats);
  };

  const refreshHistory = async () => {
    const records = await getHistory();
    setHistory(records);
  };

  useEffect(() => {
    const existingToken = getAuthToken();
    if (existingToken) {
      getMe()
        .then((profile) => setUser(profile))
        .catch(() => {
          setAuthToken(null);
          setUser(null);
        });
    }
    Promise.all([refreshHistory(), refreshDashboard()]).catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    const pendingJobs = activeJobs.filter((job) => !["completed", "failed"].includes(job.status));
    if (pendingJobs.length === 0) {
      return;
    }

    const interval = window.setInterval(async () => {
      await Promise.all(
        pendingJobs.map(async (job) => {
          const next = await getJob(job.job_id);
          setJobs((current) => ({ ...current, [job.job_id]: next }));
          if (next.status === "completed") {
            await Promise.all([refreshHistory(), refreshDashboard()]);
          }
        }),
      ).catch((reason: Error) => setError(reason.message));
    }, 1500);

    return () => window.clearInterval(interval);
  }, [activeJobs]);

  const handleFilesSelected = (selectedFiles: File[]) => {
    const invalid = selectedFiles.find(
      (file) => file.size > MAX_FILE_SIZE_MB * 1024 * 1024 || !file.name.toLowerCase().endsWith(".pdf"),
    );
    if (invalid) {
      setError(`Only PDF files up to ${MAX_FILE_SIZE_MB} MB are allowed.`);
      return;
    }
    setError(null);
    setFiles(selectedFiles);
  };

  const handleConvert = async () => {
    if (files.length === 0) {
      setError("Select at least one PDF to convert.");
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      if (files.length === 1) {
        const created = await createJob(files[0]);
        setJobs((current) => ({
          ...current,
          [created.job_id]: {
            job_id: created.job_id,
            filename: created.filename,
            status: created.status,
            progress: 0,
            stage_message: "Queued for conversion",
            created_at: new Date().toISOString(),
          },
        }));
      } else {
        const created = await createBatchJobs(files);
        const nextJobs: Record<string, JobProgressResponse> = {};
        created.jobs.forEach((job) => {
          nextJobs[job.job_id] = {
            job_id: job.job_id,
            filename: job.filename,
            status: job.status,
            progress: 0,
            stage_message: "Queued for conversion",
            created_at: new Date().toISOString(),
          };
        });
        setJobs((current) => ({ ...current, ...nextJobs }));
      }
      setFiles([]);
      await refreshDashboard();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Upload failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = async (jobId: string) => {
    try {
      const created = await retryJob(jobId);
      setJobs((current) => ({
        ...current,
        [created.job_id]: {
          job_id: created.job_id,
          filename: created.filename,
          status: created.status,
          progress: 0,
          stage_message: "Queued for retry",
          created_at: new Date().toISOString(),
        },
      }));
      await refreshDashboard();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Retry failed.");
    }
  };

  const handlePreview = (path: string) => {
    setPreviewUrl(`${API_BASE}${path}`);
  };

  const handleDownload = async (path: string) => {
    try {
      await downloadDocx(path);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Download failed.");
    }
  };

  const handleAuthResponse = async (response: AuthResponse) => {
    setAuthToken(response.access_token);
    setUser(response.user);
    setError(null);
    await Promise.all([refreshHistory(), refreshDashboard()]);
    return response;
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    setSummary(null);
    setInsights(null);
    setError(null);
    Promise.all([refreshHistory(), refreshDashboard()]).catch(() => undefined);
  };

  const handleGenerateSummary = async (
    jobId: string,
    sourceType: SummarySource,
    mode: SummaryMode,
    length: SummaryLength,
  ) => {
    try {
      const nextSummary = await generateSummary(jobId, {
        source_type: sourceType,
        mode,
        length,
        language_hint: "auto",
      });
      setSummary(nextSummary);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Summary generation failed.");
    }
  };

  const handleLoadInsights = async (jobId: string, sourceType: SummarySource) => {
    try {
      const nextInsights = await getInsights(jobId, sourceType);
      setInsights(nextInsights);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Document analysis failed.");
    }
  };

  const handleExportSummary = async (
    jobId: string,
    sourceType: SummarySource,
    mode: SummaryMode,
    length: SummaryLength,
    formatType: "txt" | "docx",
  ) => {
    try {
      const query = `/api/v1/jobs/${jobId}/summary/export?source_type=${sourceType}&mode=${mode}&length=${length}&format_type=${formatType}`;
      await downloadFile(query);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Summary export failed.");
    }
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-8 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-accent">AlignPDF</p>
          <h1 className="mt-3 text-4xl font-black tracking-tight sm:text-5xl">
            AI-powered PDF conversion, document intelligence, and enterprise-ready review workflows.
          </h1>
          <p className="mt-4 max-w-2xl text-base text-slate-700 dark:text-slate-300">
            Convert PDFs into editable Word documents, preview original pages, generate AI summaries, extract document insights,
            and manage downloads from a production-style dashboard.
          </p>
        </div>
        <ThemeToggle />
      </header>

      {error ? (
        <div className="mb-6 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-200">
          {error}
        </div>
      ) : null}

      <div className="space-y-6">
        <DashboardOverview stats={dashboardStats} />

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <AuthPanel
              user={user}
              onLogin={(email, password) => login(email, password).then(handleAuthResponse)}
              onRegister={(email, password) => register(email, password).then(handleAuthResponse)}
              onLogout={handleLogout}
            />

            <UploadDropzone
              files={files}
              maxSizeMb={MAX_FILE_SIZE_MB}
              onFilesSelected={handleFilesSelected}
              onClear={() => setFiles([])}
            />

            <div className="panel p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Queue Controls</h2>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                    Submit single or batch conversions with background processing, OCR fallback, and retry support.
                  </p>
                </div>
                <button
                  type="button"
                  disabled={isSubmitting || files.length === 0}
                  onClick={handleConvert}
                  className="rounded-full bg-gradient-to-r from-accent to-glow px-6 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSubmitting ? "Submitting..." : files.length > 1 ? "Convert Batch" : "Convert PDF"}
                </button>
              </div>
            </div>

            <section className="space-y-4">
              <div>
                <h2 className="text-xl font-semibold">Active Jobs</h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  Polling is automatic while jobs are running, and completed items stay available for preview, summary, and download.
                </p>
              </div>
              {activeJobs.length === 0 ? (
                <div className="panel p-6 text-sm text-slate-500 dark:text-slate-400">No active jobs yet.</div>
              ) : (
                activeJobs.map((job) => (
                  <ProgressCard
                    key={job.job_id}
                    job={job}
                    onRetry={handleRetry}
                    onPreview={handlePreview}
                    onDownload={handleDownload}
                  />
                ))
              )}
            </section>

            <AnalysisPanel
              records={history}
              summary={summary}
              insights={insights}
              onGenerateSummary={handleGenerateSummary}
              onLoadInsights={handleLoadInsights}
              onExportSummary={handleExportSummary}
            />
          </div>

          <div className="space-y-6">
            <PreviewPanel previewUrl={previewUrl} />
            <DownloadManager records={history} onDownload={handleDownload} />
            <HistoryPanel records={history} onPreview={handlePreview} onDownload={handleDownload} />
          </div>
        </div>
      </div>
    </main>
  );
}
