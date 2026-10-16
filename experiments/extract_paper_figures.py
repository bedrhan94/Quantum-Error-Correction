"""Extract the raster images of Figures 1-3 from the paper PDF (needed by plot_awgn.py).

    .venv/Scripts/python.exe experiments/extract_paper_figures.py
Page 20 holds Figures 1 (X1.jpg) and 2 (X2.jpg); page 21 holds Figure 3 (X1.jpg).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "original_source" / "paper" / "1-s2.0-S1071579726000924-main.pdf"
OUT = ROOT / "figures" / "paper_extracted"
TARGETS = {(20, "X1.jpg"): "paper_fig1.jpg", (20, "X2.jpg"): "paper_fig2.jpg", (21, "X1.jpg"): "paper_fig3.jpg"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reader = pypdf.PdfReader(str(PDF))
    found = 0
    for (page, name), out in TARGETS.items():
        for im in reader.pages[page - 1].images:
            if im.name == name:
                (OUT / out).write_bytes(im.data)
                found += 1
                print(out, im.image.size, hashlib.sha256(im.data).hexdigest()[:12])
    if found != len(TARGETS):
        raise SystemExit(f"only {found} of {len(TARGETS)} figures found")
    # crops of the printed dual conditions (review item A3): rendered at 3x, fixed boxes in pixels
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(PDF))
    for page, box, out in ((14, (150, 1000, 1250, 1180), "ex6_step4.png"), (15, (150, 1320, 1250, 1430), "ex7_step3.png")):
        im = pdf[page - 1].render(scale=3.0).to_pil()
        im.crop(box).save(OUT / out)
        print(out, box)


if __name__ == "__main__":
    main()
