# Manifesto → outcomes

`penumbra-manifesto.md` is the pre-registration. It was amended once, on 2026-08-02, before
any datum was fetched and before any model existed; the amendment is recorded in its own §0
and the text as first written is commit `410121f`. **From that point it is fixed.** Editing a
prediction after seeing the data would destroy the one property that makes the programme
falsifiable, and the reconciliation belongs here instead.

This file plays the role `MANIFESTO-OUTCOMES.md` plays for CLIQUEBAIT: clause by clause, what
held, what did not, and where the manifesto's own instructions have to be overridden. The
prior programme falsified one of its five hypotheses and overrode three of its four
diagnostics. That is the expected rate, not a failure mode.

**Status, 2026-08-03, end of the first working period.** Corpus built and validated, observation
graph built and coverage audited, provenance declared, $\Delta^\star_{\text{lo}}$ calibrated on
synthetics against a known back-dating horizon, U1 and U2 run on real data, and the
interval-censored competing-risks hazard implemented, verified against closed forms, and fitted for
both T1 and T2.

**Six of seven predictions have been touched.** P4 and P5 **hold**. P6 is **falsified**, and its
association runs backwards for a reason that can be named (V7). P1 and P2 are **non-identified** — by
the instrument, not by the world. P3 cannot be read cleanly, because the horizon it names does not
exist and it does not say which discrimination it means. Only **P7** is untouched; it needs ladder
rungs 4–7, which are not built.

One verdict was **withdrawn** (V0) and its replacement reversed its conclusion. That is recorded at
the top of the verdicts rather than buried, because the retraction is the most informative thing in
this file.

Three kinds of entry live below and the difference between them is the point. **C1–C6** were
written with nothing measured. **C7–C18** are measurements taken before the thing they bear on was
computed. **V-entries** are verdicts on §8's predictions. Anything moving from the second category
to the third has to cite the measurement that did it.

---

## §8 — falsifiable predictions

| | prediction | test statistic | verdict |
|---|---|---|---|
| **P1** | penumbra wider than one year, $\Delta^\star_{\text{lo}} \geq 2$ | U1 clique contrast, lower bound | **not decided** — non-identified on both $r^\star$: flat and above band on co-membership (V2), noise-limited on alliance edges (V8) |
| **P2** | penumbra bounded, $\Delta^\star_{\text{hi}} \leq 6$, shortcut curve decays | U1 upper bound + U2 | **not decided** (V2, V8). Flat-curve clause not met — curve decays 0.133 — but the decay is not diagnostic, and $\Delta^\star_{\text{hi}}$ is unreachable on co-membership and noise-limited on alliance edges |
| **P3** | T1 discrimination 0.70–0.85 at $\Delta = \Delta^\star$ | T1 rolling-origin AUC | **not cleanly decided** (V5). Not falsified — nothing near 0.95. Pooled 0.80–0.92, within-coalition 0.57–0.68, and $\Delta^\star$ non-identified |
| **P4** | termination harder than accession | T2 cause-specific concordance vs T1 | **HOLDS** on pooled-vs-pooled (V6): T2 0.614 against T1 0.80-0.92 |
| **P5** | competing risks not decomposable; a covariate reverses sign | cause-specific vs pooled hazards | **HOLDS** (V6): two covariates reverse -- cohesion and duration |
| **P6** | shortcut reliance predicts fragility under temporal shift (CLIQUEBAIT H4) | ten models across the 1964 break | **FALSIFIED** (V7): rho = -0.529, p = 0.116, and the association runs *backwards* -- explained by saturation drifting in time |
| **P7** | graph earns its keep at long horizons or not at all | ladder rung 6/7 minus rung 4, by $\Delta$ | not yet measured |

## Deliverables (§10)

| | status |
|---|---|
| $\Delta^\star$ definition with signature-to-force external validation | defined (§5.1); **calibrated on synthetics**, $\Delta^\star_{\text{lo}}$ recovering $\beta+1$ in 6 of 6 (C18); not yet estimated on real data. External anchor measured (C7) |
| UMBRA — lagged diagnostic suite U1–U3 | **U1, U2 and U3 all built and run.** U1 on real data (V2), U2 with the capacity sweep (V2, V1d), U3 focal exclusion run on T2 and found to be a no-op (V6) |
| LEDGER — event corpus | **built and validated**: 573 entities, 10,556 events, four dating strata. `agreement` entities deferred (LEDGER.md §1.1) |
| Three tasks with declared risk sets, origin times, censoring rules | **declared before construction** (LEDGER.md §4). T1 and T2 built and fitted; **T3 not started** |
| Cause-specific hazard results for termination | **done** (V6): 152 events, P5 holds with two sign reversals, ATOP's 19 uncoded entering through the cause-unknown branch |
| Architectural ladder, each rung earning its place | **rungs 1–3 done** (V5), each beating the one below on both metrics. Rungs 4–7 need the encoders and are not built, so P7 is untouched |

---

## Concerns recorded before measurement

These were found while reading the manifesto against CLIQUEBAIT's results and against the
primary sources. They are written down **now**, with nothing measured, for the same reason the
predictions are: a caveat produced after an inconvenient number is worth much less than one
produced before. None of them changed the manifesto — the amendment was confined to §5.1's
instrument and §11's corpus decision — so each is either a pre-specification the manifesto
leaves open or a limit on how a result may be read.

**C1 — P3's anchor is not like-for-like, and the paper must not present it as a drop.**
P3 places T1 discrimination at 0.70–0.85 "against CLIQUEBAIT's corrected detection figure of
0.993". Those are different tasks over different risk sets with different class balance. The
prediction is a legitimate bet on the absolute level; the *comparison* is rhetorical and has
to be labelled as such wherever it appears. A reviewer will otherwise read a like-for-like
degradation that was never measured.

**C2 — T3's stated mitigation does not remove its stated bias.** §4 concedes that de novo
formation samples on the dependent variable and suffers immortal-time bias unless candidates
are generated identically for formed and never-formed groups, and mitigates by generating from
the graph alone with no reference to the canon. That closes one route and leaves another open:
$G_{\leq t}$ *contains the back-dated edges*, so at $\Delta < \Delta^\star$ a dense-subgraph
candidate generator is enriched for groups that are about to form, by exactly the mechanism the
programme exists to measure. Excluding $r^\star$ from the features does not touch it, because
the bias enters through the **risk set**. Pre-specification: T3 candidate generation runs on a
graph with the provenance set already excluded, and the same generator is run with and without
exclusion so the size of the effect is reported rather than assumed small.

**C3 — P7 must name which bound of $\Delta^\star$ it is tested at.** P7 compares the graph's
contribution at $\Delta \geq \Delta^\star$ against $\Delta = 1$, and $\Delta^\star$ is now an
interval. Pre-specification: **$\Delta^\star_{\text{hi}}$**, the conservative bound, so that
the long-horizon region is the one where residual leakage is least arguable. Reporting P7 at
$\Delta^\star_{\text{lo}}$ would let the effect be carried by horizons still inside the
penumbra, which is the opposite of what P7 claims.

