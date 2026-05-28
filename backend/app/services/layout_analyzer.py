from __future__ import annotations

import logging
from pathlib import Path

import fitz
import pdfplumber

from app.schemas.jobs import ImageBlock, PageLayout, ParagraphBlock, PdfAnalysis, SpanStyle, TableBlock, TableCellLayout, TextSpan
from app.services.ocr_service import OcrService

logger = logging.getLogger(__name__)


class LayoutAnalyzer:
    """Build a normalized page layout model from text PDFs and OCR output."""

    def __init__(self, ocr_service: OcrService) -> None:
        self.ocr_service = ocr_service

    def extract_layout(self, pdf_path: Path, detection: dict, temp_dir: Path, file_name: str, languages: str) -> PdfAnalysis:
        page_layouts: list[PageLayout] = []

        with fitz.open(pdf_path) as document, pdfplumber.open(pdf_path) as plumber_doc:
            for page_index, (page, plumber_page) in enumerate(zip(document, plumber_doc.pages), start=1):
                page_stats = detection["page_stats"][page_index - 1]
                if page_stats["is_scanned"]:
                    page_layouts.append(self.ocr_service.extract_page(page, page_stats, temp_dir))
                    continue

                table_bboxes, tables = self._extract_tables(plumber_page)
                text_blocks = self._extract_text_blocks(page, page_stats, table_bboxes)
                image_blocks = self._extract_images(page, temp_dir, page_index)
                blocks = sorted([*text_blocks, *tables, *image_blocks], key=lambda block: (block.bbox[1], block.bbox[0]))

                header_text, footer_text = self._extract_header_footer(text_blocks, page.rect.height)
                page_layouts.append(
                    PageLayout(
                        page_number=page_index,
                        width=float(page.rect.width),
                        height=float(page.rect.height),
                        rotation=int(page.rotation),
                        columns=page_stats["columns"],
                        header_text=header_text,
                        footer_text=footer_text,
                        blocks=blocks,
                    )
                )

        return PdfAnalysis(
            file_name=file_name,
            page_count=detection["page_count"],
            mode=detection["mode"],
            languages=languages,
            has_rotated_pages=detection["has_rotated_pages"],
            has_columns=detection["has_columns"],
            has_tables=detection["has_tables"],
            has_images=detection["has_images"],
            pages=page_layouts,
        )

    def _extract_text_blocks(self, page: fitz.Page, page_stats: dict, table_bboxes: list[list[float]]) -> list[ParagraphBlock]:
        blocks: list[ParagraphBlock] = []
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            bbox = [float(value) for value in block.get("bbox", [0, 0, 0, 0])]
            if self._intersects_table(bbox, table_bboxes):
                continue

            spans: list[TextSpan] = []
            line_heights: list[float] = []
            text_fragments: list[str] = []
            for line in block.get("lines", []):
                line_bbox = line.get("bbox", bbox)
                line_heights.append(float(line_bbox[3] - line_bbox[1]))
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if not span_text.strip():
                        continue
                    text_fragments.append(span_text)
                    color = span.get("color")
                    hex_color = f"{color:06x}" if isinstance(color, int) else None
                    spans.append(
                        TextSpan(
                            text=span_text,
                            bbox=[float(value) for value in span.get("bbox", bbox)],
                            style=SpanStyle(
                                font_name=span.get("font", "Calibri"),
                                font_size=float(span.get("size", 11)),
                                bold="bold" in span.get("font", "").lower() or bool(span.get("flags", 0) & 16),
                                italic="italic" in span.get("font", "").lower() or bool(span.get("flags", 0) & 2),
                                underline=bool(span.get("flags", 0) & 1),
                                color=hex_color,
                            ),
                        )
                    )

            text = " ".join(fragment.strip() for fragment in text_fragments if fragment.strip())
            if not text or not spans:
                continue

            kind, list_type = self._classify_list(text)
            font_size = spans[0].style.font_size
            line_spacing = max((sum(line_heights) / max(len(line_heights), 1)) / max(font_size, 1), 1.0)
            blocks.append(
                ParagraphBlock(
                    kind=kind,
                    bbox=bbox,
                    spans=spans,
                    alignment=self._infer_alignment(bbox, page_stats["width"]),
                    line_spacing=line_spacing,
                    left_indent=bbox[0],
                    first_line_indent=0.0,
                    space_before=2.0,
                    space_after=3.0,
                    list_level=self._infer_list_level(bbox[0], page_stats["width"]),
                    list_type=list_type,
                )
            )
        return blocks

    def _extract_tables(self, plumber_page) -> tuple[list[list[float]], list[TableBlock]]:
        tables: list[TableBlock] = []
        table_bboxes: list[list[float]] = []
        try:
            raw_tables = plumber_page.find_tables()
        except Exception as exc:  # pragma: no cover - parser robustness
            logger.warning("pdfplumber table parsing failed: %s", exc)
            raw_tables = []

        for table in raw_tables:
            extracted = table.extract()
            if not extracted:
                continue

            normalized_rows: list[list[TableCellLayout]] = []
            for row in extracted:
                row_layout: list[TableCellLayout] = []
                for cell in row:
                    cell_text = (cell or "").strip()
                    row_layout.append(TableCellLayout(text=cell_text))
                normalized_rows.append(self._apply_colspan_heuristic(row_layout))

            bbox = [float(table.bbox[0]), float(table.bbox[1]), float(table.bbox[2]), float(table.bbox[3])]
            table_bboxes.append(bbox)
            tables.append(TableBlock(bbox=bbox, rows=normalized_rows))

        return table_bboxes, tables

    def _extract_images(self, page: fitz.Page, temp_dir: Path, page_number: int) -> list[ImageBlock]:
        images: list[ImageBlock] = []
        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = image_info[0]
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            base_image = page.parent.extract_image(xref)
            image_bytes = base_image.get("image")
            if not image_bytes:
                continue
            ext = base_image.get("ext", "png")
            image_path = temp_dir / f"page_{page_number}_img_{image_index}.{ext}"
            image_path.write_bytes(image_bytes)
            rect = rects[0]
            images.append(
                ImageBlock(
                    bbox=[float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)],
                    image_path=str(image_path),
                    width_px=base_image.get("width", 0),
                    height_px=base_image.get("height", 0),
                )
            )
        return images

    @staticmethod
    def _apply_colspan_heuristic(row: list[TableCellLayout]) -> list[TableCellLayout]:
        """Merge runs of empty cells into the previous populated cell as a best-effort colspan guess."""

        result: list[TableCellLayout] = []
        for cell in row:
            if cell.text or not result:
                result.append(cell)
                continue
            result[-1].col_span += 1
        return result

    @staticmethod
    def _extract_header_footer(blocks: list[ParagraphBlock], page_height: float) -> tuple[str, str]:
        header = " ".join(span.text for block in blocks if block.bbox[1] < page_height * 0.08 for span in block.spans).strip()
        footer = " ".join(span.text for block in blocks if block.bbox[3] > page_height * 0.92 for span in block.spans).strip()
        return header[:255], footer[:255]

    @staticmethod
    def _infer_alignment(bbox: list[float], page_width: float) -> str:
        left_gap = bbox[0]
        right_gap = page_width - bbox[2]
        center_shift = abs(left_gap - right_gap)
        if center_shift < page_width * 0.05:
            return "center"
        if left_gap > page_width * 0.45:
            return "right"
        return "left"

    @staticmethod
    def _classify_list(text: str) -> tuple[str, str]:
        stripped = text.strip()
        if stripped.startswith(("•", "-", "*", "o")):
            return "list", "bullet"
        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ").":
            return "list", "number"
        return "paragraph", "none"

    @staticmethod
    def _infer_list_level(x0: float, page_width: float) -> int:
        indent_unit = max(page_width / 12, 1)
        return max(int(x0 // indent_unit) - 1, 0)

    @staticmethod
    def _intersects_table(bbox: list[float], table_bboxes: list[list[float]]) -> bool:
        for table_bbox in table_bboxes:
            horizontal = min(bbox[2], table_bbox[2]) - max(bbox[0], table_bbox[0])
            vertical = min(bbox[3], table_bbox[3]) - max(bbox[1], table_bbox[1])
            if horizontal > 0 and vertical > 0:
                return True
        return False
