"""Rasterise the eight published figure PDFs to PNG so python-docx can embed them."""
import pathlib
import fitz

SRC = pathlib.Path("../jmlr/figures")
OUT = pathlib.Path("figures")
OUT.mkdir(exist_ok=True)
ZOOM = 300 / 72.0  # 300 dpi

for n in range(1, 9):
    pdf = SRC / f"figure-{n}.pdf"
    doc = fitz.open(pdf)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
    dest = OUT / f"figure-{n}.png"
    pix.save(dest)
    print(f"{pdf.name} -> {dest.name}  {pix.width}x{pix.height}")
    doc.close()
