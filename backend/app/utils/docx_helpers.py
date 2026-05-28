from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.section import Section


ALIGNMENT_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def set_section_columns(section: Section, count: int) -> None:
    """Set the number of columns on a section using low-level OOXML."""

    sect_pr = section._sectPr
    cols = sect_pr.xpath("./w:cols")
    cols_el = cols[0] if cols else OxmlElement("w:cols")
    cols_el.set(qn("w:num"), str(max(1, count)))
    if not cols:
        sect_pr.append(cols_el)


def ensure_continuous_section(section: Section) -> None:
    """Keep new sections continuous so column changes do not always force a new page."""

    type_el = section._sectPr.xpath("./w:type")
    target = type_el[0] if type_el else OxmlElement("w:type")
    target.set(qn("w:val"), WD_SECTION_START.CONTINUOUS)
    if not type_el:
        section._sectPr.append(target)

