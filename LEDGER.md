# LEDGER — the event corpus

Declared before construction, because §9.1 requires the origin, the risk set and the censoring
rule stated per task, and because a corpus whose definitions are written after the first fit is
a corpus whose definitions were chosen. Every count cited here comes from
`scripts/audit_corpus_scale.py` or `scripts/detect_entity_overlap.py`.

Window: **1946–2014.** The upper bound is COW IGO's last year and therefore the last year any
event is observable; the lower bound is the observation graph's. §6's relations run to 2016 for
three of four, which buys nothing here because the events stop first.

---

## 1. Entities

### 1.1 Two entity types, one registry, no merging

| type | source | population in window | what an entity is | built |
|---|---|---|---|---|
| `alliance` | ATOP 5.1 | 70 multilateral (≥3 members), 564 including bilateral | a treaty, identified by `atopid` | v1 |
| `organisation` | COW IGO v3 | 491 active | a body, identified by `ionum` | v1 |
| `agreement` | DESTA v02.03 | 903 base treaties | a preferential or economic agreement, identified by `base_treaty` | **deferred** |

**Why `agreement` is deferred rather than dropped.** DESTA contributes no entity terminations at
all (§2.2), so T2 is unaffected by its absence, and its 208 accession events are 3 % of COW IGO's
6,115. What it does contribute is unique — the whole of dating stratum 2 and the
signed-but-never-in-force negatives — and both are consumed by U1 validation, which cannot run
until the corpus exists. It also needs its own crosswalk with its own validation: DESTA keys
states by ISO numeric code, of 204 distinct parties 179 match COW by name and 25 do not, and nine
of those are **not COW system members at all** — Cook Islands, Faroe Islands, Greenland, Hong
Kong, Macao, Montserrat, Niue, Palestinian Territories, Western Sahara. Those are trade parties
that are not states, and they must be excluded from the risk set explicitly rather than
force-matched onto whichever state administers them. Its files are also cp1252, not the latin-1
the other sources need, which silently corrupts an apostrophe in three country names. Building
that halfway to keep the corpus on schedule is the kind of shortcut this programme exists to
find in other people's work.

The prior canon's mistake is not repeated: it held NATO as six entities — `NATO_founding`,
`NATO_15`, `NATO_16_GFR` and so on — one per membership composition, which is what a detection
formulation produces when it has no notion of when a group came into being. Here NATO is **one**
entity with accession events, and its composition is a function of time rather than an identity.

### 1.2 Entity identity is not membership, and this was measured rather than assumed

The obvious deduplication rule — same members, same coalition — fails, and it fails in the
direction that would have destroyed the corpus. Matching ATOP multilateral treaties against COW
IGO organisations on mean Jaccard of member sets over shared years gives 178 candidate pairs at
$J \geq 0.6$, seven of them at $J = 1.000$. But the structure is many-to-many: **27 treaties
match more than one organisation and 41 organisations match more than one treaty**, and the
extremes are not marginal — one ATOP treaty matches **24** organisations, another 20, another 16.

Reading which ones settles it. The 24-match treaty is inter-American, and its matches are the
Pan-American Union/OAS, the Pan-American Health Organization, the Inter-American Children's
Institute, the Inter-American Defense Board, the Inter-American Commission of Women, the
Permanent Association of Pan-American Highway Congresses, the Central Pan-American Bureau of
Eugenics. The 16-match treaty is European, and its matches are the European Union, the European
Training Foundation, the European Monetary Institute, the European Foundation for the
Improvement of Living and Working Conditions.

These are not duplicates. They are a **family**: many bodies over one membership. A
deduplication rule on membership would collapse the entire Pan-American system into a single
entity and delete precisely the variation T2 exists to explain — organisations with identical
members and different fates.

**Rule.** No automatic deduplication. `alliance` and `organisation` entities coexist in the
registry. A `same_instrument` link between one of each is asserted only on **instrument-level**
evidence — the ATOP treaty being the founding instrument of the organisation — verified by hand,
and the resulting list is short, printed in full, and reviewable. Membership overlap is
evidence for looking, never evidence for merging. Anything not on the list is two entities, and
any T1 or T2 statistic that pools the two entity types reports the double-count exposure
alongside it.

