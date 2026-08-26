# JMLR submission

Everything JMLR needs, and nothing that is not needed to compile it.

```
penumbra.tex          the manuscript, generated
penumbra.bib          46 entries, author-year keys
jmlr2e.sty            the class file, as published by JMLR
figures/              figure-1.pdf to figure-8.pdf, copied from ../Figures
penumbra-overleaf.zip the four of those, ready to upload
sample.tex            JMLR's own annotated example, kept for reference; not submitted
captions-trimmed.md   the caption sentences the conversion dropped, for review
```

## Compiling

```
pdflatex penumbra
bibtex   penumbra
pdflatex penumbra
pdflatex penumbra
```

### On Overleaf

`python scripts/pack_jmlr.py` writes `penumbra-overleaf.zip` — the four things a compile needs and
nothing else, with the figures under `figures/` where the document looks for them. The script reads
the archive back after writing it and fails if a file the document asks for is not in it.

1. Overleaf → **New Project** → **Upload Project** → that zip.
2. **Menu → Compiler: pdfLaTeX.** Not XeLaTeX or LuaLaTeX: `jmlr2e` requires `epsfig`, and the
   document sets `[T1]{fontenc}`, both of which assume the pdfTeX route.
3. **Menu → Main document: `penumbra.tex`** if Overleaf has not picked it already.
4. **Recompile.** Overleaf runs `latexmk`, which does the BibTeX pass and the reruns by itself. If the
   citations come out as `[?]` on the first go, recompile once more; if they stay, Menu → Clear cached
   files, then recompile.

Nothing in the document needs a particular TeX Live version, and `jmlr2e.sty` is in the archive
because it is not on CTAN.

Two things look wrong in the PDF and are not:

* the title block prints **Editor:** with nothing after it, because the journal assigns one. To drop
  the line for a preprint, `\usepackage[preprint]{jmlr2e}`, which also drops the running heading;
* the availability section reads `[ARCHIVE-DOI]` until the declaration bundle is deposited.

Both are covered under **Before submitting** below, and the build prints the placeholder every run.

`jmlr2e.sty` sets `\bibliographystyle{plainnat}` itself, so the document does not, and the citations
are natbib author-year throughout.

**This has not been compiled here.** No TeX distribution is installed on the machine the conversion
was run on, and none was installable, so every claim below about the file compiling is the result of
a static check rather than of a compiler. `scripts/build_jmlr.py` runs twenty-two checks that stand in
for the ones a compiler would make, and the build fails rather than warns:

1. every environment opened is closed, in order
2. braces balance
3. inline and display maths delimiters pair
4. every cited key is in the `.bib`, and every entry in the `.bib` is cited
5. every figure file the document asks for is on disk
6. no residue from the conversion: no `{[}N{]}`, no `\includesvg`, no marker, no `\LTcaptype`
7. the JMLR front matter is complete, macro by macro
8. nothing outside ASCII survives, so no glyph depends on the compiling toolchain
9. every macro pandoc emits is defined, since pandoc's own preamble is not the one used here
10. no stray carriage return, and no blank line where TeX would read a `\par`
11. tables are numbered as the running text says they are, and no row disagrees on its column count
12. the guide's structural rules: no section opening on a subsection, acknowledgements before the
    appendices before the bibliography
13. every `\ref` has a `\label`
14. wording retired by a decision does not come back
15. the prose does not drift back past 12 percent of sentences at forty words or more
16. a count the paper gives for its own table is that table's count
17. nothing set in small caps carries a Turkish dotted i: the small capital has no dot, and in
    Turkish that is a different letter
18. the abstract stays inside 250 words and 6 numeric tokens, with no number appearing twice, and
    no revision tag survives in the body
19. no caption runs longer than two sentences
20. the title and the running head fit the measure, since neither can be broken to fit
21. nothing set in a fixed width exceeds the measure: the flow diagram is wrapped to the 84 columns
    a six-inch measure fits at `\small`, because a `verbatim` running past the margin is silent
22. a float in an appendix carries the section letter, because the running text gives it one — the
    article class would number Tables A.1, B.1 and C.1 as 12, 13 and 14

The first compile will still find things a static check cannot: an overfull line, a float that will
not place, a page break inside a table that would read better elsewhere. Those are typesetting, and
they need the compiler.

## Regenerating

The `.tex` is generated and carries a header saying so. Edit `paper/penumbra-revised.docx`, then:

```
python scripts/build_jmlr.py
python scripts/build_jmlr.py --keep-raw    # also writes _raw.tex, pandoc's unprocessed output
```

Editing `penumbra.tex` directly means the next build discards the edit. Three things in the file do
not come from the docx and live in the script instead, where they are visible and reviewable:

* the front matter, which the docx has no equivalent of;
* the title, in `TITLE` at the top of the script. It is printed three times — the file header, the
  running head and the title block — so it is defined once. The docx still carries the old long
  title in its own heading; that block is dropped rather than converted, so the two do not have to
  agree, but the docx is worth updating the next time it is edited;
* one-sentence openings for Sections 3 and 6, which in the docx open directly on a subsection. The
  guide forbids that. Both sentences describe what already follows and assert nothing new.

