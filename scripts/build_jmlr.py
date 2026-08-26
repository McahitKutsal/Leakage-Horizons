r"""Convert the revised manuscript to JMLR LaTeX, deterministically and checkably.

JMLR accepts LaTeX only, so `paper/penumbra-revised.docx` has to become a `.tex` that compiles
against `jmlr2e.sty` and follows the author guide. Doing that by hand would be a transcription of
34,000 words with no way to tell whether anything was dropped, which is the class of defect Section 9
of the paper is about. So it is a script, and the script checks itself.

Pandoc does the language conversion, which it is good at: OMML becomes `\(...\)`, the tables become
`longtable` bodies with the right column widths, the emphasis survives. Everything pandoc cannot know
about is done here:

* **Front matter.** JMLR wants `\jmlrheading`, `\ShortHeadings`, `\firstpageno`, an `\author` block of
  `\name`/`\email`/`\addr` groups joined by `\AND`, an `\editor`, and `abstract` and `keywords`
  environments. The docx has a centred title block instead, so it is parsed and rebuilt.
* **Citations.** The manuscript is numbered `[1]` to `[46]`; JMLR requires natbib author-year. Each of
  the 54 sites is rewritten as `\citet` where the author's name precedes it in the running text, so the
  name is not printed twice, and `\citep` otherwise. The mapping from number to key is asserted against
  the reference list in the docx rather than assumed.
* **Figures.** The docx carries rasterised SVGs; `\includesvg` needs Inkscape at compile time. They are
  replaced by the vector PDFs the figure generator already produces, matched in reading order.
* **Tables.** Pandoc emits `longtable` with no caption and the caption as the preceding paragraph. Each
  becomes a float with the caption beneath the rule, which is what the guide asks for, except the ones whose
  estimated height exceeds a page, which stay `longtable`.
* **Guide compliance.** Headings are capitalised, the appendices follow the acknowledgements, section
  cross-references are capitalised, and no section opens on a subsection.

The self-checks at the end are the point. They fail the build rather than warn.

    python scripts/build_jmlr.py
    python scripts/build_jmlr.py --keep-raw     # also write the unprocessed pandoc output
"""
from __future__ import annotations

import argparse
import re
import textwrap
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "paper" / "penumbra-revised.docx"
OUT = ROOT / "paper" / "jmlr"
TEX = OUT / "penumbra.tex"
BIB = OUT / "penumbra.bib"
FIGDIR = "figures"

# Reference number to bibliography key, in the order the reference list prints. Asserted against the
# list extracted from the docx below, so a reordering upstream fails the build instead of silently
# shifting every citation by one.
KEYS = [
    "kaufman", "rao", "kapoor_leakage", "reforms", "shchur", "ogb", "tgb", "yang_lp", "poursafaei",
    "cronbach", "jacobs", "geiger", "geirhos", "gururangan", "mccoy", "simmhan", "cheney",
    "datasheets", "modelcards", "paullada", "sambasivan", "henderson", "dodge", "benson", "do_hyper",
    "yoon", "hamilton", "rgcn", "tgn", "cow_igo", "cow_igo2", "eilstrup", "corum", "complexportal",
    "string", "choobdar", "cox", "allison", "prentice", "finegray", "finkelstein", "boxsteff",
    "desta", "atop", "bailey", "mid5",
]
# A distinctive surname per key, used to check the extracted reference list is in this order and to
# decide where a \citet has to swallow the name printed before it.
SURNAME = {
    "kaufman": "Kaufman", "rao": "Rao", "kapoor_leakage": "Kapoor", "reforms": "Kapoor",
    "shchur": "Shchur", "ogb": "Hu", "tgb": "Huang", "yang_lp": "Yang", "poursafaei": "Poursafaei",
    "cronbach": "Cronbach", "jacobs": "Jacobs", "geiger": "Geiger", "geirhos": "Geirhos",
    "gururangan": "Gururangan", "mccoy": "McCoy", "simmhan": "Simmhan", "cheney": "Cheney",
    "datasheets": "Gebru", "modelcards": "Mitchell", "paullada": "Paullada",
    "sambasivan": "Sambasivan", "henderson": "Henderson", "dodge": "Dodge", "benson": "Benson",
    "do_hyper": "Do", "yoon": "Yoon", "hamilton": "Hamilton", "rgcn": "Schlichtkrull",
    "tgn": "Rossi", "cow_igo": "Pevehouse", "cow_igo2": "Pevehouse", "eilstrup": "Eilstrup",
    "corum": "Steinkamp", "complexportal": "Meldal", "string": "Szklarczyk", "choobdar": "Choobdar",
    "cox": "Cox", "allison": "Allison", "prentice": "Prentice", "finegray": "Fine",
    "finkelstein": "Finkelstein", "boxsteff": "Box-Steffensmeier", "desta": "D", "atop": "Leeds",
    "bailey": "Bailey", "mid5": "Palmer",
}

# A table stays breakable when it cannot fit a page, and becomes a float with the caption underneath
# when it can, which is what the guide asks for. The line count is estimated from the cell text rather
# than declared, so adding rows upstream moves a table across the boundary on its own. A JMLR page
# holds about 45 lines of body text; 30 leaves room for the caption, the rules and a float's own
# reluctance to share a page.
LONG_TABLE_LINES = 30

# The title, defined once. It is printed three times — the file header, the running head and the title
# block — and a rename that reaches two of the three is worse than no rename. Short enough for one line
# of the title block and for the running head, which is why \ShortHeadings can take it unchanged: at
# \Large bold it measures about 356pt against a 434pt measure, and the version it replaced measured
# 448pt on its first line alone and ran past the margin.
TITLE = "Leakage Horizons in Group Membership Prediction"

# jmlr2e sets \textwidth to 6 true inches. A rough advance width is enough to catch a line that runs
# past the measure: about 0.55 em per letter in the bold face the title block uses, 0.58 in the small
# caps of the running head, a third of an em for a space. This is for catching 15pt of overflow, not
# for typesetting.
TEXTWIDTH_PT = 6.0 * 72.27

# How wide the flow diagram may be. jmlr2e sets \textwidth to 6 true inches, and a Computer Modern
# typewriter character is half an em, so at \small in an 11pt document — that is 10pt — 86 characters
# fit the measure. Wrapping at 84 leaves a little room rather than trusting the arithmetic exactly.
VERBATIM_SIZE_PT = 10.0
VERBATIM_COLUMNS = int(6.0 * 72.27 / (VERBATIM_SIZE_PT * 0.5)) - 2

# The manuscript cites its appendix tables as A.1, B.1 and C.1. The article class does not reset the
# table counter at an appendix and does not letter it, so those three would print as 12, 13 and 14 and
# every reference to them would be wrong. amsmath's \numberwithin gives the counter the section letter
# and resets it at each \section, which is what the manuscript's own naming assumes.
APPENDIX_HEAD = "\n".join([
    r"\appendix",
    r"%% The appendix tables are cited as A.1, B.1 and C.1. Without this they number 12, 13 and 14.",
    r"\numberwithin{table}{section}",
])

# pdfTeX has no Turkish letters of its own. With T1 fonts loaded, LaTeX's UTF-8 support maps them,
# but writing the accent commands leaves nothing depending on the reader's toolchain, and the author
# names are the one place in this paper where a mangled character is a person's name.
ACCENTS = {
    "\u00fc": '\\"u', "\u00dc": '\\"U', "\u00f6": '\\"o', "\u00d6": '\\"O',
    "\u00e7": "\\c{c}", "\u00c7": "\\c{C}", "\u011f": "\\u{g}", "\u011e": "\\u{G}",
    "\u015f": "\\c{s}", "\u015e": "\\c{S}", "\u0131": "\\i{}", "\u0130": "\\.{I}",
    "\u00e2": "\\^a", "\u00ee": "\\^i", "\u00fb": "\\^u",
    "\u2013": "--", "\u2014": "---", "\u2018": "`", "\u2019": "'",
    "\u201c": "``", "\u201d": "''", "\u2026": "\\ldots{}", "\u00a0": "~",
    "\u00d7": "\\(\\times\\)", "\u2212": "-", "\u2248": "\\(\\approx\\)",
    "\u2264": "\\(\\leq\\)", "\u2265": "\\(\\geq\\)", "\u2032": "\\(\\prime\\)",
}


def asciify(text: str) -> str:
    for ch, esc in ACCENTS.items():
        text = text.replace(ch, esc)
    return text


