# What this programme found

Written 2026-08-04, after the measurement phase. Revised the same day, three times: when the
corpus-wide focal-isolation run came in (§2(h)–(j), §4, §6; V11, V12); when closing the provenance gap
those runs exposed produced nine more defects and one correction to the capstone (§5, §7, §8; D-31 to
D-42); and when the second domain **falsified §2(d)**, narrowed (h), generalised (c) and produced the
programme's only positive result (§2.1, V13, D-43). `PENUMBRA-OUTCOMES.md` records verdicts clause by
clause and `DECISIONS.md` records how each number was arrived at; neither shows the shape. This file
decides what the paper is.

The short version: **the programme set out to measure a quantity and instead established that the
instrument it built cannot measure that quantity — and proved it on a corpus where the quantity is
known exactly.** That is a stronger result than the one intended, and it is a different paper.

---

## 1. What was intended and what happened

The manifesto's thesis is that an event casts a shadow backwards into the data preceding it, that
this shadow is measurable as a **leakage horizon** $\Delta^\star$, and that forecasting outside it
escapes the leak while forecasting inside it does not. Seven predictions follow, five of which are
about $\Delta^\star$ or about what depends on it.

$\Delta^\star$ was never identified on the coalition corpus. Not because the measurement was
careless — it was calibrated against a known back-dating parameter on synthetics and recovered it in
6 of 6 settings — but because **the diagnostic the manifesto specifies is blind to the phenomenon
whenever the leaking relation carries contributions from anything other than the focal group**, and
in a curated coalition corpus it always does.

Worse than blind, and this is the sharpest form of the result. Run as specified over all 8,062
accessions, U1 returns a monotone decaying contrast from 0.3114 at $\Delta = 0$ to 0.1490 at
$\Delta = 8$ that never returns to band — the signature of a penumbra at least eight years wide.
Measured on the focal entity's own record, the same events carry a trace at $\Delta = 0$ and
**exactly none at $\Delta \geq 1$**. The corpus has no penumbra and the instrument reports one eight
years wide, because a trace of the event and a persistent similarity to the members enter the
statistic identically (V12).

The proof is V10, on a corpus where the width is printed in the source. DESTA codes an agreement's
signature year and its entry-into-force year, so a relation built from the earlier one carries the dyad
`gap` years before the event — real exposure for anyone forecasting from signature-dated data, and its
width is read off the coding rather than estimated. Measured the way the manifesto specifies, as a
density over the whole relation, the contrast between inside and outside that coded gap is **0.102**
against a truth of 1.000, and the curve is nearly flat: 0.752 at $\Delta = 0$ to 0.621 at $\Delta = 8$.
The penumbra is there, its width is known, and the instrument recovers a tenth of it.

Two things this argument does **not** rest on, and D-34 separates them out because the first version of
V10 leaned on both. The focal-isolation step table is entailed by its own construction, so it verifies
the pipeline rather than recovering $\beta$; the evidence that the *estimator* recovers a known $\beta$
is C18's synthetic calibration, 6 of 6 settings. And the COW IGO negative control returns zero because
COW IGO codes one date per membership, which entails it. The surviving claim is narrower than "two
ground-truth corpora, one with a penumbra and one without" and it is sufficient.

## 2. The contribution: ten ways a leakage diagnostic fails, each with its proof

None of these is in the manifesto. Together they are the paper.

**(a) The diagnostic needs an operation the manifesto does not specify.** §5.3 prescribes focal-group
*exclusion*, to stop the focal group's own edges standing in for the label. Detecting the shadow
requires the *isolation* of those same edges, since that is the only place back-dating lives. Two
operations, opposite purposes, one of them absent. UMBRA now ships both (D-27). **Proof: V10.**

