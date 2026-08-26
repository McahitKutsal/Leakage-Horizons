# Revision log: what the external reading changed

**Source of the review.** `penumbra-revizyon-notlari.md`, an external reading of the manuscript dated
24 August 2026. This file records what was done about each item, what the new experiments found, and
what remains for the authors. It exists because Section 9 of the paper argues that a claim is worth what
its artefact supports, and a revision is a claim about a manuscript.

---

## 1. New measurements

Four experiments were run that did not exist before. Two of them changed a finding.

### 1.1 Is the focal group's own record the only place back-dating lives? (objection 3.1)

New: `penumbra/synthetic.py` grows a **co-back-dating axis** — a share of accession events arrive with
the acceding entity also entered into a second, overlapping group at the same true period, and that
second register is back-dated by its own law. The generator now records, per event, the reach of the
administrative trace and which record carries it, split into the focal group's own record, the part the
event's own wave caused elsewhere, and the ambient part any group's back-dating puts into `r*` whether
or not the focal event happened.

New: `scripts/run_co_backdating.py` → `results/co_backdating.json`. 840 corpora: six widths, four
homophily settings, five seeds, four wave shares, two convention regimes. Density picked from a declared
ladder by a measured worst case, exactly invariant across every cell.

**Result.** Section 3.3's claim holds under one dating convention and fails under mixed ones.

| | one convention | mixed conventions |
|---|---|---|
| Corpora | 480 | 360 |
| Events with an off-focal trace the focal record misses | **0**, in every cell | 1.8 to 8.9 percent by wave share, 42 percent in the worst corpus |
| Shortfall, focal record only | 0.00 periods, max 0 | +0.82 to +2.68 mean, max 9 |
| Shortfall, every register read | 0.00 periods | -0.81 to -1.32, that is a small overshoot |
| Focal isolation, mean error / slope | 0.00 / 1.00 | +1.67 to +4.33 / 0.03 to 0.34 |

Three further findings fell out. The failure is **administrative, not homophily**: the gap is 3.77, 2.07,
2.67 and 2.23 periods at homophily 0, 1, 2 and 3 under mixed conventions and 0.00 at all four under one.
The **pooled statistics do not recover it** — the clique estimate undershoots the truth in 39 to 53 of
120 cells and the residual rule in 53 to 91 — so reading `r*` is not a substitute for reading the
registers. And the **ambient off-focal content is not a trace**: mean reach 1.0053 for positives against
0.8396 for matched negatives, share carrying one 0.1401 against 0.1359.

**In the paper.** New Section 6.3 with Table 6 and Figure 3; mechanism (k); a fifth term in Section 3.4's
decomposition; Section 3.3 rewritten; a threat in Section 10; a fifth item in Section 8; the first
instruction of Section 11 changed.

### 1.2 Is Table 4's collapse a censoring artefact? (objection 3.3)

`scripts/run_synthetic_homophily.py` now records, per cell, how many of the six widths leave the
estimate at the top of the examined range, recomputes the slope over the uncensored ones, and reruns the
collapsing cells over lead times to **twenty** against the original eight.

**Result: the objection is right about the mechanism and wrong about the conclusion.** Every cell whose
slope is 1.00 has censoring zero, so those are the strong reading. The collapsed cells are censored in
all six widths, so their slope of zero is arithmetically forced. Widening the range makes it worse rather
than better: at homophily 3 the unbanded rule moves from a constant 9 to 21, 19, 11, 18, 19, 12 against
true widths of 1 to 6, a slope of **-1.09**, with nothing censored. The uncensored cells return the
identical six estimates at both ranges, which is the control.

### 1.3 Five seeds on Table 4's transition rows, ten seeds on Table 10

Five seeds on the rows where an estimator is neither exact nor collapsed. Two entries move. The residual
rule at homophily 2 with independent anchors, reported as +2.00 / +0.54, is 0.88 in slope over five seeds
with a range of 0.54 to 1.00, so the single-seed cell was the least favourable of five. The clique
estimate at homophily 3, reported as exactly 1.00, is 0.97 with a range of 0.86 to 1.00.

Ten seeds on the architectural comparison, all six encoders rerun from scratch:
`results/p7_s10.json`, `results/p7_ctrl_w96_s10.json`, `results/p7_ctrl_w128_s10.json`.

**One verdict reverses.** The homogeneous message-passing encoder was reported as *indistinguishable*
from its width-matched graph-free control: -0.0009, half a standard error, winning exactly 24 of 48
cells. At ten seeds it is **-0.0091, 3.7 standard errors, winning 25 of 120 cells** — significantly
worse than a graph-free model of the same size, at every lead time. The other two margins survive:
relation-specific +0.0100 at 4.5 SE against +0.0121 at 2.7, and temporal +0.0192 at 13.4 SE.

This is Section 9's fourth question applied to the paper's own most-quoted number and finding another
defect in it. Both seed counts are printed in Table 10 for that reason.

### 1.4 Mechanism (g)'s model set

`scripts/run_p6.py`'s ten hand-listed models are replaced by a declared enumeration: the node covariate
block present or absent, crossed with seven relational blocks, so fourteen cells of which the original
ten are a subset.

**Result: the sign holds and the p value halves.** Spearman **-0.667 at p = 0.0092 over fourteen models**,
against -0.699 at p = 0.0245 over the hand-listed ten. Reliance spread 0.1667, fragility spread 0.0837.
The four models the grid was missing came in without being chosen for what they would do, which is the
point: the review's objection was that ten hand-picked points can flip, and the answer is a larger set
fixed by a rule rather than a larger set chosen after seeing the first. The paper still declines to
claim the sign as an established reversal, for the reason it gave before.

---

## 2. The count chain, and four pairs of numbers

New: `scripts/audit_filter_chain.py` → `results/filter_chain.json`, which reaches every reported count
through the same code path the reporting script uses. Three pairs the external read flagged, and a fourth
found by chasing them:

| Pair | Reason | Where it is now stated |
|---|---|---|
| 528 against 527 groups | 528 overlap the window on the entity table's dates; 527 contribute a period to the likelihood. One entity, `igo:4110`, has no active membership row inside the window. | Section 5.5 flow, 6.7, Appendix A |
| 151 against 150 terminations | The same entity carries one of the 151 coded terminations inside the window. **Not previously noticed.** | Section 5.5 flow, Appendix A |
| 7,146 against 7,084 events | The lead time the count is taken at. Focal isolation is undefined at lead time one where the group has no preceding-year record; 62 exactly dated first entries are accessions in a group's founding period. | Section 5.5 flow, 6.5 |
| 6,597 against 6,501 | The hazard's unit is the dyad and a dyad exits the risk set when it accedes, so 96 repeat accessions on 94 dyads collapse onto the first. | Section 5.5 flow, 6.7 |

---

## 3. Terminology corrected against the measurements

Three claims the numbers do not support.

**"Lower bound" is not a lower bound.** The rule never undershoots the synthetic width and exceeds it in
a third of resamples at the widest setting, so it does not bound the horizon from below. Section 3.2 now
states what it is — a conservative estimate under an asymmetric loss that is written down — the symbol is
`\hat\Delta^\star`, and the withdrawn interval is discussed as two *ends* rather than two bounds. The
67 percent figure at beta 4 is reported as a coverage rate rather than as an error profile virtue.

**"Recovers a tenth of a width" mixes units.** The numerator is a presence probability, exactly 1 by
entailment, and the denominator a dimensionless density contrast. Section 6.4's claim is now the 6.8
percent share of the relation that the back-dated dyads constitute, which is what the mechanism actually
is; the ratio is kept as a description of how far two instruments diverge on one set of events, with the
unit caveat stated.

**Corpus B is a scope test, not a replication.** It has no time axis, so it cannot reproduce any result
about lead time, and no central measurement of the paper has been reproduced on a second corpus. Section
6.6 says so and Section 10 lists it.

