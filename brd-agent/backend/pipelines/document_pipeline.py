"""
Document Generation Pipeline — Professional BRD formatting.
Inspired by the technical documentation renderer with:
- Design token system (all colours/sizes in one place)
- Proper TOC with estimated page numbers (no "right-click to update")
- Dark navy header rows, alternating stripe tables
- Title page with accent bar, metadata card, left accent strip
- Running header/footer with page numbers
- Per-section page breaks
- Inline markdown parser (bold, italic, code)
"""

import os
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from models.project import Project, ProjectStore
from utils.logger import info, success, divider

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.enum.section import WD_SECTION
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


# ── Design Tokens ───────────────────────────────────────────────────────────
class T:
    INK        = RGBColor(0x0F, 0x0F, 0x1A)
    HEADING    = RGBColor(0x0D, 0x1B, 0x3E)
    ACCENT     = RGBColor(0x1A, 0x56, 0xDB)
    MUTED      = RGBColor(0x5A, 0x5A, 0x72)
    LIGHT_MUTED= RGBColor(0x9C, 0xA3, 0xAF)
    CODE_TEXT  = RGBColor(0x1E, 0x3A, 0x8A)
    WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
    STRIPE     = RGBColor(0xF8, 0xF9, 0xFF)
    ACCENT_BG  = RGBColor(0xEB, 0xF0, 0xFF)

    FONT_BODY    = "Calibri"
    FONT_HEADING = "Calibri"
    FONT_MONO    = "Consolas"

    DISPLAY  = Pt(38)
    H1       = Pt(16)
    H2       = Pt(13)
    H3       = Pt(11)
    BODY     = Pt(10.5)
    CAPTION  = Pt(9)
    CODE     = Pt(9)
    META_LBL = Pt(8)
    META_VAL = Pt(10.5)

    MARGIN_TOP    = Cm(2.8)
    MARGIN_BOTTOM = Cm(2.8)
    MARGIN_LEFT   = Cm(3.0)
    MARGIN_RIGHT  = Cm(2.5)


PAGE_W = Cm(21)
BODY_W = PAGE_W - T.MARGIN_LEFT - T.MARGIN_RIGHT


# ── XML helpers ─────────────────────────────────────────────────────────────