**(b) A saturating relation hides the shadow, and coalition relations saturate.** IGO co-membership
has density 0.995 — with 490 organisations over 168 states almost every pair shares something. The
focal contribution is 6.8 % of the relation. Thresholding does not fix it, and is non-monotone in
density; excluding near-universal bodies does not fix it either, leaving 0.706 after dropping every
organisation that ever spans half the state system. **Proof: C15, V10**, with V13 fixing the scope: no
protein relation exceeds density 0.001887 and $r^\star$ there is 0.001153, a factor of 864 (corrected in
D-51 from 0.00377, 0.00231 and 431, which were every corpus B density doubled by a directed row count),
so this is correctly a claim about coalition relations and a second domain cannot test it further.

**(c) The exact-clique statistic is structurally zero on large groups.** A 90-member coalition has
4,005 dyads and a clique needs all of them, so the contrast is 0.20–0.25 below twenty members and
identically **0.000** above eighty, **at the declared primary level $k = 25$** — where 41.1 % of the
corpus's events live on v4, 36 % on v1. The level is not optional: at $k = 1$ the same statistic on the
same corpus *rises* with size, 0.0625 to 0.4778, because co-membership is saturated there, so (b) and
(c) interact rather than standing separately (D-44). CLIQUEBAIT chose this
statistic because it survived all three settings it was tested in; none had this size distribution,
the protein benchmark's median complex being 3 against LEDGER's mean positive stratum of 66.
**Proof: V3, and V13 generalises it.** Run on that benchmark the contrast is 0.412 at 2-3 members, 0.467 at
4-5, 0.366 at 11-20, 0.177 at 21-80 and **identically 0.000 above eighty** -- the same function, in a
domain with no states, no treaties and no time axis. V3 could only see the large end because LEDGER has no
small groups in quantity; the two corpora together trace the whole curve.

**(d) In LEDGER there is no subpopulation where both problems go away — and that is a fact about LEDGER,
not about group corpora.** Large groups kill the statistic by arithmetic; small groups come with small
samples. On the 59 alliance entities, median membership 5, the statistic has power in principle and the
standard error equals the effect — separating a contrast of 0.03 from a band of 0.01 needs about 600
positives per horizon against the 110–176 available. On the corrected corpus the pre-specified rule stops
returning an interval at all: $\Delta^\star_{\text{lo}} = 2$ sits **above**
$\Delta^\star_{\text{hi}} = 1$, and the lower bound moved from 3 to 2 for no reason except that the sample
shrank 47 %, while the band itself nearly tripled as positives fell 176 → 110. A horizon estimate that is
a function of $n$ is not a horizon. **Proof: V8, D-30.**

**This claim was stated generally and the second domain falsified it (V13, D-43).** The protein benchmark
has **1,399** positives at 2–3 members with a clique contrast of **0.4124** against a negative clique rate
of **0.0000** — size and sample favourable at once, cleanly. The trade-off holds where a corpus's group
size **correlates with entity type and the small-size type is rare**, which is LEDGER exactly: 59
alliances at median 5 carrying 177 events, against numerous large organisations. It is not a property of
curated group corpora as such, and the earlier wording generalised from LEDGER's composition. The
restatement is the more useful claim because it says when to expect the problem.

**(e) The horizon-resolved shortcut probe can manufacture a penumbra in principle, and on this corpus it
does not.** The positive count *necessarily* falls with horizon, 1,061 at $\Delta = 1$ against 508 at 10,
so a high-capacity probe has more room to overfit where the sample is smallest. The concern is sound a
priori. **The measurement is not: it was V1d's, and V1d's numbers were void.** They came from the panel V0
retracted, and its artefact carries neither an invocation nor a corpus fingerprint, which is how it was
identified (D-45). Recomputed with matched negatives the decay runs 0.2160, 0.2596, 0.2686 across 30, 100
and 300 trees, a ratio of **1.24** rather than a near tripling, and the **linear** probe decays **0.2597**,
between the two extremes. A decay present at every capacity including linear is not a capacity artefact.
**Status: sound in principle, not demonstrated here.** What survives is the rule that produced the
correction, report a linear probe beside any non-linear one, which settled the question against the
mechanism it was introduced to support.