**C4 — the cluster-bootstrap unit is ambiguous for T1 and the manifesto does not resolve it.**
§9.4 says resample coalitions. In T1 an observation is a (coalition, state, year) triple, so
repeated observations of the same **state** across many coalitions are dependent too, and in
the IGO backbone a single state contributes to hundreds of risk sets. Pre-specification:
coalition-level resampling is primary, because that is what the manifesto commits to and what
CLIQUEBAIT left as an outstanding gap; a state-level cross-check is reported alongside, and if
the two intervals disagree materially that disagreement is the finding.

**C5 — COW IGO's missing-data code is a risk-set decision, not a cleaning step.** Membership
cells carry `-9` and `-1`. Per the v3 codebook §III.A these are **`-9` missing data** and
**`-1` state not a system member** — stated here because this file had them the wrong way
round until the codebook was read, which is the same failure §5.4 exists to prevent and is
recorded rather than quietly corrected. Treating either as absence manufactures accessions out
of missing data and out of state birth; treating either as membership manufactures exits.
Pre-specification: both are out of the risk set for that organisation-year, and the exclusion
is tabulated per year, so a coverage defect in the source shows up as a shrinking denominator
rather than as events. The counts in `results/corpus_scale.json` were never affected — they
require an explicit `0 → 1` transition — but the reasoning behind them was wrong, and a right
answer reached by wrong reasoning is not reliable at the next step.

**C6 — the decolonisation cluster is a population, not an outlier.** Recorded in §11 as a
cost of the corpus decision. Concretely: a newly independent state joining many organisations
within a few years produces accession events that are neither independent nor the coalition
decision the programme models. Pre-specification: report T1 with and without the first $k$
years of each state's system membership, $k$ fixed before fitting, and treat the difference as
a reported sensitivity rather than choosing the favourable one.

---

## Verdicts

### V0 — RETRACTION. V1 and the first U1 run are withdrawn: the negatives were not the declared risk set

**Written 2026-08-03, before the corrected panel was run**, so that the retraction cannot be read
as a response to nicer numbers. Everything in V1–V1d below is struck through in effect and kept
visible; nothing is deleted, because the mistake is more instructive than the result was.

`accession_panel` drew its negatives by sampling **(entity, year) uniformly at random** and then a
state. LEDGER.md §4.1 declares the risk set as "states in the COW system at $t$ that are not full
members of $c$ at $t$" — that is, *within* a coalition-year, not across them. The consequence,
measured at $\Delta = 3$ on the primary regime:

| | mean group size | median |
|---|---|---|
| positives | **66.4** | 51 |
| negatives (as drawn) | **18.2** | 11 |

A 3.7× gap, and structural rather than accidental: accessions happen in large active organisations,
while a uniformly drawn coalition-year is a small one. A group of 11 dyads-few members is far more
likely to be a clique than a group of 51, so:

* **U1's clique contrast came out negative** — −0.12 at $k = 25$, −0.24 at $k = 17$, −0.12 for
  `trades` — meaning negatives were cliques *more often* than positives. The statistic was
  measuring group size, not leakage. The sign is what gave it away; the verdict it produced
  ($\Delta^\star_{\text{lo}} = 1$, P1 falsified) is void.
* **U2's 0.87 is not interpretable either.** `size` and `log_size` are in the feature set by the
  manifesto's own D1 specification, so with unmatched negatives the probe could separate the
  classes on "is this a big organisation that gains members" without any information about the
  candidate state at all. V1's falsification of P2's shortcut clause is withdrawn pending
  re-measurement.

**Fix.** Negatives are now drawn from the **same (entity, year)** as each positive, which holds the
group and therefore its size fixed across the classes, so $\phi$ can differ only through the
candidate state's own relationship to the members. Verified: mean group size 66.4 against 66.4.
`matched=False` is retained so the defective construction can be reproduced deliberately, since
the size confound is itself worth reporting as a trap.

**What survives and what does not.** V1a's stratum gap, V1b's null non-linear gain and V1d's
capacity result were all computed on the defective panel and their *numbers* are void. V1c —
horizon 0 being inexpressible in the T1 risk set — is a property of the risk set and stands. V1d's
*mechanism* (a shrinking positive count at long horizons lets a high-capacity probe manufacture
decay) does not depend on the panel and is expected to reproduce, but it is re-measured rather
than assumed.

**Why this was caught.** Not by review, and not by the validation suite, which checks the corpus
rather than the audit. It was caught by looking at the **sign** of a statistic that had no business
being negative, and refusing a verdict that arrived in the convenient direction. That is the only
mechanism that would have caught it, and it is worth saying so in the paper.

### V2 — the corrected measurement. No penumbra is detected, and neither P1 nor P2 is decided

Everything below is on the matched panel of V0, primary regime 1965–2014, anchors and primary level
$k = 25$ declared before the runs. Four measurements, and they only make sense together.

**(a) The shortcut curve decays, monotonically and for real.** `results/u2_matched.parquet`.

| $\Delta$ | 1 | 2 | 3 | 5 | 7 | 10 | decay |
|---|---|---|---|---|---|---|---|
| GBM 300/3 | .7658 | .7241 | .7030 | .6693 | .6479 | .6330 | **0.133** |
| GBM 30/2 | .7388 | .7040 | .6810 | .6510 | .6287 | .6109 | 0.128 |
| linear | .7423 | .7081 | .6861 | .6566 | .6442 | .6196 | 0.123 |

Monotone at every step, and **capacity-invariant** — so this is not V1d's artefact. Note what the
matched risk set cost: 0.87 at $\Delta = 1$ became **0.766**, so roughly 0.10 of the withdrawn
figure was group size.

**(b) A decaying shortcut curve is not evidence for P2, because it is also the null.** P2 reads
decay as the leak falling away and flatness as the leak surviving. But predicting ten years ahead
is harder than predicting one year ahead *with no leakage at all*, so decay is what the null
predicts too. Flatness would have been the surprise. P2's confirmation condition is therefore
not diagnostic as written, and the manifesto does not supply the test that would make it so.

**(c) The test that does: U2 with $r^\star$ excluded, horizon by horizon.** This is D2's
horizon-resolved analogue and it is not in the manifesto's U2 specification.

| $\Delta$ | anchors only | with $r^\star$ | $r^\star$'s contribution |
|---|---|---|---|
| 1 | .5657 | .7658 | **.2001** |
| 3 | .5463 | .7030 | .1567 |
| 5 | .5572 | .6693 | .1121 |
| 7 | .5377 | .6479 | .1102 |
| 10 | .5376 | .6330 | **.0954** |
| decay | **0.028** | 0.133 | halves |

Without co-membership the probe is barely above chance and nearly flat. **Essentially all the
predictive content is in $r^\star$, and its contribution halves across nine horizons.** So the
decay in (a) is not forecasting difficulty — the anchors show almost none of it — it is
specifically $r^\star$'s contribution falling away.

**(d) And that still does not identify a penumbra**, because a decaying contribution from
$r^\star$ is equally what a genuine predictor does. Co-membership in 2003 predicts a 2004 accession
better than co-membership in 1994 does, for the ordinary reason that relationships change. To call
the decay a shadow requires the traces to be administrative, and `PROVENANCE.md` §2 says they are
not: five of 495 organisations mention signature or accession dating and one explicitly refuses.
Meanwhile the statistic that *would* separate the two — exact cliqueness, CLIQUEBAIT's leakage
fingerprint — is **flat** across all ten horizons (0.0606 → 0.0545 at $k = 25$) and, per V3,
structurally blind on a third of the corpus.

