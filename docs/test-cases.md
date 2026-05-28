# Sample Test Cases

## Functional Cases

1. Text-based annual report PDF
   - Expected: paragraph alignment, headings, bold emphasis, page breaks, and embedded charts remain readable and close to source layout.

2. Scanned invoice PDF
   - Expected: OCR activates automatically, invoice tables are reconstructed, and headers/footers remain present.

3. Mixed PDF with scanned appendix
   - Expected: native text pages avoid OCR, scanned appendix pages use OCR, and final DOCX stays in one output file.

4. Two-column research paper
   - Expected: column detection is applied per page and section layout uses multiple columns.

5. Rotated landscape spreadsheet export
   - Expected: page rotation is detected and the page dimensions in Word reflect the source orientation as closely as Word permits.

6. Complex table with visually merged cells
   - Expected: table grid remains readable, colspan heuristics preserve structure where possible, and borders remain visible.

7. Nested bullet and numbered list PDF
   - Expected: list paragraphs remain lists in DOCX and indentation hierarchy is mostly retained.

8. Image-heavy brochure
   - Expected: images are extracted, reinserted, and previewable before download.

9. Batch upload of five PDFs
   - Expected: jobs queue asynchronously, progress is individually visible, and history records all results.

10. Oversized file upload
    - Expected: upload is rejected with a clear message before conversion is queued.

## Error Handling Cases

1. Corrupted PDF bytes
   - Expected: job moves to `failed`, error is surfaced in UI, and retry remains available if the stored source is intact.

2. Missing Tesseract binary in a custom deployment
   - Expected: OCR jobs fail with a diagnostic error, but text-based PDFs still process successfully.

3. Preview asset missing on disk
   - Expected: preview returns a 404 for the missing asset rather than crashing the whole job history endpoint.

4. DOCX output path unavailable
   - Expected: conversion is marked failed and the failure is recorded in persistent history.

## Suggested Automated Test Expansion

- Add API tests for `/jobs`, `/jobs/{job_id}`, `/retry`, `/history`.
- Add fixture PDFs for each major document pattern.
- Add visual regression scoring by comparing PDF page renders against DOCX-to-PDF output renders.
- Add benchmark tests for OCR pages per minute and DOCX output latency.
