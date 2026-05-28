from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

import fitz
import pytesseract
from PIL import Image, ImageFilter, ImageOps
from pytesseract import Output

from app.core.config import get_settings
from app.schemas.jobs import PageLayout, ParagraphBlock, SpanStyle, TextSpan

logger = logging.getLogger(__name__)


class OcrService:
    """Extract text from scanned pages using Tesseract while keeping coarse geometry."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if self.settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_cmd

    def extract_page(self, page: fitz.Page, page_stats: dict, temp_dir: Path) -> PageLayout:
        zoom = self.settings.ocr_dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = temp_dir / f"ocr_page_{page_stats['page_number']}.png"
        pixmap.save(image_path)

        image = self._prepare_image(Image.open(image_path))
        data = pytesseract.image_to_data(
            image,
            lang=self.settings.ocr_languages,
            config="--oem 3 --psm 1",
            output_type=Output.DICT,
        )

        grouped: dict[tuple[int, int, int], list[dict]] = defaultdict(list)
        total = len(data.get("text", []))
        for index in range(total):
            text = (data["text"][index] or "").strip()
            conf_raw = data.get("conf", ["-1"] * total)[index]
            try:
                confidence = float(conf_raw)
            except (TypeError, ValueError):
                confidence = -1
            if not text or confidence < 0:
                continue

            key = (
                int(data["block_num"][index]),
                int(data["par_num"][index]),
                int(data["line_num"][index]),
            )
            grouped[key].append(
                {
                    "text": text,
                    "left": int(data["left"][index]),
                    "top": int(data["top"][index]),
                    "width": int(data["width"][index]),
                    "height": int(data["height"][index]),
                }
            )

        blocks: list[ParagraphBlock] = []
        scale = 72 / self.settings.ocr_dpi
        for words in grouped.values():
            words = sorted(words, key=lambda item: item["left"])
            text = " ".join(item["text"] for item in words).strip()
            if not text:
                continue

            x0 = min(item["left"] for item in words) * scale
            y0 = min(item["top"] for item in words) * scale
            x1 = max(item["left"] + item["width"] for item in words) * scale
            y1 = max(item["top"] + item["height"] for item in words) * scale

            kind, list_type = self._classify_list(text)
            font_size = max((item["height"] for item in words), default=14) * scale
            blocks.append(
                ParagraphBlock(
                    kind=kind,
                    bbox=[x0, y0, x1, y1],
                    spans=[
                        TextSpan(
                            text=text,
                            bbox=[x0, y0, x1, y1],
                            style=SpanStyle(font_size=font_size, font_name="Calibri"),
                        )
                    ],
                    line_spacing=1.15,
                    list_level=0,
                    list_type=list_type,
                )
            )

        blocks.sort(key=lambda block: (block.bbox[1], block.bbox[0]))
        return PageLayout(
            page_number=page_stats["page_number"],
            width=page_stats["width"],
            height=page_stats["height"],
            rotation=page_stats["rotation"],
            columns=page_stats["columns"],
            blocks=blocks,
        )

    @staticmethod
    def _classify_list(text: str) -> tuple[str, str]:
        bullets = ("•", "-", "*", "o")
        if text.startswith(bullets):
            return "list", "bullet"
        if len(text) > 2 and text[0].isdigit() and text[1] in ").":
            return "list", "number"
        return "paragraph", "none"

    def _prepare_image(self, image: Image.Image) -> Image.Image:
        """Enhance scans before OCR to reduce noise and straighten orientation."""

        processed = ImageOps.grayscale(image)
        processed = ImageOps.autocontrast(processed)
        processed = processed.filter(ImageFilter.MedianFilter(size=3))
        processed = processed.filter(ImageFilter.SHARPEN)
        processed = self._deskew(processed)
        processed = processed.point(lambda pixel: 255 if pixel > 155 else 0)
        return processed

    def _deskew(self, image: Image.Image) -> Image.Image:
        try:
            osd = pytesseract.image_to_osd(image)
            rotation_line = next((line for line in osd.splitlines() if line.lower().startswith("rotate:")), "")
            rotation = int(rotation_line.split(":", 1)[1].strip()) if rotation_line else 0
            if rotation:
                return image.rotate(-rotation, expand=True, fillcolor=255)
        except Exception:
            return image
        return image