**(f) A decaying shortcut curve is not evidence of anything.** Predicting ten years ahead is harder
than predicting one year ahead with no leakage at all, so decay is the null. The test that separates
them is the $r^\star$-exclusion contrast horizon by horizon — D2's horizon-resolved analogue, absent
from the manifesto's U2. Measured: anchors alone sit at 0.54–0.57 and decay 0.028 while $r^\star$
adds 0.200 at $\Delta = 1$ falling to 0.095 at $\Delta = 10$. **Proof: V2.**

**(g) "Shortcut reliance" is not a property of a model.** It depends on how saturated the leaking
relation is in the regime the model is evaluated in, and saturation drifts with the institutional
population: co-membership density is 0.970 in 1948–63 against 0.995 in 1965–2014, with 116
organisations per year against 273. The most shortcut-reliant models are therefore *more* robust to a
shift toward the earlier regime, which is the reverse of the assumed mechanism. CLIQUEBAIT's H4 and
this programme's P6 both treat a model-by-regime interaction as a model attribute, which is why
neither could be made to work. **Proof: V7.**

**(h) The band cannot subtract homophily, because every relation with homophily decays the same way.**
§5.4 sets the band from relations declared not to carry the label. Measured with matched negatives:
`trades`, which cannot record an IGO accession, contrasts 0.264 at $\Delta = 0$ and 0.146 at
$\Delta = 8$, retaining 55 % where $r^\star$ retains 48 %. `votes_with` retains 61 %. The only flat
relation is `conflicts_with`, at 0.004 everywhere, and it is the only one with no homophily content.
$r^\star$ minus the strongest anchor falls below 0.01 at $\Delta = 5$, so the pre-specified rule
returns $\Delta^\star_{\text{lo}} \approx 5$ against a truth of 0 — the residual is the *difference
in homophily strength* between co-membership and trade, not a trace. This is a third and deeper reason
for the same non-identification: V8's was noise, V10's saturation, and this one no amount of data or
thresholding touches. **Proof: V12 — and V13 narrows it to this corpus.** On the protein benchmark
$r^\star$ contrasts 0.4240 against a strongest anchor of 0.0165, residual +0.4075, and the anchors are
flat. The mechanism needs the anchors to share the focal relation's generative structure: in IR, trade,
UNGA voting and co-membership all express which states are close to which, so subtracting one from another
removes almost nothing. mRNA co-expression and gene fusion bear no such relation to a curator's complex
boundaries. (h) is about the IR corpus.

**(i) The trace confound rises with the horizon, and it rises toward confirmation.** A state that left
and rejoined is on the record at long horizons for a reason that is not anticipation, and reaching
further back is likelier to land inside an earlier spell: presence among recurrent accessions runs
0.185 at $\Delta = 1$ to 0.330 at $\Delta = 8$ against 0.0009 among first-time ones. Unconditioned,
the `declared_resolution` stratum shows a textbook four-year decay, 0.349 → 0.249 → 0.118 → 0.045; it
is almost entirely this, since that stratum's recurrence rate is 30.7 % against 6.2 %. Any horizon
statistic must be computed conditional on first entry, which the manifesto does not say. **Proof: V12.**

**(j) A diagnostic with a known answer finds coding defects that validation cannot.** Focal isolation
asks *is the member on the record before it joined?*, whose answer is known in advance, and at the
first corpus-wide attempt it located ATOP's phase structure: 221 of 481 alliance accessions were
founders of multi-phase treaties, 45.9 % against a measured presence of 0.458. The defect had survived
a validation suite, two independent count audits and a consistency checker, all of which check
internal agreement rather than agreement with a known answer. **Proof: V11.**

### 2.1 One thing that works, and it is the only positive result in the programme

Ten failure modes need a counterweight, and until the second domain there was none: every verdict had
found something that does not work.

§5.4 asserts that **no statistic computed from the graph can separate leakage from legitimate signal** — a
relation that genuinely informs the labels and one generated from them both make positives denser than
negatives — so the verdict requires reading the coding rules, and the automated part is triage. That is an
assertion about method, and it had never been tested prospectively: on LEDGER the provenance reading and
the statistics were developed together, which is exactly the circumstance in which a discipline cannot
prove itself.

