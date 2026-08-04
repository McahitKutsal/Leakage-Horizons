# What this programme found

Written 2026-08-04, after the measurement phase. `PENUMBRA-OUTCOMES.md` records verdicts clause by
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

The proof is V10 and it is not an inference. DESTA codes an agreement's signature year and its
entry-into-force year, so the back-dating width is printed in the source. Measured on the focal
agreement alone, the trace is present for exactly the horizons inside the coded gap and absent
outside it, at every width, contrast **1.000**. Measured the way the manifesto specifies — a density
over the whole relation — the same corpus returns **0.102**. The penumbra is there, its width is
known, and the instrument recovers a tenth of it.

## 2. The contribution: seven ways a leakage diagnostic fails, each with its proof

None of these is in the manifesto. Together they are the paper.

**(a) The diagnostic needs an operation the manifesto does not specify.** §5.3 prescribes focal-group
*exclusion*, to stop the focal group's own edges standing in for the label. Detecting the shadow
requires the *isolation* of those same edges, since that is the only place back-dating lives. Two
operations, opposite purposes, one of them absent. UMBRA now ships both (D-27). **Proof: V10.**

**(b) A saturating relation hides the shadow, and coalition relations saturate.** IGO co-membership
has density 0.995 — with 491 organisations over 168 states almost every pair shares something. The
focal contribution is 6.8 % of the relation. Thresholding does not fix it, and is non-monotone in
density; excluding near-universal bodies does not fix it either, leaving 0.706 after dropping every
organisation that ever spans half the state system. **Proof: C15, V10.**

**(c) The exact-clique statistic is structurally zero on large groups.** A 90-member coalition has
4,005 dyads and a clique needs all of them, so the contrast is 0.20–0.25 below twenty members and
identically **0.000** above eighty — where 36 % of the corpus's positives live. CLIQUEBAIT chose this
statistic because it survived all three settings it was tested in; none had this size distribution,
the protein benchmark's median complex being 3 against LEDGER's mean positive stratum of 66.
**Proof: V3.**

**(d) There is no subpopulation where both problems go away.** Large groups kill the statistic by
arithmetic; small groups come with small samples. On the 66 alliance entities, median membership 4,
the statistic has power in principle and the standard error equals the effect — separating a contrast
of 0.03 from a band of 0.01 needs about 600 positives per horizon against the 111–180 available.
Group size and sample size trade off against each other in any curated coalition corpus, and this
statistic needs both favourable at once. **Proof: V8.**

**(e) The horizon-resolved shortcut probe can manufacture a penumbra.** The positive count
*necessarily* falls with horizon, so a high-capacity probe overfits more at long horizons and yields
a decaying curve whatever the leakage is. Measured: in a small regime the apparent decay nearly
triples as probe capacity triples (0.058 → 0.143) while the linear probe holds at 0.041. The
confound is in the shape of the diagnostic and runs in the direction that confirms the hypothesis.
CLIQUEBAIT's rule to use a non-linear D1 probe, carried into a horizon setting without that caveat,
is an instruction to build a penumbra detector that finds penumbras in small corpora. **Proof: V1d.**

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
heterogeneous encoder in 12 of 12 cells and beats a **parameter-matched** control by +0.0245, where
doubling the control's parameters buys 0.0009. But the graph's contribution is *largest at
$\Delta = 1$* and erodes with distance — the reverse of P7's rationale. §7 committed in advance to
reporting a negative architectural result if the temporal encoder failed. It did not fail; the
prediction about it did.

**Calibration, which the prior programme left qualitative.** Rung 3's calibration slope averages 0.82
and never exceeds 1.0: systematically overconfident by about 18 % on the logit scale. §9.3 asked for
a number instead of a caveat.

## 4. The predictions, scored

| | verdict |
|---|---|
| P1 penumbra wider than a year | **not identified** — and V10 proves the instrument, not the world, is why |
| P2 penumbra bounded | **not identified** — flat-curve clause not met, but decay is not diagnostic |
| P3 T1 discrimination 0.70–0.85 | **not cleanly decided** — its horizon does not exist, and it does not say which discrimination |
| P4 termination harder | **holds** |
| P5 competing risks not decomposable | **holds**, with two reversals rather than one |
| P6 shortcut reliance predicts fragility | **falsified**, and the association runs backwards |
| P7 graph earns its keep at long horizons | **falsified**, and the mechanism runs backwards |

