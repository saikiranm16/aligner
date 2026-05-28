interface PreviewPanelProps {
  previewUrl: string | null;
}

export function PreviewPanel({ previewUrl }: PreviewPanelProps) {
  return (
    <section className="panel flex min-h-[32rem] flex-col overflow-hidden">
      <div className="border-b border-slate-200/80 px-6 py-4 dark:border-white/10">
        <h2 className="text-xl font-semibold">Document Preview</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Review the reconstructed layout before downloading the final DOCX.
        </p>
      </div>

      {previewUrl ? (
        <iframe
          title="document-preview"
          src={previewUrl}
          className="min-h-[30rem] w-full flex-1 bg-slate-100 dark:bg-slate-950"
        />
      ) : (
        <div className="flex flex-1 items-center justify-center px-8 text-center text-sm text-slate-500 dark:text-slate-400">
          Choose a completed job or history item to inspect its reconstructed layout preview.
        </div>
      )}
    </section>
  );
}

