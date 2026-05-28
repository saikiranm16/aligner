import { HistoryRecordResponse } from "../types";

interface DownloadManagerProps {
  records: HistoryRecordResponse[];
  onDownload: (url: string) => void;
}

export function DownloadManager({ records, onDownload }: DownloadManagerProps) {
  const downloadable = records.filter((record) => record.download_url);

  return (
    <section className="panel p-6">
      <div>
        <h2 className="text-xl font-semibold">Download Manager</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Quick access to successful conversion artifacts and re-downloads.
        </p>
      </div>

      <div className="mt-6 space-y-3">
        {downloadable.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No downloadable documents yet.</p>
        ) : (
          downloadable.slice(0, 6).map((record) => (
            <div
              key={`download-${record.job_id}`}
              className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200/80 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-white/5"
            >
              <div>
                <p className="font-medium">{record.original_filename}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{record.processing_mode}</p>
              </div>
              <button
                type="button"
                onClick={() => onDownload(record.download_url!)}
                className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
              >
                Download
              </button>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