### 1.3 The resampling unit is the family, not the entity

Membership-equivalence is the wrong tool for identity and the right tool for dependence.
Clustering organisations at $J \geq 0.90$ over at least five shared years gives **31 families
covering 107 of 491 organisations** — a fifth of the corpus. Within a family, pairs of deaths
fall within two years of each other **26.9 %** of the time (7 of 26) against **10.1 %** for
random pairs from the same population: an enrichment of **2.66×**, nominal one-sided
$p = 0.013$. The nominal $p$ is anti-conservative because pairs inside a family share entities,
so this is suggestive rather than settled — but it points one way only.

**Rule.** The primary cluster-bootstrap unit for T2 is the **family**, with a singleton family
being an entity on its own; entity-level resampling is reported alongside as the
anti-conservative comparison. This supersedes the pre-specification recorded as C4, and the
direction is why it is legitimate: family-level resampling can only widen intervals, and moving
to a more conservative unit on discovering dependence is not the same act as moving to a less
conservative one on discovering an inconvenient interval. Recorded as C13.

---

## 2. Events

### 2.1 Types

| event | entity type | source field | count in window |
|---|---|---|---|
| founding | both | `sdate` / `begyr` | 304 organisations (1965+), 564 treaties |
| accession | both | `0 → 1` in membership / `yrent > begyr` | 6,115 (1966+) / 335 multilateral |
| exit | both | `1 → 0` / `yrexit` | 901 (1966+) / 756 |
| termination | both | `dead`/`integrated`/`replaced` / `endyr` | **157** organisations / 26 multilateral treaties |

### 2.2 Termination causes, and why they come from one source

COW IGO codes three mutually exclusive causes — `integrated` and `replaced` are modes of `dead`
rather than alternatives to it:

| cause | 1946+ | 1965+ | dating |
|---|---|---|---|
| dissolution | 103 | 84 | **rule-assigned** (§3, stratum 4) |
| replaced by a successor | 32 | 30 | exact |
| absorbed into an existing body | 22 | 20 | exact |

ATOP codes termination on its own vocabulary, `termmode` (7 values) × `termcaus` (9 values), and
**that vocabulary cannot be interpreted here**: the codebook is at `atopdata.org`, which refuses
the TLS handshake from this network, as CLIQUEBAIT also found. Until it is obtained by other
means, ATOP contributes terminations as *events without causes*.

**Consequence, stated plainly.** T2's competing-risks estimation rests on COW IGO's 157 coded
events alone. That is not a loss — it is 6× ATOP's multilateral supply — but it means the
cause-specific results are organisation results, and §11's heterogeneous-$r^\star$ note applies
to them: the leaking relation for an organisation is co-membership, not alliance edges. No
pooled cause-specific number may be reported before the ATOP crosswalk exists (C10).

---

## 3. Dating strata

§9.6 and §9.7 require these declared per event. There are four, and the fourth is not a width.

| stratum | meaning | source | volume |
|---|---|---|---|
| 1 `exact` | the source records a date | ATOP `begyr/mo/day`, `yrent`, `yrexit`; COW IGO 1965+; DESTA `entryforceyear` | the majority |
| 2 `bracketed` | two coded dates bound the event, $(t_L, t_R]$ | DESTA signature → entry into force | 1,050 agreements; median width **1 year**, 29.9 % ≥ 2, max 17 |
| 3 `declared_resolution` | the source states its own uncertainty | COW IGO pre-1965: `imputed = 1` on 1,388 organisation-years, and 96 organisations flagged "within 5 years" | pre-1965 only; **zero** imputed organisation-years after 1964 |
| 4 `rule_assigned` | the date is a function of data *after* it | COW IGO dissolution: dead once ten consecutive years have passed without a plenary session | 103 of 157 terminations |