The protein benchmark supplied a clean test. STRING has ten channels; before running anything, each was
classified in writing from what it records. `database` imports CORUM and ComplexPortal — the label source —
so it is $r^\star$. `textmining` reads papers that describe complexes and `experiments` covers
co-immunoprecipitation, which detects them, so both were declared **contaminated and ineligible as
anchors**. The remaining five were declared anchors.

The statistic then ranked those three **first, second and third** on clique contrast — 0.4579, 0.4240,
0.3075 — against every anchor at ≤ 0.0165, with `textmining` scoring **above $r^\star$ itself**. Reading
the coding rules identified all three leaking channels, in advance, with no false positives among five
anchors. **Proof: V13.**

This is worth stating as prominently as the failures. The paper's argument is that a leakage diagnostic
built without provenance discipline will report homophily as leakage and miss penumbras it should see; the
complement of that argument is that the discipline itself pays, and this is the evidence.

## 3. What the domain application shows

Secondary to §2, and that ordering is the paper's argument rather than a concession.

**Termination is a real competing-risks problem and pooling it is wrong.** 152 events over 535
coalitions: 83 dissolution, 30 replaced, 20 absorbed, 19 whose cause ATOP cannot state and which
enter through the likelihood's cause-unknown branch. **Two** covariates reverse sign between
dissolution and supersession — internal cohesion and duration dependence — where P5 asked for one, and
a pooled model would have averaged both to nothing. Old coalitions fade; young ones are replaced or
merged. **P5 holds.**

**Termination is harder than accession.** T2's any-cause AUC is 0.614 against T1's pooled 0.80–0.92.
**P4 holds** on the comparable metric, with the within-coalition figure stated so the choice is
visible.

**Relational structure answers a different question from node covariates.** Densities beat covariates
by +0.010 pooled and +0.039 within-coalition — four times more once the coalition is held fixed.
Covariates say which coalitions grow; relations say which state, for this coalition. A single metric
hides which question each rung answers.

**A temporal encoder earns its place, and the prediction about it does not.** Rung 7 beats the
heterogeneous encoder in 42 of 48 cells and beats a **parameter-matched** control by **+0.0214**, about
fifteen standard errors, where doubling the control's parameters buys +0.0014 and is non-monotone in
width. But the graph's contribution is *largest at $\Delta = 1$* and erodes with distance — +0.0251 at
$\Delta = 1$ against +0.0228 at 10 for rung 7, and +0.0188 against +0.0130 for rung 6 — the reverse of
P7's rationale. §7 committed in advance to reporting a negative architectural result if the temporal
encoder failed. It did not fail; the prediction about it did.

Two things about *rung 6* rather than rung 7, both of which took four seeds to see. Its
parameter-matched margin is +0.0121 at about 2.6 standard errors, and **at two seeds it read as +0.0009**
— rung 6 has the widest seed variance in the ladder, sd 0.0065 against rung 7's 0.0019, so it is the one
rung whose margin two draws cannot resolve. "The relational encoder does not survive parameter matching"
is the sharper sentence and it was the underpowered one (D-41). And rung 5's failure is milder than first
reported: −0.0009 over 48 cells, beating the graph-free control in exactly 24 of them, is
**indistinguishable from an MLP** rather than worse than one. §7's rule turns on beating the rung below,
so rung 5 is still out of the headline, but on the correct ground.

**Calibration, which the prior programme left qualitative.** Rung 3's calibration slope averages 0.82
and never exceeds 1.0: systematically overconfident by about 18 % on the logit scale. §9.3 asked for
a number instead of a caveat.

## 4. The predictions, scored

