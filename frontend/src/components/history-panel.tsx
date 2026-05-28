import { HistoryRecordResponse } from "../types";

interface HistoryPanelProps {
  records: HistoryRecordResponse[];
  onPreview: (url: string) => void;
  onDownload: (url: string) => void;
}

function formatBytes(bytes: number): string {
  if (!bytes) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** power).toFixed(2)} ${units[power]}`;
}

export function HistoryPanel({ records, onPreview, onDownload }: HistoryPanelProps) {
  return (
    <section className="panel p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">Conversion History</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            Persisted activity for auditability, retries, and download recovery.
          </p>
        </div>
      </div>

      <div className="mt-6 space-y-3">
        {records.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No conversion history yet.</p>
        ) : (
          records.map((record) => (
            <article
              key={record.job_id}
              className="rounded-2xl border border-slate-200/80 bg-white/70 p-4 dark:border-white/10 dark:bg-white/5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{record.original_filename}</p>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Mode: {record.processing_mode} | Pages: {record.total_pages} | Output: {formatBytes(record.output_size_bytes)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {record.preview_url ? (
                    <button
                      type="button"
                      onClick={() => onPreview(record.preview_url!)}
                      className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold transition hover:border-slate-900 dark:border-white/15 dark:hover:border-white/40"
                    >
                      Preview
                    </button>
                  ) : null}
                  {record.download_url ? (
                    <button
                      type="button"
                      onClick={() => onDownload(record.download_url!)}
                      className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
                    >
                      Download
                    </button>
                  ) : null}
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