---

## 4. The declaration, and what preparing it found

New: `scripts/build_declaration.py` → `declaration/` and `results/declaration.json`.

The two halves of the declaration are not equally supported, and the weaker half is the one the
prospective test rests on:

- **Corpus A**: a genuine pre-registration. `penumbra-manifesto.md`, committed 2026-08-02 19:50:31,
  amended 19:58:55, frozen 2026-08-03 10:24:59, all before any data was materialised. Three commits with
  dates, and the bundle carries the file as the freezing commit left it plus a SHA-256.
- **Corpus B**: **not timestamped**. The ten-channel assignment lives in the docstring of
  `scripts/run_second_domain.py`, which was never committed before it was run, and the pre-registration
  does not name the channels.

Depositing now cannot repair the second: a timestamp obtained after a statistic is not evidence about
the order. So the paper downgrades what it claims from Section 6.6 — from "a prospective test of the
discipline" to "a reading consistent with a ranking it did not use, with the ordering resting on our
account" — and says so where the result appears rather than only in the threats section.

---

## 5. References

Renumbered to first appearance. Every field taken from the publisher record through the CrossRef API
rather than from a reference manager. Six errors, of which the external read had found three:

| # | Was | Is |
|---|---|---|
| 1 | M. R. Bailey | **M. A. Bailey**, JCR 61(2):430-456, 2017 |
| 2 | R. W. Frank, MID5 | **R. W. McManus** and nine co-authors, CMPS 39(4):470-482, 2022 |
| 3 | ATOP cited by an article covering 1815-1944 with no data version | article plus **ATOP v5.1**, `atop5_1m`, coverage 1815-2018, access date |
| 4 | STRING v11 title, 2021 year, v12 author list | **The STRING database in 2023**, NAR 51(D1):D638-D646, and the data pinned at **v12.0** |
| 5 | CORUM 2019 release note | **CORUM in 2024**, NAR 53(D1):D651-D657, and the data pinned at **release 5.3 of 2026-04-14** |
| 6 | Complex Portal 2018 release note | **Complex Portal 2022**, NAR 50(D1):D578-D586, and the data pinned at the current human release |

Items 4 to 6 were not in the review. They are the same defect class one level down: three of the four
biological sources were cited by an earlier release note than the release the corpus was built from, so
a reader following the citation would have found a different version of the data.

A seventh correction is in Section 2 rather than the bibliography: the leakage horizon was placed under
Kapoor and Narayanan's type **L1**, and it belongs under **L2**. All eight leaves of the taxonomy are now
checked in the text, with the reason each is or is not the home.

---

## 6. Structure

- Section 6.1.2 promoted to **Section 6.2**; the identification measurement is the paper's backbone and
  was two levels deep.
- Section 7.2 promoted to **Section 8**, with Table 11 moved back into Section 7 where it belongs.
- New **Section 6.3**; Sections 6.2 to 6.5 renumbered to 6.4 to 6.7; Sections 8 to 10 to 9 to 11.
- Tables 5 and 6 are new, so Tables 5 to 9 became 7 to 11. Figure 3 is new, so Figures 3 to 7 became 4
  to 8.
- Two definition boxes: the level ladder in Section 4 and the six questions in Section 9.
- Section 9's heading is now **six** questions, the sixth being the one no check can automate.
- Nine long run-in headings shortened.
- `check_paper.py` grows a cross-reference check: every section a sentence points at must exist, and any
  blockquote that is not a declared box fails. Two renumberings moved eleven headings and thirty-eight
  references in this revision, and a stale pointer reads as a correct sentence about the wrong object.

---

## 7. What is left for the authors

Four items, all of which need an account, a decision, or a signature rather than work on the manuscript.

1. **Deposit `declaration/` and paste the identifier.** The bundle is built and checksummed. One
   sentence in Data and code availability is marked for it, together with the repository URL and the
   release tag, which do not exist until the release is made. The honest status of the corpus B half
   travels with the artefact and should not be edited out of it.
2. **Confirm the licence.** The paper states MIT. That is a default, not a decision anyone made, and it
   is the authors' to make.
3. **Decide the journal.** The review recommends *Patterns* first and *Knowledge-Based Systems* second,
   on the grounds that this is a measurement-validity paper with a negative result and that Patterns
   hosts the leakage literature it argues with. The manuscript is left journal-agnostic in an Elsevier
   numbered style that both accept, with Highlights that KBS requires and Patterns permits, so the
   decision costs no rework either way. It was not made here because it is not a scientific question.
4. **Check the CRediT roles for the five co-authors.** They are assigned conservatively and the paper
   states plainly that no audit it reports was performed by an author who had not written the code being
   audited. If any was, that is a stronger claim than the paper currently makes and it belongs in that
   statement.

---

## 7b. Regression evidence for the generator change

`penumbra/synthetic.py` gained three configuration fields and a ground-truth pass, so the first
question is whether anything already published moved.

- Table 3's calibration comes from `generate`, the legacy generator, which was not touched.
- `bootstrap_diagnostics.py`'s resampling of that calibration also uses `generate`, so the 67 percent
  at beta 4 is unaffected.
- The two artefacts that do use `generate_parametric` were both regenerated. Table 4's cells come back
  identical to the published values, +4.33 / -0.03 at homophily 2, +5.50 / 0.00 at 3 and 4, and
  +2.00 / +0.54 in the independent regime at 2, which is the regression check: at a wave share of zero
  the new code path is skipped entirely, the added ground-truth pass draws from its own random
  generator, and the main stream is therefore untouched.

## 7c. One thing the review did not raise: length

The manuscript is **28,850 words of prose** excluding tables and references. That was true of the
version the review read and it is not something this revision introduced, which added about 900 words
net after tightening. It is nevertheless a submission risk at any venue, and it is worth stating with a
concrete plan rather than as a worry.

Word counts by section, the ones above 1,500 first: Section 6.5 at 2,153; Section 6.6 at 2,076;
Section 6.2 at 1,850; Section 9 at 1,851; Section 7 at 1,824; Section 6.3 at 1,636; Section 10 at 1,602.

If a venue forces a cut, the order that costs the argument least is:

1. **Section 6.7, the task results, 1,294 words.** The section opens by saying it is reported for
   completeness because the paper is about instruments. It carries two things the argument uses, the
   0.25 gap between the two discriminations and the architectural seed lesson, and both survive as a
   paragraph with the rest in supplementary material.
2. **Section 5.5's negative construction, 747 words.** The verifiability argument is three sentences;
   the rest is method that a supplement can hold.
3. **Section 6.6's per-bin discussion, about 800 of its 2,076.** Table 8 carries the numbers and the
   text restates several of them.

What should not be cut, because the review identified each as a contribution independent of the rest:
Section 6.2, Section 9, Table 1, and Section 8. Cutting Section 6.3 would remove the answer to the
review's highest-value objection.

## 8. Checks

    python scripts/check_paper.py        # 188 registered claims, 30 retired phrases, structure
    python scripts/check_consistency.py  # every artefact stamped with what wrote it
    python scripts/build_figures.py      # all eight figures, from the artefacts
    python scripts/build_paper.py        # docx, no dashes, headings black

---

# Round two: what the second reading changed

A second external reading raised six criticisms, none of which overlapped the first reading's. They were
about presentation, about what the central corpus can establish, about how much weight the generator
carries, about proportionality, and about the bibliography. This part of the log records what was done
about each.

## R2.1 Readability, which the reading called the biggest problem

Three separate faults were named and all three are measured rather than asserted fixed.

**The revision history was woven through the body.** Thirty-eight sentences in the running text
distinguished what the paper now claims from what it used to claim: "an earlier version of this
paragraph", "the first version of this table reported neither", "we had held". The reading's judgement
was that the honesty is admirable and the place for it is one appendix, not every section, because a
reader meeting a result for the first time should not have to sort a conclusion from its history.

