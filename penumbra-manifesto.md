# PENUMBRA: Forecasting Coalition Formation and Termination under Precursor Leakage

### A Research Manifesto

**Working title of the paper:** *The Penumbra of an Event: Leakage Horizons and Event-History Forecasting of International Coalitions*

**Programme name:** PENUMBRA
**Diagnostic suite:** UMBRA — the lagged extension of the CLIQUEBAIT D-series
**Event corpus:** LEDGER — formations, accessions, exits and terminations at annual resolution

---

## 0. Status of this document

This is a pre-registration, written before the data are built and before any model is fitted. It is fixed on completion. Predictions in §8 are committed to in the form given there; if they are later falsified, that falsification means something only because the commitment preceded the measurement. A separate reconciliation file will record outcomes clause by clause, as `MANIFESTO-OUTCOMES.md` did for CLIQUEBAIT.

The prior programme falsified one of its own five hypotheses and had to override three of its four diagnostics. That is the expected rate. This document should be written so that the same thing can happen visibly.

---

## 1. Thesis

An event casts a shadow backwards into the data that precede it. A coalition that will be founded in 2004 is already visible in 2002 — accession negotiations are under way, interim protocols are signed, observers are seated, trade reorients in anticipation. Two entirely different things live in that shadow and they are easily confused:

- **Signal.** Relational conditions that *cause* or *predispose* the event. Deepening trade, converging votes, shared threat. Recovering these is the whole point of forecasting.
- **Leakage.** Administrative traces of the event *itself*, back-dated into the observation window because the curator recorded the process rather than only the outcome. An accession protocol coded as an alliance edge two years before entry into force is not evidence that the coalition was coming; it is the coalition, recorded early.

CLIQUEBAIT showed that in the *detection* formulation these are not merely confusable but indistinguishable, because the target relation sits in the graph at the same instant as the label. Forecasting appears to solve this: predict at $t+\Delta$ from $G_{\leq t}$ and the treaty has not been signed yet. **That relief is partial and its extent is measurable.** The leak does not vanish at $\Delta = 1$; it decays over some horizon, and the width of that decay is a property of the curation process, not of the model.

We call that region the **penumbra**, and its width the **leakage horizon** $\Delta^\star$: the smallest forecast horizon at which the target relation no longer carries administrative traces of the event. PENUMBRA measures $\Delta^\star$, forecasts inside and outside it, and reports what the difference costs.

The programme has a second face. The prior work could not model dissolution at all — the Warsaw Pact's fitted value declined only marginally through the late 1980s. If events cast shadows, terminations should cast them too, and the failure to see one is a finding about either the model or the world. PENUMBRA treats formation and termination symmetrically and expects them to behave differently.

## 2. Constraints inherited from CLIQUEBAIT

This is not a fresh start. The prior programme removed several options that would otherwise be available, and they are binding here.

| Finding | Consequence for this programme |
|---|---|
| Heterogeneous advantage reverses under target-relation exclusion (rich pooling: $+0.0129 \to -0.0127$) | A relational encoder is **not** a justified default. RGCN must earn its place against homogeneous and graph-free controls under the corrected protocol, or be dropped. |
| Graph worth $+0.023$ against a capacity-matched control, against $+0.05$–$0.09$ versus the published baselines | Every architectural claim is measured against a **capacity-matched graph-free control**, from the first experiment, not as a late robustness check. |
| Pooled ranking metrics across a data-regime break invert model orderings | Coverage is audited per relation per year **before** any model is fitted. Metrics are reported per regime. No headline number spans a coverage change. |
| Undeclared coverage defects invert D2 rather than weakening it | The provenance audit is a precondition, not a companion. UMBRA runs before UMBRA's own masking experiments. |
| Leakage is a provenance *set*, not a relation | Exclusion operates on sets. For termination, see the focal-group refinement in §5.3. |
| Interaction tests on a bounded metric are headroom-confounded | Any difference-of-differences is reported on the normalised scale $(\cdot)/(1-\text{baseline})$ alongside the raw one. |
| Cluster bootstrap at entity level | Coalition-years are not independent. Resample coalitions, not observations. Non-negotiable, and the outstanding gap on the IR side of the prior work. |

**A methodological debt is repaid here.** CLIQUEBAIT's H4 — that the negative-difficulty statistic predicts fragility under distribution shift — was orphaned when its motivating anomaly dissolved into relation dropout. This programme supplies genuine temporal shift by construction. H4 is restated in §8 as **P6** and tested here.

## 3. Why forecasting, and why it is not merely detection with a lag

Three claims justify the reformulation.

**It removes the leak structurally rather than by ablation.** In CLIQUEBAIT the leak was removed by deleting a relation from a graph that legitimately contained it — an intervention that also destroys real information and whose result is therefore a lower bound. In forecasting at $\Delta > \Delta^\star$, the offending edges do not exist yet. Nothing is deleted and nothing legitimate is lost.