**Verdicts.**

* **P1 — not decided.** $\Delta^\star_{\text{lo}}$ is never reached at $k = 25$: the clique contrast
  stays above the band (0.055–0.061 against 0.019–0.026) at every horizon without decaying. Per C18
  that is instrumental non-identification, reported as prominently as a verdict and not as support.
  Reading it as "the penumbra exceeds ten years" would be wrong: a penumbra decays, and this does
  not move.
* **P2 — not decided either, and the clause structure is the reason.** The "falsified by a flat
  curve" condition is **not met** — the curve decays 0.133, monotonically, capacity-invariantly. But
  the decay is not diagnostic per (b), and $\Delta^\star_{\text{hi}}$ is unreachable because
  $r^\star$ never loses top rank on clique contrast, exactly the structural failure C18 predicted
  from synthetics and now reproduced on real data. Non-identification, not confirmation.
* **$\phi$-alone AUC for $r^\star$ at $k = 25$ is 0.52–0.53** — barely above chance, and *below* the
  anchor band at every horizon. The relation that carries all the graded signal carries almost none
  of it in the form $\phi$ measures.

**What this is, stated plainly.** No penumbra is detected in the relation that carries $r^\star$ for
493 of 573 entities, and the instrument cannot distinguish that from a penumbra it is unable to see.
That is §5.4's limit — the automated part is triage, the verdict needs the coding rules — arrived at
empirically rather than quoted. The coding rules say there is no systematic back-dating, so the
reading that survives all four measurements is: **co-membership is a genuine, decaying predictor of
accession, not an administrative shadow.** §11's contingency for a trivially narrow penumbra is the
operative one, and the programme's weight moves to T2 and to the instrument findings.

### V3 — the exact-clique statistic is blind on large groups, and a third of the corpus contributes nothing

Clique rate at $k = 25$ by group size, horizon 3, matched panel:

| members | 2–5 | 6–10 | 11–20 | 21–40 | 41–80 | **81+** |
|---|---|---|---|---|---|---|
| positives | .487 | .451 | .449 | .105 | .021 | **.0000** |
| negatives | .291 | .202 | .244 | .059 | .011 | **.0000** |
| contrast | .196 | .249 | .205 | .047 | .010 | **.000** |
| n positives | 115 | 324 | 816 | 1044 | 1284 | **2056** |

The contrast is informative below about twenty members, an order of magnitude weaker by forty, and
**exactly zero above eighty** — where 2,056 of 5,639 positives live. **36 % of the corpus cannot
contribute to the statistic at all**, and 52 % of every positive clique comes from the 11–20 band.
The pooled 0.058 is a size-weighted average of a small-coalition subpopulation.

The mechanism is arithmetic: a clique at level $k$ requires *every* dyad to clear the threshold, and
a 90-member coalition has 4,005 dyads. The probability of all of them clearing anything is nil, so
the statistic is not weak on large groups — it is identically zero.

**This bounds the statistic CLIQUEBAIT selected.** Its `clique_contrast` was chosen as "the only
ranking statistic that survived all three settings tested", and none of those settings had this size
distribution: the protein benchmark's median complex size is **3**, and LEDGER's positive strata
average **66**. Pre-specification, forced: any clique-based contrast is reported **stratified by
group size** with the share of the corpus at zero power stated, and a pooled clique contrast over a
heterogeneous size distribution is not interpretable. For corpora like this one the graded
$\phi_r(S; k)$ and the $r^\star$-exclusion contrast of V2(c) are the instruments that work; exact
cliqueness is not.

### V8 — the manifesto's original $r^\star$, tested at last. Noise-limited, and that completes the argument

`scripts/run_u1_alliance.py` → `results/u1_alliance_primary.json`. Everything before this tested
$r^\star$ = co-membership, leaving the manifesto's **original** claim untested: §3's table names
alliance edges as the suspected $r^\star$, and CLIQUEBAIT *measured* them leaking — $\omega = 0.718$,
clique lift **590×**, $\phi$-alone AUC 0.806. That gap was mine and it is now closed.

Two structural reasons to expect this test to speak where the co-membership one could not: alliance
entities have a **median membership of 4** against the organisation majority's 51, so V3's
size-blindness does not apply; and `allies` has density **0.15** against co-membership's 0.995, so
cliqueness is discriminative rather than universal. 66 entities, 1,572 alliance-years, 336 accessions.

**The pre-specified rule returned $\Delta^\star_{\text{lo}} = 3$ and $\Delta^\star_{\text{hi}} = 10$,
so P1 would read as holding and P2 as falsified. Both readings are rejected.** The rule is not wrong;
it has no power at this sample size, and the check that shows it was run before the verdict was
accepted.

| $\Delta$ | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| clique contrast | .0319 | .0205 | .0290 | .0226 | .0303 | .0308 | .0229 | .0169 | .0194 | .0135 |
| its standard error | .0135 | .0117 | .0163 | .0153 | .0170 | .0173 | .0170 | .0151 | .0152 | .0130 |
| band | .0248 | .0203 | .0342 | .0373 | .0395 | .0324 | .0288 | .0251 | .0341 | .0446 |
| **z vs band** | +0.5 | +0.0 | −0.3 | −1.0 | −0.5 | −0.1 | −0.3 | −0.5 | −1.0 | **−2.4** |

**At no horizon is the contrast significantly above the band.** The only $|z| > 2$ is at $\Delta = 10$
and it is *negative* — the in-band direction, so not evidence of leakage. The standard error is the
same magnitude as the effect throughout, and the contrast is **not monotone**: it falls, rises, falls,
rises. $\Delta^\star_{\text{lo}} = 3$ is where two series at the noise floor happen to cross.

**The power requirement, concretely.** To separate a contrast of 0.03 from a band of 0.01 at
conventional power the standard error must be about 0.007, which needs roughly **600 positives per
horizon**. The corpus supplies **111–180**. Resolving $\Delta^\star$ on the small-group subpopulation
would take about 4.5 times the alliance accessions that exist.

**This completes the negative argument rather than adding to it, and the completion is what makes it
general.** There are two subpopulations and the instrument fails in each for the opposite reason:

| | group size | sample | why the clique contrast cannot resolve $\Delta^\star$ |
|---|---|---|---|
| organisations (493) | median 51 | 6,606 events | the statistic is **structurally zero** above 80 members; 36 % of positives contribute nothing (V3) |
| alliances (66) | median 4 | 336 events | the statistic has power in principle, but the **sample is too small** — SE ≈ effect |

**So there is no subpopulation of this corpus in which the exact-clique contrast can identify
$\Delta^\star$.** Large groups kill it by arithmetic; small groups come with small samples. That is not
a property of these data being unlucky — it is a property of the statistic, since group size and
sample size trade off against each other in any curated corpus of coalitions, and the statistic needs
both to be favourable at once.

**And the caveat stated before the run still binds.** ATOP's codebook is unreachable (PROVENANCE §4),
so `allies`'s dating convention is unverified. A null here cannot rule out that ATOP dates from entry
into force, in which case there is nothing to back-date and the absence is the source's property
rather than the world's. §5.4 says the verdict requires reading the coding rules; here they cannot be
read, and the honest consequence is that the automated part ran and the verdict stays suspended.