Body sentences carrying revision narration: **38 before, 0 after.** Every retraction is kept. Each is
now a tag of the form `(R7)` in the body and a row in the new **Appendix B**, which lists twenty changes
with what each was, what it is, and what forced it. Eight are the substantive ones Section 11 counts;
the other twelve are corrections of naming, arithmetic or presentation. The appendix ends by saying what
the table is not evidence for, which is that the paper is now correct.

**Sentences were routinely 60 to 80 words.** Forty-four were split, in two passes, and nothing was
dropped: nested conditions became separate sentences.

| | before | after |
|---|---|---|
| Mean sentence length | 30.1 words | 27.7 |
| Median | 28 | 27 |
| Over 40 words | 191 | 153 |
| Over 50 words | 91 | 40 |
| Over 60 words | 35 | 4 |
| Over 70 words | 15 | 2 |

The two remaining over 70 are the count-chain flow diagram and the displayed decomposition, neither of
which is a sentence.

**Section headings were full sentences.** Every heading in Section 6 is now a noun phrase: "Calibration
against a width the generator sets", "Homophily against back-dating", "Where the administrative trace
lives", "A width printed in the source", "The coalition corpus". Twenty-eight run-in headings were cut
to their claim, with the lost clause moved into the paragraph rather than deleted; run-in headings over
nine words fell from 42 to 22, and the longest is now 13 words against 27.

## R2.2 The central field comparison rests on an entailment

The objection: corpus A codes one date for 94 percent of its events, so focal isolation returns zero
structurally, and showing that the pooled statistic reports something the focal statistic cannot express
is not the same as showing it is wrong. The real evidence is the trade register, and there $n = 759$.

**This is right, and looking for the repair found that the repair does not exist.** The obvious fix is
to find a stratum of corpus A where focal isolation *measures* and compare the two instruments there as
two measurements. Exactly one stratum qualifies, the declared-resolution stratum, and
`scripts/run_both_instruments.py` establishes that it cannot serve:

- the register assigns that stratum only to organisations founded before 1965, so all **447** of its
  accessions carry a coded year of **1965 or earlier**;
- the analysis window opens in 1965, so **the deepest lead time at which the pooled statistic could be
  read on those events, inside the window, is 0**;
- reading it at one to eight periods puts **86 percent** of the rows before the window, inside the
  coverage break Section 5.4 exists to exclude.

So on corpus A the two instruments cannot both be measurements on the same events anywhere, and the
reason is structural rather than a matter of 94 percent against 6. That is a sharper statement of the
objection than the objection, and it is now stated in Section 6.5, in Table 1, and as a threat in
Section 10.

**What changed in the argument.** Section 6.5 opens by separating what the corpus cannot do from what it
does, and the section's weight moves onto three results that need no focal isolation at all: the target
relation is statistically indistinguishable at eight periods from a relation that cannot record the
event; the crossing lead time's bootstrap interval spans the whole examined range; and the unconditioned
four-period decay is almost entirely prior spells. The two-instrument comparison is reported as a
magnitude rather than as a refutation, and the falsification against a *known* width is attributed where
it belongs, to the 759 agreements of Section 5.3. Section 6.5's heading no longer leads with the factor
of 6.8.

## R2.3 The generator carries too much load

Two sub-objections: a single functional form for homophily, and a mostly single-seed grid.

**Three kernels rather than one.** `penumbra/synthetic.py` grows a `homophily_form` axis with three
options that are not reparametrisations of each other: `power`, an unbounded power law on inverse squared
latent distance; `logistic`, a bounded kernel that saturates instead of diverging as distance goes to
zero; and `block`, which discards the distance kernel entirely for discrete latent communities, so two
nodes are similar if they share a block and not otherwise. All three reduce to a uniform weight at
$h = 0$, which keeps the negative control comparable across them.

**Three seeds across the whole grid rather than the transition rows only.** The full six-by-six grid in
both anchor regimes, under all three kernels, at three seeds: 648 corpora.

**What the kernels found, and why it needed a second measurement.** Under `power` and `block` the
collapse reproduces; under `logistic` nothing collapses inside the swept range of $h$. That is not
evidence that the collapse is a property of the power law, and reporting it that way would be wrong:
$h$ is a kernel parameter and the three kernels scale it differently. The block kernel collapses
earliest, at $h$ between 1 and 2; the power kernel between 2 and 3; the logistic kernel not at all.

So the collapse is reported against a quantity a field corpus also has, and
`scripts/run_homophily_scale.py` measures it: the **strongest anchor's clique contrast at level 1**,
read at one period. It has to be the clique contrast on both sides and not Table 7's density
contrast, or the comparison commits the units error Section 6.4 documents; the reference is read out
of corpus A's own horizon curve rather than typed in.

| | collapse threshold, anchor clique contrast | |
|---|---|---|
| power kernel | **0.0152** | |
| block kernel | **0.0186** | two mechanisms sharing no functional form, agreeing to a fifth |
| logistic kernel | never reached; its maximum is **0.0063** | silent rather than contrary: it
does not resist the collapse, it never reaches the concentration |
| **corpus A, strongest anchor** | **0.0259** | above both thresholds, by 1.7 and 1.4 |

That is the bridge the first review asked for and the second review's objection made necessary. It
does not show that corpus A's phantom is caused by homophily, because the trace there is the
unknown; it shows that the regime in which the pooled statistic provably loses identification is
one corpus A is inside. Section 10's threat is narrowed accordingly rather than deleted.

## R2.4 Corpus B does too little for the space it gets

Section 6.6 went from **2,076 words to about 1,400**, and now opens by stating exactly what it delivers:
the size dependence generalises to a domain sharing no entities, relations or subject matter; one general
claim is falsified and restated; a documentary reading ranks the three contaminated channels first,
second and third, with the caveat on its prospectiveness; and, negatively, nothing in the domain
saturates, so mechanism (b) is correctly a claim about coalition relations. Three paragraphs that
restated Table 8's numbers were folded into one.

## R2.5 Section 9 was almost a separate paper

Section 9 went from **1,851 words to 1,145**, and the engineering detail moved to the new **Appendix C**,
which tables the nine defects with what each was and what it changed. What stayed in the body is the
argument: a diagnostic's output is only as good as the artefact chain behind it, the four defects that
changed a leakage number are named in the opening paragraph rather than left to be inferred, the box of
six questions, and the two questions the first four do not contain. The section also now connects to the
provenance literature it was previously silent about.

## R2.6 The bibliography was thin

**20 references before, 46 after**, every field taken from the publisher record through the CrossRef API
and every entry cited for a stated purpose. The three literatures the reading named as single-citation
passes are the ones that grew:

- **Measurement validity**: Cronbach and Meehl on construct validity, which is the position a leakage
  diagnostic is in, plus Geiger et al. on whether papers report where their labels came from.
- **Survival analysis**, previously one uncited sentence: Cox, Allison on the discrete-time formulation
  we actually estimate, Prentice et al. on cause-specific competing risks, Fine and Gray on the
  subdistribution alternative we do not use and why, Finkelstein on interval censoring, and
  Box-Steffensmeier and Jones for the same machinery in the substantive field.
- **Provenance**: Simmhan et al. and Cheney et al. for the why/how/where distinction the stamping
  implements, model cards, Paullada et al. on dataset practice, and Sambasivan et al. on data cascades,
  which is the shape of every defect Appendix C reports.

Also added: seed variance and reporting practice (Henderson et al., Dodge et al.), which is what Table
10's lesson is an instance of; shortcut diagnosis in natural language inference (Gururangan et al.,
McCoy et al.), with a note on why their diagnostic-set method is unavailable here; the encoders we
compare (Hamilton et al., Schlichtkrull et al., Rossi et al.); link-prediction evaluation (Yang et al.);
hypergraph structure (Do et al.); the substantive literature on why international organisations end
(Eilstrup-Sangiovanni) and the version 2 IGO release whose coding rules the corpus inherits; and the
community assessment of module identification on interaction networks (Choobdar et al.).