**It is the formulation the applied question actually wants.** "Which states will form a bloc" is a forecasting question. The detection formulation answers "which observed groups were coalitions," which is a question whose answer is already written down.

**It makes the target well-defined in time.** Detection scores a group-year with no notion of when the group came into being; the value trajectory is an artifact of the scoring function. Event-history modelling gives the timing first-class status and yields quantities — hazard, expected duration, cause-specific risk — that a validity score cannot express.

The honest counterweight: forecasting is a strictly harder problem and the numbers will be much worse. §8 commits to how much worse.

## 4. Task suite

The risk set is the crux. A naive formulation ranges over all $2^{|V_t|}$ subsets, which is neither computable nor meaningful. Three tasks are specified, in descending order of well-posedness, and the manifesto states plainly which ones carry the paper.

### T1 — Accession (core)
For each active coalition $c$ and each year $t$, the risk set is the set of states active at $t$ and not yet members of $c$. The event is entry into $c$ at $t+\Delta$. This is a recurrent-event, member-level formulation with an unambiguous risk set, exact dates from ATOP and DESTA, and direct policy meaning.

### T2 — Termination (core)
Each coalition is an entity entering at founding and exiting at termination, right-censored at the end of the window. **Competing risks** are essential and are the substantive contribution of this task: a coalition can end by dissolution, by absorption or merger into a successor, by transformation of membership beyond recognition, or by dormancy without formal termination. ATOP codes termination circumstances directly; COW IGO distinguishes dead from dormant. Pooling these into one event type is the standard practice and we expect it to be wrong.

### T3 — De novo formation (exploratory, and labelled as such)
Predicting the emergence of a group that does not yet exist. The risk set problem is unsolved and we do not claim to solve it. The approach is two-stage: candidate generation by dense-subgraph and community detection over $G_{\leq t}$, then hazard estimation over the generated risk set. **This task samples on the dependent variable and suffers immortal-time bias unless the candidate pool is generated identically for formed and never-formed groups.** We state the bias, mitigate it by generating candidates from the graph alone with no reference to the canon, and report T3 as exploratory regardless of outcome. If it does not work, that is reported.

T1 and T2 carry the paper. T3 is a section, not a claim.

## 5. UMBRA: the lagged diagnostic suite

CLIQUEBAIT's diagnostics measure leakage at zero lag. Their extension to horizons is the methodological core of this paper and is domain-general even though it is applied in one domain.

### 5.1 U1 — Leakage-horizon curve
Compute $\omega_{r}(\Delta) = \mathbb{E}[\phi_r(S) \mid \text{event at } t+\Delta]$ over the observation graph $G_t$, for $\Delta = 0, 1, \ldots, 10$, for every relation. Plot against $\Delta$. Report alongside it the clique-contrast statistic $P(\phi_r = 1 \mid \text{event}) - P(\phi_r = 1 \mid \text{no event})$, which CLIQUEBAIT established as the only ranking statistic that survived all three settings tested — $\omega$ alone mis-ranks.

**Define $\Delta^\star$ as the smallest $\Delta$ at which the clique contrast for $r^\star$ falls within the band established by known non-leaking relations.** The threshold is set on the synthetic testbed, not by eye.

