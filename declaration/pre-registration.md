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

### Amendment record

Amended in two rounds and then fixed. The text as first written is commit `410121f`, and every change is recoverable against it.

**Round 1 — 2026-08-02, before any datum was fetched and before any model existed.** Two things forced it.

**The instrument §5.1 named is blind in the range that matters.** CLIQUEBAIT calibrated the clique contrast against a known leakage coefficient and found it perfectly specific and badly insensitive: zero false flags at any $\alpha$, but it *flags* $r^\star$ only from $\alpha \geq 0.7$ while still *ranking* it first from $\alpha \geq 0.2$. A stopping rule built on it alone does not return the smallest $\Delta$ at which leakage is absent — it returns the smallest $\Delta$ at which leakage has fallen below roughly $\alpha = 0.7$. $\Delta^\star$ would be biased low, which makes P1 easier to falsify and P2 easier to confirm: the programme's two headline predictions would be pushed in opposite directions by a documented defect of the measuring device rather than by the world. §5.1 now brackets $\Delta^\star$ between two statistics with opposite error profiles, and P1 and P2 are each tested against whichever bound makes them harder to confirm. The same clause also declares the comparison group, which at a horizon is not the same object it is at zero lag.

**§11's first decision was made, and it went against the default.** The default — restrict to exactly-dated sources, keep IGO as context — was measured against ATOP 5.1 before being adopted, and it fails on its own terms: 52 multilateral alliances entering after 1946 and **26 multilateral terminations**, against the several hundred entities and low thousands of events §6 declares a precondition. T2 is a core task and would not be estimable at any resolution. The objection to IGO was also measured rather than inherited, and it does not survive contact with the materialised file: COW IGO v3 is annual across 1816–2014, its imputation flag is set on 1,388 organisation-years of which **none fall after 1964**, and it carries a per-organisation date-accuracy field. The five-year problem is real, confined to pre-1965 membership dating, and declared by the source itself — which is what makes the third option, interval censoring, available in practice rather than merely correct in principle. §6, §7, §9 and §11 follow.

**Round 2 — 2026-08-03, after the coding rules were read, and confined to what they falsified.** §5.4 requires the paper to state what each source records as the start date, and calls that paragraph load-bearing rather than boilerplate. Doing it found that §4's T2 described a cause structure COW IGO does not have. The source treats renaming, reorganisation and reconstitution as continuity rather than termination, so "transformation of membership beyond recognition" is not an available cause; it does not distinguish dormancy from death but *defines death by dormancy*, through a ten-year rule; and it codes a cause the manifesto failed to name, `replaced`, which is more frequent than the absorption cause P5 is built on. §4 is corrected, and §9 gains a seventh item, because that ten-year rule assigns an event's own timestamp using data from beyond it — which is neither censoring nor the penumbra, and for which the document had no category.

**What round 2 deliberately did not touch.** By this point the event counts and the DESTA signature-to-entry-into-force gap had been measured. No prediction was altered. P1 is left standing although the external anchor §6 nominates now leans against it: the measured gap has a median of one year, against P1's committed $\Delta^\star_{\text{lo}} \geq 2$. The distinction that makes round 2 legitimate and any third round illegitimate is that round 2 corrects claims about what the instruments *contain* — always allowed, and here required by §5.4 — whereas adjusting a prediction to fit a number already seen is the one move that would make the rest of this document worthless.

**Fixed 2026-08-03.** No further amendment. Everything from here goes to `PENUMBRA-OUTCOMES.md`.

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
Each coalition is an entity entering at founding and exiting at termination, right-censored at the end of the window. **Competing risks** are essential and are the substantive contribution of this task. The causes are taken from the sources rather than from intuition, because reading the coding rules changes the list: COW IGO codes an organisation as **dissolved**, as **integrated** into an already-existing organisation, or as **replaced** by a new one, and treats renaming, reorganisation and reconstitution as continuity rather than as termination. So "transformation of membership beyond recognition" is not an available cause, and dormancy is not a separate one — it is what death *means* in that source, through the ten-year rule of §9.7. ATOP codes termination circumstances directly and on its own vocabulary, which must be reconciled with COW's rather than assumed to match. Pooling these into one event type is the standard practice and we expect it to be wrong.