Strata 1–3 differ in the **width** of the interval and all three feed §7's likelihood directly.
Stratum 4 differs in **provenance**: its dates look exact and are not knowable at the time they
name. §7's exactly-dated stratum — the one carrying the $\Delta^\star$ claim — is stratum 1
only. Stratum 4 is reported separately throughout, and $\Delta^\star$ is given with and without
it, because an event whose timestamp consumed ten years of subsequent data cannot be used to
measure how far ahead of an event its traces appear.

DESTA supplies one further class that is not a dating stratum but belongs here because it is
dated: **282 agreements signed from 1946 that never entered into force.** Administrative traces,
no event. They are U1's specificity control (C9).

---

## 4. Task declarations

### 4.1 T1 — accession

- **Unit of observation** — (entity $c$, state $s$, year $t$).
- **Origin** — the later of $c$'s founding and 1946. Entities founded earlier enter under
  **left truncation** and are flagged; their pre-1946 accessions are not in the corpus and no
  duration-dependence term may be fitted as though they were.
- **Risk set at $t$** — states in the COW system at $t$ that are not full members of $c$ at $t$
  and whose membership cell is neither `-9` (missing) nor `-1` (not a system member). Both
  exclusions are tabulated per year, so a coverage defect appears as a shrinking denominator
  rather than as events (C5).
- **Event** — $s$ is a full member of $c$ at $t+\Delta$: COW IGO `0 → 1`, ATOP `yrent`.
- **Not an event** — associate membership (`2`) and observer status (`3`). These are *not*
  accessions, and they are also the single most interesting covariate the corpus holds, because
  seating an observer is exactly the administrative precursor §1 describes. They are carried as
  a time-varying covariate, never as an outcome, and `crosswalk.igo_membership_long(full_only=False)`
  returns them.
- **Censoring** — right-censored at the earliest of $c$'s termination, $s$'s exit from the
  system, and 2014.
- **Declared sensitivity** — reported with and without the first $k$ years of each state's
  system membership, $k$ fixed before fitting, because the decolonisation decades produce
  clustered accessions that are not the decision being modelled (C6).

### 4.2 T2 — termination

- **Unit of observation** — (entity $c$, year $t$).
- **Origin** — founding if in window, else 1946 under left truncation. This is the binding
  constraint of the §11 decision and the reason §9.1 was singled out there: an entity observed
  from 1946 that was founded in 1919 has 27 years of unobserved duration, and treating its
  origin as 1946 would make it look young.
- **Risk set at $t$** — entities alive at $t$, by type.
- **Event** — termination at $t+\Delta$, with cause in {dissolution, replaced, absorbed} for
  organisations and uncoded for alliances (§2.2).
- **Censoring** — right-censored at 2014. Two organisations vanish from the file without a
  termination flag and are treated as censored, not dead, with the choice recorded.
- **Interval censoring** — per §3; stratum 4 held out of the primary $\Delta^\star$ estimate.
- **P5** — tested as dissolution (103) versus superseded (54 = replaced + absorbed), which is
  the contingency §11 already contains rather than an amendment to it (C8). The three-cause
  decomposition is still fitted and reported, descriptively.
- **Resampling** — family-level primary, entity-level alongside (§1.3, C13).

### 4.3 T3 — de novo formation, exploratory

- **Candidate generation** — dense-subgraph and community detection over $G_{\leq t}$, run on a
  graph with the **provenance set already excluded**, and run again without exclusion so the
  difference is reported rather than assumed small. §4's stated mitigation closes the route
  through the canon and leaves the route through the graph open, because $G_{\leq t}$ contains
  the back-dated edges and a density-based generator is therefore enriched for groups about to
  form (C2). The bias enters through the risk set, so excluding $r^\star$ from the features does
  not touch it.
- **Reported as exploratory regardless of outcome**, per §4.

---

## 5. Built — v1, 2026-08-03

`scripts/build_ledger.py`, which validates before it writes and writes nothing on a failure.
Summary in `results/ledger_summary.json`.

