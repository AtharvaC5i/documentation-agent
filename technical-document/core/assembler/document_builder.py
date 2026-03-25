import os
from pathlib import Path
from datetime import date
from typing import List, Dict, Any
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT
import re
import copy

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join("..", "storage"))

# ─────────────────────────────────────────────────────────────
# DESIGN TOKENS — Single source of truth for all visual values
# ─────────────────────────────────────────────────────────────

class DesignTokens:
    # Brand palette
    COLOR_INK           = RGBColor(0x0F, 0x0F, 0x1A)   # Near-black for body text
    COLOR_HEADING       = RGBColor(0x0D, 0x1B, 0x3E)   # Deep navy for headings
    COLOR_ACCENT        = RGBColor(0x1A, 0x56, 0xDB)   # Corporate blue for accents
    COLOR_ACCENT_LIGHT  = RGBColor(0xE8, 0xF0, 0xFF)   # Tinted blue for table headers
    COLOR_MUTED         = RGBColor(0x5A, 0x5A, 0x72)   # Muted gray for metadata text
    COLOR_RULE          = RGBColor(0xD0, 0xD8, 0xF0)   # Subtle blue-gray rule lines
    COLOR_CODE_BG       = RGBColor(0xF5, 0xF7, 0xFF)   # Code block background
    COLOR_CODE_TEXT     = RGBColor(0x1E, 0x3A, 0x8A)   # Code text (dark blue)
    COLOR_TABLE_STRIPE  = RGBColor(0xF8, 0xF9, 0xFF)   # Alternating row tint
    COLOR_WHITE         = RGBColor(0xFF, 0xFF, 0xFF)

    # Typography scale
    FONT_BODY           = "Calibri"
    FONT_HEADING        = "Calibri"
    FONT_MONO           = "Consolas"

    SIZE_DISPLAY        = Pt(32)    # Title page main title
    SIZE_SUBTITLE       = Pt(13)    # Title page subtitle
    SIZE_H1             = Pt(16)    # Section heading
    SIZE_H2             = Pt(13)    # Sub-section heading
    SIZE_H3             = Pt(11)    # Sub-sub-section heading
    SIZE_BODY           = Pt(10.5)  # Body text
    SIZE_CAPTION        = Pt(9)     # Captions, footer, metadata
    SIZE_CODE           = Pt(9)     # Monospace code

    # Spacing (in Pt — used for paragraph spacing)
    SPACE_BEFORE_H1     = Pt(18)
    SPACE_AFTER_H1      = Pt(6)
    SPACE_BEFORE_H2     = Pt(14)
    SPACE_AFTER_H2      = Pt(4)
    SPACE_BEFORE_H3     = Pt(10)
    SPACE_AFTER_H3      = Pt(3)
    SPACE_AFTER_BODY    = Pt(6)
    LINE_SPACING_BODY   = Pt(15)    # 1.43× leading for 10.5pt body

    # Margins
    MARGIN_TOP          = Cm(2.8)
    MARGIN_BOTTOM       = Cm(2.8)
    MARGIN_LEFT         = Cm(3.0)
    MARGIN_RIGHT        = Cm(2.5)


T = DesignTokens  # shorthand alias


# ─────────────────────────────────────────────────────────────
# LOW-LEVEL XML HELPERS
# ─────────────────────────────────────────────────────────────

def _set_cell_shading(cell, fill_hex: str):
    """Apply background fill to a table cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tcPr.append(shd)


def _set_paragraph_shading(paragraph, fill_hex: str):
    """Apply background fill to a paragraph (used for code blocks)."""
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    pPr.append(shd)


def _set_cell_border(cell, sides: dict):
    """
    Apply borders to specific sides of a cell.
    sides: e.g. {'bottom': {'sz': '4', 'val': 'single', 'color': '1A56DB'}}
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side, attrs in sides.items():
        border_el = OxmlElement(f"w:{side}")
        border_el.set(qn("w:val"), attrs.get("val", "single"))
        border_el.set(qn("w:sz"), attrs.get("sz", "4"))
        border_el.set(qn("w:space"), "0")
        border_el.set(qn("w:color"), attrs.get("color", "000000"))
        tcBorders.append(border_el)
    tcPr.append(tcBorders)