### T3 — De novo formation (exploratory, and labelled as such)
Predicting the emergence of a group that does not yet exist. The risk set problem is unsolved and we do not claim to solve it. The approach is two-stage: candidate generation by dense-subgraph and community detection over $G_{\leq t}$, then hazard estimation over the generated risk set. **This task samples on the dependent variable and suffers immortal-time bias unless the candidate pool is generated identically for formed and never-formed groups.** We state the bias, mitigate it by generating candidates from the graph alone with no reference to the canon, and report T3 as exploratory regardless of outcome. If it does not work, that is reported.

T1 and T2 carry the paper. T3 is a section, not a claim.

## 5. UMBRA: the lagged diagnostic suite

CLIQUEBAIT's diagnostics measure leakage at zero lag. Their extension to horizons is the methodological core of this paper and is domain-general even though it is applied in one domain.

### 5.1 U1 — Leakage-horizon curve
Compute $\omega_{r}(\Delta) = \mathbb{E}[\phi_r(S) \mid \text{event at } t+\Delta]$ over the observation graph $G_t$, for $\Delta = 0, 1, \ldots, 10$, for every relation. Plot against $\Delta$. Report alongside it the clique-contrast statistic $P(\phi_r = 1 \mid \text{event}) - P(\phi_r = 1 \mid \text{no event})$, which CLIQUEBAIT established as the only ranking statistic that survived all three settings tested — $\omega$ alone mis-ranks.

**The comparison group is declared, not assumed.** At a horizon, "no event" is ambiguous in a way it is not at zero lag: a state that accedes at $t+1$ is a non-event for $\Delta = 3$ and already carries in $G_t$ the back-dated traces the statistic is looking for. Every curve is therefore reported against two strata — *never-event*, units experiencing no event anywhere in the window, and *not-at-this-horizon*, the full complement. The first is the estimand; the second is what a naive implementation computes. The gap between them is contamination the horizon formulation introduces and the zero-lag formulation cannot have. CLIQUEBAIT's rule that a contrast is uninterpretable without its negative stratum holds here with the stratum choice also changing what is being estimated.

**$\Delta^\star$ is an interval, bracketed by two statistics with opposite error profiles.** No single statistic can carry it, and the reason is measured rather than supposed: against known $\alpha$, the clique contrast is perfectly specific and insensitive below $\alpha \approx 0.7$, while rank position and $\phi$-alone AUC are sensitive and fire even at $\alpha = 0$, where by construction there is no leak.

- $\Delta^\star_{\text{lo}}$ — the smallest $\Delta$ at which the **clique contrast** for $r^\star$ falls within the band established by known non-leaking relations. It declares the penumbra closed too early, so it is a lower bound.
- $\Delta^\star_{\text{hi}}$ — the smallest $\Delta$ at which $r^\star$ additionally loses top rank under the CLIQUEBAIT triage ranking **and** its $\phi$-alone AUC falls within the band. Both statistics keep firing on relations that merely predict, so this declares the penumbra closed too late, and is an upper bound.

Both bands are set on the synthetic testbed with a tunable back-dating parameter $\beta$, not by eye. Report the pair and its width: $\Delta^\star_{\text{hi}} - \Delta^\star_{\text{lo}}$ is the resolution of the instrument on this corpus and belongs in the results rather than a footnote. Where one figure is needed to *choose* a forecasting horizon, use $\Delta^\star_{\text{hi}}$ — forecasting further out than necessary costs discrimination, forecasting inside the penumbra costs the whole claim.

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
| COW IGO v3 | Organisation founding and death, membership, dead/dormant status | **Annual 1816–2014, with dating precision declared per organisation** | The imputation flag covers 1,388 organisation-years, none after 1964. This is the entity backbone, not context. See §11 |
| COW / V-Dem / Polity | Node covariates | Annual | Unchanged from prior work |
| UNGA ideal points, trade, MID | Relations | Annual | Unchanged; coverage audited per year before use |

Target scale: several hundred entities and low thousands of events, against 38 and ~50.