## R2.7 Net effect on length

Body prose fell from **28,850 to about 26,500 words** despite the reference expansion, because the
history strip, the two compressions and the sentence splitting removed more than Sections 2, 6.3 and
6.5 added. The three appendices now hold the audit trail, the nine defects and the termination task,
which is where a reader who wants them can find them and where a reader who does not can skip them.

# JMLR conversion: what became LaTeX, and what the conversion found

The target journal accepts LaTeX only, so `paper/penumbra-revised.docx` — the authors' edit of the
round-two manuscript, four authors on the byline rather than six — became `paper/jmlr/penumbra.tex`
against `jmlr2e.sty`. `scripts/build_jmlr.py` does it, and re-does it: the `.tex` is generated and
says so in its first line.

## J.1 Why a script and not a transcription

Retyping 34,000 words into a class file has no way of telling anyone whether something was dropped,
which is the defect class Section 9 is about. Pandoc does the language conversion. The script does
the eight things pandoc cannot know about, and then checks its own output fourteen ways, failing the
build rather than warning. Two of those checks earned their place immediately.

The first version indexed the document by heading title and emitted the titles matching `^\d+\. `.
Pandoc writes every heading at the same level, so subsection bodies became their own entries and
were never emitted: Sections 3.1 to 3.4, 5.1 to 5.5, 6.1 to 6.7 and 7.1 went missing, taking seven
of the eight figures, eleven of the fourteen tables and four references with them. Nothing about the
output looked wrong. What said so was the check that every entry in the `.bib` is cited: four keys
were not, and they were all in the missing sections. The assembly now walks the document in order.

The second was quieter. Pandoc returns CRLF here, so every `\n` written back out was translated to
`\r\n` again and each line ended `\r\r\n` — which pdfTeX reads as two ends of line, that is, a blank
line after every line of the document. A blank line in a tabular preamble is `\par` where `\par` is
illegal, and the same inside display maths ends the paragraph before the maths closes. In memory the
string was clean, so the checks passed; the file on disk would not have compiled. Line endings are
normalised at the pandoc boundary now, and the written file is checked for a stray carriage return.

## J.2 What the script does that pandoc cannot

- **Front matter.** `\jmlrheading`, `\ShortHeadings`, `\firstpageno`, an `\author` block of
  `\name`/`\email`/`\addr` groups joined by `\AND`, `\editor`, and `abstract` and `keywords`
  environments. The docx has a centred title block instead, which is parsed and rebuilt.
- **Citations.** The manuscript is numbered `[1]` to `[46]`; JMLR requires natbib author-year. All 54
  sites were rewritten, 33 as `\citet` where the author's name precedes the marker in running text so
  the name is not printed twice, 21 as `\citep`. The number-to-key mapping is asserted against the
  reference list extracted from the docx, by surname, rather than assumed: a reordering upstream
  fails the build instead of shifting every citation by one.
- **Figures.** The docx carries rasterised SVGs, and `\includesvg` would need Inkscape at compile
  time. Each is replaced by the vector PDF the figure generator already writes, and the image's
  position in reading order is checked against the number its own caption printed.
- **Tables.** Pandoc emits a captionless `longtable` with the caption in the preceding paragraph.
  Each pair is rewritten together, so a table cannot acquire the wrong caption. Whether a table stays
  breakable is decided by estimating its typeset height rather than by a list of numbers, so adding
  rows upstream moves a table across the boundary on its own. Four exceed the threshold: Tables 1, 5,
  B.1 and C.1.
- **Accents.** Every character outside ASCII is written as an accent command. Six of the fourteen in
  the document are in author names, which is the one place in a paper where a mangled glyph is a
  person's name rather than a typographic annoyance.
- **`\tightlist`.** Pandoc emits it and defines it in its own preamble, which this document does not
  use. It is defined here, and there is a check for the next macro pandoc decides to emit.

## J.3 Two additions to the manuscript, both recorded

Sections 3 and 6 open directly on a subsection, which the guide forbids. Each gained one sentence
naming what its subsections cover. Both describe text that already follows and assert nothing new;
both live in `SECTION_LEADS` in the script rather than in the `.tex`, where they are visible.

## J.4 One citation corrected

Section 9's "REFORMS [3]" pointed at Kapoor and Narayanan's *Patterns* paper; REFORMS is [4]. The
sentence was rewritten after the bibliography was renumbered by key and the hand-typed number was
never remapped — the claim-to-artefact class that Section 9 is itself about, committed in the section
that describes it. Section 2's citation of the same work was correct, which is why nothing noticed.

Fixed in `paper/penumbra-kbs.md`, and applied on the way through by the converter, since the docx
still carries it. `scripts/check_paper.py` now checks the class rather than the instance: an acronym a
reference title names must be cited to an entry that names it, and a surname printed in front of a
number must appear in that entry's authors. Run against the manuscript before the fix, the check
found the REFORMS site and nothing else — no false positive across 46 references and 54 sites.

## J.5 What the conversion could not decide

The byline names four authors. The contribution statement names six: Ömür Koçyiğit and Ayşe Gizem
Ergör have CRediT roles and no place on the byline. Related, the disclaimer says two authors are
affiliated with the Ministry and the affiliation block now lists three. Both follow from the byline
being cut from six to four without the back matter being cut with it. The manuscript is left as the
authors wrote it and the build reports the disagreement every run; resolving it is theirs.

JMLR prints one address per author and the manuscript states only the corresponding author's, so
three are placeholders. So are the repository URL, the release tag and the deposit DOI, which were
already open from round one. The build lists all six every run.

## J.6 What was dropped

The five Highlights lines. JMLR has no highlights section and each restates a sentence of the
abstract. Nothing else: the build asserts eleven numbered sections, seventeen subsections, three
appendices, three back-matter sections, eight figures and fourteen tables, and fails if a count moves.

## J.7 What has not been verified

**The file has not been compiled.** No TeX distribution is installed on this machine and none was
installable, so the thirteen checks stand in for a compiler and are not one. They cover structure,
balance, references, residue, encoding and the arithmetic of float numbering. They cannot see an
overfull line, a float that will not place, or a page break landing badly inside Table 5. The first
compile is still a real step, and `paper/jmlr/README.md` says so in the same words.

## J.8 One more thing the checks found

The manuscript cites its appendix tables as A.1, B.1 and C.1. The article class does not letter the
table counter at an appendix and does not reset it, so those three would have printed as 12, 13 and
14, and every reference to them in the running text would have pointed at nothing. `\numberwithin`
from amsmath now letters the counter and resets it at each appendix, and check 14 fails the build if
a float ever lands in an appendix without it — which is what would happen if a figure moved there.

## J.9 The flow diagram ran off the page

Reported from the first Overleaf compile: the block under "Corpus A, from the register to each
reported count" overflowed the measure. It is the paper's one `verbatim`, the count chain from the
register to each reported number, and the docx had wrapped it by hand for a wider page. Its longest
line was 98 characters; jmlr2e sets `\textwidth` to 6 true inches, and at 11pt a Computer Modern
typewriter character is 5.5pt wide, so 78 fit. The block ran an inch and a half past the margin.

A `verbatim` past the margin is not an error and not a warning either, so the log would not have
named it. The converter now rewraps the block to the number of columns the measure actually fits —
84 at `\small`, computed from the two numbers rather than typed — and preserves the structure, which
carries meaning: an unindented line is a count the register reports, a line opening `->` is a filter,
and the lines under it are that filter's explanation, aligned under the text rather than the arrow.
Check 14 fails the build if any fixed-width line exceeds the measure.

The same scan over everything else that cannot be broken to fit found nothing else. No prose word is
long enough to overhang, and of the fourteen tables, twelve have every word inside its column; two
have one word each overhanging by 2 and 3 points, which hyphenation inside a `p{}` column absorbs.