def _remove_table_borders(table):
    """Remove all internal and external borders from a table element."""
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    tblBorders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "none")
        tblBorders.append(el)
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None:
        tblPr.remove(existing)
    tblPr.append(tblBorders)


def _add_horizontal_rule(doc: Document, color_hex: str = "D0D8F0", thickness: str = "4"):
    """Insert a full-width horizontal rule paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), thickness)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)


def _add_page_number(paragraph):
    """Insert a PAGE field code into a paragraph run."""
    run = paragraph.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.text = "PAGE"
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def _add_numpages_field(paragraph):
    """Insert NUMPAGES field for 'Page X of N' footers."""
    run = paragraph.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.text = "NUMPAGES"
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def _add_toc(doc: Document):
    """Insert a TOC field that Word regenerates on open."""
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run()
    fldChar = OxmlElement("w:fldChar")
    fldChar.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "separate")
    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)


# ─────────────────────────────────────────────────────────────
# DOCUMENT-LEVEL SETUP
# ─────────────────────────────────────────────────────────────

def _configure_margins(doc: Document):
    for section in doc.sections:
        section.top_margin    = T.MARGIN_TOP
        section.bottom_margin = T.MARGIN_BOTTOM
        section.left_margin   = T.MARGIN_LEFT
        section.right_margin  = T.MARGIN_RIGHT


def _apply_base_styles(doc: Document):
    """
    Override the document's built-in styles so every paragraph
    rendered through doc.add_paragraph() / doc.add_heading()
    inherits the correct defaults without per-run overrides.
    """
    styles = doc.styles

    # Normal (body) style
    normal = styles["Normal"]
    normal.font.name        = T.FONT_BODY
    normal.font.size        = T.SIZE_BODY
    normal.font.color.rgb   = T.COLOR_INK
    normal.paragraph_format.space_after  = T.SPACE_AFTER_BODY
    normal.paragraph_format.line_spacing = T.LINE_SPACING_BODY

    # Heading 1
    h1 = styles["Heading 1"]
    h1.font.name        = T.FONT_HEADING
    h1.font.size        = T.SIZE_H1
    h1.font.bold        = True
    h1.font.color.rgb   = T.COLOR_HEADING
    h1.font.underline   = False
    h1.paragraph_format.space_before    = T.SPACE_BEFORE_H1
    h1.paragraph_format.space_after     = T.SPACE_AFTER_H1
    h1.paragraph_format.keep_with_next  = True

    # Heading 2
    h2 = styles["Heading 2"]
    h2.font.name        = T.FONT_HEADING
    h2.font.size        = T.SIZE_H2
    h2.font.bold        = True
    h2.font.color.rgb   = T.COLOR_HEADING
    h2.font.underline   = False
    h2.paragraph_format.space_before    = T.SPACE_BEFORE_H2
    h2.paragraph_format.space_after     = T.SPACE_AFTER_H2
    h2.paragraph_format.keep_with_next  = True

    # Heading 3
    h3 = styles["Heading 3"]
    h3.font.name        = T.FONT_HEADING
    h3.font.size        = T.SIZE_H3
    h3.font.bold        = True
    h3.font.italic      = False
    h3.font.color.rgb   = T.COLOR_ACCENT
    h3.font.underline   = False
    h3.paragraph_format.space_before    = T.SPACE_BEFORE_H3
    h3.paragraph_format.space_after     = T.SPACE_AFTER_H3
    h3.paragraph_format.keep_with_next  = True

    # List Bullet
    try:
        lb = styles["List Bullet"]
        lb.font.name        = T.FONT_BODY
        lb.font.size        = T.SIZE_BODY
        lb.font.color.rgb   = T.COLOR_INK
        lb.paragraph_format.space_after  = Pt(3)
        lb.paragraph_format.left_indent  = Inches(0.25)
    except KeyError:
        pass

    # List Number
    try:
        ln = styles["List Number"]
        ln.font.name        = T.FONT_BODY
        ln.font.size        = T.SIZE_BODY
        ln.font.color.rgb   = T.COLOR_INK
        ln.paragraph_format.space_after  = Pt(3)
        ln.paragraph_format.left_indent  = Inches(0.25)
    except KeyError:
        pass


# ─────────────────────────────────────────────────────────────
# HEADER & FOOTER
# ─────────────────────────────────────────────────────────────

def _configure_header_footer(doc: Document, project_name: str):
    section = doc.sections[0]

    # ── Header ──────────────────────────────────────────────
    header = section.header
    header.is_linked_to_previous = False

    # Clear default paragraph, add a 2-column table for left/right alignment
    for para in header.paragraphs:
        para._element.getparent().remove(para._element)

    header_table = header.add_table(rows=1, cols=2, width=Inches(7))
    _remove_table_borders(header_table)

    left_cell  = header_table.cell(0, 0)
    right_cell = header_table.cell(0, 1)

    # Left: document title
    lp = left_cell.paragraphs[0]
    lp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    lr = lp.add_run(project_name)
    lr.font.name      = T.FONT_BODY
    lr.font.size      = T.SIZE_CAPTION
    lr.font.bold      = True
    lr.font.color.rgb = T.COLOR_HEADING

    # Right: static label
    rp = right_cell.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rr = rp.add_run("TECHNICAL DOCUMENTATION")
    rr.font.name      = T.FONT_BODY
    rr.font.size      = T.SIZE_CAPTION
    rr.font.color.rgb = T.COLOR_MUTED

    # Thin accent rule under header
    rule_para = header.add_paragraph()
    rule_para.paragraph_format.space_before = Pt(2)
    rule_para.paragraph_format.space_after  = Pt(0)
    pPr = rule_para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1A56DB")
    pBdr.append(bottom)
    pPr.append(pBdr)

    # ── Footer ──────────────────────────────────────────────
    footer = section.footer
    footer.is_linked_to_previous = False

    for para in footer.paragraphs:
        para._element.getparent().remove(para._element)

    footer_table = footer.add_table(rows=1, cols=2, width=Inches(7))
    _remove_table_borders(footer_table)

    fl_cell = footer_table.cell(0, 0)
    fr_cell = footer_table.cell(0, 1)

    # Left: confidentiality notice
    flp = fl_cell.paragraphs[0]
    flp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    flr = flp.add_run(f"© {date.today().year}  {project_name}  ·  Confidential")
    flr.font.name      = T.FONT_BODY
    flr.font.size      = T.SIZE_CAPTION
    flr.font.color.rgb = T.COLOR_MUTED

    # Right: "Page X of N"
    frp = fr_cell.paragraphs[0]
    frp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pre_run = frp.add_run("Page ")
    pre_run.font.name      = T.FONT_BODY
    pre_run.font.size      = T.SIZE_CAPTION
    pre_run.font.color.rgb = T.COLOR_MUTED
    _add_page_number(frp)
    frp.runs[-1].font.name      = T.FONT_BODY
    frp.runs[-1].font.size      = T.SIZE_CAPTION
    frp.runs[-1].font.color.rgb = T.COLOR_MUTED
    of_run = frp.add_run("  of  ")
    of_run.font.name      = T.FONT_BODY
    of_run.font.size      = T.SIZE_CAPTION
    of_run.font.color.rgb = T.COLOR_MUTED
    _add_numpages_field(frp)
    frp.runs[-1].font.name      = T.FONT_BODY
    frp.runs[-1].font.size      = T.SIZE_CAPTION
    frp.runs[-1].font.color.rgb = T.COLOR_MUTED


# ─────────────────────────────────────────────────────────────
# TITLE PAGE
# ─────────────────────────────────────────────────────────────

def _build_title_page(
    doc: Document,
    project_name: str,
    client_name: str,
    team_str: str,
    description: str,
):
    # Generous top whitespace
    for _ in range(4):
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(0)
        spacer.paragraph_format.space_after  = Pt(0)

    # Accent bar before title (2-column table trick: colored left column)
    accent_table = doc.add_table(rows=1, cols=2)
    _remove_table_borders(accent_table)
    accent_table.columns[0].width = Inches(0.12)
    accent_table.columns[1].width = Inches(6.5)
    left_accent = accent_table.cell(0, 0)
    _set_cell_shading(left_accent, "1A56DB")
    left_accent.paragraphs[0].paragraph_format.space_before = Pt(0)
    left_accent.paragraphs[0].paragraph_format.space_after  = Pt(0)

    right_content = accent_table.cell(0, 1)
    right_content._tc.get_or_add_tcPr()
    rp = right_content.paragraphs[0]
    rp.paragraph_format.left_indent  = Inches(0.3)
    rp.paragraph_format.space_before = Pt(0)
    rp.paragraph_format.space_after  = Pt(0)
    title_run = rp.add_run(project_name)
    title_run.font.name      = T.FONT_HEADING
    title_run.font.size      = T.SIZE_DISPLAY
    title_run.font.bold      = True
    title_run.font.color.rgb = T.COLOR_HEADING

    # Subtitle row
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(6)
    sub_p.paragraph_format.space_after  = Pt(0)
    sub_p.paragraph_format.left_indent  = Inches(0.42)
    sub_run = sub_p.add_run("TECHNICAL DOCUMENTATION")
    sub_run.font.name      = T.FONT_BODY
    sub_run.font.size      = T.SIZE_SUBTITLE
    sub_run.font.color.rgb = T.COLOR_ACCENT
    sub_run.font.bold      = False

    doc.add_paragraph().paragraph_format.space_after = Pt(0)

    # Thin rule
    _add_horizontal_rule(doc, color_hex="1A56DB", thickness="6")

    doc.add_paragraph().paragraph_format.space_after = Pt(0)

    # Description block (if provided)
    if description:
        desc_p = doc.add_paragraph()
        desc_p.paragraph_format.left_indent  = Inches(0.42)
        desc_p.paragraph_format.space_before = Pt(6)
        desc_p.paragraph_format.space_after  = Pt(16)
        desc_run = desc_p.add_run(description)
        desc_run.font.name      = T.FONT_BODY
        desc_run.font.size      = Pt(11)
        desc_run.font.color.rgb = T.COLOR_MUTED
        desc_run.font.italic    = True

    # Metadata table (client / team / date)
    meta_rows = []
    if client_name:
        meta_rows.append(("Client", client_name))
    if team_str:
        meta_rows.append(("Team", team_str))
    meta_rows.append(("Date", date.today().strftime("%B %d, %Y")))
    meta_rows.append(("Classification", "Confidential"))

    meta_table = doc.add_table(rows=len(meta_rows), cols=2)
    _remove_table_borders(meta_table)
    meta_table.alignment = WD_TABLE_ALIGNMENT.LEFT

    for i, (label, value) in enumerate(meta_rows):
        label_cell = meta_table.cell(i, 0)
        value_cell = meta_table.cell(i, 1)

        label_cell.width = Inches(1.6)
        value_cell.width = Inches(4.5)

        lp = label_cell.paragraphs[0]
        lp.paragraph_format.left_indent  = Inches(0.42)
        lp.paragraph_format.space_before = Pt(3)
        lp.paragraph_format.space_after  = Pt(3)
        lr = lp.add_run(label.upper())
        lr.font.name      = T.FONT_BODY
        lr.font.size      = T.SIZE_CAPTION
        lr.font.bold      = True
        lr.font.color.rgb = T.COLOR_MUTED

        vp = value_cell.paragraphs[0]
        vp.paragraph_format.space_before = Pt(3)
        vp.paragraph_format.space_after  = Pt(3)
        vr = vp.add_run(value)
        vr.font.name      = T.FONT_BODY
        vr.font.size      = T.SIZE_BODY
        vr.font.color.rgb = T.COLOR_INK

    doc.add_page_break()


# ─────────────────────────────────────────────────────────────
# TABLE OF CONTENTS PAGE
# ─────────────────────────────────────────────────────────────

def _build_toc_page(doc: Document):
    toc_heading_p = doc.add_paragraph()
    toc_heading_p.paragraph_format.space_before = Pt(0)
    toc_heading_p.paragraph_format.space_after  = Pt(4)
    thr = toc_heading_p.add_run("Table of Contents")
    thr.font.name      = T.FONT_HEADING
    thr.font.size      = T.SIZE_H1
    thr.font.bold      = True
    thr.font.color.rgb = T.COLOR_HEADING

    _add_horizontal_rule(doc, color_hex="1A56DB", thickness="6")

    hint_p = doc.add_paragraph()
    hint_p.paragraph_format.space_before = Pt(6)
    hint_p.paragraph_format.space_after  = Pt(12)
    hint_r = hint_p.add_run(
        "Update this field in Word: right-click → Update Field → Update entire table."
    )
    hint_r.font.name      = T.FONT_BODY
    hint_r.font.size      = T.SIZE_CAPTION
    hint_r.font.color.rgb = T.COLOR_MUTED
    hint_r.font.italic    = True

    _add_toc(doc)
    doc.add_page_break()


# ─────────────────────────────────────────────────────────────
# TABLE RENDERER
# ─────────────────────────────────────────────────────────────

def _collect_table_rows(lines: list, start_idx: int):
    """
    Consume consecutive pipe-delimited lines starting from start_idx.
    Returns (rows_list, next_line_index).
    Separator rows (---|---) are discarded.
    """
    rows = []
    i = start_idx
    while i < len(lines):
        line = lines[i]
        if not (line.startswith("|") and "|" in line[1:]):
            break
        # Skip separator rows
        if re.match(r"^\|[\s\-|:]+\|$", line.strip()):
            i += 1
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def _render_professional_table(doc: Document, rows: List[List[str]]):
    """Render a list of row data as a polished, borderless data table."""
    if not rows:
        return

    col_count = max(len(r) for r in rows)
    # Pad short rows
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    table = doc.add_table(rows=len(rows), cols=col_count)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    _remove_table_borders(table)

    for row_idx, row_data in enumerate(rows):
        is_header = (row_idx == 0)
        tr = table.rows[row_idx]

        for col_idx, cell_text in enumerate(row_data):
            cell = tr.cells[col_idx]

            # Row background
            if is_header:
                _set_cell_shading(cell, "0D1B3E")
            elif row_idx % 2 == 0:
                _set_cell_shading(cell, "F8F9FF")
            else:
                _set_cell_shading(cell, "FFFFFF")

            # Bottom border on header row only
            if is_header:
                _set_cell_border(cell, {
                    "bottom": {"val": "single", "sz": "6", "color": "1A56DB"}
                })

            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            para = cell.paragraphs[0]
            para.paragraph_format.space_before = Pt(5)
            para.paragraph_format.space_after  = Pt(5)
            para.paragraph_format.left_indent  = Inches(0.08)

            run = para.add_run(cell_text)
            run.font.name = T.FONT_BODY
            run.font.size = T.SIZE_BODY

            if is_header:
                run.font.bold      = True
                run.font.color.rgb = T.COLOR_WHITE
            else:
                run.font.bold      = False
                run.font.color.rgb = T.COLOR_INK

    # Breathing room below table
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after  = Pt(8)


# ─────────────────────────────────────────────────────────────
# INLINE MARKDOWN PARSER (bold/italic within a run)
# ─────────────────────────────────────────────────────────────

def _apply_inline_markdown(paragraph, text: str):
    """
    Parse **bold**, *italic*, and `code` spans within a line
    and add them as styled runs to the given paragraph.
    """
    # Pattern: captures **bold**, *italic*, `code`, or plain text
    token_pattern = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|[^*`]+)")
    for match in token_pattern.finditer(text):
        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            run.font.name      = T.FONT_BODY
            run.font.size      = T.SIZE_BODY
            run.font.color.rgb = T.COLOR_INK
        elif token.startswith("*") and token.endswith("*"):
            run = paragraph.add_run(token[1:-1])
            run.italic = True
            run.font.name      = T.FONT_BODY
            run.font.size      = T.SIZE_BODY
            run.font.color.rgb = T.COLOR_INK
        elif token.startswith("`") and token.endswith("`"):
            run = paragraph.add_run(token[1:-1])
            run.font.name      = T.FONT_MONO
            run.font.size      = T.SIZE_CODE
            run.font.color.rgb = T.COLOR_CODE_TEXT
        else:
            run = paragraph.add_run(token)
            run.font.name      = T.FONT_BODY
            run.font.size      = T.SIZE_BODY
            run.font.color.rgb = T.COLOR_INK


# ─────────────────────────────────────────────────────────────
# SECTION CONTENT RENDERER
# ─────────────────────────────────────────────────────────────

def _render_section_content(doc: Document, content: str):
    """
    Parse markdown-like content and render each element
    with professional, precise styling.
    """
    lines = content.split("\n")
    in_code_block = False
    code_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── Code block toggle ──────────────────────────────
        if line.strip().startswith("```"):
            if in_code_block:
                # Flush accumulated code lines as a styled block
                _render_code_block(doc, code_lines)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # ── Table detection (multi-row aware) ──────────────
        if line.startswith("|") and "|" in line[1:]:
            rows, next_i = _collect_table_rows(lines, i)
            _render_professional_table(doc, rows)
            i = next_i
            continue

        # ── ATX Headings ───────────────────────────────────
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)

        # ── Bullet list item ───────────────────────────────
        elif line.startswith("- ") or line.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(2)
            _apply_inline_markdown(p, line[2:].strip())

        # ── Numbered list item ─────────────────────────────
        elif re.match(r"^\d+\.\s", line):
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(2)
            _apply_inline_markdown(p, re.sub(r"^\d+\.\s", "", line).strip())

        # ── Standalone bold line → callout label ───────────
        elif re.match(r"^\*\*(.+)\*\*$", line.strip()):
            label_text = re.match(r"^\*\*(.+)\*\*$", line.strip()).group(1)
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after  = Pt(2)
            r = p.add_run(label_text)
            r.bold            = True
            r.font.name       = T.FONT_BODY
            r.font.size       = Pt(11)
            r.font.color.rgb  = T.COLOR_HEADING

        # ── Horizontal rule ───────────────────────────────
        elif line.strip() in ("---", "***", "___"):
            _add_horizontal_rule(doc)

        # ── Normal paragraph ──────────────────────────────
        elif line.strip():
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after  = T.SPACE_AFTER_BODY
            p.paragraph_format.line_spacing = T.LINE_SPACING_BODY
            _apply_inline_markdown(p, line.strip())

        i += 1

    # Flush any unclosed code block
    if in_code_block and code_lines:
        _render_code_block(doc, code_lines)


def _render_code_block(doc: Document, code_lines: List[str]):
    """Render a fenced code block as a shaded monospace paragraph."""
    # Top micro-spacer
    pre_spacer = doc.add_paragraph()
    pre_spacer.paragraph_format.space_before = Pt(4)
    pre_spacer.paragraph_format.space_after  = Pt(0)

    code_para = doc.add_paragraph()
    code_para.paragraph_format.space_before = Pt(0)
    code_para.paragraph_format.space_after  = Pt(0)
    code_para.paragraph_format.left_indent  = Inches(0.22)
    code_para.paragraph_format.right_indent = Inches(0.22)

    _set_paragraph_shading(code_para, "F5F7FF")

    run = code_para.add_run("\n".join(code_lines))
    run.font.name      = T.FONT_MONO
    run.font.size      = T.SIZE_CODE
    run.font.color.rgb = T.COLOR_CODE_TEXT

    # Left accent stripe via border
    pPr = code_para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    left_border = OxmlElement("w:left")
    left_border.set(qn("w:val"), "single")
    left_border.set(qn("w:sz"), "12")
    left_border.set(qn("w:space"), "6")
    left_border.set(qn("w:color"), "1A56DB")
    pBdr.append(left_border)
    pPr.append(pBdr)

    # Bottom micro-spacer
    post_spacer = doc.add_paragraph()
    post_spacer.paragraph_format.space_before = Pt(0)
    post_spacer.paragraph_format.space_after  = Pt(8)


# ─────────────────────────────────────────────────────────────
# PUBLIC API — build_document (unchanged signature)
# ─────────────────────────────────────────────────────────────

def build_document(
    project_id: str,
    metadata: Dict[str, Any],
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a professional technical document.

    Parameters
    ----------
    project_id : str
        Unique project identifier used to derive the output path.
    metadata : dict
        Keys: project_name, client_name, team_members (list|str), description
    sections : list of dict
        Each dict: {name: str, content: str, order: int}

    Returns
    -------
    dict
        {file_path, word_count, page_estimate, section_count}
    """
    doc = Document()

    # 1. Margins
    _configure_margins(doc)

    # 2. Base styles (must happen before any content is added)
    _apply_base_styles(doc)

    # 3. Unpack metadata
    project_name = metadata.get("project_name", "Untitled Project")
    client_name  = metadata.get("client_name", "")
    team_members = metadata.get("team_members", [])
    team_str     = ", ".join(team_members) if isinstance(team_members, list) else team_members
    description  = metadata.get("description", "")

    # 4. Title page
    _build_title_page(doc, project_name, client_name, team_str, description)

    # 5. Table of contents
    _build_toc_page(doc)

    # 6. Section pages
    sorted_sections = sorted(sections, key=lambda s: s.get("order", 0))
    for sec in sorted_sections:
        # Section heading with decorative underline via border
        heading_p = doc.add_paragraph()
        heading_p.paragraph_format.space_before = Pt(0)
        heading_p.paragraph_format.space_after  = Pt(2)
        heading_p.paragraph_format.keep_with_next = True
        hr = heading_p.add_run(sec["name"])
        hr.font.name      = T.FONT_HEADING
        hr.font.size      = T.SIZE_H1
        hr.font.bold      = True
        hr.font.color.rgb = T.COLOR_HEADING

        _add_horizontal_rule(doc, color_hex="D0D8F0", thickness="4")

        _render_section_content(doc, sec.get("content", ""))
        doc.add_page_break()

    # 7. Header / Footer (applied last — references first section)
    _configure_header_footer(doc, project_name)

    # 8. Persist to disk
    out_dir = Path(STORAGE_DIR) / "projects" / project_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "output.docx"
    doc.save(str(out_path))

    # 9. Return stats
    full_text  = " ".join(sec.get("content", "") for sec in sections)
    word_count = len(full_text.split())
    page_estimate = max(1, round(word_count / 300))

    return {
        "file_path":     str(out_path),
        "word_count":    word_count,
        "page_estimate": page_estimate,
        "section_count": len(sections),
    }