| | verdict |
|---|---|
| P1 penumbra wider than a year | **falsified on the source-dating channel** — $\beta = 0$ for 94 % of the corpus, $\leq 1$ everywhere; **ill-posed** on the anticipation channel, where the estimand is not separable from homophily (V12) |
| P2 penumbra bounded | **not identified** — flat-curve clause not met, decay is not diagnostic, and the upper bound is unreachable by construction |
| P3 T1 discrimination 0.70–0.85 | **not cleanly decided** — its horizon does not exist, and it does not say which discrimination |
| P4 termination harder | **holds** |
| P5 competing risks not decomposable | **holds**, with two reversals rather than one |
| P6 shortcut reliance predicts fragility | **falsified**, and the association runs backwards |
| P7 graph earns its keep at long horizons | **falsified**, and the mechanism runs backwards |

Two hold, three are falsified — two with reversed mechanisms and one on the channel where it could be
measured at all — one is ill-posed and two are non-identified. The prior programme
falsified one of five and overrode three of four diagnostics; this is the same rate.

One verdict was **withdrawn** after publication inside this repository (V0). Its replacement reversed
its conclusion. The retraction was written before the corrected numbers existed, and the defect —
negatives drawn across coalition-years rather than within them, giving positive groups a mean size of
66 against 18 — was caught by the *sign* of a statistic that had no business being negative, not by
review and not by the validation suite.

## 5. What this means for the paper

**The framing is the instrument, and §11 anticipated needing it to be.** "The contribution is the
instrument, not the application" was written as a mitigation against the single-domain risk. It is now
the load-bearing claim, and §2's ten failure modes are its body. The domain application is where
each failure was found, not what the paper is about.

**The synthetic component has to carry more than planned, and after D-34 it carries the whole of one
claim.** §11 said that without it "this is an IR paper", and that is now more than doubly true. The
calibration of $\Delta^\star$ against a $\beta$ the *generator* sets — 6 of 6 settings, C18 — is the
**only** evidence that the estimator recovers a known width, because V10's real-data step table turned
out to be entailed by its own construction rather than measured. DESTA's coded gap licenses the other
claim, that the specified diagnostic fails in practice: 0.102 against 1.000 on the same events. Two
ground-truth arguments doing two different jobs, neither about international relations, and neither
substitutable for the other.

**The honest risk.** A paper whose headline is "the diagnostic we defined cannot measure the quantity
we defined" is harder to place than one that measures a new quantity. It needs the negative results to
be sharp, general and constructive. §2(a)–(j) are sharp and general; (a) is constructive because it
names the missing operation and ships it, and (i) and (j) because each states the correction it
implies — condition the trace on first entry, and prefer diagnostics whose answer is known in advance.
That is the strongest available position and it is not the position the manifesto expected to be in.

**Venue.** §12's read needs one correction. The International Journal of Forecasting remains a good
fit — an evaluation-protocol contribution with negative results about a forecasting diagnostic is
squarely what it publishes. But the paper is now closer to a **measurement-validity** paper than a
forecasting-benchmark paper, which makes NeurIPS Datasets & Benchmarks and TMLR stronger than §12
judged them: the D4→D2 ordering result and the provenance-set finding were what that track rewarded
for CLIQUEBAIT, and "here is a diagnostic, here is ground truth, here is the width of its blind spot"
is the same shape. Political Analysis and JPR are weaker than §12 allows, because the IR content did
not grow — T2's 150 events and T1's ladder are competent and secondary.

## 6. What remains

Blocked, and both stated rather than worked around:

1. **ATOP's codebook is unreachable.** Its `termmode`/`termcaus` cannot be interpreted, so T2's
   competing risks rest on COW IGO alone. Its *dating* convention is now partly settled without the
   codebook: focal isolation on the corrected corpus gives alliance accessions 1.000 at $\Delta = 0$
   and **0.000 at every $\Delta \geq 1$** (V12), so `yrent` and the accession date agree exactly. That
   is a weaker statement than it looks, and the limit is worth naming because it generalises: focal
   isolation can only detect back-dating **relative to a second date in the same source**. ATOP and COW
   IGO record one date each, so their $\beta = 0$ is entailed by the source's structure rather than
   measured. DESTA records two, which is why it is the only real-data ground truth the programme has.
   What would settle P1 for alliances remains a source coding both signature and force dates.