## J.10 The title was too long for the page it is printed on

Reported from the compile: the title did not fit where it is set. Measured rather than guessed, the
running head fits with room to spare — 321pt of a 434pt measure, since `\ShortHeadings` is set in
`\small` small caps — and what overflowed was the first line of the title block, 448pt against 434pt
at `\Large` bold. So the problem was the title itself and not the abbreviation of it.

**Leakage horizons in relational group membership prediction: a diagnostic suite, its ground-truth
calibration, and the ways it misreports** becomes **Leakage horizons in group membership
prediction**: 134 characters to 46, and one line of 356pt where there were three.

What went: "relational", which is implied by a task read off a graph, and a three-part subtitle whose
three parts are the abstract's first, fourth and last sentences. What stayed: the term the paper
coins, and the task it is about.

The title is now defined once, in `TITLE`, because it is printed three times — the file header, the
running head and the title block — and a rename reaching two of the three is worse than no rename.
Check 14 estimates the width of every title line and of both sides of the running head and fails the
build above the measure; run against the old title it reports 589pt against 434pt, so it fails for
the right reason and not by accident.

Also retitled: `paper/penumbra-kbs.md`, in its front matter and its heading, and the bibliography's
header comment. `penumbra-revizyon-notlari.md` keeps the old title, because it is a record of what an
outside reader was given to read. The docx keeps it too, in the centred block the converter drops
rather than converts; the two do not need to agree, and the block is now skipped by position so that
retitling the docx cannot turn its title into a section.

## J.11 The captions were doing the body's work

Reported from the compile: the table captions are far too long, and the floats should explain
themselves. They were. The longest ran to eight sentences and 216 words, and the average across the
eight figures and fourteen tables was 71.

Read as sentences, every caption has the same shape. The first says what the float is. The second
gives the setup a reader needs to read it: the corpus, the counts, the levels, the lead times, how
the intervals were taken. From the third on it describes the panels and argues from them, and that is
the body's work — the body already does it, in the section the float sits in.

So the cut is at two sentences, applied mechanically. A word budget was tried first and rejected: it
takes the setup sentence off the long-titled figures, which is the half that makes a figure readable
without the text. A sentence count keeps the setup and drops the argument, and nothing is shortened
by a judgement about which of a caption's claims matters. The longest caption is now 50 words, the
average 34, and the document is 5,500 characters shorter.

Thirty-six sentences left seventeen floats. All thirty-six are written to
`paper/jmlr/captions-trimmed.md`, because a caption sentence that is gone is gone whether or not
anyone counts it, and because a sentence worth keeping can be moved into the body from there.

Four of the thirty-six defined something the float itself prints: Figure 7's level \(k = 25\), Table
3's **coverage rate**, Table 4's **censored** column, Table 8's expected-count basis. Dropping a
definition would make the float less self-explaining, which is the opposite of what was asked, so the
build checks each against the body rather than assuming: all four are named there — Section 6.1 for
the coverage rate, 6.2 for censoring, 6.5 for the primary level, 5.5 for the expected count. Had one
not been, the build would name it as a sentence to move rather than drop.

Two checks came out of this. Check 14 fails the build on a caption longer than two sentences. And the
figure captions are now read by matching braces rather than by `[^}]*`, which stopped at the first
`\textbf{` or `\(...\)` group inside a caption and would have truncated it there in silence.

# Round three: what the third reading changed

The reading was about the writing, and it named three things. The abstract was nearly unreadable. The
forward pointers were dense enough to keep a reader turning pages. The revision tags in the body were
well meant and belonged to Appendix B. It ended by saying the risk is a good result going unread,
which is the right way to put the cost.

## R3.1 The abstract

Measured before touching it: **257 words, eleven sentences, ten numeric tokens**, of which two pairs
repeated — and one of those repeats was the reading's sharpest point. `6.8` appeared once as a
percentage of a relation and once as a ratio between two instruments. Two unrelated quantities, the
same digits, four sentences apart.

Three of the ten numbers could not mean anything to someone who had not read the paper: the anchor
clique contrasts 0.0152, 0.0186 and 0.0259 are on a scale the abstract never gives. A fourth, the 562
entities of corpus A, is a corpus size and not a finding. All four are gone from the abstract and all
four are still in the body, which the manuscript's own numeric check confirms: 206 registered claims
still match their artefacts.

What is left is **243 words and three numeric tokens** — the slope going from 1.00 to 0.00, which is
the paper's sharpest single result and legible on sight, and the 6.8 percent of a named relation.
Nothing repeats. Counts that were digits are words now: "all six settings", "after eight years", "Ten
ways". The ratio between the two instruments is stated as the thing it is instead — the pooled reading
still shows a contrast after eight years where the group's own record carries nothing past one.

## R3.2 The forward pointers

**182 "Section N" mentions in 30,000 words of body**, one every 165 words, plus 49 to tables and 11 to
figures. Counting them by section found where it actually hurt, and it was not spread evenly: Related
Work ended nearly every paragraph by pointing forward at where the paper does the same thing. Twenty
of its sentences carried a cross-reference. A reader placing the work in the literature does not want
to be sent to Sections 6.6, 5.5, 5.1, 9 and 6.7 in consecutive sentences; they will reach those
sections anyway.

Nearly all of those pointers had the same repair, and it was not deletion. The sentence was saying
*ours* and pointing at *where ours is*: "Section 5.1's declaration protocol is that idea pushed one
step further" is our declaration protocol, and "which is the shape of every defect Section 9 reports"
is the shape of every defect our own audit reports. Naming the thing instead of its location keeps the
claim and drops the page turn.

**158 mentions after, one every 189 words.** Related Work keeps two. By density the worst prose section
is now at twelve per thousand words, which is ordinary. The two densest sections left are Threats to
Validity and the contribution statement, and pointing is what those are for.

Sentences naming two or more targets went from 26 to 18, and of the 18 the remainder are enumerations
that earn it: "Table 10 and Figure 8 give the architectural comparison". Three that did not were
rewritten, including the one closest to the reading's own example, a clause chain naming Section 6.5
and Section 6.2 in one breath.

## R3.3 The revision tags

**Thirty-eight in the body, zero in the appendices.** Appendix B already carries all twenty in a
table, with what each change was and what forced it, so in the body they were a pointer at a list the
reader can find. Removed by pattern, and the pattern is parenthesised so Appendix B's own `R1` column
is untouched. The conclusion's one sentence naming Appendix B is the pointer that remains.

## R3.4 Where the changes live, and why not in the .tex

The `.tex` is generated, so an edit made there is discarded by the next build. The prose changes live
in `paper/round3-edits.txt`, one block each with the reason and the text it replaces, and the build
requires every one to match exactly once across the abstract, the body and the acknowledgements: an
edit that matches nothing means the docx moved under it, and one that matches twice would change a
sentence nobody looked at. Twenty-five applied.

`scripts/sync_round3_markdown.py` applies the same edits to `paper/penumbra-kbs.md`, translating the
markup and matching across that file's hard line wrapping. Without it the two sources drift on exactly
what the reading complained about: regenerate the docx from the markdown and the tags and the
number-heavy abstract come back. Twenty-four of the twenty-five apply there; the abstract is the
exception, because the docx carries a rewrite of it that the markdown never had, so it has its own
replacement written to the same brief.

## R3.5 One error the reading did not name, and one it did not have

Fixing the multi-reference sentences surfaced "That much Sections 3.4 and Table 1 already state" — a
plural agreeing with one section and one table. It is in the docx, not in the conversion. Corrected.

The reading also reported a missing closing parenthesis under Corpus A. There is none: parentheses
balance in the `.tex`, in the markdown and in the docx, the only apparent exception being the
half-open interval \((t_L, t_R]\), which closes with a bracket because that is what it means. The one
mechanism that could have produced the symptom was real, though, and is now closed: figure captions
were being read with a pattern that stops at the first `\textbf{` or `\(...\)` group inside them, so a
caption could have been truncated mid-parenthetical in silence. They are read by matching braces now.

