"""Render the project's Markdown documents to PDF (reportlab, embedded DejaVu fonts).

    .venv/Scripts/python.exe experiments/make_pdf.py
Writes reports/CALISMA_OZETI.pdf and reports/teknik_rapor.pdf.  Supports the Markdown subset used in
this project: headings, paragraphs, **bold**, *italic*, `code`, links, bullet/numbered lists, pipe
tables (with \\| escapes), fenced code blocks, horizontal rules and images (scaled to the page).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import matplotlib
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
from reportlab.platypus.flowables import HRFlowable

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
for name, file in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
                   ("DV-BI", "DejaVuSans-BoldOblique.ttf"), ("DVM", "DejaVuSansMono.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

INK, INK2, RULE, HEAD_BG, CODE_BG, ACCENT = (colors.HexColor(c) for c in
                                             ("#111111", "#4a4a48", "#c9c8c3", "#eef2f8", "#f4f4f2", "#2a5fa8"))
BASE = ParagraphStyle("base", fontName="DV", fontSize=9.6, leading=13.4, textColor=INK, spaceAfter=5)
STY = {
    "title": ParagraphStyle("t", parent=BASE, fontName="DV-B", fontSize=17, leading=21, spaceAfter=8, textColor=ACCENT),
    "h1": ParagraphStyle("h1", parent=BASE, fontName="DV-B", fontSize=14.5, leading=18, spaceBefore=12, spaceAfter=6, textColor=ACCENT),
    "h2": ParagraphStyle("h2", parent=BASE, fontName="DV-B", fontSize=12.2, leading=15.5, spaceBefore=10, spaceAfter=5, textColor=ACCENT),
    "h3": ParagraphStyle("h3", parent=BASE, fontName="DV-B", fontSize=10.6, leading=14, spaceBefore=8, spaceAfter=4),
    "p": BASE,
    "li": ParagraphStyle("li", parent=BASE, spaceAfter=2),
    "cap": ParagraphStyle("cap", parent=BASE, fontName="DV-I", fontSize=8.2, leading=10.5, textColor=INK2,
                          alignment=TA_CENTER, spaceAfter=10),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=7.6, leading=9.8, textColor=INK, backColor=CODE_BG,
                           borderPadding=5, spaceBefore=3, spaceAfter=8),
    "quote": ParagraphStyle("quote", parent=BASE, fontSize=8.2, leading=11, textColor=INK2, backColor=CODE_BG,
                            leftIndent=10, borderPadding=4, spaceBefore=2, spaceAfter=8),
}
EMOJI = {"✅": "✓", "❌": "✗", "️": "", "⚠": "⚠"}


def clean(s: str) -> str:
    for k, v in EMOJI.items():
        s = s.replace(k, v)
    return s


def inline(s: str) -> str:
    """Markdown inline -> reportlab mini-HTML."""
    s = clean(s).replace("\\|", "|")
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", keep_code, s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#2a5fa8">\1</link>', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f'<font name="DVM" size="8.4">{codes[int(m.group(1))]}</font>', s)
    return s


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def make_table(rows: list[list[str]], width: float):
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    fs = 8.6 if ncol <= 4 else 7.6 if ncol <= 6 else 6.8 if ncol <= 8 else 6.0
    cs = ParagraphStyle("c", parent=BASE, fontSize=fs, leading=fs * 1.28, spaceAfter=0)
    hs = ParagraphStyle("h", parent=cs, fontName="DV-B")
    lens = [max(min(len(clean(r[j])), 60) for r in rows) + 3 for j in range(ncol)]
    tot = sum(lens)
    widths = [max(width * l / tot, 1.2 * cm if ncol <= 8 else 0.9 * cm) for l in lens]
    scale = width / sum(widths)
    widths = [w * scale for w in widths]
    data = [[Paragraph(inline(c), hs if i == 0 else cs) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK2),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def make_image(path: Path, caption: str, width: float, max_h: float):
    with PILImage.open(path) as im:
        w, h = im.size
    s = min(width / w, max_h / h)
    img = Image(str(path), width=w * s, height=h * s)
    return KeepTogether([img, Paragraph(inline(caption), STY["cap"])]) if caption else img


def md_to_flowables(md_path: Path, width: float, max_img_h: float) -> list:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    out, i, first_h1 = [], 0, True
    para: list[str] = []

    def flush():
        if para:
            out.append(Paragraph(inline(" ".join(para)), STY["p"]))
            para.clear()

    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if st.startswith("```"):
            flush()
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                buf.append(clean(lines[j]))
                j += 1
            out.append(Preformatted("\n".join(buf), STY["code"]))
            i = j + 1
            continue
        if not st:
            flush()
            i += 1
            continue
        if st.startswith(">"):
            flush()
            buf = []
            j = i
            while j < len(lines) and lines[j].strip().startswith(">"):
                buf.append(lines[j].strip()[1:].strip())
                j += 1
            out.append(Paragraph("<br/>".join(inline(b) for b in buf) or "—", STY["quote"]))
            i = j
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", st)
        if m:
            flush()
            lvl = len(m.group(1))
            key = "title" if (lvl == 1 and first_h1) else f"h{lvl}"
            first_h1 = first_h1 and lvl != 1
            out.append(Paragraph(inline(m.group(2)), STY[key]))
            i += 1
            continue
        if re.match(r"^-{3,}$", st):
            flush()
            out.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=4, spaceAfter=8))
            i += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", st)
        if m:
            flush()
            p = (md_path.parent / m.group(2)).resolve()
            if p.exists():
                # keep the explanatory paragraph / heading directly above an image on the same page
                grp = []
                while out and isinstance(out[-1], Paragraph) and len(grp) < 2:
                    grp.insert(0, out.pop())
                out.append(KeepTogether(grp + [Spacer(1, 4), make_image(p, m.group(1), width, max_img_h)]))
            else:
                out.append(Paragraph(f"[görsel bulunamadı: {m.group(2)}]", STY["cap"]))
            i += 1
            continue
        if st.startswith("|") and i + 1 < len(lines) and re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lines[i + 1].strip()):
            flush()
            rows = [split_row(st)]
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(split_row(lines[j]))
                j += 1
            out.append(make_table(rows, width))
            out.append(Spacer(1, 6))
            i = j
            continue
        m = re.match(r"^(\s*)([*-]|\d+\.)\s+(.*)$", line)
        if m:
            flush()
            items, numbered = [], m.group(2)[0].isdigit()
            j = i
            while j < len(lines):
                mm = re.match(r"^(\s*)([*-]|\d+\.)\s+(.*)$", lines[j])
                if not mm:
                    break
                text = [mm.group(3)]
                k = j + 1
                while k < len(lines) and lines[k].startswith("  ") and lines[k].strip() and \
                        not re.match(r"^\s*([*-]|\d+\.)\s+", lines[k]):
                    text.append(lines[k].strip())
                    k += 1
                items.append(ListItem(Paragraph(inline(" ".join(text)), STY["li"]), leftIndent=14,
                                      value=mm.group(2).rstrip(".") if numbered else None))
                j = k
            out.append(ListFlowable(items, bulletType="1" if numbered else "bullet", start=None,
                                    bulletFontName="DV", bulletFontSize=8.5, leftIndent=14, spaceAfter=4))
            i = j
            continue
        para.append(st)
        i += 1
    flush()
    return out


def build(md_path: Path, pdf_path: Path, title: str):
    margin = 1.6 * cm
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=margin, rightMargin=margin,
                            topMargin=1.5 * cm, bottomMargin=1.6 * cm, title=title,
                            author="epsilon_qec_research", subject="ε-QEC over R_Q - reproduction")
    width = A4[0] - 2 * margin
    max_h = (A4[1] - 3.1 * cm) * 0.62

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(INK2)
        canvas.drawString(margin, 0.9 * cm, title)
        canvas.drawRightString(A4[0] - margin, 0.9 * cm, f"sayfa {d.page}")
        canvas.restoreState()

    doc.build(md_to_flowables(md_path, width, max_h), onFirstPage=footer, onLaterPages=footer)
    print("wrote", pdf_path, f"({os.path.getsize(pdf_path) / 1e6:.1f} MB)")


def main():
    (ROOT / "reports").mkdir(exist_ok=True)
    build(ROOT / "CALISMA_OZETI.md", ROOT / "reports" / "CALISMA_OZETI.pdf", "Çalışma Özeti — ε-QEC (R_Q) yeniden üretimi")
    build(ROOT / "reports" / "teknik_rapor.md", ROOT / "reports" / "teknik_rapor.pdf",
          "Teknik Rapor — ε-QEC (R_Q) bağımsız yeniden üretim")
    if (ROOT / "reports" / "kapi_duzeyi_ozet.md").exists():
        build(ROOT / "reports" / "kapi_duzeyi_ozet.md", ROOT / "reports" / "kapi_duzeyi_ozet.pdf",
              "Kapı düzeyi CSS simülasyonu — kısa özet")


if __name__ == "__main__":
    main()