One correction is applied on the way through: Section 9's citation of REFORMS pointed at the other
Kapoor paper, because the sentence was rewritten after the bibliography was renumbered and the
hand-typed number was not remapped. It is the claim-to-artefact class that Section 9 itself is about.
`scripts/check_paper.py` now checks that class directly, and `paper/penumbra-kbs.md` is corrected.

## Round-three and round-four edits

The third external reading was about the writing: an abstract of context-free numbers, forward
pointers dense enough to keep a reader turning pages, and revision tags in the body that belong to
Appendix B. The prose changes live in `paper/round3-edits.txt`, one block each, with the reason and
the text they replace, so every one can be read against what it changed. Each must match exactly once
across the abstract, the body and the acknowledgements: an edit matching nothing means the docx moved
under it, and one matching twice would change a sentence nobody looked at.

The revision tags go by pattern instead, in the script — there were thirty-eight of them and the
pattern is parenthesised, so Appendix B's own `R1` column is untouched.

Round four answered a second reading, which had two complaints. The counts the paper gave for its own
audit did not agree with each other — four separate places, listed in `paper/round4-edits.txt` — and the
sentences ran long. `round4-splits.txt` and `round4-splits2.txt` hold 55 sentence splits; the share of
prose sentences at forty words or more went from 16.2 percent to 10.6, and check 15 fails the build
above 12.

`scripts/sync_markdown_edits.py` applies every round's edits to `paper/penumbra-kbs.md`, translating
`\textbf{x}` to `**x**`, the accent commands back to their letters, and matching across that file's
hard line wrapping. Without it the two sources drift on exactly what the readings complained of:
regenerate the docx from the markdown and the tags, the number-heavy abstract and the long sentences
come back. Sixteen of the edits quote a citation or inline maths and cannot be translated; the script
names them rather than forcing them, and all of them are sentence splits rather than claims.

## Before submitting

One thing in the file is a placeholder, and the build prints it every run:

| Placeholder | What it needs |
| --- | --- |
| `[ARCHIVE-DOI]` | The DOI of the deposited declaration bundle. |

The DOI is not typed into the manuscript. Deposit `declaration/` — three files, 41 KB — then

```
python scripts/build_declaration.py --doi 10.5281/zenodo.NNNNNNN
python scripts/build_jmlr.py
```

The first writes it into `declaration/MANIFEST.json`, whose `deposit_identifier` field has been
waiting for it since the bundle was built; the second reads it from there and replaces the placeholder
with a `\url` to doi.org. A value that is not a DOI fails the build rather than printing a broken
reference. Entering a number once is Section 9's fifth question applied to this paper's own front
matter.

Print the **version** DOI rather than Zenodo's concept DOI. The concept DOI resolves to whatever the
newest version is, and the sentence in the paper claims the deposit fixes a text.

All four author addresses are supplied. The repository is
<https://github.com/McahitKutsal/Leakage-Horizons>, public and MIT-licensed, and there is no release
tag: the sentence that named one no longer does.

**The repository is currently empty apart from its LICENSE file.** The availability section describes
the corpus construction, the diagnostic suite, the survival estimators, the synthetic generators,
every analysis script, the consistency checker and the second implementation of the density code as
released there. Until they are, that section is a claim whose artefact does not exist — the class of
defect Section 9 is about, and the first thing a reviewer who clicks the link will find.

The running head gives the short author form as `Kutsal et al.`, which is the class's own documented
usage. It is not only brevity: `\ShortHeadings` is set in small caps, and in these fonts the small
capital of *i* has no dot, so a Turkish name reaches the page misspelled — dotted and dotless i are
different letters. The full author list keeps its dots in the page footer, which is not small caps.

Two further items are decisions, not blanks:

* **The byline names four authors and the contribution statement names six.** Ömür Koçyiğit and Ayşe
  Gizem Ergör have CRediT roles and are not on the byline. The two consistent resolutions are to
  restore them to the byline or to move them to the acknowledgements. The conversion leaves the
  manuscript as it is and reports the disagreement on every build.
* **The disclaimer says two of the authors are affiliated with the Ministry**; the affiliation block
  now lists three. Whichever way the byline is resolved, that sentence needs to match it.

`\jmlrheading` and `\editor{}` carry submission placeholders as JMLR's own sample does; the editor is
assigned by the journal.

## Captions

Each caption is cut to its first two sentences: what the float is, and the setup a reader needs to
read it — the corpus, the counts, the levels, the lead times, how the intervals were taken. What
followed described the panels and argued from them, which is the body's work. The docx's longest
caption ran to eight sentences and 216 words; the longest now is 50, and the average is about 34.

The cut is at a sentence count and not at a word count, so no caption is shortened by a judgement
about which of its claims matters. The 36 dropped sentences are written to `captions-trimmed.md` so
that none of them left the paper unrecorded, and a sentence worth keeping can be moved into the body.

Four of them defined something the float itself prints: Figure 7's level \(k = 25\), Table 3's
**coverage rate**, Table 4's **censored** column and Table 8's expected-count basis. Each is named in
the body as well, which the build checks rather than assumes — a definition the body does not carry
is reported as one to move rather than dropped.

## What was dropped

The docx has a Highlights list of five lines. JMLR has no highlights section and each of the five
restates a sentence of the abstract, so they are not in the `.tex`. Nothing else in the docx is
absent: the build asserts eleven numbered sections, seventeen subsections, three appendices, three
back-matter sections, eight figures and fourteen tables, and fails if any count moves.