| | |
|---|---|
| entities | **573** — 493 organisations, 80 alliances |
| left-truncated | 75 (founded before 1946) |
| terminated / censored | 190 / 383 |
| families | 475, of which **43** hold more than one entity |
| events | **10,556** — 8,243 accession, 1,625 exit, 498 founding, 190 termination |
| dating strata | 9,779 exact, 646 declared-resolution, **103 rule-assigned** |
| termination causes | 103 dissolution, 32 replaced, 22 absorbed, 33 uncoded (ATOP) |
| membership rows | 505,951 — 502,634 full, 1,082 associate, 2,235 observer |
| risk-set exclusions | 190,750 missing cells over 19,335 organisation-years |

Rule-assigned dates are **54.2 %** of all terminations. More than half of T2's event supply is
dated by a rule that consumes ten years of subsequent data, which is why §9.7 exists and why the
$\Delta^\star$ claim rests on stratum 1 alone.

### Two source findings the build turned up

**COW keeps some organisations in the file after their coded death.** The Francophone Agency
(`ionum` 270) is coded dead in 2005, `replaced` by a successor, and its rows run to 2014 with
membership still changing — one accession in 2008 and 622 membership-years after its exit. §4.2
censors an entity at termination, so those belong to the successor and are dropped, counted, and
reported in `dropped_declared`. It is the only entity of 198 whose last observed year exceeds its
`deaddate`, so this is an exception rather than a pattern, and it is handled as one.

**The `-1` code never appears.** The v3 codebook gives `-9` as missing data and `-1` as
state-not-a-system-member for the IGO-year file, and C5 pre-specifies both as outside the risk
set. Materialised, `-9` occurs 190,750 times and **`-1` not once**: state-system membership is
carried by `0` in this file. C5's rule is unchanged and one half of it is inert, which is worth
knowing before someone reads a zero exclusion count as a clean join.

### Outputs

    data/interim/igo_state_crosswalk.csv     217 IGO columns -> COW codes, validated both ways
    data/ledger/entities.parquet             registry: id, type, origin, truncation, family, exit
    data/ledger/events.parquet               id, type, cause, (t_L, t_R], stratum, knowable_from
    data/ledger/membership.parquet           (entity, state, year, status) for risk sets
    data/ledger/families.csv                 membership-equivalence families, the resampling unit
    data/ledger/riskset_exclusions.parquet   per organisation-year missing / not-system counts
    data/ledger/same_instrument.csv          hand-verified ATOP <-> COW IGO links — not yet built

## 6. The observation graph

Built by `scripts/build_graph.py` into `data/graph/`; coverage in `results/graph_coverage.json`.
Four relations are CLIQUEBAIT's rebuilt canonical edges, reused unchanged. The fifth does not
exist in the prior work and has to, because §11 makes $r^\star$ depend on entity type.

| relation | source | edges 1965–2014 | mean density | mean edges/yr |
|---|---|---|---|---|
| `igo_comembership` | built here, COW IGO v3 full members | 717,950 | **0.9954** | 14,359 |
| `trades` | IMF IMTS, CLIQUEBAIT rebuild | 459,768 | 0.6405 | 9,195 |
| `votes_with` | UNGA ideal points, k-NN k=30 | 148,834 | 0.2297 | 2,976 |
| `allies` | ATOP v5.1 defence pacts, CLIQUEBAIT rebuild | 49,118 | 0.1536 | 982 |
| `conflicts_with` | COW MID 5.0 | 2,526 | 0.0398 | 50 |

### 6.1 An undeclared coverage hole at 1964

`votes_with` carries **zero edges in 1964**, the only such year in 1946–2016, and CLIQUEBAIT's own
rebuilt `graph_1964.pt` confirms it by shipping three edge types instead of four. Its `FINDINGS.md`
§4 declares the trade gap at 1946–47 and the conflict gap at 2015–16 and does not declare this
one — because it falls in the training period, where nobody was looking. Found here by applying
that programme's own rule to its own artefact.

The likely explanation is substantive rather than defective: the UN General Assembly's nineteenth
session, 1964–65, proceeded without recorded votes during the Article 19 crisis over peacekeeping
arrears, so there are no roll-calls to build ideal points from. **That is stated as the probable
cause, not a verified one** — it has not been checked against the ideal-point release's own
documentation, and it is on the open list below. Either way the consequence for this programme is
identical, because PROTOCOL §3 forbids pooling a ranking metric across it regardless of why the
hole is there.