## R3.6 Checks

Three, because the failure mode here is drift back rather than a one-off. The converter's check 14
fails the build on an abstract over 250 words, over six numeric tokens, carrying the same number
twice, or leaving a revision tag in the body. `scripts/check_paper.py` now applies the number and tag
rules to the markdown as well. Both were tested by injecting a duplicated 6.8 and an `(R9)` into the
abstract: three failures, for the three right reasons.

## R3.7 The author block, and a letter small caps cannot spell

The four author addresses were supplied and are in place, so the only placeholders left are the
repository URL, the release tag and the deposit DOI.

The second half was reported from the page: the running head spelled Koçyiğit with dotless i's. It was
not an escaping fault — the accent commands were right. `\ShortHeadings` is set in `\small\sc`, and in
these fonts the lowercase slots hold small capitals, whose *i* has no dot. In English that is correct
typography. In Turkish the dotted and the dotless i are separate letters, so the running head was
carrying a misspelled name on every even page.

There is no faithful repair that keeps both the small caps and the name: the fonts have no dotted
small capital, and writing an uppercase İ among small capitals sets it at full height. The fix is the
class's own documented short author form — its usage comment reads `\ShortHeadings{Minimizing
Conflicts}{Minton et al}` — so the running head now gives **Kutsal et al.** The full list keeps its
dots in the page footer, which `jmlrheading` sets in `\scriptsize` roman with no small caps, and in
the author block, which is roman too.

Check 14 fails the build if a Turkish accent command and an undotted *i* ever appear together in
either side of the running head. Its first version passed the negative test it should have failed: it
read the running head with a pattern, and `\u{g}` closed the argument early, so it inspected half the
author list and found no accent. It reads both arguments by matching braces now, which is the third
time in this conversion that a pattern where brace matching was needed has quietly read half of
something — the figure captions and the CRediT names were the other two.

# Round four: what the fourth reading changed

Two complaints. The prose was hard to read, and the paper did not agree with itself about its own
counts — which the reading called ironic in a paper about auditing, and it is.

## R4.1 Four places where the paper contradicted itself

Each was traced to its arithmetic before being changed, because a count fixed by guessing is the same
defect with a different number.

**The abstract said ten ways with one undemonstrated. Section 7 says eleven are listed and ten
demonstrated.** The abstract's phrasing implied nine demonstrated. Section 7 is right and states its
reason: item (e) is a concern that is sound a priori, that we tested and could not demonstrate, and a
tally of the ways an instrument fails should not be padded by a way it did not. The abstract now reads
eleven listed and ten demonstrated.

**Section 9 said two external reads produced thirteen defects. Its own breakdown is three count pairs,
three terminological and six citations, which is twelve** — and the thirteenth is the pair that
chasing the twelve turned up, 151 coded terminations against the 150 the panel scores, which we found
ourselves. Twelve from the reads, a thirteenth from following them, both stated.

**Section 10 called the same set four.** Stale: it was four in an earlier draft. Section 9 says every
one of them is a claim-to-artefact mismatch, so the number there is twelve.

**Appendix B said thirteen of its twenty were found from outside; its table shows eleven.** It had
borrowed Section 9's count of *defects* for a count of its own *rows*, and a row can absorb several
defects — six citation corrections are one row. Counted from the table: ten rows where an outside read
came first, one where an outside read named what our own test had found, nine ours alone. The appendix
now says eleven, and says which eleven. The acknowledgements had the same borrowed thirteen and now
say eleven too.

## R4.2 The byline

The title page listed four authors and the contribution statement six. This was reported here twice
before an outside reader found it, which is its own small lesson.

The byline is the authors' own decision, taken when the docx was edited from six names to four. The
contribution statement now matches it, and Ömür Koçyiğit and Ayşe Gizem Ergör are thanked in the
acknowledgements for the investigation and validation their CRediT roles named. **This is one block in
`paper/round4-edits.txt` and deleting it restores the six-author statement**; if the intent was the
other resolution, restoring the two to the byline is the edit to make instead.

The disclaimer said two of the authors are affiliated with the Ministry. Three of the four are.

## R4.3 One sentence that had broken in two

`... and Section 5.5's flow separates the two. and one figure from it belongs here because ...` — a
full stop mid-sentence with the next clause starting in lower case. It is in the docx.

## R4.4 The correction list, told five times

Section 5.1, Section 9, Section 10, Section 11 and Appendix B all told the story of the paper's own
corrections. Counting audit vocabulary per thousand words found where: Appendix B at 19.5, Section 9
at 9.0, the conclusion at 5.7.

Each of the five has a different argument to make, and the redundancy was in re-narrating the items
rather than in referring to them. So each keeps its argument and stops narrating:

* **Section 5.1** keeps the principle that an amendment to a declared protocol must be visible, and
  drops the list of which three amendments; Appendix B tags them.
* **Section 9** keeps the four defects that changed a leakage number, which is the section's own
  argument, and points at Appendix C for the other five.
* **Section 10** keeps the threat and loses nothing but a wrong number.
* **Section 11** kept a full re-narration of all eight substantive changes *in the sentence after
  pointing the reader at Appendix B*. That is now the pointer and the verdict, 150 words shorter.
* **Appendix B** is the canonical list and is unchanged.

## R4.5 The sentences

Measured first: **157 of 967 prose sentences at forty words or more, 16.2 percent**, mean 26.4, with 43
at fifty or more.

Ninety-two edits later: **109 of 1,027 at forty or more, 10.6 percent**, mean 25.0, with 11 at fifty
or more, and most of those eleven are the display-maths and diagram blocks that the sentence splitter
counts as sentences.

Only nested sentences were split. An enumeration is long but not hard — a list of six data sources
reads straight through at seventy words, and breaking it up would make it worse. What got split is a
sentence that suspends its main clause while two or three subordinate ones resolve. Every split keeps
the words: it moves a comma to a full stop and names the subject the second half had been borrowing.
Two of them also repaired a fragment that the length had been hiding.

## R4.6 Where it lives, and four checks

The prose changes are in `paper/round4-edits.txt`, `round4-splits.txt` and `round4-splits2.txt`, one
block each with its reason and the text it replaces, and the build requires every one to match exactly
once. Ninety-two applied across four round files. `scripts/sync_markdown_edits.py` carries them to the
markdown source, and names the sixteen it cannot translate.

Four checks, because every one of these defects had passed everything:

* **Check 14** fails the build above 12 percent of prose sentences at forty words or more.
* **Check 15** counts Appendix B's rows and compares them with the number the appendix claims for
  itself. Run against the old text it reports both errors; run with the claim deleted it says the
  claim is missing.
* `scripts/check_paper.py` compares the byline with the contribution statement, name by name.
* The same checker no longer dies while reporting: a failure naming a Turkish author crashed it on a
  console that cannot encode the letters, so the check fired and the message never arrived.

## R4.7 Two mistakes worth recording

The edit mechanism cost two errors of its own, both of the same shape: **something written against the
finished document, applied to a text that was not finished yet.**

The `find` strings were read off the compiled `.tex`, where the accents are LaTeX commands and the
revision tags are gone. The edits were applied before either had happened, so a sentence ending in a
full stop could not match the same sentence ending in `(R13).`, and a Unicode minus could not match
`\(-\)`. Both are now ordered the other way: the mechanical passes run first, and an edit file is
written against the document as a reader sees it.

The second was worse and reached the output. The parser skipped comment lines only while no block was
open, so the `# ---` separators between blocks fell into the replacement text. A bare `#` is a macro
parameter character and the document would not have compiled. It is a comment wherever it appears now,
and check 6 looks for a stray one.

## R4.8 Nothing was lost

