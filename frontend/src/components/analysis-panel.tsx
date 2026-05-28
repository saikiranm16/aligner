import { useMemo, useState } from "react";
import { HistoryRecordResponse, InsightResponse, SummaryLength, SummaryMode, SummaryResponse, SummarySource } from "../types";

interface AnalysisPanelProps {
  records: HistoryRecordResponse[];
  summary: SummaryResponse | null;
  insights: InsightResponse | null;
  onGenerateSummary: (jobId: string, sourceType: SummarySource, mode: SummaryMode, length: SummaryLength) => Promise<void>;
  onLoadInsights: (jobId: string, sourceType: SummarySource) => Promise<void>;
  onExportSummary: (jobId: string, sourceType: SummarySource, mode: SummaryMode, length: SummaryLength, formatType: "txt" | "docx") => Promise<void>;
}

export function AnalysisPanel({
  records,
  summary,
  insights,
  onGenerateSummary,
  onLoadInsights,
  onExportSummary,
}: AnalysisPanelProps) {
  const completedRecords = useMemo(() => records.filter((record) => record.status === "completed"), [records]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [sourceType, setSourceType] = useState<SummarySource>("pdf");
  const [mode, setMode] = useState<SummaryMode>("extractive");
  const [length, setLength] = useState<SummaryLength>("medium");
  const [loading, setLoading] = useState(false);

  const selected = completedRecords.find((record) => record.job_id === selectedJobId);

  const run = async (action: () => Promise<void>) => {
    if (!selectedJobId) {
      return;
    }
    setLoading(true);
    try {
      await action();
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel p-6">
      <div>
        <h2 className="text-xl font-semibold">AI Summary And Analysis</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Generate extractive, abstractive, or bullet summaries plus keywords, topics, sentiment, and document classification.
        </p>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-2">
        <select
          value={selectedJobId}
          onChange={(event) => setSelectedJobId(event.target.value)}
          className="rounded-2xl border border-slate-300/80 bg-white/70 px-4 py-3 text-sm outline-none transition focus:border-slate-900 dark:border-white/15 dark:bg-white/5 dark:focus:border-white/40"
        >
          <option value="">Select a completed document</option>
          {completedRecords.map((record) => (
            <option key={record.job_id} value={record.job_id}>
              {record.original_filename}
            </option>
          ))}
        </select>

        <select
          value={sourceType}
          onChange={(event) => setSourceType(event.target.value as SummarySource)}
          className="rounded-2xl border border-slate-300/80 bg-white/70 px-4 py-3 text-sm outline-none transition focus:border-slate-900 dark:border-white/15 dark:bg-white/5 dark:focus:border-white/40"
        >
          <option value="pdf">Analyze Original PDF</option>
          <option value="docx">Analyze Converted DOCX</option>
        </select>

        <select
          value={mode}
          onChange={(event) => setMode(event.target.value as SummaryMode)}
          className="rounded-2xl border border-slate-300/80 bg-white/70 px-4 py-3 text-sm outline-none transition focus:border-slate-900 dark:border-white/15 dark:bg-white/5 dark:focus:border-white/40"
        >
          <option value="extractive">Extractive Summary</option>
          <option value="abstractive">Abstractive Summary</option>
          <option value="bullet">Bullet Summary</option>
        </select>

        <select
          value={length}
          onChange={(event) => setLength(event.target.value as SummaryLength)}
          className="rounded-2xl border border-slate-300/80 bg-white/70 px-4 py-3 text-sm outline-none transition focus:border-slate-900 dark:border-white/15 dark:bg-white/5 dark:focus:border-white/40"
        >
          <option value="short">Short</option>
          <option value="medium">Medium</option>
          <option value="long">Long</option>
        </select>
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={!selectedJobId || loading}
          onClick={() => run(() => onGenerateSummary(selectedJobId, sourceType, mode, length))}
          className="rounded-full bg-gradient-to-r from-accent to-glow px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Working..." : "Generate Summary"}
        </button>
        <button
          type="button"
          disabled={!selectedJobId || loading}
          onClick={() => run(() => onLoadInsights(selectedJobId, sourceType))}
          className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold transition hover:border-slate-900 dark:border-white/15 dark:hover:border-white/40 disabled:opacity-50"
        >
          Analyze Document
        </button>
        {summary ? (
          <>
            <button
              type="button"
              disabled={loading}
              onClick={() => run(() => onExportSummary(summary.job_id, summary.source_type, summary.mode, summary.length, "txt"))}
              className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold transition hover:border-slate-900 dark:border-white/15 dark:hover:border-white/40 disabled:opacity-50"
            >
              Export TXT
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => run(() => onExportSummary(summary.job_id, summary.source_type, summary.mode, summary.length, "docx"))}
              className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold transition hover:border-slate-900 dark:border-white/15 dark:hover:border-white/40 disabled:opacity-50"
            >
              Export DOCX
            </button>
          </>
        ) : null}
      </div>

      {selected ? (
        <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">
          Active document: <span className="font-semibold">{selected.original_filename}</span>
        </p>
      ) : null}

      {summary ? (
        <div className="mt-6 rounded-3xl border border-slate-200/80 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold">Summary Preview</h3>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-200">
              {summary.mode}
            </span>
            {summary.used_fallback ? (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800 dark:bg-amber-500/20 dark:text-amber-200">
                Fallback Model
              </span>
            ) : null}
          </div>
          <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700 dark:text-slate-200">{summary.summary_text}</p>
          {summary.bullets.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {summary.bullets.map((bullet, index) => (
                <span
                  key={`${index}-${bullet}`}
                  className="rounded-full bg-slate-100 px-3 py-2 text-xs font-medium text-slate-700 dark:bg-white/10 dark:text-slate-200"
                >
                  {bullet}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {insights ? (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl border border-slate-200/80 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5">
            <h3 className="text-lg font-semibold">Keywords</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {insights.keywords.map((keyword) => (
                <span
                  key={keyword}
                  className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700 dark:bg-white/10 dark:text-slate-200"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5">
            <h3 className="text-lg font-semibold">Topics</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {insights.topics.map((topic) => (
                <span
                  key={topic}
                  className="rounded-full bg-emerald-100 px-3 py-2 text-xs font-semibold text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-200"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5">
            <h3 className="text-lg font-semibold">Sentiment</h3>
            <p className="mt-4 text-sm text-slate-700 dark:text-slate-200">
              {insights.sentiment_label} ({(insights.sentiment_score * 100).toFixed(1)}%)
            </p>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-white/70 p-5 dark:border-white/10 dark:bg-white/5">
            <h3 className="text-lg font-semibold">Classification</h3>
            <p className="mt-4 text-sm text-slate-700 dark:text-slate-200">
              {insights.classification_label} ({(insights.classification_score * 100).toFixed(1)}%)
            </p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
