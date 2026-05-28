from __future__ import annotations

from html import escape
from pathlib import Path

import fitz

from app.core.config import get_settings


class PreviewRenderer:
    """Render a faithful browser preview by rasterizing PDF pages to images."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def render(self, pdf_path: Path, output_path: Path, asset_dir: Path, job_id: str, source_name: str) -> None:
        image_tags: list[str] = []

        with fitz.open(pdf_path) as document:
            for page_index, page in enumerate(document, start=1):
                # A moderate zoom gives a crisp preview without making the HTML too heavy.
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(self.settings.preview_render_zoom, self.settings.preview_render_zoom),
                    alpha=False,
                )
                image_name = f"page_{page_index}.png"
                image_path = asset_dir / image_name
                pixmap.save(image_path)

                image_tags.append(
                    f"""
                    <figure class="page-shell">
                      <figcaption>Page {page_index}</figcaption>
                      <img
                        src="/api/v1/jobs/{job_id}/preview-assets/{image_name}"
                        alt="Preview page {page_index} for {escape(source_name)}"
                        loading="lazy"
                      />
                    </figure>
                    """
                )

        html = f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>{escape(source_name)} Preview</title>
          <style>
            body {{
              margin: 0;
              padding: 24px;
              background: #0f172a;
              color: #e2e8f0;
              font-family: Arial, sans-serif;
            }}
            .preview-stack {{
              max-width: 1200px;
              margin: 0 auto;
              display: grid;
              gap: 24px;
            }}
            .page-shell {{
              margin: 0;
              padding: 20px;
              background: rgba(255, 255, 255, 0.05);
              border-radius: 20px;
              box-shadow: 0 16px 40px rgba(2, 6, 23, 0.35);
            }}
            .page-shell figcaption {{
              margin-bottom: 12px;
              font-size: 14px;
              color: #cbd5e1;
            }}
            .page-shell img {{
              display: block;
              width: 100%;
              height: auto;
              background: white;
              border-radius: 12px;
            }}
          </style>
        </head>
        <body>
          <main class="preview-stack">
            {''.join(image_tags)}
          </main>
        </body>
        </html>
        """
        output_path.write_text(html, encoding="utf-8")
