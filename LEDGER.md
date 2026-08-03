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

| type | source | population in window | what an entity is |
|---|---|---|---|
| `alliance` | ATOP 5.1 | 70 multilateral (≥3 members), 564 including bilateral | a treaty, identified by `atopid` |
| `organisation` | COW IGO v3 | 491 active | a body, identified by `ionum` |

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
| accession | both | `0 → 1` in membership / `yrent > begyr` | 6,290 (1966+) / 335 multilateral |
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

## 5. Outputs

    data/interim/igo_state_crosswalk.csv     217 IGO columns -> COW codes, validated both ways
    data/ledger/entities.parquet             registry: id, type, source, origin, truncation flag
    data/ledger/events.parquet               id, type, cause, (t_L, t_R], dating stratum, source
    data/ledger/membership.parquet           (entity, state, year, status) for risk sets
    data/ledger/families.csv                 membership-equivalence families, the resampling unit
    data/ledger/same_instrument.csv          hand-verified ATOP <-> COW IGO links, short

## 6. Open before the first fit

1. **ATOP `termmode`/`termcaus` crosswalk.** Blocked on a codebook this network cannot reach.
   Until then ATOP terminations are causeless and no pooled cause-specific number is reported.
2. **`same_instrument` list**, hand-verified from the 178 candidates. Membership overlap is the
   shortlist, not the answer.
3. **Left-truncation audit** — how many entities in each type enter under truncation, and what
   fraction of T2's risk-set exposure they carry.
4. **Observer-status coverage** — associate and observer codes exist, but their coverage across
   years has not been verified against the materialised file, and PROTOCOL §1 says documentation
   is not evidence.
