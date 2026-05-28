# Deployment And Docker

## Environment Variables

### Backend

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | Human-readable service name |
| `APP_ENV` | Environment label such as `development` or `production` |
| `API_PREFIX` | Versioned API prefix |
| `MAX_FILE_SIZE_MB` | Per-file upload limit |
| `MAX_BATCH_SIZE` | Maximum PDFs per batch request |
| `JOB_RETENTION_HOURS` | Retention target for stored artifacts |
| `MAX_CONCURRENT_JOBS` | Local concurrency cap |
| `RATE_LIMIT_REQUESTS` | Maximum requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | Length of the API rate-limit window |
| `STORAGE_ROOT` | Root path for uploads, outputs, previews, temp files, and caches |
| `DATABASE_URL` | SQLAlchemy connection string |
| `OCR_LANGUAGES` | Tesseract language pack list |
| `OCR_DPI` | Rasterization DPI for OCR |
| `ENABLE_LAYOUT_REFINER` | Enable heuristic refinement |
| `PREVIEW_RENDER_ZOOM` | Preview rasterization zoom factor |
| `CORS_ORIGINS` | Allowed frontend origins |
| `TESSERACT_CMD` | Optional explicit Tesseract binary path |
| `AUTH_SECRET_KEY` | Token signing secret |
| `AUTH_TOKEN_EXPIRY_MINUTES` | Bearer token lifetime |
| `ENABLE_MALWARE_SCAN` | Enable upload security scanning |
| `CLAMAV_HOST` | Optional ClamAV host |
| `CLAMAV_PORT` | Optional ClamAV port |
| `SUMMARY_DEFAULT_MODEL` | Default HuggingFace summary model |
| `CLASSIFICATION_DEFAULT_MODEL` | Default zero-shot classification model |
| `SENTIMENT_DEFAULT_MODEL` | Default sentiment model |
| `AI_CACHE_TTL_MINUTES` | Cache TTL for AI outputs |
| `ENABLE_TRANSFORMERS` | Enable transformer-backed AI services |

### Frontend

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Base URL for the FastAPI service |
| `VITE_MAX_FILE_SIZE_MB` | Client-side validation limit |

## Docker Setup

### Backend Container

- Uses `python:3.12-slim`.
- Installs Tesseract OCR and English language data.
- Exposes FastAPI on port `8000`.
- Creates persistent directories for uploads, outputs, previews, summaries, cache, and temp assets.

### Frontend Container

- Uses a multi-stage build with `node:20-alpine`.
- Compiles the Vite app into static assets.
- Serves the build through Nginx on port `80`.

## Docker Compose

Run:

```bash
docker compose up --build
```

Services:

- `backend`: `http://localhost:8000`
- `frontend`: `http://localhost:3000`

## Production Deployment Steps

1. Build the images and publish them to your registry.
2. Provision persistent storage for `backend/data`.
3. Point `DATABASE_URL` to PostgreSQL for multi-instance deployments.
4. Use S3, Azure Blob, or GCS for document storage when scaling beyond a single node.
5. Put the frontend and backend behind an HTTPS reverse proxy.
6. Install all required Tesseract language packs for your target regions.
7. Install HuggingFace model dependencies in production if you want abstractive summarization and zero-shot classification enabled without heuristic fallback.
8. Add observability, audit logging, and alerting before public exposure.

## Enterprise Hardening Recommendations

- Add SSO or external identity integration if this moves into a multi-user production environment.
- Scan uploaded files with a live malware engine such as ClamAV when `ENABLE_MALWARE_SCAN=true`.
- Enforce tenant isolation in database and storage paths.
- Encrypt persisted files at rest.
- Add API gateway or WAF controls for internet-facing deployments.