# The guide asks that a section not open straight on a subsection. Two do, because the docx uses the
# heading itself as the whole of the section's opening. Rather than renumber the paper, each gets one
# sentence naming what its subsections cover; both are descriptive of text that already follows and
# assert nothing new. Recorded in REVISION-LOG.md under the JMLR conversion.
SECTION_LEADS = {
    "3. Problem formulation":
        "This section fixes the objects the diagnostics act on: a corpus and the dating strata its "
        "register imposes, the horizon itself, the two operations the suite applies to a focal group, "
        "and the line between what those operations measure and what they can only entail.",
    "6. Results":
        "The results run from the testbed, where the width is a parameter we set and the answer is "
        "therefore known, to two field corpora, where the width is a property of a register we did not "
        "build, and end at what the horizon costs a model trained across it.",
}

# ---------------------------------------------------------------------------------------------------
# One defect this conversion fixes rather than carries. Section 9 cites REFORMS and the number points
# at the other Kapoor paper: the sentence was rewritten after the bibliography was renumbered and the
# hand-typed number was never remapped. It is exactly the claim-to-artefact class Section 9 describes,
# committed in the section that describes it, so it is corrected here and recorded in the log.
CITATION_FIXES = [
    ("the reporting standard this section is an instance of is REFORMS \\citep{kapoor_leakage}",
     "the reporting standard this section is an instance of is REFORMS \\citep{reforms}"),
]


def run_pandoc() -> str:
    r"""Pandoc's LaTeX, with the line endings made LF.

    Pandoc returns CRLF here. Left alone, every `\n` written back out is translated to `\r\n` again,
    so each line ends `\r\r\n`, and pdfTeX reads the extra carriage return as a second end of line:
    a blank line after every line of the document. Inside a tabular preamble or display maths that is
    a `\par` where one is illegal. The file is written with `newline="\n"` for the same reason.
    """
    import pypandoc
    text = pypandoc.convert_file(str(SRC), "latex", extra_args=["--wrap=none"])
    return text.replace("\r\n", "\n").replace("\r", "\n")


# --------------------------------------------------------------------------------- reference mapping
def check_reference_order(raw: str) -> None:
    """Assert the docx's reference list is in KEYS order, by surname of the first author."""
    sec = raw[raw.index("References}"):raw.index("Data and code availability")]
    m = re.search(r"\\begin\{enumerate\}(.*?)\\end\{enumerate\}", sec, re.S)
    if not m:
        raise SystemExit("FAIL: the reference list is not an enumerate; cannot verify its order")
    items = [re.sub(r"\s+", " ", x).strip()
             for x in re.split(r"\n\s*\\item\s*\n", m.group(1)) if x.strip()]
    items = [x for x in items if not x.startswith("\\def")]
    if len(items) != len(KEYS):
        raise SystemExit(f"FAIL: {len(items)} references in the docx against {len(KEYS)} keys")
    for i, (item, key) in enumerate(zip(items, KEYS), start=1):
        want = SURNAME[key]
        if want.lower() not in item[:200].lower():
            raise SystemExit(f"FAIL: reference {i} should be {key} ({want}) but reads: {item[:90]}")
    print(f"  reference order verified: {len(items)} entries match the key list")


def convert_citations(body: str) -> tuple[str, int, int]:
    r"""`{[}N{]}` becomes \citet or \citep, and a name printed before it is removed.

    natbib prints the author, so "Kaufman et al.~[1]" has to become "\citet{kaufman}" and not
    "Kaufman et al. \citep{kaufman}", which would print the name twice. The rule is mechanical: if the
    text immediately before the marker ends with the cited work's surname, optionally followed by
    "et al." or "and <name>" and an apostrophe-s, that run is replaced by the \citet.
    """
    n_citet = n_citep = 0

    def repl(m: re.Match) -> str:
        nonlocal n_citet, n_citep
        nums = [int(x) for x in re.split(r",\s*", m.group(1).strip())]
        keys = []
        for x in nums:
            if not 1 <= x <= len(KEYS):
                raise SystemExit(f"FAIL: citation [{x}] is outside the reference list")
            keys.append(KEYS[x - 1])
        before = m.string[:m.start()]
        if len(keys) == 1:
            sn = re.escape(SURNAME[keys[0]])
            # "Kaufman et al.~", "Kapoor and Narayanan ", "Cronbach and Meehl's ", "Cox's "
            pat = re.compile(
                r"(" + sn + r"[A-Za-z-]*"
                r"(?:\s+(?:et\s+al\.|and\s+[A-Z][A-Za-z-]+(?:\s+and\s+[A-Z][A-Za-z-]+)?))?"
                r"(?:'s|s')?)(\s|~)*$")
            mm = pat.search(before)
            if mm:
                n_citet += 1
                # keep a possessive: "Cox's [37]" -> "\citet{cox}'s"
                poss = "'s" if mm.group(1).endswith("'s") else ""
                return f"@@CUT{len(mm.group(0))}@@\\citet{{{keys[0]}}}{poss}"
        n_citep += 1
        return "\\citep{" + ", ".join(keys) + "}"

    out = re.sub(r"\{\[\}([\d,\s]+)\{\]\}", repl, body)
    # apply the cuts recorded by the marker, longest first so offsets cannot collide
    for ln in sorted({int(x) for x in re.findall(r"@@CUT(\d+)@@", out)}, reverse=True):
        out = re.sub(r".{" + str(ln) + r"}@@CUT" + str(ln) + r"@@", "", out, flags=re.S)
    leftover = re.findall(r"@@CUT\d+@@", out)
    if leftover:
        raise SystemExit(f"FAIL: {len(leftover)} citation cut markers survived")
    return out, n_citet, n_citep


# --------------------------------------------------------------------------------- figures and tables
def convert_figures(body: str) -> tuple[str, int]:
    r"""`\includesvg` of an extracted raster becomes the vector PDF the figure generator writes.

    The docx carries the figures as rasterised SVGs and `\includesvg` would need Inkscape at compile
    time, so each is replaced by `figures/figure-N.pdf`. N is the position in reading order, and the
    caption below the image says which figure it is, so the two are checked against each other rather
    than assumed to agree: `scripts/build_figures.py` writes `figure-N` from its own `figure_N`, and
    an image inserted out of order in the docx would otherwise attach the wrong plot to the wrong
    caption without anything saying so.
    """
    order = []

    def repl(m: re.Match) -> str:
        order.append(len(order) + 1)
        return f"\\includegraphics[width=\\textwidth]{{{FIGDIR}/figure-{len(order)}.pdf}}"

    body = re.sub(r"\\includesvg(?:\[[^\]]*\])?\{[^}]*\}", repl, body)

    # The caption reads "Figure N. ..." and LaTeX numbers it itself, so the printed number goes. It
    # is checked against the image's position on the way out. No \label: the manuscript refers to its
    # figures by number in running text, and an unused label would only be one more thing to keep
    # true.
    # Brace matching rather than a pattern: a caption holds \textbf{...} and \(...\) groups, and
    # `[^}]*` stops at the first of them and silently truncates the caption at that point.
    captions, dropped = [], []
    pieces, pos = [], 0
    for c in re.finditer(r"\\caption\{", body):
        if c.start() < pos:
            continue
        a, b = braced(body, c.end() - 1)
        h = re.match(r"(\\textbf\{)Figure (\d+)\.\s*", body[a:b])
        if not h:
            raise SystemExit(f"FAIL: a figure caption does not open with its number: {body[a:a+60]!r}")
        captions.append(int(h.group(2)))
        kept, rest = trim_caption(h.group(1) + body[a:b][h.end():])
        dropped += [(f"Figure {h.group(2)}", x) for x in rest]
        pieces.append(body[pos:a] + kept)
        pos = b
    body = "".join(pieces) + body[pos:]
    if captions != order:
        raise SystemExit(f"FAIL: {len(order)} images in reading order against captions numbered "
                         f"{captions}: the image order and the figure numbers do not agree")
    body = re.sub(r"\\begin\{figure\}", "\\\\begin{figure}[!htbp]", body)
    return body, len(order), dropped


