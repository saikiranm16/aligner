from __future__ import annotations

import logging
from pathlib import Path

import fitz
import pdfplumber

logger = logging.getLogger(__name__)


class PdfDetector:
    """Classify PDFs and collect page-level clues used by downstream layout extraction."""

    def inspect_pdf(self, pdf_path: Path) -> dict:
        page_stats: list[dict] = []

        with fitz.open(pdf_path) as document, pdfplumber.open(pdf_path) as plumber_doc:
            for page_index, (page, plumber_page) in enumerate(zip(document, plumber_doc.pages), start=1):
                text_dict = page.get_text("dict")
                words = plumber_page.extract_words() or []
                images = [block for block in text_dict.get("blocks", []) if block.get("type") == 1]

                char_count = 0
                word_count = len(words)
                for block in text_dict.get("blocks", []):
                    if block.get("type") != 0:
                        continue
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            char_count += len(span.get("text", "").strip())

                page_area = max(page.rect.width * page.rect.height, 1)
                image_area = sum(
                    max((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 0)
                    for bbox in (block.get("bbox", [0, 0, 0, 0]) for block in images)
                )
                image_ratio = image_area / page_area

                try:
                    tables = plumber_page.find_tables()
                except Exception as exc:  # pragma: no cover - parser robustness
                    logger.warning("Table detection failed on page %s: %s", page_index, exc)
                    tables = []

                columns = self._estimate_columns(words, float(page.rect.width))
                has_text = char_count > 20 and word_count > 3
                scanned_like = not has_text and (image_ratio > 0.45 or len(images) > 0)

                page_stats.append(
                    {
                        "page_number": page_index,
                        "width": float(page.rect.width),
                        "height": float(page.rect.height),
                        "rotation": int(page.rotation),
                        "char_count": char_count,
                        "word_count": word_count,
                        "has_text": has_text,
                        "is_scanned": scanned_like,
                        "image_ratio": image_ratio,
                        "image_count": len(images),
                        "table_count": len(tables),
                        "columns": columns,
                    }
                )

        scanned_pages = sum(1 for item in page_stats if item["is_scanned"])
        text_pages = sum(1 for item in page_stats if item["has_text"])
        if scanned_pages == len(page_stats):
            mode = "scanned"
        elif scanned_pages > 0 and text_pages > 0:
            mode = "mixed"
        else:
            mode = "text"

        return {
            "mode": mode,
            "page_count": len(page_stats),
            "has_rotated_pages": any(item["rotation"] for item in page_stats),
            "has_columns": any(item["columns"] > 1 for item in page_stats),
            "has_tables": any(item["table_count"] > 0 for item in page_stats),
            "has_images": any(item["image_count"] > 0 for item in page_stats),
            "page_stats": page_stats,
        }

    @staticmethod
    def _estimate_columns(words: list[dict], page_width: float) -> int:
        """Infer one- vs two-column layout using word midpoint clusters."""

        if len(words) < 20:
            return 1

        midpoints = sorted(float(word["x0"] + word["x1"]) / 2 for word in words if "x0" in word and "x1" in word)
        if not midpoints:
            return 1

        largest_gap = 0.0
        split_index = 0
        for index in range(1, len(midpoints)):
            gap = midpoints[index] - midpoints[index - 1]
            if gap > largest_gap:
                largest_gap = gap
                split_index = index

        gap_threshold = page_width * 0.18
        if largest_gap < gap_threshold:
            return 1

        left_cluster = midpoints[:split_index]
        right_cluster = midpoints[split_index:]
        if not left_cluster or not right_cluster:
            return 1
        return 2