**P1 and P2 remain non-identified.** On the original $r^\star$ as on co-membership, and now for
reasons that are understood in both cases rather than merely observed.

### V7 — P6 is falsified, and the association runs backwards for a reason that can be named

`scripts/run_p6.py` → `results/p6.json`. P6 is CLIQUEBAIT's H4 restated, and H4 was **orphaned**
there: its motivating anomaly dissolved into relation dropout and the statistic it named did not
calibrate. §2 says this programme supplies genuine temporal shift by construction, so this is a debt
being paid rather than a new question.

Ten models spanning the reliance gradient, trained on 1965–2014 and evaluated across the 1964
coverage break. **Shortcut reliance** is the AUC a model loses when its density features are held at
their means, measured *within* the training regime so shift cannot contaminate it. **Shift fragility**
is in-regime AUC minus out-of-regime AUC.

| model | reliance | fragility |
|---|---|---|
| duration only | 0.0000 | **+0.0256** |
| node only | 0.0000 | +0.0208 |
| node + all $\phi$ | 0.0034 | +0.0195 |
| node + all $\phi$ + clique | 0.0160 | +0.0081 |
| clique only | 0.0613 | +0.0274 |
| all $\phi$ only | **0.1393** | **−0.0333** |
| all $\phi$ + clique only | **0.1721** | **−0.0347** |

**Spearman $\rho = -0.529$, $p = 0.116$** over ten models. P6's falsification condition is that
reliance and fragility are uncorrelated, and at $p = 0.116$ they are. **P6 is falsified as stated.**

**But "uncorrelated" understates it, and the understatement matters.** The reliance spread is 0.172
and the fragility spread 0.062, so this is not the immaterial case CLIQUEBAIT's H5 lesson warns
about — where a control scored $\rho = -0.887$ while moving 0.004. It is a real-magnitude association
in the **opposite direction to P6**, underpowered at ten models. The two most shortcut-reliant models
have *negative* fragility: they perform **better** out of regime than in it, 0.7369 → 0.7702 and
0.7698 → 0.8045. P6 predicted that these would be the fragile ones.

P6's wording does not cover this. It says "falsified if shortcut reliance and shift fragility are
uncorrelated" and is silent on a negative association, which is both a falsification *and* a reversal
of the mechanism the manifesto assumes. Recorded as both rather than folded into the null.

**The reversal has a mechanism, and it is V3's saturation moving in time.**

| | 1948–1963 | 1965–2014 |
|---|---|---|
| co-membership density | **0.9704** | **0.9954** |
| mean shared organisations per dyad | 14.8 | 26.1 |
| organisations per year | 116 | 273 |
| states per year | 88 | 169 |

The relation is markedly **less** saturated in the earlier regime, because there were less than half
as many organisations. Density features are therefore more informative there — which is exactly where
the density-only models improve. So shortcut-reliant models are not robust to shift in general; they
are helped by *this* shift, because it moves them into a regime where their features carry more
information. A different shift, toward more saturation, should hurt them.

**This is a finding about the diagnostic, not only about P6.** Shortcut reliance is not a stable
property of a model: it depends on how saturated the leaking relation happens to be in the regime the
model is evaluated in, and saturation drifts with the size of the institutional population. Any
programme that treats "shortcut reliance" as a model attribute — CLIQUEBAIT's H4 did, and P6 inherits
it — is treating a model-times-regime interaction as though it belonged to the model. That is why H4
could not be made to work in the prior programme and why restating it did not rescue it.

### V6 — T2. P5 holds, P4 holds on the comparable metric, and §5.3's intervention is a no-op

`penumbra/t2.py`, `results/t2_ladder.json`, `results/t2_focal.json`. Regime 1965–2014: **535
coalitions, 16,146 coalition-years, 152 events** — 83 dissolution, 30 replaced, 20 absorbed, and 19
whose cause ATOP cannot tell us. Those 19 enter through the likelihood's **cause-unknown** branch,
contributing $S(t_L) - S(t_R)$, rather than being dropped (17 % of events) or assigned a cause
(invented data). That branch was written for algebraic consistency and verified before ATOP's gap
was known to need it.

**83 of the events carry rule-assigned dates** — all the dissolutions, since the ten-year plenary
rule *is* how COW dates them. They stay in estimation and leave rolling-origin evaluation per §9.7.

Covariates are the four pre-specified in D-19, **after a 36-feature fit was rejected as
under-identified**: with 38 parameters per cause the three causes had 2.18, 0.79 and 0.53 events per
parameter. At four covariates the collapsed model has 13.8 and 8.3. The reduction was made on
substantive grounds before any coefficient was read, because choosing covariates by significance is
the garden of forking paths.

**P5 — HOLDS.** Cause-specific coefficients, dissolution against superseded:

| | log duration | log size | internal co-membership | polity2 mean | polity2 sd |
|---|---|---|---|---|---|
| dissolution | **+0.135** | −0.402 | **+0.255** | −0.080 | −0.115 |
| superseded | **−0.238** | −0.121 | **−0.086** | −0.014 | −0.105 |

Two covariates reverse sign, not one: internal co-membership density and duration dependence. P5
asked for at least one, so the prediction is met, and the pooled model would have averaged both
reversals to near zero. Duration reads cleanly — old coalitions fade, young ones get replaced or
merged. The cohesion reversal is counterintuitive and is reported without a story attached: with 83
and 50 events, an explanation would be decoration.

**P4 — holds on the comparable metric, and the ambiguity is the same one P3 has.** T2's any-cause
AUC is **0.614**, cause-specific 0.633 for dissolution and 0.576 for superseded. Against T1's pooled
0.80–0.92, termination is clearly harder and P4 holds. Against T1's within-coalition 0.57–0.68, T2
is *inside* the range and P4 would not hold. The like comparison is pooled against pooled — both are
"across all units at risk", T2's units being coalitions and T1's being dyads, and T2 has no strata
to hold fixed — so **P4 is recorded as holding**, with the within-coalition figure stated so the
reader can see what the choice was.

**§5.3's focal-group exclusion is a no-op here, and that is a finding about the intervention.** §4
calls competing risks the substantive contribution of T2 and §5.3 calls focal exclusion "a refinement
forced by T2", severe regardless of $\Delta^\star$. Measured:

| $\phi$ level | focal exclusion moves loglik by | moves AUC by |
|---|---|---|
| $k = 1$ | **−1.88** | −0.0039 |
| $k = 25$ | −0.22 | −0.0013 |

Eight and a half times larger at $k = 1$ than at $k = 25$, and negligible at both. The reason is V3's
saturation, not the level: at $k = 1$ co-membership has density 0.995, so removing the focal
organisation leaves the relation still saturated; at $k = 25$ the focal organisation is one unit of a
twenty-five-unit threshold. Either way the intervention barely moves the fit.

**This is bounded and the boundary matters.** §5.3's argument is about *alliance* edges — "an
alliance that ends is an alliance edge that disappears" — and `allies` has density 0.15, nowhere near
saturated, so focal exclusion should bite there. It is untested: `allies` is excluded from the anchor
set because its dating convention is unverified (PROVENANCE §4), and alliance entities are 80 of 535.
What is shown is that for the relation carrying $r^\star$ across the organisation majority, the
intervention §5.3 was written to force is not doing work. The alliance case remains open.

