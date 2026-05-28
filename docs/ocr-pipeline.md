# OCR Pipeline And Formatting Strategy

## OCR Detection Flow

1. The backend opens the PDF with PyMuPDF and pdfplumber.
2. For each page, it measures:
   - character count
   - word count
   - image density
   - page rotation
   - detected tables
   - likely column count
3. If the page has a healthy text layer, it is processed as native text.
4. If the page is image-dominant and text-poor, it is sent through Tesseract OCR.
5. Mixed documents use both strategies page-by-page.

## OCR Extraction Details

- Pages are rasterized from PyMuPDF at configurable DPI.
- Tesseract returns token-level coordinates through `image_to_data`.
- Tokens are regrouped into line blocks using `block_num`, `par_num`, and `line_num`.
- Those OCR lines are converted into the same normalized `ParagraphBlock` shape used by native text pages.

## Multi-Language Support

- OCR languages are controlled through `OCR_LANGUAGES`.
- Example values:
  - `eng`
  - `eng+hin`
  - `eng+deu+fra`

This makes multilingual OCR a deployment concern rather than a code rewrite.

## Formatting Preservation Strategy

### Paragraphs

- Use PyMuPDF span geometry and font metadata to preserve:
  - font size
  - font family
  - bold
  - italic
  - underline
  - alignment
  - line spacing
  - indentation
  - spacing before and after

### Tables

- Use pdfplumber table detection because its cell geometry is often more reliable than raw span grouping.
- Rebuild tables with `python-docx` using `Table Grid` and best-effort merged-cell heuristics.
- Empty-cell runs are collapsed into neighboring cells as a basic colspan inference strategy.

### Headers And Footers

- Text blocks near the top and bottom page bands are promoted into header and footer fields.
- The preview preserves them visually, and the DOCX builder places them into section headers/footers.

### Images

- Embedded image bytes are extracted with PyMuPDF and saved as reusable assets.
- The DOCX builder reinserts them with size derived from PDF bounding boxes.
- The preview uses the same persistent image assets for browser rendering.

### Columns

- Column count is inferred from word midpoint clustering.
- DOCX sections are configured with matching column counts using low-level OOXML helpers.

### Page Layout

- PDF page dimensions map into Word section width and height.
- Margins are configurable in the normalized layout layer.
- Each PDF page becomes a dedicated Word section to minimize page-break drift.

## Known Library Constraints

- Word does not support arbitrary PDF-like absolute text placement as precisely as a PDF renderer.
- `python-docx` cannot fully recreate every advanced PDF artifact such as layered transparency, irregular vector graphics, or all floating text behaviors.
- The architecture is designed to push fidelity as high as possible despite those format differences, with the best results on structured business PDFs, reports, contracts, and forms.
