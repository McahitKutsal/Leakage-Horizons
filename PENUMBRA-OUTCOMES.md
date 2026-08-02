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

**Nothing below has been measured yet.** The programme is at corpus construction.

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
| LEDGER — event corpus | source audit done (`scripts/audit_corpus_scale.py`), corpus not built |
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
cells carry `-9` (state not a system member) and `-1` (membership unrecorded). Treating `-1`
as absence manufactures accessions out of missing data; treating it as membership manufactures
exits. Pre-specification: `-9` is out of the risk set, `-1` is out of the risk set for that
organisation-year and the exclusion is tabulated per year, so a coverage defect in the source
shows up as a shrinking denominator rather than as events.

**C6 — the decolonisation cluster is a population, not an outlier.** Recorded in §11 as a
cost of the corpus decision. Concretely: a newly independent state joining many organisations
within a few years produces accession events that are neither independent nor the coalition
decision the programme models. Pre-specification: report T1 with and without the first $k$
years of each state's system membership, $k$ fixed before fitting, and treat the difference as
a reported sensitivity rather than choosing the favourable one.

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
