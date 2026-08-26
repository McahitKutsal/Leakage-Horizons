"""Build the manuscript: markdown to .docx, then fix the styles the default template gets wrong.

Kept as a script rather than run by hand because the conversion has to be repeated after every edit to
the source, and a hand-run pandoc invocation loses the post-processing (D-35's lesson applied to the
paper rather than to a results file).

Two post-processing steps, both on the *style* definitions rather than on individual paragraphs, so a
heading the author adds later inherits the corrected appearance:

1. **Headings in black.** Pandoc's default reference document colours every heading `0F4761`, a dark
   blue. Setting the run colour is not enough on its own: a `w:themeColor` attribute on the same element
   takes precedence in Word, so it has to be removed as well.
2. **No dashes anywhere.** Checked rather than assumed. An em dash, en dash or Unicode minus in the
   output fails the build, because the requirement is that none reach the manuscript and a silent
   substitution somewhere in the toolchain would otherwise go unnoticed.

    python scripts/build_paper.py
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "penumbra-kbs.md"
OUT = ROOT / "paper" / "penumbra-kbs.docx"

# Every style whose colour the template sets to something other than black.
HEADING_STYLES = [f"Heading {i}" for i in range(1, 10)]
HEADING_STYLES += [f"Heading {i} Char" for i in range(1, 10)]
HEADING_STYLES += ["Title", "Title Char", "Subtitle", "Subtitle Char"]
# `TOC Heading` carries the same blue and is unused here, but it is a heading style and a table of
# contents added later would arrive blue. `Hyperlink` is left alone: the document contains no
# hyperlink elements, and a blue link is conventional rather than a heading colour.
HEADING_STYLES += ["TOC Heading"]

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
BLACK = "000000"

# Dash characters that must not appear. The minus sign is included because a negative number set with
# U+2212 renders differently from one set with a hyphen and the manuscript uses hyphens throughout.
FORBIDDEN = {
    "em dash": "—", "en dash": "–", "minus sign": "−",
    "horizontal bar": "―", "figure dash": "‒", "non breaking hyphen": "‑",
}


def convert() -> None:
    import pypandoc
    pypandoc.convert_file(
        str(SRC), "docx", outputfile=str(OUT),
        extra_args=["--standalone", "--from", "markdown+tex_math_dollars+pipe_tables",
                    # Image paths in the manuscript are relative to the manuscript, and pandoc
                    # resolves them against the working directory. Without this the figures are
                    # silently dropped and the document builds clean with nothing in it, which is
                    # exactly the kind of silent success `verify` below now refuses to accept.
                    f"--resource-path={SRC.parent}"])


def blacken_headings() -> list[str]:
    """Set every heading style's colour to black, in the style definition, and drop themeColor."""
    import docx
    from docx.shared import RGBColor

    d = docx.Document(str(OUT))
    changed = []
    for name in HEADING_STYLES:
        try:
            st = d.styles[name]
        except KeyError:
            continue
        before = None
        try:
            before = st.font.color.rgb
        except Exception:
            pass
        st.font.color.rgb = RGBColor.from_string(BLACK)
        # `themeColor` on the same w:color element wins over w:val in Word, so remove it. Setting the
        # rgb above creates the element if it was absent, so this always has something to clean.
        for col in st.element.iter(f"{W}color"):
            for attr in (f"{W}themeColor", f"{W}themeTint", f"{W}themeShade"):
                if attr in col.attrib:
                    del col.attrib[attr]
        changed.append(f"{name}: {before} -> {BLACK}")
    d.save(str(OUT))
    return changed


ABSTRACT_MAX_WORDS = 250          # the journal's limit; enforced rather than checked once by hand


def check_abstract() -> tuple[int, int]:
    """The abstract must be one paragraph and within the journal's word limit.

    Checked on the markdown source rather than the .docx, because that is where it is edited and a
    failure has to point at the file the author would fix.
    """
    src = SRC.read_text(encoding="utf-8")
    blank = chr(10) + chr(10)
    m = re.search("## Abstract" + blank + "(.*?)" + blank + re.escape("**Keywords"), src, re.S)
    if m is None:
        raise SystemExit("abstract not found between the Abstract heading and the Keywords line")
    body = m.group(1)
    return len(body.split()), body.count(blank) + 1


