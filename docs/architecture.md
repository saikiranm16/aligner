# AlignPDF Architecture

## System Overview

`AlignPDF` combines a React frontend with a FastAPI backend, an asynchronous conversion pipeline, optional bearer-token authentication, and an AI document-intelligence layer.

```text
Browser UI
  -> Upload / Poll / Preview / Download / Summary / Analysis
React + Tailwind
  -> REST API + Auth
FastAPI
  -> Job Manager + Background Tasks
  -> Rate Limiter
  -> Secure Upload Validation
  -> Auth Service
  -> PDF Detector
  -> Layout Analyzer
  -> OCR Service
  -> Layout Refiner
  -> DOCX Builder
  -> Preview Renderer
  -> Document Intelligence
  -> Dashboard Service
  -> SQLite History + Local Storage
```

## Major Architectural Decisions

### 1. Normalized Layout Model Between Extraction And DOCX Generation

- PDF extraction output is noisy and library-specific.
- `python-docx` needs a stable representation of paragraphs, tables, images, page geometry, and spacing.
- The normalized layout model keeps extraction and Word generation loosely coupled.

### 2. Native Text First, OCR Only Where Needed

- Text-based PDFs preserve font and coordinate data better than OCR.
- Scanned and mixed PDFs still need a fallback.
- Detection happens per page so mixed documents are handled accurately.

### 3. Async Job Flow For Heavy Document Work

- PDF analysis, OCR, and DOCX generation are expensive.
- Jobs are tracked in memory for live progress and persisted in SQLite for history and retries.
- The same pattern can later move to Redis-backed workers.

### 4. Faithful Preview As Rendered PDF Pages

- Browser DOCX preview is inconsistent.
- The current preview path rasterizes original PDF pages for visual verification.
- This gives users a more trustworthy review surface than a rough HTML reconstruction.

### 5. Optional Auth And Security Layers

- Backward compatibility matters, so the app still works without mandatory login.
- Security-sensitive deployments can use bearer-token auth, rate limiting, stronger upload validation, and optional malware scanner connectivity.
- This keeps the core conversion flow stable while allowing the platform to mature.

### 6. AI Services Separated From Conversion Core

- Summaries, keywords, sentiment, classification, and export logic live outside the conversion pipeline.
- Transformer-backed features can evolve independently from PDF fidelity work.
- Heuristic fallbacks keep the platform functional even when large models are unavailable.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Root service liveness |
| `GET` | `/api/v1/health` | API-scoped liveness |
| `POST` | `/api/v1/auth/register` | Create an account |
| `POST` | `/api/v1/auth/login` | Sign in and receive a bearer token |
| `GET` | `/api/v1/auth/me` | Retrieve the current user profile |
| `POST` | `/api/v1/jobs` | Create one conversion job |
| `POST` | `/api/v1/jobs/batch` | Create batch conversion jobs |
| `GET` | `/api/v1/jobs/{job_id}` | Poll job status and progress |
| `POST` | `/api/v1/jobs/{job_id}/retry` | Retry a failed or previous job |
| `GET` | `/api/v1/jobs/{job_id}/download` | Download output DOCX |
| `GET` | `/api/v1/jobs/{job_id}/preview` | Load preview HTML |
| `GET` | `/api/v1/jobs/{job_id}/preview-assets/{asset_name}` | Fetch preview page images |
| `POST` | `/api/v1/jobs/{job_id}/summary` | Generate a PDF or DOCX summary |
| `GET` | `/api/v1/jobs/{job_id}/summary/export` | Export a summary as TXT or DOCX |
| `GET` | `/api/v1/jobs/{job_id}/insights` | Retrieve keywords, topics, sentiment, and classification |
| `GET` | `/api/v1/dashboard` | Retrieve dashboard metrics |
| `GET` | `/api/v1/history` | Retrieve conversion history |

## Scalability Notes

- Replace the in-memory queue with Redis + worker processes for multi-instance scale.
- Move uploads, outputs, and previews to S3 or Blob storage for stateless deployments.
- Replace SQLite with PostgreSQL once concurrency and tenancy requirements grow.
- Persist AI caches in Redis if the summarization workload becomes significant.