### V5 — T1's ladder, rungs 1–3. Every rung earns its place, and the two AUCs disagree by 0.25

`scripts/run_t1_ladder.py` → `results/t1_ladder.json`. Regime 1965–2014, the dyad-level risk set of
LEDGER.md §4.1: **2,211,354 dyad-years, 93,450 (coalition, state) dyads, 6,606 event dyads**, an
event rate of 0.00299 per dyad-year. Four rolling origins × four horizons, family cluster bootstrap,
discrimination and calibration reported jointly per §9.3.

| rung | features | pooled AUC | within-coalition AUC | calibration slope |
|---|---|---|---|---|
| 1 — duration alone | 1 | 0.476–0.715 | 0.481–0.524 | −0.13 … 1.03 |
| 2 — + node covariates | 22 | 0.791–0.913 | 0.530–0.630 | 0.66–1.03 |
| 3 — + densities | 34 | **0.798–0.920** | **0.570–0.680** | 0.64–0.99, mean 0.82 |

**§7's rule is satisfied at every step, and it is a rule rather than a preference.**

| | pooled | within-coalition |
|---|---|---|
| rung 2 − rung 1 | **+0.3195**, 16/16 cells | **+0.0975**, 16/16 |
| rung 3 − rung 2 | **+0.0096**, 15/16 | **+0.0393**, 16/16 |

**(a) The two AUCs differ by about 0.25, and that gap is the finding.** Pooled, the model scores
0.80–0.92; holding the coalition fixed and asking only *which candidate state accedes*, it scores
0.57–0.68 — a median of 120 coalition strata per cell. So most of the pooled discrimination is
between-coalition and between-state structure: which coalitions grow, and which states join things
in general. That is legitimate for the forecasting question §4 poses, and it is **not** the quantity
U2's matched design measured. Both are reported because V0 was retracted for conflating exactly
these, and reporting one number here would repeat the error with a better excuse.

**(b) Relational features answer a different question from node covariates, and the split is
clean.** Rung 3's gain over rung 2 is **+0.010 pooled** and **+0.039 within-coalition** — four times
larger once the coalition is held fixed. Node covariates say which coalitions grow and which states
are joiners; densities say *which state, for this coalition*. On the pooled metric the densities look
marginal and would have been dropped by an inattentive reading of §7's rule; on the metric that
isolates the relational question they are the larger contribution.

**(c) The gain grows with horizon, weakly.** Rung 3 − rung 2, within-coalition: +0.036 at $\Delta=1$,
+0.039 at 3, +0.038 at 5, **+0.045 at 10**. That is the direction P7 predicts — relational structure
mattering more at distance — but P7 is about rungs 6/7 against rung 4, not rung 3 against 2, so this
is suggestive of the mechanism and not a test of the prediction.

**(d) Duration alone is worse than chance at half the origins**, and its calibration slope runs from
−0.13 to 1.03. Accession is not explained by how long a dyad has been eligible, so §7's floor is a
genuine floor rather than a formality.

**(e) Calibration, which the prior programme left as an acknowledged qualitative failing.** Rung 3's
slope averages **0.82** across origin-horizon cells and never exceeds 1.0. The model is
systematically overconfident by about 18 % on the logit scale — modest, consistent, and now a number
rather than a caveat. §9.3 asked for exactly this.

**P3 cannot be read cleanly, for two independent reasons, and neither is resolved by choosing a
number.** P3 predicts T1 discrimination in 0.70–0.85 *at $\Delta = \Delta^\star$*, falsified above
0.95. First, $\Delta^\star$ is not identified (V2), so the horizon P3 names does not exist. Second,
the prediction does not say which discrimination: pooled lands at 0.80–0.92, straddling the band and
exceeding it at three origins; within-coalition lands at 0.57–0.68, below it throughout. The pooled
metric is the closer analogue of the 0.993 figure P3 anchors against, since that was a pooled
group-classification AUC — but C1 already recorded that this comparison is not like-for-like. **What
can be said without choosing:** nothing anywhere near 0.95, so P3's falsification condition is not
met, and no reading of the numbers indicates residual leakage. P3 is recorded as **not cleanly
decided**, with both metrics stated, and the choice between them is left to the reader rather than
made silently in the direction that fits.

### V4 — the observer channel exists, is unmeasurable, and a quarter of accessions are lost to missing data

Three things came out of testing a mechanism §1 names explicitly and V2's four measurements could
not see. §1 says the shadow contains "interim protocols … observers are seated", and
`build_igo_comembership` counts **full members only**, so if accession is preceded by observer
status the penumbra would live in a channel $r^\star$ excludes by construction.

**(a) The test was circular, and that was my error.** `igo_membership_events` defined an accession as
`prev == 0 & cur == 1`, which excludes any state that held observer or associate status the year
before. Asking "were acceding states observers first" of events defined to exclude prior observers
can only return zero, and it did — 0.0000 at every lag against a control rate of 0.0012.

**(b) The channel is real and negligible.** Entries into full membership over 1965–2014, by prior
status: **6,397 from no membership, 22 from observer, 2 from associate**, and 1,977 from missing
data. So the observer route is 24 of 8,398 — **0.29 %**. The event definition is corrected to admit
entry from any non-member status, and no number in V2 or V3 is re-run, because 24 events against
6,397 is below the resolution of every figure in them. Saying so is the point: a fix that cannot
move a result should be recorded and not used as an excuse to recompute one.

**(c) §1's observer mechanism is not measurable in this corpus.** With 24 cases there is no power to
test whether seating an observer precedes accession, at any horizon. That is a limit on what the
corpus can say about the manifesto's own stated mechanism, and it is a limit rather than a finding:
COW IGO records observer status sparsely (2,235 observer-years in 505,951 membership rows, 0.44 %),
so the absence may be the source's coverage rather than the world's behaviour.

**(d) 1,977 accessions — 24 % of all entries into full membership — are unusable.** Their prior year
is `-9`, missing data, so whether the state was already a member is unknown and C5 puts it outside
the risk set. That rule is right, and its cost had not been reported: **the risk-set rule discards a
quarter of the observable entries into membership.** It compounds with PROVENANCE §3's finding that
205 organisation-years of missing data are undeclared by the codebook. Every T1 count in this
programme is therefore a count of *cleanly observable* accessions, and the denominator that phrase
implies belongs in the paper next to it.

### V1 — P2's shortcut-curve clause is falsified. U2 on real LEDGER, 2026-08-03 — **WITHDRAWN, see V0**

`scripts/run_u2.py --regime primary` → `results/u2_real.json`. Regime 1965–2014, 6,732 accession
events, 438 family clusters, gradient-boosted probe cross-fitted with folds grouped on the family,
both negative strata. Features are per-relation densities and clique indicators at the declared
co-membership level ladder, plus group size — no learned representation of any kind.

$\mathrm{AUC}_{\text{shortcut}}(\Delta)$, primary stratum (*never-event*):

| $\Delta$ | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| AUC | .8905 | .8762 | .8759 | .8703 | .8675 | **.8703** | .8679 | .8638 | **.8687** | .8661 |