def add_raster_fallbacks() -> list[str]:
    r"""Give every embedded SVG the PNG fallback that Word's own insert produces.

    Pandoc writes the picture as an `<a:blip>` carrying **only** the `svgBlip` extension, with no
    `r:embed` on the blip itself. Word 2016 and later render the SVG and everything older renders
    nothing at all: not a placeholder, not a broken-image box, nothing. The authors' own earlier
    document pairs each SVG with a PNG, which is what Word does when a user inserts one, and this
    reproduces that pairing.

    For each picture: add the matching PNG to the package, register a relationship for it, and set
    `r:embed` on the blip to point at it. The SVG stays where it is in the extension list, so a
    current Word still draws the vector and an older reader draws the raster.
    """
    import shutil
    import tempfile

    with zipfile.ZipFile(str(OUT)) as z:
        names = z.namelist()
        blobs = {n: z.read(n) for n in names}

    doc = blobs["word/document.xml"].decode("utf-8")
    rels_path = "word/_rels/document.xml.rels"
    rels = blobs[rels_path].decode("utf-8")
    ctypes = blobs["[Content_Types].xml"].decode("utf-8")

    added, next_id = [], 9000
    # One picture at a time, so the descr that names the source file and the blip that needs the
    # fallback are matched to each other rather than by position.
    for pic in re.findall(r"<pic:pic>.*?</pic:pic>", doc, flags=re.S):
        m_src = re.search(r'descr="Figures/(figure-\d+)\.svg"', pic)
        m_blip = re.search(r"<a:blip>(?=.*?svgBlip)", pic, flags=re.S)
        if not m_src or not m_blip:
            continue
        png = SRC.parent / "Figures" / f"{m_src.group(1)}.png"
        if not png.exists():
            continue
        next_id += 1
        rid = f"rIdPng{next_id}"
        member = f"word/media/{rid}.png"
        blobs[member] = png.read_bytes()
        rels = rels.replace(
            "</Relationships>",
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument'
            f'/2006/relationships/image" Target="media/{rid}.png"/></Relationships>')
        doc = doc.replace(pic, pic.replace("<a:blip>", f'<a:blip r:embed="{rid}">', 1), 1)
        added.append(f"{m_src.group(1)}: raster fallback {rid}")

    if added and 'Extension="png"' not in ctypes:
        ctypes = ctypes.replace(
            "</Types>",
            '<Default ContentType="image/png" Extension="png"/></Types>')

    blobs["word/document.xml"] = doc.encode("utf-8")
    blobs[rels_path] = rels.encode("utf-8")
    blobs["[Content_Types].xml"] = ctypes.encode("utf-8")

    tmp = Path(tempfile.mkdtemp()) / OUT.name
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in blobs.items():
            z.writestr(n, b)
    shutil.move(str(tmp), str(OUT))
    return added


def audit() -> tuple[dict, dict]:
    import docx
    d = docx.Document(str(OUT))
    text = "\n".join(p.text for p in d.paragraphs)
    for t in d.tables:
        for r in t.rows:
            text += "\n" + " | ".join(c.text for c in r.cells)
    dashes = {k: text.count(v) for k, v in FORBIDDEN.items()}

    xml = zipfile.ZipFile(str(OUT)).read("word/document.xml").decode("utf-8")
    media = [n for n in zipfile.ZipFile(str(OUT)).namelist() if "/media/" in n]
    stats = {
        "words": len(text.split()),
        "tables": len(d.tables),
        # The figures are images now, not specification blocks, so the thing to count is whether they
        # reached the document. Pandoc resolves relative image paths against the working directory and
        # drops what it cannot find *without failing*, so a build with no figures in it looks exactly
        # like a good one until someone opens it.
        "figure_captions": len(re.findall(r"^Figure \d+\. ", text, re.M)),
        "images_embedded": len(media),
        "raster_fallbacks": sum(1 for n in media if n.endswith(".png")),
        "svg_natively_embedded": xml.count("svgBlip"),
        "equations": xml.count("<m:oMath"),
        "headings": sum(1 for p in d.paragraphs if p.style.name.startswith("Heading")),
    }
    return dashes, stats


def main() -> int:
    words, paras = check_abstract()
    print(f"  abstract: {words} words in {paras} paragraph(s)")
    if words > ABSTRACT_MAX_WORDS or paras != 1:
        print()
        print(f"FAIL: the abstract must be one paragraph of at most "
              f"{ABSTRACT_MAX_WORDS} words")
        return 1
    convert()
    for line in blacken_headings():
        print("  " + line)
    for line in add_raster_fallbacks():
        print("  " + line)
    dashes, stats = audit()
    print()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if stats["svg_natively_embedded"] < stats["figure_captions"]:
        print()
        print(f"FAIL: {stats['figure_captions']} figure captions but only "
              f"{stats['svg_natively_embedded']} figures in the document. Pandoc drops an image "
              f"it cannot resolve and still reports success, so this is checked rather than "
              f"assumed.")
        return 1
    bad = {k: v for k, v in dashes.items() if v}
    if bad:
        print(f"\nFAIL: forbidden characters present: {bad}")
        return 1
    print("\nok: no dashes of any kind; headings black in the style definitions")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