2. **The 1964 `votes_with` hole** is probably the nineteenth General Assembly session taking no
   recorded votes, and that is unverified against the ideal-point release's own documentation.

Unbuilt, and deliberately:

3. **T3**, de novo formation. §4 labels it exploratory and C2 records that its stated mitigation does
   not remove its stated bias, since the candidate generator reads a graph that contains the
   back-dated edges. The pre-specification for building it is written; the build is not.
4. **The `same_instrument` list**, hand-verified from the 192 membership-overlap candidates. Until it
   exists, no statistic pooling alliance and organisation entities reports its double-count exposure
   from anything but the candidate count.
5. **A left-truncation audit** and **observer-coverage verification**, both on LEDGER.md's open list.

Worth doing next, in order of what it would change:

- ~~**Re-run U1 with focal isolation across the corpus.**~~ **Done, 2026-08-04**, and it moved two
  things rather than one: it falsified P1 on the channel where P1 is measurable, and it found a corpus
  defect on the way (V11, V12, `scripts/run_u1_isolation.py`). It did not move P1's anticipation
  channel, and §2(h) is why nothing will by a statistic of that form.
- ~~**A second domain for the instrument findings.**~~ **Done 2026-08-04, and it broke one claim.** On
  CLIQUEBAIT's protein benchmark — 2,540 complexes, median size 3 against LEDGER's 66 — (c) generalises
  exactly, (b) is confirmed in scope, **(d) is falsified** and restated as a property of corpora whose
  group size correlates with a rare entity type, and (h) narrows to the IR corpus. It also produced the
  programme's first positive methodological result (§2.1). V13, D-43.

---

## 7. The audit that found the most, and it was not about penumbras

This is the part of the programme least tied to its subject, and on reflection the most transferable.

A results file with nothing attached to it cannot be audited, and **an unauditable number in a document
reads exactly like an audited one**. Three verdicts turned out to rest on JSON that no code path
regenerated — V11's defect quantification, V6's T2 tables, V10's focal-isolation evidence, the last of
them this paper's capstone. Writing the script that should have produced each one found a further defect
every time:

| closing the gap on | found | recorded |
|---|---|---|
| V11's numbers | a **third** instance of ATOP's phase-row confusion, this time adding 298 redundant membership rows, 596 standing in duplicate pairs, and inflating 162 coalition-years' size by up to 2× | D-32 |
| | and, before that, 8 of 80 alliance entities were bilateral treaties admitted by a phase-**row** count | D-31 |
| V6's T2 tables | a mislabelled coefficient key still live in the artefact a day after the document was fixed, and a reversal detector scanning the four covariates — which drops `log_duration`, **one of the two reversals P5 is scored on** | D-33 |
| V10's evidence | the capstone's headline step table is **entailed by construction**, not measured, and its negative control's $\beta = 0$ is entailed by the source coding one date | D-34 |
| the corpus document's open list | left truncation **declared, tested, and never wired**: 183 of 528 T2 entities and 58.4 % of T1's positive dyads on the wrong clock | D-36, D-37 |
| P7's crash | three readers resolving relations by **glob** over a directory two scripts write to — one crash, one silent set of leaking features, one wasted read | D-38, D-39 |
| the risk-set cache | keyed on the regime, not the corpus, and deleted by hand before each of four rebuilds | D-40 |
| the calibration count | a `--betas` default omitting 4, so the script said "5 of 5" where both documents said six — and a checker entry that read *density invariance* and printed the string "6 of 6" | D-35 |
| V9's parameter-matched margin | two seeds put rung 6's edge at +0.0009, which was noise; four put it at +0.0121 | D-41 |

**Nine defects from one audit, and the audit was bookkeeping.** Not one was found by the validation suite,
the two independent count audits, or the consistency checker — all of which test whether the pipeline
agrees with **itself**. What found them was asking questions with externally checkable answers: *what
command produced this file*, *what is this cache derived from*, *does anything actually call this*, *how
much does this number move between seeds*.

