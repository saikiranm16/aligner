import { DragEvent, useRef, useState } from "react";

interface UploadDropzoneProps {
  files: File[];
  maxSizeMb: number;
  onFilesSelected: (files: File[]) => void;
  onClear: () => void;
}

export function UploadDropzone({ files, maxSizeMb, onFilesSelected, onClear }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (selected: FileList | null) => {
    if (!selected) {
      return;
    }
    onFilesSelected(Array.from(selected));
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  };

  return (
    <section className="panel p-6 lg:p-8">
      <div
        onDrop={onDrop}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        className={`rounded-[2rem] border-2 border-dashed p-8 text-center transition ${
          isDragging
            ? "border-accent bg-emerald-50/80 dark:bg-emerald-950/20"
            : "border-slate-300/80 bg-white/50 dark:border-white/15 dark:bg-white/5"
        }`}
      >
        <p className="text-lg font-semibold">Drop one or more PDF files here</p>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Text-based and scanned PDFs are supported. Max size: {maxSizeMb} MB per file.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            Choose PDFs
          </button>
          <button
            type="button"
            onClick={onClear}
            className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-900 dark:border-white/15 dark:text-slate-100 dark:hover:border-white/40"
          >
            Clear Queue
          </button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      <div className="mt-6 space-y-3">
        {files.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No files selected yet.</p>
        ) : (
          files.map((file) => (
            <div
              key={`${file.name}-${file.size}`}
              className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-white/5"
            >
              <div>
                <p className="font-medium">{file.name}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-white/10 dark:text-slate-200">
                Ready
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