Two hold, two are falsified with reversed mechanisms, three are non-identified. The prior programme
falsified one of five and overrode three of four diagnostics; this is the same rate.

One verdict was **withdrawn** after publication inside this repository (V0). Its replacement reversed
its conclusion. The retraction was written before the corrected numbers existed, and the defect —
negatives drawn across coalition-years rather than within them, giving positive groups a mean size of
66 against 18 — was caught by the *sign* of a statistic that had no business being negative, not by
review and not by the validation suite.

## 5. What this means for the paper

**The framing is the instrument, and §11 anticipated needing it to be.** "The contribution is the
instrument, not the application" was written as a mitigation against the single-domain risk. It is now
the load-bearing claim, and §2's seven failure modes are its body. The domain application is where
each failure was found, not what the paper is about.

**The synthetic component has to carry more than planned.** §11 said that without it "this is an IR
paper", and that is now doubly true: the calibration of $\Delta^\star$ against a known $\beta$ is what
licenses the claim that the instrument works in principle, and DESTA's coded gap is what licenses the
claim that it fails in practice. Both are ground-truth arguments and neither is about international
relations.

**The honest risk.** A paper whose headline is "the diagnostic we defined cannot measure the quantity
we defined" is harder to place than one that measures a new quantity. It needs the negative results to
be sharp, general and constructive. §2(a)–(g) are sharp and general; (a) is constructive because it
names the missing operation and ships it. That is the strongest available position and it is not the
position the manifesto expected to be in.

**Venue.** §12's read needs one correction. The International Journal of Forecasting remains a good
fit — an evaluation-protocol contribution with negative results about a forecasting diagnostic is
squarely what it publishes. But the paper is now closer to a **measurement-validity** paper than a
forecasting-benchmark paper, which makes NeurIPS Datasets & Benchmarks and TMLR stronger than §12
judged them: the D4→D2 ordering result and the provenance-set finding were what that track rewarded
for CLIQUEBAIT, and "here is a diagnostic, here is ground truth, here is the width of its blind spot"
is the same shape. Political Analysis and JPR are weaker than §12 allows, because the IR content did
not grow — T2's 152 events and T1's ladder are competent and secondary.

## 6. What remains

Blocked, and both stated rather than worked around:

1. **ATOP's codebook is unreachable.** Its `termmode`/`termcaus` cannot be interpreted, so T2's
   competing risks rest on COW IGO alone; and its dating convention is unverified, so P1's own
   scope — alliance-sourced events — cannot be computed. What would settle P1 is now precisely
   specifiable: a source coding both signature and force dates for alliances, as DESTA does for
   trade.
2. **The 1964 `votes_with` hole** is probably the nineteenth General Assembly session taking no
   recorded votes, and that is unverified against the ideal-point release's own documentation.

Unbuilt, and deliberately:

3. **T3**, de novo formation. §4 labels it exploratory and C2 records that its stated mitigation does
   not remove its stated bias, since the candidate generator reads a graph that contains the
   back-dated edges. The pre-specification for building it is written; the build is not.
4. **The `same_instrument` list**, hand-verified from the 178 membership-overlap candidates. Until it
   exists, no statistic pooling alliance and organisation entities reports its double-count exposure
   from anything but the candidate count.
5. **A left-truncation audit** and **observer-coverage verification**, both on LEDGER.md's open list.

Worth doing next, in order of what it would change:

- **Re-run U1 with focal isolation across the corpus.** The operation now exists; V10 used it on
  DESTA and COW IGO but the full $\Delta^\star$ curve under isolation has not been computed for every
  entity. This is the one remaining measurement that could move a non-identification.
- **A second domain for the instrument findings.** §2(b)–(d) are claims about relations that saturate
  and groups that are large, and both are properties any curated group corpus can have. CLIQUEBAIT's
  protein benchmark has the opposite size distribution — median complex size 3 — which makes it the
  natural test of whether (c) and (d) are general or particular.
