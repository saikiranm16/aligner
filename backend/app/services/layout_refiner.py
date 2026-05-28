from __future__ import annotations

from app.schemas.jobs import PageLayout, ParagraphBlock, PdfAnalysis


class LayoutRefiner:
    """Apply heuristics that smooth extraction artifacts before DOCX generation."""

    def refine(self, analysis: PdfAnalysis) -> PdfAnalysis:
        refined_pages: list[PageLayout] = []
        for page in analysis.pages:
            refined_pages.append(self._refine_page(page))
        analysis.pages = refined_pages
        return analysis

    def _refine_page(self, page: PageLayout) -> PageLayout:
        merged_blocks = []
        pending: ParagraphBlock | None = None

        for block in sorted(page.blocks, key=lambda item: (item.bbox[1], item.bbox[0])):
            if isinstance(block, ParagraphBlock) and pending and block.kind == "paragraph" and pending.kind == "paragraph":
                close_vertically = abs(block.bbox[1] - pending.bbox[3]) < 8
                similar_indent = abs(block.left_indent - pending.left_indent) < 6
                if close_vertically and similar_indent:
                    pending.spans.extend(block.spans)
                    pending.bbox[2] = max(pending.bbox[2], block.bbox[2])
                    pending.bbox[3] = max(pending.bbox[3], block.bbox[3])
                    pending.space_after = max(pending.space_after, block.space_after)
                    continue

            if pending:
                merged_blocks.append(pending)
            pending = block if isinstance(block, ParagraphBlock) else None
            if not isinstance(block, ParagraphBlock):
                merged_blocks.append(block)

        if pending:
            merged_blocks.append(pending)

        page.blocks = merged_blocks
        return page

