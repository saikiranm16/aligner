import { DashboardStatsResponse } from "../types";

interface DashboardOverviewProps {
  stats: DashboardStatsResponse | null;
}

function metric(label: string, value: string | number) {
  return (
    <div className="rounded-3xl border border-slate-200/80 bg-white/70 p-4 dark:border-white/10 dark:bg-white/5">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-3 text-3xl font-black tracking-tight">{value}</p>
    </div>
  );
}

export function DashboardOverview({ stats }: DashboardOverviewProps) {
  return (
    <section className="panel p-6">
      <div>
        <h2 className="text-xl font-semibold">AlignPDF Dashboard</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Live snapshot of conversion throughput, reliability, and document volume.
        </p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {metric("Total Jobs", stats?.total_jobs ?? 0)}
        {metric("Completed", stats?.completed_jobs ?? 0)}
        {metric("Failed", stats?.failed_jobs ?? 0)}
        {metric("Queued", stats?.queued_jobs ?? 0)}
        {metric("Pages Processed", stats?.total_pages_processed ?? 0)}
        {metric("Avg Output Size", `${(((stats?.average_output_size_bytes ?? 0) / 1024 / 1024) || 0).toFixed(2)} MB`)}
      </div>

      {stats?.latest_job_filename ? (
        <p className="mt-5 text-sm text-slate-600 dark:text-slate-300">
          Latest processed file: <span className="font-semibold">{stats.latest_job_filename}</span>
        </p>
      ) : null}
    </section>
  );
}
