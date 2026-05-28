# Performance, Accuracy, And Error Handling

## Performance Optimization Techniques

### CPU And Concurrency

- Limit active conversions with `MAX_CONCURRENT_JOBS` so OCR-heavy loads do not overwhelm the server.
- Use background tasks and `asyncio.to_thread` for CPU-heavy extraction work.
- Cache summaries and document insights to avoid repeated model execution.

### File Handling

- Stream uploads to disk instead of buffering them fully in memory.
- Persist output and preview artifacts separately so retries and downloads avoid recomputation.
- Keep temporary OCR assets isolated per job for easier cleanup.

### Extraction Strategy

- Skip OCR for text-native pages.
- Perform OCR only on scanned pages inside mixed documents.
- Use PDF-native coordinates wherever possible because they are usually faster and more accurate than OCR geometry.

### Future Optimizations

- Cache page classification results for repeated documents.
- Parallelize page extraction inside worker processes for large PDFs.
- Introduce adaptive OCR DPI based on source resolution and text density.
- Add learned table-structure and reading-order reconstruction.
- Replace the in-process queue with Redis-backed workers for true horizontal scale.

## Error Handling Logic

### Backend

- Upload validation rejects non-PDF files, invalid PDF signatures, oversized payloads, and encrypted documents.
- Rate limiting protects the API from burst abuse.
- Optional auth protects dashboard and document-management workflows without breaking backward compatibility.
- Conversion jobs move through explicit states such as `queued`, `analyzing`, `ocr`, `building`, `completed`, and `failed`.
- Exceptions during conversion are persisted in history and surfaced to the UI.
- Preview and download endpoints return `404` when assets are missing instead of failing ambiguously.

### Frontend

- Client-side file validation catches obvious mistakes before upload.
- Polling continues until terminal states are reached.
- Failed jobs expose a retry action.
- Summary, insight, preview, and download actions surface clear error messages.

## Accuracy Strategy

The current implementation targets high fidelity through:

- page-by-page mode detection
- span-level font extraction
- OCR image enhancement and deskewing
- section-level page geometry
- column inference
- table extraction via pdfplumber
- faithful preview rendering from original PDF pages
- refinement heuristics before DOCX generation

For the 90-95% fidelity target, the strongest gains in real production use usually come from:

1. collecting representative PDFs from the target business domain
2. tuning table extraction and reading-order heuristics on those samples
3. plugging in a stronger learned layout reconstructor for edge cases
4. comparing source PDF renders against DOCX round-trip renders in regression tests