The general fix is not a fifth audit but a property of the artefact: every results file now records the
command that wrote it and a three-integer corpus fingerprint, and the consistency checker **requires**
it, so a new ad-hoc artefact fails rather than waiting in `results/` to be cited (D-35). No timestamp —
that changes on every rerun and turns a byte-identical result into a diff. The corpus fingerprint is what
actually disambiguates two runs of the same command, and this corpus went through four versions in a
single working day.

Two things worth keeping from how it went wrong. The first version of the attribution check tested
whether a filename appeared anywhere under `scripts/`, and one file passed because a **comment** I had
just written mentioned the name: a check satisfiable by prose is not a check. And the mechanical rewrite
across sixteen files left an unbalanced parenthesis in each, which is the ordinary failure of regex
surgery and is why every file was re-parsed before anything was run.

### 7.1 A capability that was built, tested, and never used

Working through the corpus document's own open list found the same shape from the other direction.
`PeriodPanel.entry` is documented as "the last period BEFORE observation begins", `hazard.py` implements
left truncation, and **the test suite carries cases named after it** — "2 causes, exact, truncated", "3
causes, interval, truncated" — agreeing with the closed form to $10^{-13}$, beside a separate check that
immortal time is refused. §9.1 names left truncation; D-03 recorded that it "binds hard".

Every caller passed zeros. T2 set duration to 1 at the regime start for all 528 coalitions, of which
**183 predate it** with a median true age of 13 years and a maximum of 150, carrying 45.7 % of the
coalition-years and 39.1 % of the terminations — and `log_duration` is one of the two cross-cause sign
reversals P5 is scored on (D-36). T1's clock was `cumcount() + 1`, with 19.9 % of dyads truncated and
**58.4 % of positive dyads** in coalitions founded before the regime (D-37).

**A test that exercises a capability proves the capability exists. It says nothing about whether anything
uses it**, and no suite here was positioned to notice the difference. Both verdicts survived the fix —
P5's reversals hold at +0.095/−0.143, and the ladder's rung ordering is invariant to which clock is used —
which is the outcome that makes the finding reportable rather than embarrassing: the concern was declared,
the machinery was correct, and the wiring was absent.

### 7.2 A shared directory read by a glob is an implicit contract

`data/graph/` is written by two scripts and read by four. Three of the readers resolved their relations
with `glob("edges_*.parquet")` rather than from the declared list, so when V10's DESTA validation wrote
`edges_pta_signature.parquet` and `edges_pta_force.parquet` into that directory, all three silently
changed behaviour. One pattern, three symptoms:

| reader | symptom |
|---|---|
| `neural.py` | an unmapped relation cast from NaN to int64 → **device-side CUDA assert** inside RGCN, two indirections and a device boundary from its cause (D-38) |
| `run_u2.py` | **four extra features** in the shortcut probe — 24 where V1 and V2 were measured on 20 — and `pta_signature` is *deliberately back-dated*, so the probe measuring leakage was handed a leaking feature (D-39) |
| `t2.py` | the extra edges loaded and then filtered out downstream: wasted, harmless, and harmless only by accident |

The crash is the benign case. The silent one produced plausible numbers in the direction that confirms
P2's premise, and the third was safe for a reason — "something downstream filters it" — that had already
stopped being true one file over. Relations are now read by name, with a `FileNotFoundError` when a
declared relation has no file, which is the failure a missing relation should produce.

### 7.3 What the nine have in common, and it is not carelessness

Each defect is a place where something was **re-derived instead of declared**, or **declared instead of
checked**:

| | re-derived where it should have been declared | declared where it should have been checked |
|---|---|---|
| corpus | treaty size from phase rows, three times (D-28, D-31, D-32) | `MIN_MEMBERS` trusted from COW's documentation until the data was asked — three organisations fail it |
| relations | `glob("edges_*")` instead of the declared list (D-38, D-39) | — |
| caches | risk set keyed on the regime, not its inputs (D-40) | — |
| duration | "dyad time" and "duration" left undefined against founding (D-36, D-37) | `PeriodPanel.entry` implemented, tested under a name containing *truncated*, and wired to zeros |
| artefacts | provenance reconstructed from filenames and comments (D-35) | "6 of 6" verified by reading an unrelated field |
| estimates | a margin taken from two seeds (D-41) | — |