**The signature-to-entry-into-force gap in DESTA is a natural experiment on the penumbra** and should be exploited rather than merely noted. It gives a per-agreement, externally coded measure of how long the administrative shadow is, against which $\Delta^\star$ estimated from U1 can be validated. This is the closest thing to ground truth the programme will have outside synthetics.

## 7. Modelling

Stated deliberately last and deliberately thin. The prior programme's error was to let architecture lead.

The estimand is a discrete-time hazard $h(t \mid \cdot)$ over entity-periods, cause-specific for T2, and **interval-censored**. An event known only to fall in $(t_L, t_R]$ contributes $S(t_L) - S(t_R)$ to the likelihood; an exactly-dated event is the special case $t_R = t_L + 1$, which recovers pooled binary regression, so the two live in one estimator rather than two. Three kinds of interval enter the same machinery, and that they do is the reason for choosing it: COW IGO's pre-1965 membership dating, DESTA's signature-to-entry-into-force gap, and any event a source codes as a range. Cause-specific hazards for T2 are a multinomial logit over causes and survival on the same likelihood.

**Dating precision is a stratum, not a nuisance.** Date uncertainty and penumbra width are the same kind of object — each is a gap between when a thing happened and when the record says it did — so a $\Delta^\star$ estimated over a corpus that mixes them is not interpretable. Every U1–U3 curve and every headline metric is reported separately for the exactly-dated and the interval-dated stratum. The exactly-dated stratum carries the $\Delta^\star$ claim. The interval-dated one measures how far dating uncertainty alone inflates it, which is a second estimate of the same quantity from an independent direction and a check the single-stratum design could not perform.

The comparison ladder, in order, each capacity-matched:

1. Base rates and duration dependence alone
2. Node covariates only
3. **Density-only shortcut probe (U2)** — this is a baseline, not an ablation
4. Graph-free MLP at matched depth, width and head
5. Homogeneous encoder
6. Heterogeneous encoder
7. Temporal encoder over $G_{\leq t}$ rather than $G_t$ alone

**Each rung must beat the one below it under the corrected protocol or it does not appear in the paper's headline.** Given H2 as measured in CLIQUEBAIT, rungs 5 and 6 are at genuine risk, and rung 7 is the only architectural novelty this programme is entitled to propose. If the temporal encoder does not beat the static one, the paper reports a forecasting benchmark with a negative architectural result. That is an acceptable outcome and the manifesto commits to it now.

## 8. Falsifiable predictions

- **P1 — The penumbra exists and is wider than one year.** $\Delta^\star_{\text{lo}} \geq 2$ for alliance-sourced events. *Falsified if $\Delta^\star_{\text{lo}} \leq 1$*, which would mean precursor leakage is not a real hazard and §1's central caution is empty. The test is against the **lower** bound deliberately: the sensitive statistics would hand P1 a confirmation it has not earned, since they fire on relations that merely predict.
- **P2 — The penumbra is not unbounded.** $\Delta^\star_{\text{hi}} \leq 6$; the shortcut curve $\mathrm{AUC}_{\text{shortcut}}(\Delta)$ decays monotonically and reaches the non-leaking band within the observable range. *Falsified by a flat curve, or by $\Delta^\star_{\text{hi}} > 6$*, either of which would mean forecasting does not escape the leak and the reformulation fails on its own terms. The test is against the **upper** bound, for the mirror-image reason: the insensitive statistic would declare the penumbra bounded while moderate leakage was still present. **This is the prediction whose failure would end the programme, and it is stated first among the ones that could.**
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
5. **Report the horizon triple** $(\mathrm{AUC}(\Delta),\ \mathrm{AUC}_{\text{shortcut}}(\Delta),\ [\Delta^\star_{\text{lo}}, \Delta^\star_{\text{hi}}])$ rather than a headline number at one horizon.
6. **Declare the dating interval per event, with its source.** State for each event whether its date is exact, bracketed by two coded dates, or known only to a resolution the source itself declares, and tabulate the stratum composition of every risk set. A corpus that does not separate these is measuring the curator's filing speed alongside the phenomenon, and cannot tell the two apart afterwards.
7. **Declare where a coded date is a function of later data.** COW IGO marks an organisation dead once it has passed ten consecutive years without a plenary session, so for the largest termination cause the recorded date precedes the point at which the event became knowable, by up to a decade. This is not censoring, and it is not the penumbra: the penumbra is an event's traces reaching *backwards* into the observation window, whereas here the event's own **timestamp** is assigned using data from beyond it. A model forecasting at $t+\Delta$ against such a label is scored against a date that consumed information through $t+\Delta+10$. Report which events carry rule-assigned dates, exclude them from §7's exactly-dated stratum, and report $\Delta^\star$ with and without them. **The general form of this item is the one that matters beyond this corpus:** any curation rule that requires a waiting period before an event can be declared puts the label's timestamp and the label's knowability in different places, and a forecasting benchmark that does not separate them cannot say which it measured.

