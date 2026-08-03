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

**Status, 2026-08-03.** No model has been fitted, no $\Delta^\star$ estimated, no prediction
adjudicated. What *has* been measured is the source audit — event counts per source and cause,
COW IGO's dating rules, and the DESTA signature-to-force gap — all of it by
`scripts/audit_corpus_scale.py` into `results/corpus_scale.json`. That audit is why the
manifesto's round-2 amendment happened and why no third round may. Concerns C7–C11 below are
its output and are stated as measurements with dates, not as pre-measurement caution.

---

## §8 — falsifiable predictions

| | prediction | test statistic | verdict |
|---|---|---|---|
| **P1** | penumbra wider than one year, $\Delta^\star_{\text{lo}} \geq 2$ | U1 clique contrast, lower bound | not yet measured |
| **P2** | penumbra bounded, $\Delta^\star_{\text{hi}} \leq 6$, shortcut curve decays | U1 upper bound + U2 | not yet measured |
| **P3** | T1 discrimination 0.70–0.85 at $\Delta = \Delta^\star$ | T1 rolling-origin AUC | not yet measured |
| **P4** | termination harder than accession | T2 cause-specific concordance vs T1 | not yet measured |
| **P5** | competing risks not decomposable; a covariate reverses sign | cause-specific vs pooled hazards | not yet measured |
| **P6** | shortcut reliance predicts fragility under temporal shift (CLIQUEBAIT H4) | U2 by regime | not yet measured |
| **P7** | graph earns its keep at long horizons or not at all | ladder rung 6/7 minus rung 4, by $\Delta$ | not yet measured |

## Deliverables (§10)

| | status |
|---|---|
| $\Delta^\star$ definition with signature-to-force external validation | definition amended into §5.1; not yet estimated |
| UMBRA — lagged diagnostic suite U1–U3 | not started |
| LEDGER — event corpus | source audit done incl. causes, dating rules and DESTA gap; corpus not built |
| Three tasks with declared risk sets, origin times, censoring rules | not started |
| Cause-specific hazard results for termination | not started |
| Architectural ladder, each rung earning its place | not started |

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