P2 requires the curve to decay **monotonically** and reach the non-leaking band inside the
observable range, and states it is *"falsified by a flat curve"*. Measured: total decay from
$\Delta = 1$ to $\Delta = 10$ is **0.0244**, and the curve **rises at two of nine steps** (bold).
Nine years of additional forecast horizon cost the density-only probe two and a half AUC points.
That is a flat curve by any reading, and the falsification condition is the manifesto's own.

**What is falsified and what is not.** The shortcut clause of P2 fails. The
$\Delta^\star_{\text{hi}} \leq 6$ clause is a separate measurement that needs U1 on real data and
is untouched by this. P1 is likewise unmeasured.

**What the falsification does *not* settle, and must not be made to.** §8's gloss on P2 is that
its failure would mean *"forecasting does not escape the leak and the reformulation fails on its
own terms"*. That reading assumes the flat 0.87 is leakage. Three independent measurements point
the other way and none of them is a reinterpretation after the fact:

1. **COW IGO does not systematically back-date.** Five of 495 organisations mention signature or
   accession dating and one of those explicitly refuses to back-date (`PROVENANCE.md` §2). There is
   no mechanism planting the event in the observation window for the relation carrying $r^\star$
   across 493 of 573 entities.
2. **The clique-indicator effect is absent.** CLIQUEBAIT's D1 override rests on linear 0.915
   against gradient-boosted 0.979 — a gain of **+0.064** — because a leak is an exact-clique
   effect that a linear probe cannot see. Here the mean gain is **−0.0014**, and the linear probe
   matches or beats the boosted one at **7 of 10** horizons. Whatever produces 0.87 is linear in
   the densities, which is what graded structural signal looks like and is not what a planted
   clique looks like.
3. **Co-membership is saturated** at density 0.995, so being a clique in it carries no information
   in the first place (`LEDGER.md` §6.2).

So the honest verdict is: **the curve is flat, P2's stated condition is met, and whether that is
"the leak survives every horizon" or "there was little leak and densities carry real signal" is
exactly what U1 decides.** The provenance evidence leans hard to the second. Recording the
falsification now and the interpretation later is the only order that keeps both honest — and if
U1 returns a narrow penumbra, §11's contingency for "the penumbra turns out to be trivially narrow"
is the reframe, not a rescue invented at that point.

### V1a — horizon contamination, measured for the first time — **numbers void, see V0**

The two negative strata separate at **every** horizon, *never-event* above
*not-at-this-horizon* by a mean of **0.0129** (range 0.0073–0.0200). That gap is the contamination
§5.1 predicted and the zero-lag formulation cannot have: pooling states that accede at some *other*
horizon into the negatives puts units carrying the event's traces on the negative side, and the
task gets harder. It is small, it is consistent, and it is the first quantification of the cost of
the stratum choice. A paper that does not declare which stratum it used is reporting a number with
a 0.013 ambiguity in it.

### V1b — the inherited requirement for a non-linear probe does not transfer — **numbers void, see V0**

CLIQUEBAIT's PROTOCOL §5 says "use a **non-linear** probe for D1", on the evidence of a 0.064 gap.
On this corpus the gap is zero to negative. The rule is not wrong; its *justification* is
corpus-specific, and the honest generalisation is that both probes are reported and the gap is
itself a diagnostic — a large gap indicates a clique-indicator effect, a null gap indicates there
is not one. That is a stronger statement than the inherited rule and it is available only because
both were run. Recorded here rather than as a change to `PROTOCOL.md`, which belongs to the other
programme.

### V1c — horizon 0 is not expressible in the T1 risk set — **stands, see V0**

No panel exists at $\Delta = 0$. At the accession year the state is already recorded as a member,
so it is not in the risk set, and every positive filters out. Detection at zero lag — the
formulation CLIQUEBAIT audited — is therefore not a special case of this one but a different task
over a different risk set. That is a structural property worth stating plainly, because a reader
will expect $\Delta = 0$ to anchor the curve and it cannot.

### V1d — U2 can manufacture a penumbra, and the confound is structural to the diagnostic — **mechanism stands, numbers void, see V0**

The out-of-regime replication (1948–1963) appeared to *support* P2 where the primary regime
falsified it: the boosted probe fell from 0.844 at $\Delta = 1$ to 0.701 at $\Delta = 10$, a decay
of 0.143 — six times the primary regime's. Read at face value that is the penumbra closing, in the
window where the manifesto would most expect it.

It is not. It is the probe overfitting a smaller sample, and the test is decisive because the decay
moves with **probe capacity** rather than with anything about the data:

| | $n_{\text{pos}}$ at $\Delta=1 \to 10$ | GBM 30 trees / depth 2 | 100 / 2 | 300 / 3 | linear |
|---|---|---|---|---|---|
| replication 1948–1963 | 1061 → 508 | 0.0575 | 0.1162 | **0.1434** | 0.0411 |
| primary 1965–2014 | 6294 → 4024 | 0.0304 | 0.0313 | **0.0244** | 0.0290 |

(cells are the decay in $\mathrm{AUC}_{\text{shortcut}}$ from $\Delta = 1$ to $\Delta = 10$.)

In the small regime the apparent decay **nearly triples** as capacity triples, while the linear
probe sits fixed at 0.041. In the primary regime the decay is capacity-invariant at 0.024–0.031 and
agrees with the linear probe's 0.029. The corroborating symptom was visible before the test: at
$\Delta = 10$ the boosted probe gave 0.701 on one negative stratum and 0.824 on the other, from the
same positives — a 0.12 swing from a sampling change, which is variance, not signal.

**Why this is not a local nuisance.** The positive count *necessarily* falls with horizon: an event
at $t + \Delta$ needs an origin at $t$, so the longest horizons always have the fewest usable
events. A high-capacity probe therefore always overfits *more* at long horizons than at short ones,
and produces a decaying curve **whatever the leakage is**. The confound is built into the shape of
the diagnostic rather than into this corpus, and it runs in exactly the direction that confirms the
hypothesis U2 is meant to test.

And the inherited protocol points straight at it. CLIQUEBAIT's PROTOCOL §5 says "use a
**non-linear** probe for D1", on good evidence at zero lag where the sample does not shrink. Carried
into a horizon-resolved setting without that caveat, it is an instruction to build a penumbra
detector that finds penumbras in small corpora.

**Pre-specification, forced by this and applying to every U2 figure the paper reports.** The curve
is reported at **at least three probe capacities plus the linear probe**, and a decay that varies
with capacity is reported as an artefact rather than as evidence of a penumbra. The linear probe is
the capacity floor and the honest reading of any U2 curve is the capacity-invariant part of it.

**Consequence for V1: the falsification is strengthened, not weakened.** The primary regime's flat
curve is exactly the case that survives capacity variation and matches the linear floor, so it is
not an artefact of probe choice. And the replication does not rescue P2, because its decay
evaporates under the one test that distinguishes decay from overfitting.

---

## Measured before the corpus was built

C1–C6 above were written with nothing measured. C7–C11 are different in kind: each is a number
obtained on 2026-08-03, during the source audit, **before** any $\Delta^\star$ was estimated
and before any model existed. They are recorded here rather than folded into the manifesto
because a prediction adjusted to fit a number already seen is worthless, and the dividing line
has to be visible. All figures from `scripts/audit_corpus_scale.py`.