Of the 1,042 sentences in the docx body, every one missing from the `.tex` is accounted for: 4
Highlights lines and 30 caption sentences dropped on purpose, 9 rewritten by a named edit, and 4 short
sentences whose only eight-word run included a removed revision tag or a converted citation. No
accidental loss across 92 edits.

## R4.9 A third mistake of the same shape

The markdown sync was not idempotent. An insertion keeps its own `find` inside its `replace` — the
acknowledgement edit adds a sentence after one that stays — and the script tested for a match before
testing whether the replacement was already there. The `.tex` is rebuilt from the docx on every run so
it never accumulated, but the markdown is a file that persists, and the thanks sentence went in twice.
Found by running the sync twice and reading the count, which is the only reason to run it twice.

"Already applied" is tested first now, and running the sync three times in a row reports zero applied
on the second and third. That is the property to check for anything that edits a file in place rather
than rebuilding it.

# Round five: one phrase

The paper opened with "A knowledge-based system that predicts group membership takes a set of
candidate entities, a group, and a body of relational data, and asks whether the candidate will join."
Removed at the author's request.

It was a leftover from when the manuscript was written for *Knowledge-Based Systems* — the markdown
source is still called `penumbra-kbs.md` — and it names a research tradition this paper is not in. The
abstract already had a term for the thing, so the opening sentence now uses it: **a group membership
forecaster**. The first line of the introduction and the first line of the abstract now say the same
word for the same object, which they did not before.

One occurrence, checked rather than assumed: the phrase appeared once in the body and nowhere else.
Three "Knowledge" strings remain and stay, all journal names in the reference list — *Knowledge and
Information Systems*, *ACM Transactions on Knowledge Discovery from Data*, and the SIGKDD proceedings.

Two checks, because a phrase retired by a decision leaves no measurement behind to catch its return.
Check 14 of the converter fails the build on the phrase in the `.tex`; `scripts/check_paper.py` adds it
to the retired-phrase list for the markdown, which now stands at 31. Both were tested by putting the
phrase back: each failed, for the right reason.

The markdown file name still says `kbs`. Renaming it touches `check_paper.py`,
`sync_markdown_edits.py` and this log, and it is not in the paper, so it is left for the authors to
decide rather than changed unasked.

# Round six: the disclaimer and the repository

Both given by the authors.

## R6.1 The disclaimer

Replaced with the supplied wording, which drops the affiliation count and the sentence about no
institution having reviewed the content:

> *Disclaimer.* The views expressed in this paper are the authors' own and do not represent the
> position of the Republic of Türkiye Ministry of Foreign Affairs with which the authors are
> affiliated.

Two notes. The supplied text read "...Ministry of Foreign Affairs which the authors are affiliated";
a preposition is missing, and it reads "with which" here, which is the form the sentence it replaces
used. Nothing else in the wording was touched.

The supplied wording also drops the count. The title page shows three of the four authors with a
Ministry affiliation and the fourth with Darmstadt alone, so "the authors are affiliated" is broader
than the affiliation block. Left as supplied, because a disclaimer is the authors' own statement about
their own institution. "with which three of the four authors are affiliated" is the change to make if
the broader reading was not intended.

## R6.2 The repository, and no release tag