def convert_tables(body: str) -> tuple[str, list]:
    r"""Caption paragraph plus captionless longtable becomes a float, or a captioned longtable.

    Pandoc puts the caption in the paragraph before the table and wraps the table in
    `{\def\LTcaptype{none} ... }`. Both halves are rewritten together so a table can never end up
    with the wrong caption: the pairing is positional, and the number the docx printed is returned so
    the caller can check the order against the cross-references in the running text.

    Pandoc's body is uniform across all fourteen tables:

        \begin{longtable}[]{SPEC}
        \toprule\noalign{}
        HEAD \\
        \midrule\noalign{}
        \endhead
        \bottomrule\noalign{}
        \endlastfoot
        DATA
        \end{longtable}

    so it is parsed rather than patched. Deleting the `\endhead` and `\endlastfoot` markers and
    leaving everything else, which is what this function did first, moves the bottom rule into the
    middle of the table and leaves the table with no rule at its foot.
    """
    pat = re.compile(
        r"\\textbf\{Table ([0-9A-Z.]+)\.\}\s*(.*?)\n\s*\n"          # caption paragraph
        r"\{\\def\\LTcaptype\{none\}[^\n]*\n"                        # pandoc's wrapper
        r"(.*?\\end\{longtable\})\s*\}",                             # the table itself
        re.S)
    seen, decisions, dropped = [], [], []

    def parse(table: str, num: str) -> tuple[str, str, str]:
        m = re.match(r"\\begin\{longtable\}\[\]\s*(\{.*?\})\s*\n\\toprule", table, re.S)
        if not m:
            raise SystemExit(f"FAIL: table {num} does not start the way pandoc writes tables")
        spec = m.group(1)
        rest = table[m.end() - len("\\toprule"):]
        try:
            head, rest = rest.split("\\endhead", 1)
            _, data = rest.split("\\endlastfoot", 1)
        except ValueError:
            raise SystemExit(f"FAIL: table {num} has no \\endhead/\\endlastfoot to split on")
        head = head.replace("\\toprule\\noalign{}", "").replace("\\midrule\\noalign{}", "")
        data = data.replace("\\end{longtable}", "")
        # A blank line in the column specification is a `\par` in the tabular preamble, which is
        # "Illegal pream-token", and a blank line in a cell is a `\par` in an alignment entry. Pandoc
        # does not write either, but it costs nothing to be sure, since only a compiler would say so.
        squeeze = lambda x: re.sub(r"\n\s*\n+", "\n", x).strip()
        return squeeze(spec), squeeze(head), squeeze(data)

    def estimate_lines(data: str, n_cols: int) -> int:
        """Roughly how many typeset lines the body will take, from the widest cell in each row."""
        per_line = max(1, 62 // max(n_cols, 1) * 2)   # characters a \small p-column fits
        total = 0
        for row in (r for r in data.split("\\\\") if r.strip()):
            widest = max((len(re.sub(r"\s+", " ", c).strip()) for c in row.split("&")), default=0)
            total += max(1, -(-widest // per_line))
        return total

    def repl(m: re.Match) -> str:
        num, caption, table = m.group(1), re.sub(r"\s+", " ", m.group(2).strip()), m.group(3)
        seen.append(num)
        caption, rest = trim_caption(caption)
        dropped.extend((f"Table {num}", x) for x in rest)
        label = f"tab:{num.replace('.', '-')}"
        spec, head, data = parse(table, num)
        cap = f"\\caption{{{caption}}}\\label{{{label}}}"
        n_cols = spec.count("\\real{") or head.count("&") + 1
        lines = estimate_lines(data, n_cols)
        breakable = lines >= LONG_TABLE_LINES
        decisions.append((num, lines, "longtable" if breakable else "float"))
        if breakable:
            # Breakable, so the caption goes in the first head and the head repeats without it. This
            # is longtable's own documented pattern.
            # The size change wraps the environment: between \begin{longtable} and the first row
            # the alignment is already open and \small there is a misplaced token.
            return ("\\begingroup\\small\n\\begin{longtable}" + spec + "\n"
                    + cap + "\\\\\n\\toprule\n" + head + "\n\\midrule\n\\endfirsthead\n"
                    + "\\toprule\n" + head + "\n\\midrule\n\\endhead\n"
                    + "\\bottomrule\n\\endlastfoot\n" + data + "\n\\end{longtable}\n\\endgroup")
        # A float, caption underneath the rule as the guide asks.
        return ("\\begin{table}[!htbp]\n\\centering\n\\small\n"
                + "\\begin{tabular}" + spec + "\n\\toprule\n" + head + "\n\\midrule\n"
                + data + "\n\\bottomrule\n\\end{tabular}\n"
                + cap + "\n\\end{table}")

    body = pat.sub(repl, body)
    long_ones = [f"{n} ({ln})" for n, ln, kind in decisions if kind == "longtable"]
    print(f"    breakable, by estimated line count: {', '.join(long_ones) or 'none'}")
    return body, seen, dropped


def check_table_rows(tex: str) -> list:
    r"""Every row of a table must have the same number of `&` as the rest of its table.

    A tabular whose rows disagree on column count is the commonest way a converted table fails to
    compile, and it is invisible in the source. Rows carrying \multicolumn are exempt.
    """
    fails = []
    for env in ("tabular", "longtable"):
        for m in re.finditer(r"\\begin\{" + env + r"\}(.*?)\\end\{" + env + r"\}", tex, re.S):
            block = m.group(1)
            spec_end = block.index("\n")
            rows = [r for r in re.split(r"\\\\", block[spec_end:]) if r.strip()]
            counts = {}
            for r in rows:
                if "\\multicolumn" in r or "\\caption" in r:
                    continue
                body_only = re.sub(r"\\(toprule|midrule|bottomrule|endfirsthead|endhead|"
                                   r"endlastfoot|noalign\{\})", "", r)
                if not body_only.strip():
                    continue
                counts.setdefault(body_only.count("&"), []).append(body_only.strip()[:40])
            if len(counts) > 1:
                modal = max(counts, key=lambda k: len(counts[k]))
                for k, examples in counts.items():
                    if k != modal:
                        fails.append(f"a {env} row has {k + 1} columns where the table has "
                                     f"{modal + 1}: {examples[0]!r}")
    return fails


def check_cross_references(tex: str, n_fig: int, tables: list) -> list:
    """Every "Table N", "Figure N", "Section N" and "Appendix X" in the text must exist.

    The manuscript refers to its floats by number in running text rather than by \\ref, so LaTeX's own
    numbering has to agree with what the sentences say. It does only if the floats appear in the same
    order the docx numbered them, which is what this checks.
    """
    fails = []
    numbered = [t for t in tables if t[0].isdigit()]
    lettered = [t for t in tables if t[0].isalpha()]
    if numbered != [str(i) for i in range(1, len(numbered) + 1)]:
        fails.append(f"the body's tables are numbered {numbered}, not 1 to {len(numbered)} in order")
    if lettered != sorted(lettered):
        fails.append(f"the appendix tables are out of order: {lettered}")
    if tables != numbered + lettered:
        fails.append("an appendix table appears before a body table")
    n_sec = len(re.findall(r"\n\\section\{", tex[:tex.index("\\appendix")]))
    for m in re.finditer(r"\b(Table|Figure) (\d+)\b", tex):
        kind, num = m.group(1), int(m.group(2))
        limit = n_fig if kind == "Figure" else len([t for t in tables if t[0].isdigit()])
        if num > limit:
            fails.append(f"the text cites {kind} {num} and there are {limit}")
    for m in re.finditer(r"\bSection (\d+)", tex):
        if int(m.group(1)) > n_sec:
            fails.append(f"the text cites Section {m.group(1)} and there are {n_sec}")
    for m in re.finditer(r"\bAppendix ([A-Z])\b", tex):
        if m.group(1) not in ("A", "B", "C"):
            fails.append(f"the text cites Appendix {m.group(1)}, which does not exist")
    return fails


# --------------------------------------------------------------------------------- structure
CAPTION_SENTENCES = 2

# The manuscript's own checker uses 250, so this one does too rather than inventing a second
# standard. The complaint was never the length: it was ten numeric tokens in eleven sentences,
# two of them the same digits standing for a percentage in one place and a ratio in another.
# The fourth external reading said the sentences run to forty words and more with nested clauses,
# and the measurement agreed: 157 of 967 prose sentences, 16.2 percent. Ninety-two edits later it is
# 10.6 percent. The share is checked rather than the individual sentence, because a long sentence is
# not a defect and a document full of them is: an enumeration of six data sources reads straight
# through at seventy words, and breaking it up would make it worse.
LONG_SENTENCE_WORDS = 40
LONG_SENTENCE_SHARE = 0.12

ABSTRACT_MAX_WORDS = 250
ABSTRACT_MAX_NUMBERS = 6

# Round three of the external reading: the writing. The revision tags are the mechanical half — the
# body carried thirty-eight of them and Appendix B carries all twenty in a table, so in the body they
# are noise pointing at a list the reader can already find. Deleted by pattern rather than one at a
# time, and the pattern is parenthesised so Appendix B's own "R1" column is untouched.
REGEX_EDITS = [
    (r"\s*\(R\d+(?:\s*,\s*R\d+)*\)", "", "revision tags, which belong to Appendix B"),
]

# The prose half lives in a file rather than in this script, so that each change can be read against
# the text it replaces. Every entry must match exactly once across the abstract and the body; an entry
# that matches nothing fails the build, and one whose replacement is already in place is reported as
# no longer needed.
# One file per round of external reading, applied in order. Keeping them apart is what lets a round
# be read as a unit and, if an author disagrees with one, removed as a unit.
EDITS_FILES = [ROOT / "paper" / "round3-edits.txt",
               ROOT / "paper" / "round4-edits.txt",
               ROOT / "paper" / "round4-splits.txt",
               ROOT / "paper" / "round4-splits2.txt",
               ROOT / "paper" / "round5-edits.txt",
               ROOT / "paper" / "round6-edits.txt"]

# Wording retired by a decision rather than by a measurement, which no other check would catch. The
# manuscript was written for Knowledge-Based Systems and opened by calling the thing a knowledge-based
# system; the journal changed and the phrase names a tradition this paper is not in.
RETIRED_WORDING = [
    (r"knowledge[- ]based system", "the paper is not about knowledge-based systems"),
]


def deposit_doi() -> str:
    r"""The DOI from the declaration manifest, or "" while the bundle is undeposited.

    The manuscript does not carry the DOI as typed text. It is one field in
    `declaration/MANIFEST.json`, written there by `build_declaration.py --doi`, and the placeholder in
    the availability section is replaced from it. A number that appears in a paper and in an artefact
    should be entered once, which is the fifth of Section 9's questions applied to this paper's own
    front matter.
    """
    import json
    man = ROOT / "declaration" / "MANIFEST.json"
    if not man.exists():
        return ""
    got = json.loads(man.read_text(encoding="utf-8")).get("deposit_identifier", "")
    got = got.strip()
    if not got or got.upper().startswith("TO BE COMPLETED"):
        return ""
    if not re.match(r"^10\.\d{4,9}/\S+$", got):
        raise SystemExit(f"FAIL: the manifest's deposit_identifier is not a DOI: {got!r}")
    return got


def load_edits(path: Path) -> list:
    """Parse the edit file: blocks of `### reason`, `--- find`, `--- replace`."""
    if not path.exists():
        return []
    edits, reason, mode, buf = [], None, None, {"find": [], "replace": []}
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("### "):
            if reason is not None:
                edits.append((reason, "\n".join(buf["find"]).strip("\n"),
                              "\n".join(buf["replace"]).strip("\n")))
            reason, mode, buf = line[4:].strip(), None, {"find": [], "replace": []}
        elif line.strip() == "--- find":
            mode = "find"
        elif line.strip() == "--- replace":
            mode = "replace"
        elif line.startswith("---"):
            # An unrecognised directive would otherwise be appended to the text as content, and
            # "---" is an em dash in LaTeX, so it would reach the page as one.
            raise SystemExit(f"FAIL: {path.name} has a directive that is neither find nor replace: "
                             f"{line!r}")
        elif line.startswith("#"):
            # A comment is a comment wherever it appears, not only before the first block. Skipping
            # them only while no block was open let the separators between blocks fall into the
            # replacement text, and a bare "#" in LaTeX is a macro parameter character, so the
            # document would not have compiled. Check 6 now looks for one.
            continue
        elif mode:
            buf[mode].append(line)
    if reason is not None:
        edits.append((reason, "\n".join(buf["find"]).strip("\n"),
                      "\n".join(buf["replace"]).strip("\n")))
    return [e for e in edits if e[1]]


def apply_edits(parts: dict) -> dict:
    """Apply each round's edits to the abstract, the body and the acknowledgements.

    An edit has to match exactly once across the three, because a `find` that matches twice would
    change a sentence nobody looked at, and one that matches nothing means the source moved under it.
    """
    # The accents and the punctuation are written as commands first, so an edit file is written
    # against the .tex as a person reads it. Without this the find strings have to carry a Unicode
    # minus or a curly quote that the document no longer contains, which is invisible in a text editor
    # and fails as a mismatch nobody can see.
    parts = {k: asciify(v) for k, v in parts.items()}

    # The mechanical pass runs first. A prose edit is written against the text as the document
    # ends up reading, and until the revision tags are gone the text still carries them, so an
    # edit quoting a sentence that ends in a full stop cannot match a sentence that ends in
    # "(R13).", and the candidate sentences were read off the finished file.
    for pattern, replace, reason in REGEX_EDITS:
        n = sum(len(re.findall(pattern, v)) for v in parts.values())
        for k in parts:
            parts[k] = re.sub(pattern, replace, parts[k])
        print(f"  removed {n} {reason}")

    done = already = 0
    for path in EDITS_FILES:
        for reason, find, replace in load_edits(path):
            hits = {k: v.count(find) for k, v in parts.items()}
            n = sum(hits.values())
            if n == 1:
                for k in parts:
                    if hits[k]:
                        parts[k] = parts[k].replace(find, replace, 1)
                done += 1
            elif n == 0 and replace and any(replace in v for v in parts.values()):
                already += 1
            elif n == 0:
                raise SystemExit(f"FAIL: an edit in {path.name} matches nothing, so the source "
                                 f"moved under it ({reason}): {find[:90]!r}")
            else:
                raise SystemExit(f"FAIL: an edit in {path.name} matches {n} times and has to "
                                 f"match once ({reason}): {find[:90]!r}")
    if done or already:
        print(f"  round-edit files: {done} applied"
              + (f", {already} already in the source" if already else ""))
    return parts


def braced(text: str, i: int) -> tuple[int, int]:
    """Given the index of a `{`, the span of what it encloses. Nesting counts."""
    depth = 0
    for k in range(i, len(text)):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                return i + 1, k
    raise SystemExit("FAIL: an unclosed brace in a caption")


def sentences(text: str) -> list:
    r"""Split a caption into sentences without splitting a decimal, a symbol or a bold lead-in.

    `0.0152` and `\(k = 1\)` are hidden before the split and restored after it, and a run ending
    `.}` ends a sentence too, because the captions put their opening clause in `\textbf{...}` with the
    full stop inside the braces.
    """
    holes: list = []

    def hide(m: re.Match) -> str:
        holes.append(m.group(0))
        return f"\x00{len(holes) - 1}\x00"

    t = re.sub(r"\\\(.*?\\\)", hide, text, flags=re.S)
    t = re.sub(r"\d+\.\d+", hide, t)
    parts = re.split(r"(?<=\.)\s+|(?<=\.\})\s+", t)
    return [re.sub(r"\x00(\d+)\x00", lambda m: holes[int(m.group(1))], x).strip()
            for x in parts if x.strip()]


def trim_caption(caption: str) -> tuple[str, list]:
    r"""Keep the opening sentences, return the rest.

    The docx captions run to eight sentences and 216 words. The first says what the float is and the
    second gives the setup a reader needs to read it — the corpus, the counts, the lead times, how the
    intervals were taken. What follows describes the panels and argues from them, which is the body's
    work. Cutting at two sentences is mechanical, so no caption is shortened by anyone's judgement of
    which of its claims matters.
    """
    ss = sentences(caption)
    return " ".join(ss[:CAPTION_SENTENCES]), ss[CAPTION_SENTENCES:]


def definitions_in(sentence: str) -> list:
    r"""The terms and symbols a caption sentence defines.

    `\textbf{censored}` names a column of Table 4; `\(k = 25\)` is a level Figure 7 is read at. A
    dropped sentence carrying either is one whose loss could change what a reader can do with the
    float rather than only what they are told about it, so it is checked rather than assumed.
    """
    keys = re.findall(r"\\textbf\{([^{}]+)\}", sentence)
    keys += re.findall(r"\\\((.+?)\\\)", sentence)
    return [k for k in keys if len(k.strip()) > 2]


def _flat(x: str) -> str:
    """Compare maths by what it says, not by how it is spelled: braces and slashes go."""
    return re.sub(r"[\\{}^_ ,]", "", x)


def orphaned(sentence: str, prose: str) -> bool:
    """A definition is orphaned when the body names none of what it defined."""
    keys = definitions_in(sentence)
    if not keys:
        return False
    flat = _flat(prose)
    return not any(_flat(k) in flat for k in keys)


WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
           "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
           "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
           "nineteen": 19, "twenty": 20}


def sentence_lengths(tex: str) -> tuple:
    """The share of prose sentences at or over LONG_SENTENCE_WORDS, and the count."""
    body = tex[tex.index("\\section{Introduction}"):]
    prose = re.sub(r"\\begin\{(table|figure|longtable|verbatim)\}.*?\\end\{\1\}", " ", body,
                   flags=re.S)
    prose = re.sub(r"\\begingroup.*?\\endgroup", " ", prose, flags=re.S)
    prose = re.sub(r"\\(?:sub)?section\{[^}]*\}", " ", prose)
    prose = re.sub(r"\s*\n\s*", " ", prose)
    lens = []
    for sent in re.split(r"(?<=\.)\s+(?=[A-Z\\(])", prose):
        if len(sent.strip()) < 4:
            continue
        plain = re.sub(r"\\[a-zA-Z]+\*?", " ", sent)
        plain = re.sub(r"[{}$\\]", " ", plain)
        lens.append(len(re.findall(r"[A-Za-z][A-Za-z'-]*", plain)))
    long_ones = [x for x in lens if x >= LONG_SENTENCE_WORDS]
    return len(long_ones) / max(len(lens), 1), len(long_ones), len(lens)


def check_appendix_b_counts(tex: str) -> list:
    r"""The number Appendix B gives for its own outside reads must be the number of rows that say so.

    The fourth external reading found this: the appendix said thirteen of the twenty were found from
    outside, having borrowed Section 9's count of *defects* for a count of its own *rows*, of which
    eleven mention an outside read. It is the claim-to-artefact class the paper is about, committed in
    the appendix that tabulates the paper's own corrections, and no check could see it because every
    check compared numbers to artefacts and none compared a number to a table in the same document.
    """
    fails = []
    if "\\label{app:B}" not in tex:
        return ["Appendix B is not labelled, so its row counts cannot be checked"]
    start = tex.index("\\label{app:B}")
    end = tex.index("\\section", tex.index("\\end{longtable}", start))
    block = tex[start:end]

    rows, involved, first = 0, 0, 0
    for row in re.split(r"\\\\", block):
        cells = row.split("&")
        if len(cells) != 4 or not re.search(r"\bR\d+\b", cells[0]):
            continue
        rows += 1
        tag = cells[3].lower()
        if "outside read" in tag:
            involved += 1
            if tag.strip().startswith("outside read"):
                first += 1
    if rows == 0:
        return ["Appendix B's table has no R-numbered rows, so nothing can be counted"]

    # "Eleven of the twenty rows record an outside read, ten where the read came first"
    m = re.search(r"(\w+) of the (\w+) rows record an outside read,\s*(\w+) where the read came "
                  r"first", block)
    if not m:
        return [f"Appendix B does not state how many of its {rows} rows record an outside read, "
                f"so the claim cannot be checked against the table"]
    said_involved = WORDNUM.get(m.group(1).lower())
    said_rows = WORDNUM.get(m.group(2).lower())
    said_first = WORDNUM.get(m.group(3).lower())
    if said_rows != rows:
        fails.append(f"Appendix B says it lists {m.group(2)} rows and the table has {rows}")
    if said_involved != involved:
        fails.append(f"Appendix B says {m.group(1)} rows record an outside read and {involved} do")
    if said_first != first:
        fails.append(f"Appendix B says the read came first in {m.group(3)} rows and it does in "
                     f"{first}")
    return fails


def visible(text: str) -> str:
    r"""Roughly what a reader sees, so a width can be estimated: `\u{g}` is one letter, not five."""
    text = re.sub(r"\\[a-zA-Z]+\{([a-zA-Z])\}", r"\1", text)          # \u{g}, \c{c}
    text = re.sub(r"\\[\"\'^.`~]\{?([a-zA-Z])\}?", r"\1", text)        # \"u, \'e
    text = re.sub(r"\\[a-zA-Z]+", "", text)                          # whatever is left
    return text.replace("{", "").replace("}", "")


def estimate_width(text: str, size_pt: float, letter_em: float) -> float:
    return sum((0.33 if c == " " else letter_em) * size_pt for c in visible(text))


def rewrap_verbatim(text: str) -> str:
    r"""Rewrap the count-chain diagram to JMLR's measure, and set it one size down.

    The docx wrapped this block by hand for a wider page: its longest line is 98 characters, and a six
    inch measure fits 78 of them at 11pt. Left as it was it ran an inch and a half off the right edge,
    which is a `verbatim` running past the margin rather than a warning about one, so nothing in the
    log would have named it.

    The structure carries meaning and is preserved. An unindented line is a count the register itself
    reports. A line opening `  -> ` is a filter applied to the count above it, and the lines indented
    under it are that filter's explanation, so each filter is rewrapped as one unit with its
    continuation aligned under the text rather than under the arrow.
    """
    units: list[str] = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("     ") and units:      # a continuation of the unit above
            units[-1] += " " + line.strip()
        else:
            units.append(line.rstrip())

    out: list[str] = []
    for u in units:
        if u.startswith("  -> "):
            first, cont, body = "  -> ", "     ", u[len("  -> "):]
        else:
            first, cont, body = "", "  ", u
        out += textwrap.wrap(body, width=VERBATIM_COLUMNS, initial_indent=first,
                             subsequent_indent=cont, break_long_words=False,
                             break_on_hyphens=False)

    over = [l for l in out if len(l) > VERBATIM_COLUMNS]
    if over:
        raise SystemExit(f"FAIL: a diagram line will not fit in {VERBATIM_COLUMNS} columns "
                         f"even after wrapping: {over[0]!r}")
    # The size change wraps the environment: verbatim inherits the surrounding size, and a group is
    # what keeps it from leaking into the paragraph after it.
    return "{\\small\n\\begin{verbatim}\n" + "\n".join(out) + "\n\\end{verbatim}\n}"


def capitalise_heading(t: str) -> str:
    """Title-case a heading, leaving small words, acronyms and maths alone."""
    # Articles, coordinating conjunctions and short prepositions only. Interrogatives, verbs and
    # adverbs are capitalised: "What Is Measured", not "what is Measured".
    small = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "nor", "of", "on", "or",
             "the", "to", "with", "via", "vs"}
    words = t.split()
    out = []
    for i, w in enumerate(words):
        if w.startswith("$") or w.isupper() or any(c.isdigit() for c in w):
            out.append(w)
        elif i == 0 or i == len(words) - 1 or w.lower() not in small:
            out.append(w[0].upper() + w[1:] if w[:1].islower() else w)
        else:
            out.append(w.lower())
    return " ".join(out)


def split_document(raw: str) -> list:
    """Every heading in document order, with the text that follows it.

    Walking the document rather than indexing by title is what makes the conversion lossless: a
    subsection's body belongs to the subsection, and picking out top-level titles by name silently
    drops it. The first version of this script did exactly that and lost half the paper, which the
    validator caught on the count of resolved citations.
    """
    pat = re.compile(r"\\(?:sub){0,2}section\{([^}]*)\}(?:\\label\{[^}]*\})?")
    heads = [(m.start(), m.end(), m.group(1)) for m in pat.finditer(raw)]
    out = []
    for k, (start, after, title) in enumerate(heads):
        nxt = heads[k + 1][0] if k + 1 < len(heads) else len(raw)
        out.append({"title": title.strip(), "body": raw[after:nxt].strip()})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-raw", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    # A submission is one archive, so the figures live inside it rather than a directory above it.
    import shutil
    (OUT / FIGDIR).mkdir(exist_ok=True)
    for src in sorted((ROOT / "paper" / "Figures").glob("figure-*.pdf")):
        shutil.copy2(src, OUT / FIGDIR / src.name)
    print("converting", SRC.name)
    raw = run_pandoc()
    if args.keep_raw:
        (OUT / "_raw.tex").write_text(raw, encoding="utf-8", newline="\n")
    check_reference_order(raw)

    blocks = split_document(raw)
    titles = [b["title"] for b in blocks]
    for need in ("Abstract", "References", "Data and code availability",
                 "Declaration of competing interest", "CRediT authorship contribution statement",
                 "Acknowledgements"):
        if need not in titles:
            raise SystemExit(f"FAIL: section absent from the docx: {need}")

    by_title = {b["title"]: b["body"] for b in blocks}
    abstract_raw = by_title["Abstract"]
    acks = by_title["Acknowledgements"]

    # Everything from section 1 to the end, in document order, with the level each heading takes in
    # LaTeX. The numbered prefixes go: LaTeX numbers the headings itself.
    NUMBERED = re.compile(r"^(\d+)\.\s+(.*)$")
    SUBNUM = re.compile(r"^(\d+\.\d+)\s+(.*)$")
    APPX = re.compile(r"^Appendix ([A-Z])\.\s*(.*)$")
    BACK = ("Data and code availability", "Declaration of competing interest",
            "CRediT authorship contribution statement")

    body_chunks, back_chunks, app_chunks = [], [], []
    n_sec = n_sub = n_app = n_lead = 0
    for b in blocks:
        t, inner = b["title"], b["body"]
        if t in ("Highlights", "Abstract", "Acknowledgements", "References"):
            continue
        if b is blocks[0]:
            # The docx opens with its own centred title block. The title printed in the .tex comes
            # from TITLE above, so this one is dropped rather than converted — by position, so that
            # retitling the docx does not silently turn its title into a section.
            continue
        m = APPX.match(t)
        if m:
            n_app += 1
            app_chunks.append("\\section{" + capitalise_heading(m.group(2)) + "}\n"
                              "\\label{app:" + m.group(1) + "}\n\n" + inner)
            continue
        if t in BACK:
            back_chunks.append("\\section{" + capitalise_heading(t) + "}\n\n" + inner)
            continue
        m = SUBNUM.match(t)
        if m:
            n_sub += 1
            body_chunks.append("\\subsection{" + capitalise_heading(m.group(2)) + "}\n\n" + inner)
            continue
        m = NUMBERED.match(t)
        if m:
            n_sec += 1
            if not inner:
                lead = SECTION_LEADS.get(t)
                if lead is None:
                    raise SystemExit(f"FAIL: section {t!r} opens on a subsection and has no lead-in")
                inner = lead
                n_lead += 1
            body_chunks.append("\\section{" + capitalise_heading(m.group(2)) + "}\n\n" + inner)
            continue
        raise SystemExit(f"FAIL: heading fits no pattern and would be dropped: {t!r}")

    if n_sec != 11:
        raise SystemExit(f"FAIL: expected 11 numbered sections, emitted {n_sec}")
    if n_app != 3:
        raise SystemExit(f"FAIL: expected 3 appendices, emitted {n_app}")
    print(f"  structure: {n_sec} sections, {n_sub} subsections, {n_app} appendices, "
          f"{len(back_chunks)} back-matter sections")
    if n_lead:
        print(f"  wrote {n_lead} section lead-in(s) so no section opens on a subsection")
    if n_lead != len(SECTION_LEADS):
        raise SystemExit(f"FAIL: {len(SECTION_LEADS)} lead-ins defined but {n_lead} were needed; "
                         "the docx headings changed and SECTION_LEADS is stale")

    whole = ("\n\n".join(body_chunks) + "\n\n" + "\n\n".join(back_chunks)
             + "\n\n@@APPENDICES@@\n\n" + "\n\n".join(app_chunks))

    whole, n_citet, n_citep = convert_citations(whole)
    for a, b in CITATION_FIXES:
        if a in whole:
            whole = whole.replace(a, b)
            print("  applied citation fix:", b[-30:])
        elif b in whole:
            # The docx was rebuilt from a corrected source, so there is nothing to correct. Reporting
            # it rather than passing silently: a fix that stops firing is either done or broken, and
            # the difference matters.
            print("  citation fix no longer needed, the source is already right:", b[-30:])
        else:
            raise SystemExit(f"FAIL: citation fix matched neither form; the sentence changed: "
                             f"{a[:70]}")
    # natbib reads the key list literally, so a space after a comma becomes part of a key
    whole = re.sub(r"(\\cite[tp]\{)([^}]*)\}",
                   lambda m: m.group(1) + re.sub(r",\s*", ",", m.group(2)) + "}", whole)
    kw = re.search(r"\\textbf\{Keywords:\}\s*(.*)", abstract_raw)
    if not kw:
        raise SystemExit("FAIL: no keywords line found in the abstract block")
    keywords = kw.group(1).strip().rstrip(".")
    abstract = re.sub(r"\\textbf\{Keywords:\}.*", "", abstract_raw, flags=re.S).strip()

    doi = deposit_doi()
    if doi:
        marker = "{[}ARCHIVE-DOI{]}"
        if marker not in whole:
            raise SystemExit("FAIL: the manifest carries a DOI and the manuscript has no placeholder "
                             "for it, so it would go unprinted")
        whole = whole.replace(marker, "\\url{https://doi.org/" + doi + "}")
        print(f"  deposit DOI from declaration/MANIFEST.json: {doi}")
    else:
        print("  the declaration is not deposited yet, so [ARCHIVE-DOI] stands; run "
              "build_declaration.py --doi once it is")

    parts = apply_edits({"abstract": abstract, "body": whole, "acknowledgements": acks})
    abstract, whole, acks = parts["abstract"], parts["body"], parts["acknowledgements"]

    whole, n_fig, cut_figs = convert_figures(whole)
    whole, tables, cut_tabs = convert_tables(whole)

    # A blank line inside display maths ends the paragraph before the maths closes. The one
    # \underbrace carrying a two-row \begin{matrix} is where that would show up first.
    def squeeze_math(m: re.Match) -> str:
        return "\\[" + re.sub(r"\n\s*\n+", "\n", m.group(1)) + "\\]"

    whole = re.sub(r"\\\[(.*?)\\\]", squeeze_math, whole, flags=re.S)

    # the flow diagram: pandoc turned each line into its own paragraph inside verbatim, and the
    # docx's own line breaks are for a wider measure than JMLR's
    whole = re.sub(r"\\begin\{verbatim\}(.*?)\\end\{verbatim\}",
                   lambda m: rewrap_verbatim(m.group(1)), whole, flags=re.S)

    # JMLR has no highlights section, and every one of the five lines restates a sentence of the
    # abstract, so they are dropped rather than parked somewhere the class does not typeset.
    tex = TEMPLATE.format(
        title=TITLE, abstract=abstract, keywords=keywords,
        body=whole.replace("@@APPENDICES@@", "\\acks{" + acks + "}\n\n\\newpage\n\n" + APPENDIX_HEAD),
    )
    # Last, so that the acknowledgements and the abstract are covered too: they reach the document
    # through the template rather than through the body.
    tex = asciify(tex)
    TEX.write_text(tex, encoding="utf-8", newline="\n")

    print(f"  citations: {n_citet} \\citet, {n_citep} \\citep")
    print(f"  figures: {n_fig}   tables: {len(tables)} "
          f"({', '.join(tables)})")
    share, n_long, n_all = sentence_lengths(tex)
    print(f"  prose: {n_all} sentences, {n_long} of {LONG_SENTENCE_WORDS} words or more "
          f"({share*100:.1f} percent)")
    print(f"  wrote {TEX} ({len(tex):,} chars)")
    # Who the authors are is not something this script can decide, but it can say when the paper
    # disagrees with itself about it. The byline and the contribution statement have to name the same
    # people: a name in one and not the other is a defect a reader sees on the first page.
    byline = set(re.findall(r"\\name (.+?) \\email", tex))
    names = r"\\textbf\{((?:[^{}:]|\{[^{}]*\})+):\}"
    credit = set(re.findall(names, tex[tex.index("CRediT"):tex.index("\\acks")]))
    only_credit = sorted(credit - byline)
    only_byline = sorted(byline - credit)
    if only_credit or only_byline:
        print("  AUTHOR DECISION OUTSTANDING: the byline and the contribution statement disagree.")
        for n in only_credit:
            print(f"    contributes but is not on the byline: {n}")
        for n in only_byline:
            print(f"    on the byline but contributes nothing: {n}")
        print("    Left as the manuscript has it. Resolving it is not this script's call.")

    # What the captions lost, written out rather than summarised, because a caption sentence that is
    # gone from the paper is gone whether or not anyone reads the count.
    cut = cut_figs + cut_tabs
    if cut:
        lines = ["# Caption sentences the conversion dropped", "",
                 f"Every caption is cut to its first {CAPTION_SENTENCES} sentences: what the float is,",
                 "and the setup a reader needs to read it. What follows described the panels and argued",
                 "from them, which is the body's work. Listed here so that nothing left the paper",
                 "unrecorded, and so that a sentence worth keeping can be moved into the body.", ""]
        # A dropped sentence that defined something is only a loss if the body does not name it too.
        # Captions with their own captions removed is what "the body" means here.
        prose = whole
        for c in reversed(list(re.finditer(r"\\caption\{", prose))):
            a, b = braced(prose, c.end() - 1)
            prose = prose[:c.start()] + prose[b + 1:]

        defined, orphans = [], []
        for name in sorted({n for n, _ in cut}, key=lambda x: (x.split()[0], x.split()[1])):
            lines.append(f"## {name}")
            lines.append("")
            for n, sentence in cut:
                if n != name:
                    continue
                keys = definitions_in(sentence)
                mark = ""
                if keys and orphaned(sentence, prose):
                    mark = f" **[defines {keys[0]!r} and the body does not name it]**"
                    orphans.append((name, keys[0]))
                elif keys:
                    mark = f" *(defines {keys[0]!r}; the body names it too)*"
                    defined.append((name, keys[0]))
                lines.append(f"- {asciify(sentence)}{mark}")
            lines.append("")
        (OUT / "captions-trimmed.md").write_text("\n".join(lines), encoding="utf-8",
                                                 newline="\n")
        print(f"  captions cut to {CAPTION_SENTENCES} sentences: {len(cut)} sentence(s) dropped "
              f"from {len({n for n, _ in cut})} floats, listed in captions-trimmed.md")
        if defined:
            print(f"    {len(defined)} dropped sentence(s) defined something, and the body names "
                  f"each: " + ", ".join(f"{n} {k!r}" for n, k in defined))
        for name, key in orphans:
            print(f"    ATTENTION: {name}'s caption defined {key!r} and nothing else in the paper "
                  f"names it; move that sentence into the body")

    todo = sorted(set(re.findall(r"\{\[\}([A-Z][A-Z0-9-]+)\{\]\}", tex))
                  | set(re.findall(r"\\email (EMAIL-[A-Z]+)", tex)))
    if todo:
        print("  still to fill in before submission: " + ", ".join(todo))
    return validate(tex, n_fig, tables)


TEMPLATE = r"""%% {title}.
%% Generated from paper/penumbra-revised.docx by scripts/build_jmlr.py -- edit the source, not this.
\documentclass[twoside,11pt]{{article}}

\usepackage{{jmlr2e}}

%% jmlr2e loads epsfig, amssymb, natbib, graphicx and hyperref. These are the ones it does not.
\usepackage[T1]{{fontenc}}     % accented letters as glyphs, and hyphenation across them
\usepackage{{amsmath}}          % \underbrace with limits, \substack, \binom
\usepackage{{booktabs}}         % \toprule, \midrule, \bottomrule in the tables
\usepackage{{longtable}}        % the tables that cannot fit a page stay breakable
\usepackage{{array}}            % >{{\raggedright\arraybackslash}} column specs
\usepackage{{calc}}             % \real{{}} in the column widths

%% Pandoc emits these and defines them in its own preamble, which this document does not use.
\providecommand{{\tightlist}}{{%
  \setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}

%% Heading arguments are {{volume}}{{year}}{{pages}}{{date submitted}}{{date published}}{{paper id}}{{authors}}
\jmlrheading{{1}}{{2026}}{{1--48}}{{8/26}}{{}}{{26-0000}}{{M\"ucahit Kutsal, Alpaslan Erda\u{{g}}, U\u{{g}}ur \"Ozbek and Do\u{{g}}a Ko\c{{c}}yi\u{{g}}it}}

%% The running head is set in small caps, and in these fonts the small capital of "i" has no dot. In
%% English that is correct. In Turkish the dotted and the dotless i are different letters, so a name
%% like Ko\c{{c}}yi\u{{g}}it comes out misspelled there. The class's own documented short author form
%% is "Minton et al", which is what this is, and the full list keeps its dots in the footer, which is
%% not small caps.
\ShortHeadings{{{title}}}{{Kutsal et al.}}
\firstpageno{{1}}

\begin{{document}}

\title{{{title}}}

\author{{\name M\"ucahit Kutsal \email mucahitkutsal@ankara.edu.tr \\
       \addr Ankara University, Ankara, T\"urkiye \\
       Republic of T\"urkiye Ministry of Foreign Affairs, Ankara, T\"urkiye
       \AND
       \name Alpaslan Erda\u{{g}} \email alpaslan.erdag@ankara.edu.tr \\
       \addr Ankara University, Ankara, T\"urkiye \\
       Republic of T\"urkiye Ministry of Foreign Affairs, Ankara, T\"urkiye
       \AND
       \name U\u{{g}}ur \"Ozbek \email uozbek@mfa.gov.tr \\
       \addr Republic of T\"urkiye Ministry of Foreign Affairs, Ankara, T\"urkiye \\
       Konya Technical University, Konya, T\"urkiye
       \AND
       \name Do\u{{g}}a Ko\c{{c}}yi\u{{g}}it \email doga.kocyigit@stud.tu-darmstadt.de \\
       \addr Technical University of Darmstadt, Darmstadt, Germany}}

\editor{{}}

\maketitle

\begin{{abstract}}%
{abstract}
\end{{abstract}}

\begin{{keywords}}
{keywords}
\end{{keywords}}

{body}

\vskip 0.2in
\bibliography{{penumbra}}

\end{{document}}
"""


# --------------------------------------------------------------------------------- validation
def validate(tex: str, n_fig: int, tables: list) -> int:
    """Checks that would otherwise need a compiler. Each failure is a build failure."""
    fails = []

    # 1. every environment opened is closed, in order
    stack, lineno = [], 0
    for i, line in enumerate(tex.split("\n"), 1):
        for m in re.finditer(r"\\(begin|end)\{([a-zA-Z*]+)\}", line):
            if m.group(1) == "begin":
                stack.append((m.group(2), i))
            else:
                if not stack:
                    fails.append(f"\\end{{{m.group(2)}}} at line {i} with nothing open")
                elif stack[-1][0] != m.group(2):
                    fails.append(f"line {i}: \\end{{{m.group(2)}}} closes "
                                 f"\\begin{{{stack[-1][0]}}} from line {stack[-1][1]}")
                    stack.pop()
                else:
                    stack.pop()
    for name, ln in stack:
        fails.append(f"\\begin{{{name}}} at line {ln} is never closed")

    # 2. braces balance
    depth = 0
    for ch in re.sub(r"\\[{}]", "", tex):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                fails.append("a closing brace appears before its opening brace")
                break
    if depth > 0:
        fails.append(f"{depth} unclosed brace(s)")

    # 3. inline and display maths are balanced
    if len(re.findall(r"(?<!\\)\\\(", tex)) != len(re.findall(r"(?<!\\)\\\)", tex)):
        fails.append("unbalanced inline maths delimiters")
    if len(re.findall(r"(?<!\\)\\\[", tex)) != len(re.findall(r"(?<!\\)\\\]", tex)):
        fails.append("unbalanced display maths delimiters")

    # 4. every cited key exists in the bibliography, and nothing is cited that does not
    bib = BIB.read_text(encoding="utf-8")
    defined = set(re.findall(r"@\w+\{([^,]+),", bib))
    cited = set()
    for m in re.finditer(r"\\cite[tp]\{([^}]*)\}", tex):
        cited.update(x.strip() for x in m.group(1).split(","))
    if cited - defined:
        fails.append(f"cited but not in the .bib: {sorted(cited - defined)}")
    if defined - cited:
        fails.append(f"in the .bib but never cited: {sorted(defined - cited)}")

    # 5. every figure file the document asks for exists
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex):
        p = (OUT / m.group(1)).resolve()
        if not p.exists():
            fails.append(f"figure missing on disk: {m.group(1)}")

    # 6. no residue from the conversion
    # `{[}` on its own is pandoc's guarded literal bracket and is correct LaTeX: it is what keeps a
    # bracket after `\\` from being read as an optional argument. Only a bracket whose whole content is
    # a list of small integers is an unconverted citation. The confidence intervals in the tables read
    # `{[}0.2504, 0.3773{]}` and must survive.
    for m in re.finditer(r"\{\[\}([^{}]{1,24})\{\]\}", tex):
        if re.fullmatch(r"\d{1,2}(\s*,\s*\d{1,2})*", m.group(1).strip()):
            fails.append(f"unconverted numeric citation: {m.group(0)}")
    for bad, why in [(r"\\includesvg", "an unconverted SVG include"),
                     # A bare # is a macro parameter character and stops the compile. It got here
                     # once: the edit-file parser skipped comment lines only while no block was open,
                     # so the separators between blocks landed in the replacement text.
                     (r"(?<!\\)#", "a bare #, which LaTeX reads as a parameter character"),
                     (r"@@", "a conversion marker"),
                     (r"\\LTcaptype", "pandoc's captionless-table wrapper"),
                     (r"\\subsubsection", "a heading level JMLR does not use"),
                     (r"\\hypertarget", "a pandoc hypertarget")]:
        n = len(re.findall(bad, tex))
        if n:
            fails.append(f"{n} occurrence(s) of {why}")

    # 7. the JMLR front matter is all present
    for macro in ["\\documentclass[twoside,11pt]{article}", "\\usepackage{jmlr2e}", "\\jmlrheading{",
                  "\\ShortHeadings{", "\\firstpageno{", "\\title{", "\\author{", "\\editor{",
                  "\\maketitle", "\\begin{abstract}", "\\begin{keywords}", "\\acks{", "\\appendix",
                  "\\bibliography{penumbra}", "\\end{document}"]:
        if macro not in tex:
            fails.append(f"front matter missing: {macro}")

    # 8. nothing outside ASCII, so no glyph depends on the compiling toolchain
    stray = sorted({c for c in tex if ord(c) > 127})
    if stray:
        where = tex[max(0, tex.index(stray[0]) - 50):tex.index(stray[0]) + 20].replace("\n", " ")
        fails.append(f"characters outside ASCII survived: {stray} near ...{where}")

    # 9. every macro pandoc emits is defined, since pandoc's own preamble is not the one used here
    preamble = tex[:tex.index("\\begin{document}")]
    for macro in ("tightlist", "passthrough", "pandocbounded", "oldparagraph", "CSLReferences",
                  "pandocbounded", "subtitle"):
        used = re.search(r"\\" + macro + r"\b", tex[tex.index("\\begin{document}"):])
        got = re.search(r"\\(?:providecommand|newcommand|def|newenvironment)\s*\{?\\" + macro,
                        preamble)
        if used and not got:
            fails.append(f"the document uses \\{macro} and nothing defines it")

    # 10. no stray carriage return, and no blank line where TeX reads one as \par
    if "\r" in tex:
        fails.append("a carriage return survived; pdfTeX would read it as a second end of line")
    for env in ("tabular", "longtable"):
        for m in re.finditer(r"\\begin\{" + env + r"\}(.*?)\\end\{" + env + r"\}", tex, re.S):
            if re.search(r"\n\s*\n", m.group(1)):
                fails.append(f"a blank line inside a {env}, which TeX reads as \\par")
                break
    for m in re.finditer(r"\\\[(.*?)\\\]", tex, re.S):
        if re.search(r"\n\s*\n", m.group(1)):
            fails.append("a blank line inside display maths")
            break

    # 11. tables and the numbers the running text gives them
    fails += check_table_rows(tex)
    fails += check_cross_references(tex, n_fig, tables)

    # 12. the guide's structural rules
    if re.search(r"\\section\{[^}]*\}\s*\n+\s*\\subsection\{", tex):
        fails.append("a section opens directly on a subsection, which the guide forbids")
    order_ok = tex.index("\\acks{") < tex.index("\\appendix") < tex.index("\\bibliography{")
    if not order_ok:
        fails.append("acknowledgements, appendices and references are out of the guide's order")

    # 13. every \ref and \label pair up
    labels = set(re.findall(r"\\label\{([^}]*)\}", tex))
    refs = set(re.findall(r"\\ref\{([^}]*)\}", tex))
    if refs - labels:
        fails.append(f"\\ref with no \\label: {sorted(refs - labels)}")

    # 14. wording retired by a decision does not come back
    for pattern, why in RETIRED_WORDING:
        for m in re.finditer(pattern, tex, re.I):
            fails.append(f"retired wording present, {why}: {m.group(0)!r}")

    # 15. the prose does not drift back towards the sentence length the fourth reading objected to
    share, n_long, n_all = sentence_lengths(tex)
    if share > LONG_SENTENCE_SHARE:
        fails.append(f"{n_long} of {n_all} prose sentences are {LONG_SENTENCE_WORDS} words or more, "
                     f"{share*100:.1f} percent against a {LONG_SENTENCE_SHARE*100:.0f} percent limit")

    # 16. a count the paper gives for its own table must be that table's count
    fails += check_appendix_b_counts(tex)

    # 17. nothing set in small caps carries a Turkish dotted i, because the small capital has no dot
    # and in Turkish that is a different letter. A reader caught this, not a check.
    # Read with brace matching, not with a pattern: `\u{g}` closes the argument early otherwise, and
    # the first version of this check read half the author list and passed on a name it should
    # have caught.
    i = tex.find("\\ShortHeadings")
    if i >= 0:
        a1, b1 = braced(tex, tex.index("{", i))
        a2, b2 = braced(tex, tex.index("{", b1 + 1))
        for side, which in ((tex[a1:b1], "title"), (tex[a2:b2], "author")):
            turkish = re.search(r"\\[uc]\{[gcsGCS]\}", side) or re.search(r'\\"[oOuU]', side)
            if turkish and re.search(r"(?<![\\{])i", side):
                fails.append(f"the running head's {which} carries a Turkish name and an undotted "
                             f"\"i\" into small caps, where the small capital has no dot: {side!r}")

    # 18. the abstract stays inside what an abstract is for, and the revision tags stay in Appendix B
    a = tex.index("\\begin{abstract}")
    b = tex.index("\\end{abstract}")
    words = len(re.sub(r"\\[a-zA-Z]+|[{}]", " ", tex[a:b]).split())
    if words > ABSTRACT_MAX_WORDS:
        fails.append(f"the abstract is {words} words, and {ABSTRACT_MAX_WORDS} is the limit")
    nums = re.findall(r"\b\d[\d.]*\b", tex[a:b])
    if len(nums) > ABSTRACT_MAX_NUMBERS:
        fails.append(f"the abstract carries {len(nums)} numeric tokens, and "
                     f"{ABSTRACT_MAX_NUMBERS} is the limit: {nums}")
    dupes = sorted({n for n in nums if nums.count(n) > 1})
    if dupes:
        fails.append(f"a number appears twice in the abstract in different senses: {dupes}")
    if re.search(r"\(R\d+\)", tex[:tex.index("\\appendix")]):
        fails.append("a revision tag survived in the body, and they belong to Appendix B")

    # 19. no caption runs past the length a caption is for
    for c in re.finditer(r"\\caption\{", tex):
        a, b = braced(tex, c.end() - 1)
        ss = sentences(tex[a:b])
        if len(ss) > CAPTION_SENTENCES:
            fails.append(f"a caption has {len(ss)} sentences and {CAPTION_SENTENCES} is the limit: "
                         f"{visible(tex[a:b])[:70]!r}")

    # 20. the title and the running head must fit the measure: neither can be broken to fit, and a
    # title that runs past the margin is what sent this document back for a rename
    m = re.search(r"\\title\{(.*?)\}\s*\n", tex, re.S)
    if not m:
        fails.append("no \\title in the document")
    else:
        for line in m.group(1).split("\\\\"):
            w = estimate_width(line.strip(), 14.4, 0.55)
            if w > TEXTWIDTH_PT:
                fails.append(f"a title line measures about {w:.0f}pt against a "
                             f"{TEXTWIDTH_PT:.0f}pt measure: {visible(line).strip()!r}")
    m = re.search(r"\\ShortHeadings\{(.*?)\}\{(.*?)\}", tex)
    if not m:
        fails.append("no \\ShortHeadings in the document")
    else:
        for side, which in ((m.group(1), "title"), (m.group(2), "author")):
            w = estimate_width(side, 10.0, 0.58)
            if w > TEXTWIDTH_PT:
                fails.append(f"the running head's {which} measures about {w:.0f}pt against a "
                             f"{TEXTWIDTH_PT:.0f}pt measure: {visible(side)!r}")

    # 21. nothing set in a fixed width may exceed the measure, since it cannot be broken to fit
    for m in re.finditer(r"\\begin\{verbatim\}\n(.*?)\\end\{verbatim\}", tex, re.S):
        over = [l for l in m.group(1).split("\n") if len(l) > VERBATIM_COLUMNS]
        if over:
            fails.append(f"a verbatim line is {len(over[0])} characters and {VERBATIM_COLUMNS} fit "
                         f"the measure, so it will run past the margin: {over[0][:60]!r}")

    # 22. a float in an appendix has to carry the section letter, because the running text gives it one
    after = tex[tex.index("\\appendix"):]
    for env, counter in (("table", "table"), ("longtable", "table"), ("figure", "figure")):
        if re.search(r"\\begin\{" + env + r"\}", after) and \
                f"\\numberwithin{{{counter}}}{{section}}" not in after:
            fails.append(f"a {env} appears in an appendix and the {counter} counter is not lettered, "
                         f"so it will number straight on from the body")

    if fails:
        print("\nVALIDATION FAILED")
        for f in fails:
            print("  FAIL ", f)
        return 1
    print("\nok: environments and braces balance, maths delimiters pair, every citation resolves, "
          "every figure exists, no conversion residue, JMLR front matter complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