**C7 — the external anchor was measured, it leans against P1, and P1 was left standing.**
§6 nominates DESTA's signature-to-entry-into-force gap as "the closest thing to ground truth
the programme will have outside synthetics", and the round-1 amendment folded it into §7's
likelihood. Measured over 1,050 agreements signed from 1946: **median 1 year**, mean 1.34, max
17; 76.3 % have a gap of at least a year, **29.9 % at least two**, 11.3 % at least three.
P1 commits to $\Delta^\star_{\text{lo}} \geq 2$. On this one externally-coded channel the
administrative shadow is therefore narrower than P1 predicts, for seven agreements in ten.
P1 was **not** altered. If it falls, this entry is the record that its anchor's value was known
first; if it holds, the mechanism carrying it is not the signature-to-force gap but the
negotiation traces §1 describes, and the paper must say which. §11's risk "the penumbra turns
out to be trivially narrow" now has a measured prior behind it rather than a hypothetical.

**C8 — §11's contingency for P5 has already fired, and it fired before any model was run.**
P5 requires a covariate to reverse sign between cause-specific hazards for dissolution and for
**absorption**. COW IGO's coded causes from 1946: dissolution **103**, replaced **32**,
absorption (`integrated`) **22** — from 1965, 84 / 30 / 20. §11 states that if absorption
events number in the low tens, P5 cannot be tested at the intended resolution, and prescribes
collapsing to two causes. Twenty-two is the low tens. Pre-specification: P5 is tested as
**dissolution (103) versus superseded (54 = replaced + absorption)**, which is the contingency
the manifesto already contains, so this invokes the pre-registration rather than amending it.
The three-cause model is still fitted and reported, but as a descriptive decomposition, not as
P5's test. `replaced` is the cause the manifesto never named and it is larger than the one it
built P5 on — which is itself the finding that reading the coding rules was supposed to produce.

**C9 — DESTA supplies a negative class the manifesto does not exploit, and it is the cleanest
one available.** 282 agreements signed from 1946 never entered into force. Their administrative
traces exist — signature, text, coded provisions — and the event never happened. Every other
negative in LEDGER is a unit that simply did nothing, which cannot separate a trace from a
precursor; these are units with traces and no event, which can. Pre-specification: they enter
U1 as a third comparison stratum alongside *never-event* and *not-at-this-horizon*, and the
clique contrast measured against them is reported as the primary specificity check on
$\Delta^\star$. If leakage is what drives the horizon curve, this stratum should look like the
positives; if genuine precursor signal drives it, it should not.

**C10 — DESTA contributes no entity terminations, so T2's supply is exactly two sources.**
DESTA's `entry_type` distinguishes base treaty (903), accession (208), protocol or amendment
(77), withdrawal (72) and consolidated (72), all from 1946. Withdrawal is a **member exit**,
not an agreement termination; DESTA does not code agreements ending. T2's entity-termination
events therefore come only from COW IGO (157 coded, 1946+) and ATOP (26 multilateral, 220
including bilateral). Consequence: the two vocabularies must be reconciled explicitly, since
ATOP's `termmode`/`termcaus` and COW's dissolved/integrated/replaced are different schemes over
the same kind of event, and §4 now says so. No number pooling the two may be reported before
the crosswalk is written down.

**C11 — points on a horizon curve are not independent, and the worry it replaces was wrong.**
The concern raised first was that long horizons would leave too few forecast origins. Measured,
that is false: with the graph complete over 1948–2014 and events ending 2014, origins run 67
at $\Delta = 0$ down to **57 at $\Delta = 10$**. Ample. The real problem is the opposite shape.
A single event contributes to *every* horizon, each time from a different origin — an event in
2014 is a $\Delta = 1$ target from 2013 and a $\Delta = 10$ target from 2004 — so the points of
$\omega_r(\Delta)$, $\mathrm{AUC}_{\text{shortcut}}(\Delta)$ and the discrimination curve are
computed on largely the same events. Pre-specification: confidence bands across $\Delta$ are
produced by the cluster bootstrap of §9.4 resampling **entities**, never by treating horizons
as independent samples, and any claim of monotonicity in $\Delta$ — P2 makes one — is tested
against that resampling rather than against per-horizon intervals.

**C12 — U3's exclusion set is undefined in time for termination, which is the task it was
written for.** §5.3 removes $E^{r^\star} \cap \Pi(S_c)$ for the focal group $c$. For accession
that is unambiguous, because the candidate set is fixed at the moment of scoring. For
termination the membership of $c$ *changes over its life*, so $\Pi(S_c)$ differs depending on
whether $S_c$ is taken at founding, at the observation year $t$, or at termination — and the
three exclusion sets are not nested. Pre-specification: $S_c$ is the membership **as of the
observation year $t$**, since that is the only version available to a forecaster at $t$, and
the founding-membership variant is reported as a sensitivity. Using the termination-year
membership would import the outcome into the intervention, which is the error U3 exists to
avoid. Related and already covered: §5.3's illustration ("an alliance that ends is an alliance
edge that disappears") is written for alliance entities, and §11 states that $r^\star$ is
co-membership rather than alliance edges for the organisation majority of the corpus. The
instrument is entity-type agnostic; only the example is partial.

**C13 — the resampling unit moves from the entity to the membership-equivalent family, and the
direction of the move is what makes it legitimate.** C4 pre-specified coalition-level resampling
as primary with a state-level cross-check. Measured on 2026-08-03: clustering organisations at
Jaccard $\geq 0.90$ over at least five shared years yields **31 families covering 107 of 491
organisations**, and within a family, pairs of deaths fall within two years of each other
**26.9 %** of the time (7 of 26) against **10.1 %** for random pairs drawn from the same
population — enrichment **2.66×**, nominal one-sided $p = 0.013$. The nominal $p$ is
anti-conservative, since pairs inside a family share entities, so the finding is suggestive.
Pre-specification: the family is the primary cluster-bootstrap unit for T2, a singleton family
being an entity; entity-level resampling is reported alongside as the anti-conservative
comparison. C4's state-level cross-check for T1 stands unchanged.

Changing a pre-specification after a measurement needs its justification stated, so: family-level
resampling can only **widen** intervals. Moving to a more conservative unit on discovering
dependence is a different act from moving to a less conservative one on discovering an
inconvenient interval, and only the second is the thing pre-specification exists to prevent. The
first baseline computed for this comparison was also wrong in the direction of the conclusion —
it drew random pairs from all 534 organisations including pre-1946 deaths rather than from the
491 the families come from, which lowered the baseline to 7.2 % and inflated the enrichment to
3.72×. Naming the comparison stratum is PROTOCOL §1 and this is what it is for; the corrected
figure is the one above.

