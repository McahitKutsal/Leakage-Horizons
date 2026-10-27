# The revised manuscript

The manuscript is written here as one Markdown file per section and built into Word, which is
what the journals this version targets accept. Nothing in this directory is edited by hand except
`sections/` and `supplement/`; everything else is generated, and the generated files are not
committed because they are reproducible from what is.

```
sections/           the manuscript, one file per numbered section, in build order
supplement/         the supplementary material, same convention
build_docx.py       assembles both, writes manuscript.docx and supplementary.docx
make_dag.py         draws Figure 1, the decomposition the paper's Section 2.4 states
rasterise_figures.py  turns ../jmlr/figures/*.pdf into the PNGs Word can embed
verify.py           checks the manuscript against the JMLR source it was rewritten from
check_citations.py  checks citations against the reference list, and the list against itself
verify_references.py  checks every reference carrying a DOI against the Crossref record
inspect_docx.py     dumps what landed in the .docx, for eyeing the maths and the tables
apply_*.py          the recorded edit passes, each exact-match and idempotent
```

## Building

```
python scripts/build_jmlr.py          # from the repository root, writes paper/jmlr/figures/
cd paper/revision
python make_dag.py
python rasterise_figures.py
python build_docx.py
```

`build_docx.py` writes `manuscript.docx`, `supplementary.docx` and the concatenated `.md` beside
them. It needs `python-docx`; `make_dag.py` needs `matplotlib` and `rasterise_figures.py` needs
`pymupdf`. The first step is listed because the eight figure PDFs it writes are themselves build
output and are not committed.

## Checking

```
python verify.py
python check_citations.py
python verify_references.py
```

The three are independent and all three must pass.

`verify.py` is the one that matters most, because it holds the rewrite to the version it came from.
It measures the prose against the submitted manuscript on length and on the two things an external
reading objected to, a repeated contrast construction and a density of internal pointers, and it
fails if either runs above half the old rate. It resolves every `Section N.M` reference against a
heading that exists, checks that the tables and figures are numbered without gaps and that each is
pointed at from the running text, and it checks that **every numeral in the manuscript also occurs
in the source it was rewritten from**. That last one is the guarantee the rewrite did not invent a
number: section and table pointers are excluded as pointers rather than quantities, and small
integers are excluded as list counts, and what remains has to trace back.

`verify_references.py` fetches the Crossref record for every reference that prints a DOI and
compares the year, the first author's surname, the title, the volume and the pages. It writes
`reference-audit.txt` and names the entries that carry no DOI, which are the proceedings and books
where none exists, so that those stay a deliberate gap rather than an oversight. Set
`CROSSREF_MAILTO` to your own address before running it; Crossref's polite pool asks for a contact.

Older journal records often store only a first page, so a printed range whose start agrees is
treated as correct and the record as thin. That case is the reason the check reports the comparison
rather than the verdict alone.

## Why the generated files are not here

`manuscript.docx`, `supplementary.docx`, the concatenated `.md` files and `figures/*.png` are all
written by the three build commands above from files that are committed. They are in `.gitignore`
for the same reason `paper/jmlr/figures/` and the Overleaf archive are: a fresh clone rebuilds
them, and committing them would put a binary diff in every rebuild.