The availability section read "released as one repository at [REPOSITORY-URL], at the tagged release
[RELEASE-TAG] the reported numbers were computed from, under the MIT licence." It now reads "released
as one repository at \url{https://github.com/McahitKutsal/Leakage-Horizons}, under the MIT licence."
The tagged-release clause is gone rather than left empty.

The address was checked rather than pasted. The repository exists, is public, and carries an MIT
licence dated 2026, which is what the sentence claims and which also settles the licence question
open since round one.

**It also contains nothing but that licence file.** No code, no README, no description. The
availability section describes the corpus construction, the diagnostic suite, the survival estimators,
the synthetic generators, every analysis script, the consistency checker and the second implementation
of the density code as released there. Until they are, that paragraph is a claim whose artefact does
not exist. It is the claim-to-artefact class Section 9 is about, in the one place a reviewer can check
in a single click, and it is the reason a URL is worth resolving before it is printed rather than
after.

The two sources word this passage differently: the docx carries the bracketed placeholders and the
markdown never had them. `scripts/sync_markdown_edits.py` grew a short table of markdown-only edits
for exactly that, rather than the round file being written twice.

Only `[ARCHIVE-DOI]` is left outstanding.

## R6.3 The deposit DOI, wired rather than typed

The declaration bundle is built and waiting: `declaration/` holds `pre-registration.md` (33,841
bytes), `corpus-b-channel-declaration.md` (4,543 bytes) and `MANIFEST.json`, each file with its
sha256, and the manifest's `deposit_identifier` field has read "TO BE COMPLETED AT DEPOSIT" since it
was written.

It now takes the value from there. `build_declaration.py --doi 10.5281/zenodo.NNNNNNN` records it in
the manifest, and `build_jmlr.py` reads the manifest and replaces `[ARCHIVE-DOI]` with a `\url` to
doi.org. A string that is not a DOI fails the build instead of printing a broken reference; both paths
were tested. Nothing is typed into the manuscript, which is Section 9's fifth question applied to this
paper's own front matter: a number that appears in a paper and in an artefact should be entered once.

Two things checked while setting this up, both of which bear on claims the paper makes.

**The three pre-registration commits are in the local history**, with the hashes and dates the manifest
records: 410121f4 on 2 August 19:50, 936927fb at 19:58, 2cb2579f on 3 August 10:24. Section 5.1's
evidence is that history, not the deposit. There is no git remote configured yet and the branch is
`master`, so whatever is pushed must be the history itself — 29 commits — and not a snapshot. A fresh
repository with one commit would make the pre-registration claim false while leaving every number in
the paper correct, which is the hardest kind of defect to notice.

**The deposit does not date the declaration**, and the paper already says so: "Depositing the artefact
now fixes its text and does not make it evidence about the order in which it and the statistic were
produced, and we would rather say so than let a deposit date imply otherwise." Any archive's DOI is
minted when the deposit is made, which is after the analysis. The sentence stays as it is.

## R6.4 The deposit DOI, and what resolving it found

`10.5281/zenodo.22110800`, recorded with `build_declaration.py --doi` and taken from the manifest by
the build. The placeholder is gone and no placeholder is left in the manuscript.

The DOI was resolved before it was printed, which is the point of the exercise. It goes to the right
record: the title is the paper's, the four authors are the byline's, and the three files are the
bundle's at 4.5 kB, 2.8 kB and 33.8 kB against the manifest's 4,543, 2,769 and 33,841 bytes.

Recording the DOI did not disturb what was deposited. `build_declaration.py` rewrites the bundle, so
the checksums were compared before and after: `pre-registration.md` at cfbef64b and
`corpus-b-channel-declaration.md` at 3fc329c0 are byte-identical. Only `MANIFEST.json` changed, and it
does not record its own checksum, so the deposit is still correctly described by the manifest that
describes it.

Three things about the Zenodo record are worth writing down.

**Two author names are transposed.** Zenodo's field order is family name, then given name. The record
reads "Kutsal, Mücahit" and "Erdağ, Alpaslan" correctly, and then "Uğur, Özbek" and "Doğa, Koçyiğit",
which makes Uğur and Doğa the family names. DataCite indexes on that field, so a citation to the
deposit would render "Uğur, Ö." and "Doğa, K." Zenodo metadata stays editable after publication,
unlike the files, so this is a fix rather than a new version.

**The record is CC BY 4.0 and the repository is MIT.** For documents rather than code that is the
better licence, and the manuscript claims MIT only for the repository, so nothing in the text
contradicts it. Noted because the two differ and the difference was not stated anywhere.

**The deposited `MANIFEST.json` still reads "TO BE COMPLETED AT DEPOSIT".** A file cannot carry the
DOI that names it unless the DOI is reserved before publishing. The local copy now carries it and the
deposited one does not, which is the only difference between the two, and the two documents the
manifest makes claims about are identical in both.

`corpus-b-channel-declaration.md` now has a commit, made by this release, and
`build_declaration.py` reported it the right way: "a commit exists but postdates the analysis, which is
not evidence about the order." The manifest still records `timestamped: false` and the artefact is
still marked not timestamped in its own text. Section 6.6's limitation is unchanged.

# Round seven: the availability section, checked against what was published

Asked whether the paper was ready to submit, the useful thing to do was not to answer but to take the
availability section apart and check each artefact it names against `origin/main`. Two of them failed.

## R7.1 A fetch script that does not exist

> Every source is public and is obtained by a fetch script in the repository which records the release
> it retrieved.

There is no fetch script. Not in the published tree, not untracked, not in any of the thirty-two
commits of history, not in `vendor/`. No file in `penumbra/` or `scripts/` imports an HTTP client or
contains a data URL; the only `http://` strings in the code are XML namespaces in `build_paper.py`.

`LEDGER.md` is more specific than that. `atopdata.org` "refuses the TLS handshake from this network, as
CLIQUEBAIT also found", so at least one source demonstrably was not obtained programmatically at all.

The clause is removed rather than the script written: writing it needs network access to six sources
and one of them is unreachable from here. What the clause was for — recording which release each
source came at — the next sentence already does, naming all six with their releases.

This is the claim-to-artefact class Section 9 is about, in the paragraph a reviewer checks first, and
it survived seven readings because every check compared the paper to a results file and none compared
it to the repository.

## R7.2 A checker nobody could run

> It is released with the rest, so that a reader can run the check rather than take its output on
> trust.

The checker was released and `results/**/*.json` was in `.gitignore`, so a reader could run it and get
nothing. `check_paper.py`, `check_consistency.py` and `build_figures.py` read `results/` and nothing
else, and the raw data is not published either, so the numbers could not be regenerated to replace
them. The same gap made "all reported figures are regenerated by named scripts from the stored
results" unverifiable.

The 51 files are 2.6 MB and carry no local path or identity — the two that matched a search for one
matched inside organisation names, "Public Administration". They are published, which makes three
claims in the paper true at once, and the `.gitignore` comment that excluded them now says why they
are there instead.

Verified rather than asserted: the published tree was extracted to a clean directory and the checkers
run in it. `check_paper.py` reports 206 numeric claims matching their artefacts, and
`check_consistency.py` reports 31 registered claims matching their sources. That is the sentence in
the paper, tested the way a reader would test it.

`verify_reference_density.py`, the cross-check between the two density implementations, needs
`data/ledger/membership.parquet` and stops without it. The paper claims that both implementations and
the cross-check are released, which is true, and does not claim a reader can run it; Section 10
already says no one outside the author group has rebuilt either corpus.

# Round eight: the bibliography, against the publisher's own record

Asked to check the citations so that nobody is caught cheaply there. `scripts/check_citations.py`
compares every entry with CrossRef, and with DBLP for the six proceedings papers that mint no DOI:
the DOI resolves, the title, the print or issue year, the venue, the first author's family name, and
the number of authors.

**Forty-six entries, forty against CrossRef and six against DBLP, and after three corrections, none
with a problem and none unchecked.**

## R8.1 Three real errors

**`cheney` pointed at the wrong edition.** The DOI `10.1561/9781601982339` is the standalone
monograph, which now Publishers deposited as a 2007 book with no volume, issue or pages. Our entry
gives *Foundations and Trends in Databases* 1(4), 379–474, 2009, which is the journal article and has
its own DOI, `10.1561/1900000006`: CrossRef confirms type journal-article, that container, that
volume, those pages, print year 2009. The DOI is the one thing in an entry a reader clicks, and it was
taking them to a different object from the one described around it.

**`atop` had a name parsed wrong.** `McLaughlin Mitchell, Sara` makes McLaughlin Mitchell the family
name, so BibTeX would set "McLaughlin Mitchell, S." in the reference list and "McLaughlin Mitchell
et al." in the text. Her family name is Mitchell; it is now `Mitchell, Sara McLaughlin`. Getting a
cited author's name wrong is the cheapest catch there is, and it is worse than a wrong page number
because it is a person's name.

**Two titles had been altered.** `atop` read "1815 to 1944" and `mid5` read "2011 to 2014", where both
papers use an en dash. Writing out an en dash is this project's rule for its own prose, applied by
mistake to someone else's title. A cited title is a quotation; both now read `1815--1944` and
`2011--2014`.

## R8.2 Two the entry had right and CrossRef had wrong

**`datasheets`.** ACM deposited Hal Daumé III as given name "Hal Daumé", family name "III". Our
`Daum{\'e} III, Hal` is correct. Recorded in the checker's `CROSSREF_WRONG` table rather than
tolerated, so that "the publisher's record disagrees" keeps meaning something.

**`geiger`.** ACM deposits the part after the question mark as a subtitle, so CrossRef's title is just
"Garbage in, garbage out?". The full title is ours. The checker now joins title and subtitle before
comparing.

## R8.3 The one hard numeric attribution, verified verbatim

Section 2 says \citet{kapoor_leakage} "survey 294 papers across seventeen fields and give a taxonomy
with eight leaves", and that their remedy is a model info sheet. The published abstract says "we find
17 fields where leakage has been found, collectively affecting 294 papers", "a detailed taxonomy of
eight types of leakage", and "model info sheets, which we introduce". All three exact.

Worth noting which version that came from: **the arXiv preprint of the same paper says 329 papers, not
294.** We cite the Patterns version and carry its number. Anyone working from the preprint would have
written 329 against a published DOI and been wrong in a way no internal check could see.

The taxonomy's shape is consistent too — the paper describes L1 with four leaves, L2, and L3.1 to
L3.3, which is 4 + 1 + 3 = 8. The eight labels themselves were not independently re-read for this
round; they were checked in round one, when the L1-to-L2 assignment was corrected.

## R8.4 The checker's own three bugs

Each would have made it useless, and each is the same mistake: comparing against the wrong field and
believing the answer.

**It read CrossRef's `published`**, which is defined as the earliest date on the record. Nine of our
entries are online-first a year before their issue, and the issue year is what a citation carries. The
first run reported nine correct entries as wrong — enough noise to make anyone switch the check off.
It reads the print or issue year now, and reports which field a year came from when they differ.

**It compared a title without its subtitle**, and an ampersand without unescaping the entity, so
`geiger` and `do_hyper` were flagged for matching.

**It swallowed every DBLP failure into "nothing found".** DBLP throttles a run of queries, the fifth
and sixth failed, and two entries DBLP knows perfectly well were reported as verified — a checker
saying "checked" about something it had not asked. It now distinguishes "DBLP answered and has
nothing" from "DBLP would not answer", retries with a backoff, waits three seconds between queries,
counts unchecked entries separately, and exits non-zero if any remain.

## R8.5 An archive that could go behind

Asked whether the zip had been updated, the answer was yes, and checking it properly was worth more
than the answer. Every one of its eleven entries was compared with the file on disk by sha256: all
identical, and the deposit DOI, the corrected `cheney` DOI, `Mitchell, Sara McLaughlin`, `1815--1944`,
`2011--2014` and the repository URL are all inside it.

The failure worth guarding was a different one. `pack_jmlr.py` read the archive back and checked names
and CRC, so it could not tell a current archive from one a version behind — and neither could a
compile, because the archive is not what compiles. An archive that still holds every file under the
right name and one of them stale is exactly what gets uploaded.

The byte comparison is now in the packer, which confirms the write landed. The staleness guard is in
`build_jmlr.py` instead, because the packer rewrites the archive from disk on every run and can never
observe itself stale; the build is what knows the `.tex` has just changed. It reports either "the
Overleaf archive matches this build" or which entries it is behind on. Tested by changing `TITLE`,
building without packing, and reading the warning.
