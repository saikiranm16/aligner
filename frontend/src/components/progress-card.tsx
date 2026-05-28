import { JobProgressResponse } from "../types";

interface ProgressCardProps {
  job: JobProgressResponse;
  onRetry: (jobId: string) => void;
  onPreview: (url: string) => void;
  onDownload: (url: string) => void;
}

const STATE_LABELS: Record<string, string> = {
  queued: "Queued",
  analyzing: "Analyzing",
  extracting: "Extracting Layout",
  ocr: "OCR",
  building: "Building DOCX",
  previewing: "Rendering Preview",
  completed: "Completed",
  failed: "Failed",
};

export function ProgressCard({ job, onRetry, onPreview, onDownload }: ProgressCardProps) {
  return (
    <article className="panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-base font-semibold">{job.filename}</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{job.stage_message}</p>
        </div>
        <div className="flex gap-2">
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800 dark:bg-amber-500/20 dark:text-amber-200">
            {STATE_LABELS[job.status] ?? job.status}
          </span>
          {job.mode ? (
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-200">
              {job.mode}
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-white/10">
        <div
          className={`h-full rounded-full transition-all ${
            job.status === "failed" ? "bg-rose-500" : "bg-gradient-to-r from-accent to-glow"
          }`}
          style={{ width: `${job.progress}%` }}
        />
      </div>

      {job.error_message ? (
        <p className="mt-3 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">
          {job.error_message}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-3">
        {job.preview_url ? (
          <button
            type="button"
            onClick={() => onPreview(job.preview_url!)}
            className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold transition hover:border-slate-900 dark:border-white/15 dark:hover:border-white/40"
          >
            Preview
          </button>
        ) : null}
        {job.download_url ? (
          <button
            type="button"
            onClick={() => onDownload(job.download_url!)}
            className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            Download DOCX
          </button>
        ) : null}
        {job.status === "failed" ? (
          <button
            type="button"
            onClick={() => onRetry(job.job_id)}
            className="rounded-full bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-500"
          >
            Retry
          </button>
        ) : null}
      </div>
    </article>
  );
}