Regimes, a regime being a maximal run of years over which the set of non-empty relations is
constant:

| years | relations | note |
|---|---|---|
| 1946–1947 | 4 | no `trades`; IMF DOTS begins 1948 |
| 1948–1963 | 5 | |
| **1964** | 4 | no `votes_with` |
| **1965–2014** | 5 | 50 years, the analysis regime |

**The dominant coverage regime and the exactly-dated event stratum begin in the same year.** COW
IGO stops imputing after 1964 and `votes_with` returns in 1965, so 1965–2014 is simultaneously the
longest intact-coverage window and the window where event dates are not block-resolved. That
alignment is luck, not design, and it makes 1965–2014 the primary analysis window with 1948–1963
available as an out-of-regime replication.

### 6.2 Co-membership is saturated, so $\phi$ is generalised to a level ladder

At weight $\geq 1$ the relation has density **0.9954** — very nearly a complete graph, because
with 491 organisations over about 168 states almost every pair shares something. A binary
$\phi_{r}(S)$ is therefore $\approx 1$ for positives *and* negatives, its clique contrast is
$\approx 0$, and the relation carries no discriminative power at all despite being the channel
that must carry the leak for four fifths of the corpus.

Thresholding the dyad weight does not fix it and misleads: density falls to 0.258 at $w \geq 40$
and then **rises** to 0.281 at $w \geq 50$, because the surviving node set collapses onto densely
connected European states and density is measured over surviving nodes. Excluding near-universal
organisations does not fix it either — dropping all 47 whose peak membership share reaches half
the state system leaves density at 0.706, and dropping 87 of them at a 0.3 share still leaves
0.482. The saturation is structural.

**Rule.** Co-membership enters UMBRA as a **weighted** relation, and the density is generalised to
a declared level ladder:

$$\phi_r(S; k) \;=\; \frac{|\{(u,v) \in \Pi(S) : w_r(u,v) \geq k\}|}{|\Pi(S)|}$$

so that "$S$ is a clique in $r$ at level $k$" means every dyad in $S$ shares at least $k$
organisations. At $k = 1$ this is exactly the manifesto's $\phi_r(S)$, so the frozen definition is
generalised rather than contradicted, and `clique_contrast` — the only ranking statistic that
survived all three settings CLIQUEBAIT tested — keeps its meaning. $\Delta^\star$ is reported per
level, and $k$ is a **ladder** rather than a tuned constant, which is PROTOCOL §4's rule about
perturbation budgets applied to a construction parameter. The primary level is fixed on the
synthetic testbed, where §5.1 already requires the non-leaking band to be calibrated, and never
by matching a density to another relation's. Recorded as C15.

Observed weight quantiles over 1965–2014, for choosing the ladder's range: median 25, quartiles
17 and 33, 90th percentile 42, maximum 107.

## 7. Open before the first fit

1. **ATOP `termmode`/`termcaus` crosswalk.** Blocked on a codebook this network cannot reach.
   Until then ATOP terminations are causeless and no pooled cause-specific number is reported.
2. **`same_instrument` list**, hand-verified from the 178 candidates. Membership overlap is the
   shortlist, not the answer.
3. **Left-truncation audit** — how many entities in each type enter under truncation, and what
   fraction of T2's risk-set exposure they carry.
4. **Observer-status coverage** — associate and observer codes exist, but their coverage across
   years has not been verified against the materialised file, and PROTOCOL §1 says documentation
   is not evidence.
5. **The 1964 `votes_with` hole** — confirm against the ideal-point release's own documentation
   whether the nineteenth General Assembly session is the cause. The handling does not depend on
   the answer; the provenance paragraph §5.4 demands does.
6. **The co-membership level ladder's primary $k$** — to be fixed on the synthetic testbed with
   the back-dating parameter $\beta$, before any $\Delta^\star$ on real data is computed.