def _shd(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for s in tcPr.findall(qn("w:shd")): tcPr.remove(s)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _no_borders(table):
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr")) or OxmlElement("w:tblPr")
    bd = OxmlElement("w:tblBorders")
    for side in ("top","left","bottom","right","insideH","insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "none")
        bd.append(el)
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None: tblPr.remove(existing)
    tblPr.append(bd)


def _set_tbl_width(table, emu: int):
    dxa = int(emu * 1440 / 914400)
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    w = tblPr.find(qn("w:tblW")) or OxmlElement("w:tblW")
    w.set(qn("w:w"), str(dxa))
    w.set(qn("w:type"), "dxa")
    if tblPr.find(qn("w:tblW")) is None:
        tblPr.append(w)


def _set_col_w(table, col: int, emu: int):
    dxa = int(emu * 1440 / 914400)
    for row in table.rows:
        tc = row.cells[col]._tc
        tcPr = tc.get_or_add_tcPr()
        w = tcPr.find(qn("w:tcW")) or OxmlElement("w:tcW")
        w.set(qn("w:w"), str(dxa))
        w.set(qn("w:type"), "dxa")
        if tcPr.find(qn("w:tcW")) is None:
            tcPr.append(w)


def _make_tbl(doc, rows: int, cols: int, width_emu: int):
    table = doc.add_table(rows=rows, cols=cols)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    _set_tbl_width(table, width_emu)
    return table


def _hr(doc, color="D0D8F0", sz="4"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after  = Pt(3)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    btm = OxmlElement("w:bottom")
    btm.set(qn("w:val"), "single")
    btm.set(qn("w:sz"), sz)
    btm.set(qn("w:space"), "1")
    btm.set(qn("w:color"), color)
    pBdr.append(btm)
    pPr.append(pBdr)


def _field(para, field_name: str):
    run = para.add_run()
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.text = field_name
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    run._r.append(f1); run._r.append(instr); run._r.append(f2)


def _left_border(para, color="1A56DB", sz="18"):
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), sz)
    left.set(qn("w:space"), "6")
    left.set(qn("w:color"), color)
    pBdr.append(left)
    pPr.append(pBdr)


# ── Inline markdown ──────────────────────────────────────────────────────────

_INLINE_RE = re.compile(r"(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|[^*`]+|[*`])")

def _inline(para, text: str, color: RGBColor = None):
    if color is None: color = T.INK
    for m in _INLINE_RE.finditer(text):
        tok = m.group(0)
        if tok.startswith("***") and tok.endswith("***") and len(tok) > 6:
            r = para.add_run(tok[3:-3]); r.bold = True; r.italic = True
        elif tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = para.add_run(tok[2:-2]); r.bold = True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = para.add_run(tok[1:-1]); r.italic = True
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            r = para.add_run(tok[1:-1])
            r.font.name = T.FONT_MONO
            r.font.size = T.CODE
            r.font.color.rgb = T.CODE_TEXT
            continue
        else:
            r = para.add_run(tok)
        r.font.name = T.FONT_BODY
        r.font.size = T.BODY
        r.font.color.rgb = color


# ── Document setup ───────────────────────────────────────────────────────────

def _setup(doc: Document):
    for sec in doc.sections:
        sec.top_margin    = T.MARGIN_TOP
        sec.bottom_margin = T.MARGIN_BOTTOM
        sec.left_margin   = T.MARGIN_LEFT
        sec.right_margin  = T.MARGIN_RIGHT

    styles = doc.styles
    n = styles["Normal"]
    n.font.name = T.FONT_BODY
    n.font.size = T.BODY
    n.font.color.rgb = T.INK
    n.paragraph_format.space_after  = Pt(6)
    n.paragraph_format.line_spacing = Pt(15)

    for name, size, before, after in [
        ("Heading 1", T.H1, Pt(18), Pt(6)),
        ("Heading 2", T.H2, Pt(14), Pt(4)),
        ("Heading 3", T.H3, Pt(8),  Pt(3)),
    ]:
        try:
            h = styles[name]
            h.font.name = T.FONT_HEADING
            h.font.size = size
            h.font.bold = True
            h.font.color.rgb = T.HEADING if "1" in name else (T.ACCENT if "2" in name else T.MUTED)
            h.font.underline = False
            h.font.italic    = False
            h.paragraph_format.space_before   = before
            h.paragraph_format.space_after    = after
            h.paragraph_format.keep_with_next = True
        except KeyError:
            pass


# ── Header / footer ──────────────────────────────────────────────────────────

def _hf(doc: Document, project_name: str):
    if len(doc.sections) < 2:
        return
    body_sec = doc.sections[1]

    # Header
    hdr = body_sec.header
    hdr.is_linked_to_previous = False
    for p in list(hdr.paragraphs): p._element.getparent().remove(p._element)

    from docx.oxml.table import CT_Tbl
    from docx.table import Table

    def _hf_table(container, rows, cols, width_emu):
        tbl_xml = CT_Tbl.new_tbl(rows, cols, Inches(1))
        tbl_obj = Table(tbl_xml, container)
        tbl_obj.autofit = False
        container._element.append(tbl_xml)
        _set_tbl_width(tbl_obj, width_emu)
        return tbl_obj

    ht = _hf_table(hdr, 1, 2, BODY_W)
    _no_borders(ht)
    _set_col_w(ht, 0, BODY_W // 2)
    _set_col_w(ht, 1, BODY_W // 2)

    lp = ht.cell(0, 0).paragraphs[0]
    lp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    lr = lp.add_run(project_name)
    lr.font.name = T.FONT_BODY; lr.font.size = T.CAPTION; lr.bold = True; lr.font.color.rgb = T.HEADING

    rp = ht.cell(0, 1).paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rr = rp.add_run("BUSINESS REQUIREMENTS DOCUMENT")
    rr.font.name = T.FONT_BODY; rr.font.size = T.CAPTION; rr.font.color.rgb = T.MUTED

    rule = hdr.add_paragraph()
    rule.paragraph_format.space_before = Pt(2)
    rule.paragraph_format.space_after  = Pt(0)
    pPr = rule._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"),"single"); b.set(qn("w:sz"),"6"); b.set(qn("w:space"),"1"); b.set(qn("w:color"),"1A56DB")
    pBdr.append(b); pPr.append(pBdr)

    # Footer
    ftr = body_sec.footer
    ftr.is_linked_to_previous = False
    for p in list(ftr.paragraphs): p._element.getparent().remove(p._element)

    ft = _hf_table(ftr, 1, 2, BODY_W)
    _no_borders(ft)
    _set_col_w(ft, 0, int(BODY_W * .6))
    _set_col_w(ft, 1, int(BODY_W * .4))

    flp = ft.cell(0, 0).paragraphs[0]
    flp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    flr = flp.add_run(f"© {date.today().year}  {project_name}  ·  Confidential")
    flr.font.name = T.FONT_BODY; flr.font.size = T.CAPTION; flr.font.color.rgb = T.MUTED

    frp = ft.cell(0, 1).paragraphs[0]
    frp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for txt, is_field in [("Page ", False), ("PAGE", True), (" of ", False), ("NUMPAGES", True)]:
        if is_field:
            _field(frp, txt)
            frp.runs[-1].font.name = T.FONT_BODY
            frp.runs[-1].font.size = T.CAPTION
            frp.runs[-1].font.color.rgb = T.MUTED
        else:
            r = frp.add_run(txt)
            r.font.name = T.FONT_BODY; r.font.size = T.CAPTION; r.font.color.rgb = T.MUTED


# ── Title page ───────────────────────────────────────────────────────────────

def _title_page(doc, project_name, client_name, team_str, description, version):
    # Blue top bar
    bar = _make_tbl(doc, 1, 1, BODY_W)
    _no_borders(bar)
    c = bar.cell(0, 0)
    _shd(c, "1A56DB")
    p = c.paragraphs[0]
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(8)
    p.add_run("")

    for _ in range(5): doc.add_paragraph()

    # Project name
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(0)
    tp.paragraph_format.space_after  = Pt(4)
    tr = tp.add_run(project_name.upper())
    tr.font.name = T.FONT_HEADING
    tr.font.size = T.DISPLAY
    tr.bold = True
    tr.font.color.rgb = T.HEADING

    # Subtitle
    sp = doc.add_paragraph()
    sr = sp.add_run("BUSINESS REQUIREMENTS DOCUMENT")
    sr.font.name = T.FONT_BODY
    sr.font.size = Pt(11)
    sr.bold = True
    sr.font.color.rgb = T.ACCENT

    # Horizontal rule
    rule = doc.add_paragraph()
    rule.paragraph_format.space_before = Pt(12)
    rule.paragraph_format.space_after  = Pt(12)
    pPr = rule._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"),"single"); b.set(qn("w:sz"),"10"); b.set(qn("w:space"),"1"); b.set(qn("w:color"),"1A56DB")
    pBdr.append(b); pPr.append(pBdr)

    if description:
        dp = doc.add_paragraph()
        dp.paragraph_format.space_after = Pt(24)
        dr = dp.add_run(description)
        dr.font.name = T.FONT_BODY; dr.font.size = Pt(11); dr.italic = True; dr.font.color.rgb = T.MUTED

    # Metadata card
    meta_rows = []
    if client_name: meta_rows.append(("Client", client_name))
    if team_str:    meta_rows.append(("Prepared By", team_str))
    meta_rows.append(("Date", datetime.now().strftime("%B %d, %Y")))
    meta_rows.append(("Version", f"v{version}.0 — DRAFT"))
    meta_rows.append(("Classification", "Confidential"))

    wrapper = _make_tbl(doc, 1, 2, BODY_W)
    _no_borders(wrapper)
    _set_col_w(wrapper, 0, Inches(0.06))
    _set_col_w(wrapper, 1, BODY_W - Inches(0.06))
    _shd(wrapper.cell(0, 0), "1A56DB")
    rc = wrapper.cell(0, 1)
    _shd(rc, "F0F4FF")

    inner = rc.add_table(rows=len(meta_rows), cols=2)
    inner.autofit = False
    _no_borders(inner)
    lw = Inches(1.6)
    vw = BODY_W - Inches(0.06) - lw
    for r in inner.rows:
        for ci, cell in enumerate(r.cells):
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tw = OxmlElement("w:tcW")
            tw.set(qn("w:w"), str(int((lw if ci == 0 else vw) * 1440 / 914400)))
            tw.set(qn("w:type"), "dxa")
            tcPr.append(tw)

    for i, (label, value) in enumerate(meta_rows):
        is_last = (i == len(meta_rows) - 1)
        lc = inner.cell(i, 0); vc = inner.cell(i, 1)
        _shd(lc, "F0F4FF"); _shd(vc, "F0F4FF")
        if not is_last:
            for cell in (lc, vc):
                tc = cell._tc; tcPr = tc.get_or_add_tcPr()
                tcBd = OxmlElement("w:tcBorders"); bb = OxmlElement("w:bottom")
                bb.set(qn("w:val"),"single"); bb.set(qn("w:sz"),"2"); bb.set(qn("w:space"),"0"); bb.set(qn("w:color"),"D0D8F0")
                tcBd.append(bb); tcPr.append(tcBd)
        lp = lc.paragraphs[0]
        lp.paragraph_format.left_indent  = Inches(0.2)
        lp.paragraph_format.space_before = Pt(6)
        lp.paragraph_format.space_after  = Pt(6)
        lr = lp.add_run(label.upper())
        lr.font.name = T.FONT_BODY; lr.font.size = T.META_LBL; lr.bold = True; lr.font.color.rgb = T.LIGHT_MUTED

        vp = vc.paragraphs[0]
        vp.paragraph_format.space_before = Pt(6)
        vp.paragraph_format.space_after  = Pt(6)
        vp.paragraph_format.left_indent  = Inches(0.1)
        vr = vp.add_run(value)
        vr.font.name = T.FONT_BODY; vr.font.size = T.META_VAL; vr.font.color.rgb = T.HEADING

    for _ in range(3): doc.add_paragraph()
    doc.add_section(WD_SECTION.NEW_PAGE)


# ── TOC ──────────────────────────────────────────────────────────────────────

def _estimate_pages(sections):
    page = 3; result = []
    for s in sections:
        result.append(page)
        words = len(s.get("content", "").split())
        page += max(1, round(words / 280))
    return result


def _toc(doc, sections):
    hp = doc.add_paragraph()
    hr = hp.add_run("Table of Contents")
    hr.font.name = T.FONT_HEADING; hr.font.size = T.H1; hr.bold = True; hr.font.color.rgb = T.HEADING
    hp.paragraph_format.space_after = Pt(4)

    _hr(doc, "1A56DB", "6")

    pages = _estimate_pages(sections)
    tbl = _make_tbl(doc, len(sections), 2, BODY_W)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    _no_borders(tbl)
    _set_col_w(tbl, 0, BODY_W - Inches(0.8))
    _set_col_w(tbl, 1, Inches(0.8))

    for i, (sec, pg) in enumerate(zip(sections, pages)):
        row = tbl.rows[i]
        if i % 2 == 0:
            for cell in row.cells: _shd(cell, "F8F9FF")

        np = row.cells[0].paragraphs[0]
        np.paragraph_format.space_before = Pt(5)
        np.paragraph_format.space_after  = Pt(5)
        np.paragraph_format.left_indent  = Inches(0.12)
        nr = np.add_run(f"{i+1}.  "); nr.font.name = T.FONT_BODY; nr.font.size = T.BODY; nr.bold = True; nr.font.color.rgb = T.ACCENT
        nv = np.add_run(sec.get("name", "")); nv.font.name = T.FONT_BODY; nv.font.size = T.BODY; nv.font.color.rgb = T.HEADING

        pp = row.cells[1].paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        pp.paragraph_format.space_before = Pt(5)
        pp.paragraph_format.space_after  = Pt(5)
        pp.paragraph_format.right_indent = Inches(0.12)
        pr = pp.add_run(str(pg)); pr.font.name = T.FONT_BODY; pr.font.size = T.BODY; pr.font.color.rgb = T.MUTED

    _hr(doc, "D0D8F0", "4")
    np2 = doc.add_paragraph()
    nr2 = np2.add_run("Page numbers are estimates. Exact figures may vary after final rendering.")
    nr2.font.name = T.FONT_BODY; nr2.font.size = T.CAPTION; nr2.italic = True; nr2.font.color.rgb = T.LIGHT_MUTED
    doc.add_page_break()


# ── Table renderer ───────────────────────────────────────────────────────────

def _collect_table(lines, start):
    rows = []; i = start
    while i < len(lines):
        line = lines[i]
        if not (line.startswith("|") and "|" in line[1:]): break
        if re.match(r"^\|[\s\-|:]+\|$", line.strip()): i += 1; continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells); i += 1
    return rows, i


def _render_table(doc, rows):
    if not rows: return
    cols = max(len(r) for r in rows)
    rows = [r + [""] * (cols - len(r)) for r in rows]

    tbl = _make_tbl(doc, len(rows), cols, BODY_W)
    _no_borders(tbl)

    col_w = BODY_W // cols
    for ci in range(cols): _set_col_w(tbl, ci, col_w)

    for ri, row_data in enumerate(rows):
        is_hdr = ri == 0
        tr = tbl.rows[ri]
        for ci, text in enumerate(row_data):
            cell = tr.cells[ci]
            if is_hdr: _shd(cell, "0D1B3E")
            elif ri % 2 == 0: _shd(cell, "F8F9FF")
            else: _shd(cell, "FFFFFF")

            if is_hdr:
                tc = cell._tc; tcPr = tc.get_or_add_tcPr()
                bd = OxmlElement("w:tcBorders"); b = OxmlElement("w:bottom")
                b.set(qn("w:val"),"single"); b.set(qn("w:sz"),"6"); b.set(qn("w:space"),"0"); b.set(qn("w:color"),"1A56DB")
                bd.append(b); tcPr.append(bd)

            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after  = Pt(5)
            p.paragraph_format.left_indent  = Inches(0.08)

            if is_hdr:
                r = p.add_run(text); r.font.name = T.FONT_BODY; r.font.size = T.BODY; r.bold = True; r.font.color.rgb = T.WHITE
            else:
                _inline(p, text)

    doc.add_paragraph()


# ── Section content renderer ─────────────────────────────────────────────────

def _strip_dup_heading(content, section_name):
    lines = content.lstrip("\n").split("\n")
    if not lines: return content
    first = lines[0].strip()
    if re.match(r"^#{1,3}\s+", first):
        text = re.sub(r"^#{1,3}\s+", "", first).strip().lower()
        if text == section_name.strip().lower():
            return "\n".join(lines[1:]).lstrip("\n")
    return content


def _render_content(doc, content: str):
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped: i += 1; continue

        if stripped.startswith("|") and "|" in stripped[1:]:
            rows, next_i = _collect_table(lines, i)
            _render_table(doc, rows)
            i = next_i; continue

        if stripped.startswith("#### ") or stripped.startswith("##### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after  = Pt(2)
            r = p.add_run(stripped.lstrip("#").strip())
            r.bold = True; r.font.name = T.FONT_BODY; r.font.size = T.H3; r.font.color.rgb = T.MUTED

        elif stripped.startswith("### "):
            h = doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("## "):
            h = doc.add_heading(stripped[3:], level=2)
            _left_border(h, "1A56DB", "18")
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)

        elif stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(2)
            _inline(p, stripped[2:])

        elif re.match(r"^\d+\.\s", stripped):
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(2)
            _inline(p, re.sub(r"^\d+\.\s", "", stripped))

        elif stripped in ("---", "***", "___"):
            _hr(doc)

        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after  = Pt(6)
            p.paragraph_format.line_spacing = Pt(15)
            _inline(p, stripped)

        i += 1


# ── Document pipeline ─────────────────────────────────────────────────────────

def _get_output_path(project_name: str, version: int) -> str:
    out_dir = os.path.join(os.path.dirname(__file__), "../../outputs")
    os.makedirs(out_dir, exist_ok=True)
    safe = project_name.replace(" ", "_").replace("/", "_")
    return os.path.join(out_dir, f"BRD_{safe}_v{version}.docx")


class DocumentPipeline:

    def __init__(self, project: Project, store: ProjectStore):
        self.project = project
        self.store = store

    async def run(self):
        self.project.status = "generating_document"
        self.project.progress_message = "Generating Word document..."
        self.store.save(self.project)
        divider(f"DOCUMENT PIPELINE — {self.project.project_name}")

        if not DOCX_AVAILABLE:
            self.project.status = "error"
            self.project.progress_message = "python-docx not installed. Run: pip install python-docx"
            self.store.save(self.project)
            return

        doc = Document()
        _setup(doc)

        team_str = ", ".join(self.project.team_members) if self.project.team_members else "Project Team"

        info("DOC", "Building title page...")
        _title_page(
            doc,
            self.project.project_name,
            self.project.client_name,
            team_str,
            self.project.description,
            self.project.version,
        )

        # Decide sections to include
        approved = [s for s in self.project.generated_sections if s.get("approved")]
        if not approved:
            approved = self.project.generated_sections

        info("DOC", f"Building TOC for {len(approved)} sections...")
        _toc(doc, approved)

        info("DOC", f"Rendering {len(approved)} sections...")
        for idx, sec in enumerate(approved):
            heading = doc.add_heading(sec.get("name", "Section"), level=1)
            if idx > 0:
                heading.paragraph_format.page_break_before = True
            heading.paragraph_format.keep_with_next = True
            _left_border(heading, "D0D8F0", "4")
            _hr(doc, "D0D8F0", "4")

            content = _strip_dup_heading(sec.get("content", ""), sec.get("name", ""))
            _render_content(doc, content)

            # Quality note
            q = sec.get("quality_pct", "")
            n = sec.get("req_count", 0)
            if q:
                np = doc.add_paragraph(f"Quality: {q}  ·  Requirements used: {n}  ·  Status: {sec.get('status','')}")
                np.runs[0].font.size = Pt(7.5)
                np.runs[0].font.color.rgb = T.LIGHT_MUTED
                np.runs[0].italic = True
            info("DOC", f"  [{idx+1}/{len(approved)}] {sec.get('name','')}")

        info("DOC", "Adding header/footer...")
        _hf(doc, self.project.project_name)

        output_path = _get_output_path(self.project.project_name, self.project.version)
        doc.save(output_path)

        self.project.document_path = output_path
        self.project.status = "complete"
        self.project.progress_message = "Document ready for download."
        self.store.save(self.project)
        success("DOC", f"Saved → {output_path}")