The pattern is not inattention; every one of these passed a review at the time it was written, and the
programme already had a validation suite, two independent count audits and a document-to-artefact
consistency checker. What those instruments share is that they test **internal agreement**. A corpus can
agree with itself while counting rows as members; a document can agree with a results file that no script
produces; a test can agree with a closed form for a code path nothing calls. Each of the nine was found by
a question with an **external** answer, and the four that generalise are worth stating as a checklist:

1. *What command produced this artefact?* — and it must be recorded, not reconstructable.
2. *What is this derived thing derived from?* — a cache or panel must carry its inputs' identity.
3. *Does anything actually call this?* — a tested capability is not a used one.
4. *How much does this number move when nothing substantive changes?* — seeds, folds, resamples.

None of the four is about penumbras, coalitions, or graphs.

## 8. Where this leaves the programme

Thirteen measurement rounds, thirteen verdicts, one withdrawn and reversed, one corrected. The instrument
findings are **ten** (§2 a–j) against the manifesto's expectation of none, and three of them — (h), (i),
(j) — came from the single operation the manifesto omitted, which is the strongest available argument that
the omission was structural rather than incidental. One of the ten, (d), was **falsified by the programme's
own second domain** and restated; two more, (b) and (h), had their scope fixed by it; and (c) came back
generalised. A set of claims that survives its own adversarial test unchanged is a set that was not tested.

The programme's honest summary in one sentence: **it defined a quantity, built the instrument its own
definition implies, and established on a corpus with externally coded ground truth that the instrument
measures homophily where the definition names traces — then shipped the operation that separates them.**
The domain results stand and are secondary. Nothing in §2 depends on international relations, which is
the property that makes it a methods contribution rather than an IR one.

One claim was **weakened** on 2026-08-04 and the weakening is load-bearing. V10 read as two ground-truth
corpora, one with an exact penumbra and one without, with the same instrument recovering both. Only the
DESTA side could have come out either way: COW IGO codes one date per membership, so a zero residual
there is entailed rather than found. The surviving argument is narrower and still sufficient — one corpus
where the width is coded, on which the specified diagnostic returns 0.102 against 1.000 — plus C18's
synthetic calibration, which is what actually shows the estimator recovers a known $\beta$. Stating that
separation removes a tautology the capstone was resting part of its weight on.

**What survived the corpus corrections, and it is nearly everything.** The corpus was rebuilt four times
in one day and every verdict but V1–V2 was re-measured on the result. P4 and P5 hold with both of P5's
sign reversals intact. V5's ladder is unchanged and its rung ordering is invariant to which duration clock
is used. V7 is sharpened. V9's ordering is restored at four seeds. V8 is *stronger*: the pre-specified rule
now returns an inverted interval, $\Delta^\star_{\text{lo}} = 2$ above $\Delta^\star_{\text{hi}} = 1$,
which is the empty set and needs no argument about power. Two claims were withdrawn — V10's
"two ground-truth corpora" framing and one by-product observation of V11's — and one, V7's, kept its
verdict while changing which of P6's clauses fires. A programme that could not survive its own corrections
would be a different result; this one mostly could, and the places it could not are marked.

What would strengthen it now, in order: **a source with two coded dates for alliances**, the only thing
that would let P1's anticipation channel be measured at all rather than declared ill-posed; **T3**, whose
pre-specification is written and whose stated mitigation C2 already records as insufficient; and the
**`same_instrument` list** hand-verified from the 192 membership-overlap candidates, without which no
statistic pooling alliance and organisation entities can report its double-count exposure from anything but
the candidate count. The second domain and the U1/U2 re-run are done.