**C14 — membership overlap cannot identify duplicate entities, and a rule built on it would have
deleted the corpus's most useful variation.** Matching the 70 ATOP multilateral treaties against
the 491 organisations on membership Jaccard gives 178 candidate pairs at $J \geq 0.6$, seven at
$J = 1.000$ — but 27 treaties match more than one organisation and 41 organisations match more
than one treaty, one treaty matching **24**. Those 24 are the Pan-American system: the OAS, PAHO,
the Inter-American Children's Institute, the Inter-American Defense Board, the Commission of
Women, the Highway Congresses association. Another treaty matches 16 European bodies over EU
membership. Same members, different bodies, **different fates** — which is exactly the variation
T2 explains. Pre-specification: no automatic deduplication; a `same_instrument` link is asserted
only on instrument-level evidence, hand-verified, and printed in full, and any statistic pooling
the two entity types reports its double-count exposure. Full rule and the task declarations it
feeds are in `LEDGER.md`.

**C15 — the leaking relation for four fifths of the corpus is saturated, so $\phi$ is generalised
to a level ladder.** §11 makes $r^\star$ entity-type dependent: alliance edges for an alliance,
co-membership for an organisation. Built from COW IGO's full memberships, co-membership has mean
density **0.9954** over 1965–2014 — with 491 organisations over about 168 states almost every pair
shares something — so a binary $\phi_r(S)$ is $\approx 1$ for positives and negatives alike and its
clique contrast is $\approx 0$. The channel that must carry the leak for 493 of 573 entities
carries no signal in the form the manifesto's $\phi$ assumes.

Neither obvious repair works, and both were measured rather than reasoned about. Thresholding the
dyad weight is non-monotone in density — 0.258 at $w \geq 40$, back up to **0.281** at $w \geq 50$,
because the surviving nodes collapse onto densely connected European states. Excluding
near-universal organisations leaves 0.706 after dropping all 47 that ever reach half the state
system, and 0.482 after dropping 87 at a 0.3 share.

Pre-specification: co-membership is treated as weighted, with
$\phi_r(S; k) = |\{(u,v) \in \Pi(S): w_r(u,v) \geq k\}| / |\Pi(S)|$, so a clique at level $k$ is a
group every dyad of which shares at least $k$ organisations. At $k = 1$ this *is* the manifesto's
$\phi_r(S)$, so the frozen definition is generalised and not contradicted, and `clique_contrast`
keeps the property that made it the only statistic to survive all three of CLIQUEBAIT's settings.
$k$ is a declared ladder and $\Delta^\star$ is reported per level; the primary $k$ is fixed on the
synthetic testbed where §5.1 already requires the non-leaking band to be calibrated, and never by
matching a density to another relation's. Construction rule and the observed weight distribution
are in `LEDGER.md` §6.2.

**C16 — an undeclared coverage hole at 1964, found in the prior programme's own artefact.**
`votes_with` carries zero edges in 1964, the only such year in 1946–2016, and CLIQUEBAIT's rebuilt
`graph_1964.pt` confirms it by shipping three edge types rather than four. Its `FINDINGS.md` §4
declares the 1946–47 trade gap and the 2015–16 conflict gap and not this one, because 1964 sits in
the training period. The probable cause is substantive — the nineteenth General Assembly session
took no recorded votes during the Article 19 crisis — but **that is unverified** and is on
`LEDGER.md`'s open list. Pre-specification: 1964 is its own coverage regime and no ranking metric
is pooled across it, per PROTOCOL §3, whatever the cause turns out to be. One consequence is
favourable and worth recording so it is not mistaken for a design choice later: because COW IGO
stops imputing after 1964 and `votes_with` returns in 1965, the longest intact-coverage regime
(1965–2014, 50 years) and the exactly-dated event stratum begin in the same year, which makes that
window the primary analysis regime and 1948–1963 an out-of-regime replication.

**C17 — the non-leaking band must be anchored on a relation that shares $r^\star$'s structure, and
anchoring it on relations that merely do not leak makes $\Delta^\star_{\text{lo}}$ overshoot.**
Measured on the synthetic corpus, `scripts/calibrate_delta_star.py`. With latent-similarity and
noise relations as the only anchors, their clique rate is exactly **0.000**, because they have no
group mechanism at all: to form a clique every dyad must arrive from the background. A relation
that records current membership honestly still shows a residual clique rate of about **0.05**, since
only the acceding state's dyads are missing and a latent neighbour's dyads are favoured by a
similarity-weighted background. So the band was an order of magnitude tighter than the residual it
had to admit, and $\Delta^\star_{\text{lo}}$ fired two horizons late or never — at $\beta = 3$ the
contrast collapsed from 1.000 to 0.050 exactly on cue at $\Delta = 4$ and was rejected against a
band of 0.0487.

The fix is structural rather than a tolerance. The generator now carries `r_current`: the same
construction as $r^\star$, the same completeness, and $\beta = 0$ by declaration — a relation that
records the present and does not anticipate. It is the band's primary anchor. Pre-specification for
real data: **the band's anchor must be a relation known from the coding rules to record without
back-dating, not merely one believed not to leak.** Which relations those are cannot be decided by
any statistic and comes from §5.4's provenance paragraph, exactly as CLIQUEBAIT's triage/verdict
distinction requires. A band set on structurally dissimilar anchors systematically reports the
penumbra as wider than it is, which biases P1 toward confirmation.

**C18 — $\Delta^\star_{\text{lo}}$ calibrates exactly; $\Delta^\star_{\text{hi}}$ is frequently
unreachable, and P2 must not be falsified by that.** With the corrected band, the lower bound
recovers the known back-dating horizon in **6 of 6 settings**, $\beta = 0 \ldots 5$, landing on
$\beta + 1$ every time. That is the target the definition implies: traces are present for
$\Delta \leq \beta$, so the smallest trace-free horizon is $\beta + 1$. The estimator works.

The upper bound does not behave. Over horizons 0–8 it fired in **2 of 6** settings on the
*never-event* stratum and was unreachable in the rest. The cause is the conjunction §5.1 requires:
$r^\star$ must lose top rank **and** its $\phi$-alone AUC must enter the band, and rank is a
relative statistic that a structurally similar anchor keeps contesting. This was flagged as a risk
before any measurement and is now demonstrated.

The consequence for the frozen text is precise and must be honoured rather than argued around. P2
is falsified by a flat shortcut curve or by $\Delta^\star_{\text{hi}} > 6$. An **unreachable**
upper bound is not a large one. Pre-specification: where $\Delta^\star_{\text{hi}}$ does not exist
within the observable horizon range, that is reported as **instrumental non-identification of the
upper bound** and P2 is recorded as *not testable at this bound*, never as falsified. The
programme does not get to end on an artefact of its own measuring device, and it does not get to
quietly rescue P2 either — the non-identification is reported as prominently as a verdict would
have been. The synthetic result above is the evidence that this is a property of the definition
rather than of any particular corpus.

---

## Outstanding, carried from CLIQUEBAIT

Items its `MANIFESTO-OUTCOMES.md` left open that this programme is positioned to close.

1. **Cluster bootstrap on the IR side.** Required by PROTOCOL §6, demonstrated there only as a
   split on the protein benchmark. C4 above is how it gets done here.
2. **H4, restated as P6 and tested.** The prior programme's motivating anomaly dissolved into
   relation dropout; this one supplies genuine temporal shift by construction.
3. **Dyadic decomposition under the corrected protocol.** §11's "link prediction with extra
   steps" rebuttal is load-bearing here and rests on a comparison the prior work did not re-run.
4. Not carried: the third-party audit and D3-with-a-trained-model belong to CLIQUEBAIT.