### 5.2 U2 — Horizon-resolved shortcut probe
Run the non-linear D1 probe (gradient-boosted, per CLIQUEBAIT's override of the linear specification) separately at each horizon. The curve $\mathrm{AUC}_{\text{shortcut}}(\Delta)$ is the fraction of the forecasting task recoverable with no representation at all, as a function of how far ahead one looks. This is the single most informative plot the paper can produce, and it should appear early.

### 5.3 U3 — Focal-group exclusion
A refinement forced by T2. In termination forecasting the focal coalition's own alliance edges *are* the label: an alliance that ends is an alliance edge that disappears. Global relation exclusion is too blunt — it destroys the alliance context of every other coalition. The correct intervention removes $E^{r^\star} \cap \Pi(S_c)$ for the focal group $c$ only, leaving the rest of the relation intact. Report both global and focal exclusion; they answer different questions in the same way that CLIQUEBAIT's two halves of D2 do.

### 5.4 What no statistic can settle
CLIQUEBAIT established that no function of the graph separates a leaking relation from a legitimately predictive one — at $\alpha = 0$ every latent-similarity relation clears any threshold. The same limit applies with more force here, because a genuine precursor and an administrative back-dating produce the same edge. **The automated part of UMBRA is triage. The verdict requires reading the coding rules.** For each relation, the paper must state what the source records as the start date: signature, ratification, entry into force, or first observed activity. That paragraph is load-bearing, not boilerplate.

## 6. LEDGER: the event corpus

The prior canon holds 38 entities. Counted as events rather than entity-years that is perhaps forty formations and a dozen terminations, which will not support competing-risks estimation. Scale-up is a precondition, not an enhancement.

| Source | Contributes | Resolution | Note |
|---|---|---|---|
| ATOP v5.1 (primary release) | Alliance formation, membership change, termination **with coded circumstances** | Exact dates | The termination coding is what makes T2's competing risks possible |
| DESTA | Preferential and economic agreements, accession protocols | Signature and entry-into-force dates | Signature-vs-force gap is a direct measure of the penumbra |
| COW IGO v3 | Intergovernmental organisation membership, dead/dormant status | **Five-year intervals for much of the series** | See §11 |
| COW / V-Dem / Polity | Node covariates | Annual | Unchanged from prior work |
| UNGA ideal points, trade, MID | Relations | Annual | Unchanged; coverage audited per year before use |

Target scale: several hundred entities and low thousands of events, against 38 and ~50.

**The signature-to-entry-into-force gap in DESTA is a natural experiment on the penumbra** and should be exploited rather than merely noted. It gives a per-agreement, externally coded measure of how long the administrative shadow is, against which $\Delta^\star$ estimated from U1 can be validated. This is the closest thing to ground truth the programme will have outside synthetics.

## 7. Modelling

Stated deliberately last and deliberately thin. The prior programme's error was to let architecture lead.

The estimand is a discrete-time hazard $h(t \mid \cdot)$, fitted as pooled binary regression over entity-periods with cause-specific outcomes for T2. The comparison ladder, in order, each capacity-matched:

1. Base rates and duration dependence alone
2. Node covariates only
3. **Density-only shortcut probe (U2)** — this is a baseline, not an ablation
4. Graph-free MLP at matched depth, width and head
5. Homogeneous encoder
6. Heterogeneous encoder
7. Temporal encoder over $G_{\leq t}$ rather than $G_t$ alone

**Each rung must beat the one below it under the corrected protocol or it does not appear in the paper's headline.** Given H2 as measured in CLIQUEBAIT, rungs 5 and 6 are at genuine risk, and rung 7 is the only architectural novelty this programme is entitled to propose. If the temporal encoder does not beat the static one, the paper reports a forecasting benchmark with a negative architectural result. That is an acceptable outcome and the manifesto commits to it now.

## 8. Falsifiable predictions

- **P1 — The penumbra exists and is wider than one year.** $\Delta^\star \geq 2$ for alliance-sourced events. *Falsified if the clique contrast for $r^\star$ is already at the non-leaking band at $\Delta = 1$*, which would mean precursor leakage is not a real hazard and §1's central caution is empty.
- **P2 — The penumbra is not unbounded.** $\Delta^\star \leq 6$; the shortcut curve $\mathrm{AUC}_{\text{shortcut}}(\Delta)$ decays monotonically and reaches the non-leaking band within the observable range. *Falsified by a flat curve*, which would mean forecasting does not escape the leak and the reformulation fails on its own terms. **This is the prediction whose failure would end the programme, and it is stated first among the ones that could.**
- **P3 — Forecasting is much harder than detection.** At $\Delta = \Delta^\star$, T1 discrimination lands in $0.70$–$0.85$ against CLIQUEBAIT's corrected detection figure of $0.993$. *Falsified above $0.95$*, which would indicate residual leakage rather than success and must be investigated as such, not celebrated.
- **P4 — Termination is harder than accession.** Cause-specific concordance for T2 falls below T1 discrimination at matched horizon. *Falsified if termination is predicted as well as or better than accession*, which would contradict the prior work's failure and be a substantive finding about coalition dynamics.
- **P5 — Competing risks are not decomposable into a pooled model.** At least one major covariate reverses sign between cause-specific hazards for dissolution and for absorption. *Falsified if pooled and cause-specific models agree on all covariate signs.*
- **P6 — Restatement of CLIQUEBAIT H4.** Models whose horizon-resolved shortcut reliance is high degrade disproportionately under genuine temporal shift, measured across regime boundaries in the event corpus. *Falsified if shortcut reliance and shift fragility are uncorrelated.* This prediction was orphaned in the prior programme when its motivating anomaly dissolved; it is tested here on its own terms.
- **P7 — The graph earns its keep at long horizons or not at all.** The contribution of message passing over the capacity-matched control is larger at $\Delta \geq \Delta^\star$ than at $\Delta = 1$, because near-term events are dominated by covariates and administrative traces while distant ones require structural context. *Falsified if the contribution is flat or decreasing in $\Delta$.* This is the programme's most speculative prediction and the one most likely to fail.

## 9. Protocol additions specific to event history

Beyond inheriting CLIQUEBAIT's protocol in full:

1. **Origin time declared per task.** Immortal time bias is introduced by defining entry at a date the entity could not have been observed. State the origin, the risk set, and the censoring rule for each of T1, T2, T3.
2. **Rolling-origin evaluation.** Not a single temporal split. Fit at successive origins and forecast forward, so that performance is a function of both calendar time and horizon, and so that the coverage-break lesson cannot recur silently.
3. **Discrimination and calibration reported jointly.** The prior work reported a Brier score of 0.109 with acknowledged overconfidence and left it there. Hazard models are used for expected timing, not only for ranking, so calibration is a primary metric here: report time-dependent discrimination alongside calibration slope and integrated Brier score.
4. **Cluster bootstrap over coalitions.** Repeated observations of the same entity across years and horizons are not independent.
5. **Report the horizon triple** $(\mathrm{AUC}(\Delta),\ \mathrm{AUC}_{\text{shortcut}}(\Delta),\ \Delta^\star)$ rather than a headline number at one horizon.

## 10. Deliverables

- Definition of the leakage horizon $\Delta^\star$ and the penumbra, with the signature-to-force gap as external validation.
- UMBRA: the lagged diagnostic suite, released as an extension of the CLIQUEBAIT library, domain-general.
- LEDGER: an annual-resolution event corpus of coalition formations, accessions, exits and terminations with coded termination causes, at an order of magnitude more events than the prior canon.
- Three forecasting tasks with declared risk sets, origin times and censoring rules.
- Cause-specific hazard results for termination, a question the prior literature and the prior model both failed.
- An honest architectural ladder in which every rung had to earn its place.

## 11. Risks and contingencies

**COW IGO's five-year resolution.** Much of the IGO series is observed at five-year intervals, which is incompatible with annual event history. Three options: restrict LEDGER to exactly-dated sources (ATOP, DESTA) and accept a narrower entity population; use IGO only for covariates and context rather than events; or model IGO events as interval-censored, which is correct but adds machinery. **This is the first decision to make and it shapes the whole corpus.** The manifesto's default is the first option, with IGO as context.

**Event scarcity even after scale-up.** Competing risks need adequate events per cause. If absorption events number in the low tens, P5 cannot be tested at the intended resolution. Contingency: collapse to two causes (ended vs. superseded) and say so.

**"This is link prediction with extra steps."** It is not, and the rebuttal must be prepared: link prediction asks whether a dyad connects; T1 asks when a state enters a *group* whose composition and internal structure condition the answer, and T2 has no dyadic analogue at all. The point CLIQUEBAIT's predecessor established — that dyadic decomposition falls short of joint scoring — is now load-bearing and should be re-run under the corrected protocol, which the prior programme left undone.

**Single-domain framing at a methods venue.** The real risk of the choice made here. Mitigation is structural, not rhetorical: **the contribution is the instrument, not the application.** U1–U3 operate on any event corpus with a curation source, and the paper must demonstrate this at least on the synthetic testbed with a tunable back-dating parameter, so that the leakage-horizon construct is calibrated rather than merely illustrated in one domain. Without the synthetic component this is an IR paper. With it, it is a methods paper with one deep application.

**The penumbra turns out to be trivially narrow.** Then P1 fails, the reformulation is cleaner than expected, and the paper becomes a forecasting benchmark plus a negative methodological result. Reframe around T2, where the focal-group problem of §5.3 is severe regardless of what $\Delta^\star$ turns out to be.

## 12. Venue

- **International Journal of Forecasting** — the strongest fit and probably the primary target. Event-history forecasting with a methodological core and an evaluation-protocol contribution is squarely what it publishes, and it will not treat one domain as a deficiency.
- **DMKD** — realistic, consistent with the prior paper's placement.
- **KBS** — available again. The objection that ruled it out for CLIQUEBAIT was that it hosted the audited paper; this programme audits nothing.
- **Political Analysis / Journal of Peace Research** — viable if the IR content grows faster than the methodological content. Watch for this drift rather than choosing it deliberately.
- **TKDE** — unlikely with a single domain. Do not target it unless the synthetic component grows into a second pillar.

---

## Appendix: notation

| Symbol | Meaning |
|---|---|
| $\Delta$ | forecast horizon in years |
| $\Delta^\star$ | leakage horizon — width of the penumbra |
| $\omega_r(\Delta)$ | provenance overlap of relation $r$ at horizon $\Delta$ |
| $\phi_r(S)$ | intra-group density of $S$ in relation $r$ |
| $\Pi(S_c)$ | dyads induced by the focal group $c$ |
| $h(t \mid \cdot)$ | discrete-time hazard |
| $r^\star$ | the leaking relation, or provenance set |
| $c$ | a coalition entity |