## 10. Deliverables

- Definition of the leakage horizon $\Delta^\star$ and the penumbra, with the signature-to-force gap as external validation.
- UMBRA: the lagged diagnostic suite, released as an extension of the CLIQUEBAIT library, domain-general.
- LEDGER: an annual-resolution event corpus of coalition formations, accessions, exits and terminations with coded termination causes, at an order of magnitude more events than the prior canon.
- Three forecasting tasks with declared risk sets, origin times and censoring rules.
- Cause-specific hazard results for termination, a question the prior literature and the prior model both failed.
- An honest architectural ladder in which every rung had to earn its place.

## 11. Risks and contingencies

**COW IGO's resolution — decided, 2026-08-02, and the default was rejected.** Three options were open: restrict LEDGER to exactly-dated sources and accept a narrower entity population; use IGO for covariates and context only; or model IGO events as interval-censored, which is correct but adds machinery. **The third is taken.** Both alternatives were measured before being ruled out rather than argued away. ATOP 5.1 after 1946 supplies 52 multilateral alliances and 26 multilateral terminations, so the first two options leave T2 — a core task — with too few events to estimate at any cause resolution, and fail the scale precondition §6 sets. The materialised COW IGO file is annual over 1816–2014 with an imputation flag that is never set after 1964 and a per-organisation date-accuracy field, so the interval structure is declared by the source and does not have to be guessed. §7's likelihood absorbs it, and DESTA's signature-to-force gap enters the same estimator instead of sitting beside it as a validation check.

What this buys and what it costs are both stated now, not after the fact. It buys the entity population and the termination events the programme needs. It costs three things, and each is a live risk rather than a settled one: the machinery itself, which must be validated against the exactly-dated stratum before it is trusted anywhere; **left truncation**, since entities founded before the window's start enter under observation rather than at origin, and §9's first item binds hardest here; and the composition of the accession risk set, which in the decolonisation decades is dominated by new states joining many organisations at once — clustered events that are not the coalition-formation decision the programme means to model and must be handled explicitly rather than counted.

**Heterogeneous leakage across entity types.** A consequence of the same decision. For an alliance entity the leaking relation is the alliance edge, which is what §5.3 is written for; for an intergovernmental organisation it is co-membership, a different channel with a different curation source. $r^\star$ is therefore not one relation across LEDGER, and U1's curves must be computed within entity type rather than pooled. This is the provenance-*set* finding of CLIQUEBAIT recurring one level up: the set is now indexed by entity type as well as by relation.

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
| $\Delta^\star$ | leakage horizon — width of the penumbra, reported as the interval below |
| $\Delta^\star_{\text{lo}}$ | lower bound, from the clique contrast (specific, insensitive) |
| $\Delta^\star_{\text{hi}}$ | upper bound, from rank position and $\phi$-alone AUC (sensitive, non-specific) |
| $\beta$ | synthetic back-dating parameter — how far ahead of an event its traces appear |
| $(t_L, t_R]$ | interval a censored event date is known to fall in |
| $\omega_r(\Delta)$ | provenance overlap of relation $r$ at horizon $\Delta$ |
| $\phi_r(S)$ | intra-group density of $S$ in relation $r$ |
| $\Pi(S_c)$ | dyads induced by the focal group $c$ |
| $h(t \mid \cdot)$ | discrete-time hazard |
| $r^\star$ | the leaking relation, or provenance set |
| $c$ | a coalition entity |
