# Decision log

Design decisions, with the evidence that drove them and the date they were taken. Separate
from `PENUMBRA-OUTCOMES.md`, which reconciles predictions against results; this file records
choices that shape what gets measured at all.

The rule is CLIQUEBAIT's: a decision that cites a number names the script that produced it.

---

## D-01 — Version control, before anything else
**2026-08-02.** The repository is under git from the first commit, and that commit is the
manifesto alone, with no data and no code beside it.

§0's claim is that the predictions mean something because the commitment preceded the
measurement. Until this commit there was nothing to substantiate that, and the amendment in
D-03 would have overwritten the original text irrecoverably. Original pre-registration:
`410121f`.

## D-02 — CLIQUEBAIT is vendored and pinned, not installed
**2026-08-02.** `vendor/cliquebait/` is a byte-exact copy; hashes in `vendor/pin.json`,
rationale in `vendor/VENDORED.md`, checked by `scripts/verify_pin.py`.

CLIQUEBAIT's paper is under review and its code base is not itself under version control, so
an editable install would let an upstream edit change a PENUMBRA number with no record of
which version produced it. That is the defect CLIQUEBAIT documents in the paper it audits
(PROTOCOL §1: five construction details that did not match the released code). The four
governing documents — `PROTOCOL.md`, `MANIFESTO-OUTCOMES.md`, `FINDINGS.md` and the prior
manifesto — are hashed but left in place: PENUMBRA does not execute them, but "inherits the
protocol in full" has to name a version.

## D-03 — §11's first decision: interval-censored IGO, and the manifesto's default rejected
**2026-08-02.** Evidence: `scripts/audit_corpus_scale.py` → `results/corpus_scale.json`.

The manifesto offered three options and defaulted to the narrowest. Both alternatives were
measured before being ruled out.

| | ATOP 5.1, 1946+ | COW IGO v3, 1965+ |
|---|---|---|
| entities | 52 multilateral (70 by member count) | **470** |
| accessions | 335 multilateral | **6,115** |
| terminations | **26** multilateral | 135 candidates, 157 coded 1946+ |
| exits | 756 member-level | 901 |

The accession figure read 6,290 until 2026-08-03 and was wrong; see D-08. The decision does not
turn on it — 6,115 is the same order and the same conclusion — but the figure is corrected here
rather than left standing, because the next number derived from it would not have been so
forgiving.

§6 declares several hundred entities and low thousands of events a **precondition**. ATOP
alone reaches neither, and 26 termination events cannot support competing-risks estimation at
any cause resolution — so the default silently kills T2, which §4 says carries the paper
jointly with T1.

The objection to IGO did not survive the file. The series is annual over 1816–2014 with zero
year gaps; the `imputed` flag is set on 1,388 organisation-years, **none after 1964**; and each
organisation carries a date-accuracy field (303 created 1965 or later, 106 completely
accurate, 96 within five years, 27 accurate with minor uncertainties). The five-year problem
is real, confined to pre-1965 membership dating, and **declared by the source**, which is what
makes interval censoring implementable rather than merely correct.

Consequences taken on deliberately, recorded in §11 and §7: the interval-censored likelihood
must be validated on the exactly-dated stratum before being trusted; left truncation binds
hard, since entities founded before the window enter under observation rather than at origin;
the accession risk set is dominated in the decolonisation decades by clustered events that are
not the modelled decision; and $r^\star$ ceases to be one relation, since an alliance entity
leaks through alliance edges and an organisation through co-membership, so U1 stratifies by
entity type.

~~Unverified and open: `death_candidates_in_era` is last-observed-year, not COW's coded
dead/dormant status.~~ **Closed 2026-08-03, see D-06.** The v3 IGO-year file carries `dead`,
`integrated`, `replaced`, `sdate` and `deaddate` directly — the earlier column listing missed
them because it printed only the tail of a 235-column frame. No cross-version splice was
needed. The coded `deaddate` equals the last observed year in **197 of 198** cases, so the proxy
was sound, and only 2 organisations vanish from the file without a termination flag.

## D-04 — $\Delta^\star$ is bracketed, and the manifesto was amended to say so
**2026-08-02, before any measurement.** Evidence: CLIQUEBAIT `FINDINGS.md` §10, WS3
recalibration table.

§5.1 as first written defined $\Delta^\star$ by the clique contrast alone. That statistic was
calibrated against known $\alpha$ and is perfectly specific and badly insensitive: zero false
flags at any $\alpha$, but it flags $r^\star$ only from $\alpha \geq 0.7$ while ranking it
first from $\alpha \geq 0.2$. A stopping rule built on it returns the smallest $\Delta$ at
which leakage has fallen below roughly $\alpha = 0.7$, not the smallest at which it is absent.

The bias is not neutral between the predictions. A low $\Delta^\star$ makes **P1** ($\geq 2$)
easier to falsify and **P2** ($\leq 6$) easier to confirm, so the two headline predictions
would have been pushed in opposite directions by a documented property of the instrument.
$\Delta^\star$ is now an interval bracketed by the clique contrast below and by rank position
plus $\phi$-alone AUC above; P1 is tested against the lower bound and P2 against the upper,
each against whichever makes it harder to confirm.

Amending rather than annotating was chosen because nothing had been fetched or fitted: the
pre-registration was still genuinely prior, and a document that records a known-broken
instrument and then reports around it is worse than one corrected while correction is free.
The original text remains at `410121f`.

## D-05 — the environment, as found
**2026-08-02.** Python 3.11.8, numpy 2.2.0, pandas 3.0.3, scikit-learn 1.7.0, torch 2.7.0+cu128,
PyG 2.8.0, on an RTX 3070 (8.6 GB) and 16 cores.

No `lifelines`, `scikit-survival` or `statsmodels`. Not treated as a gap to fill by default:
§7's estimand is a **discrete-time** interval-censored hazard, whose likelihood is
$S(t_L) - S(t_R)$ over entity-periods and is a few lines of torch, while those libraries are
built around continuous-time IPCW machinery that would have to be bent to fit. Writing the
estimator directly also keeps the interval-censored and exactly-dated cases in one likelihood,
which D-03 requires. Reconsider only if a specific metric proves genuinely awkward to
implement, and record it here if so.

Network: `correlatesofwar.org`, `designoftradeagreements.org` and `ucdp.uu.se` reachable
through the MITM proxy with `truststore`; `atopdata.org` refuses the handshake, as CLIQUEBAIT
also found, and ATOP is therefore read from the local primary release.

## D-06 — read the coding rules; two clauses of the manifesto did not survive
**2026-08-03.** Evidence: COW IGO v3 codebook §§III.A and III.A(b)–(c);
`scripts/audit_corpus_scale.py`. Manifesto amended round 2, then fixed.

§5.4 says the automated part of UMBRA is triage and the verdict requires reading the coding
rules, and that the resulting paragraph is load-bearing rather than boilerplate. Applied to the
event sources rather than to the relations, it falsified two statements in §4's T2:

- *"COW IGO distinguishes dead from dormant."* It does not. Dormancy is what death **means** in
  that source: an organisation is coded dead once it has gone ten consecutive years without a
  plenary session. There is no separate dormancy code.
- *"transformation of membership beyond recognition"* as a termination cause. The codebook lists
  rename, reorganise and reconstitute as **continuity**, explicitly not termination. The cause
  cannot be measured on this corpus.

It also found a cause the manifesto never named — `replaced`, 32 events from 1946 — which is
larger than the `integrated` absorption cause P5 is built on (22). §4 now states the three
causes the source actually codes.

**The ten-year rule is the substantive finding, and it needed a new protocol item.** For the
largest cause the recorded date precedes the point at which the event became knowable, by up to
a decade. That is neither censoring nor the penumbra. The penumbra is traces reaching backwards
into the observation window; here the event's own timestamp is assigned using data from beyond
it, so a label at $t+\Delta$ encodes information through $t+\Delta+10$. §9 gains item 7, stated
in general form because any curation rule with a waiting period does the same thing, which is
the kind of clause §11's "the contribution is the instrument" mitigation needs.

**Where the amendment window closed.** The event counts and the DESTA gap were measured before
these edits were made, so round 2 was restricted to correcting claims about what the sources
*contain*. No prediction was touched — in particular P1 stands although the measured DESTA gap
has a median of 1 year against its committed $\Delta^\star_{\text{lo}} \geq 2$ (recorded as C7).
The manifesto is fixed as of 2026-08-03 and no third round is legitimate.

## D-07 — DESTA v02.03, and what it does not supply
**2026-08-03.** `data/raw/desta/`, three files from the v02.03 release.

DESTA codes accession (208 entries from 1946) and withdrawal (72) as first-class entry types
alongside base treaties (903), so it supplies T1 events directly. It does **not** code agreement
termination: withdrawal is a member exit. T2's entity events therefore come from COW IGO and
ATOP only, and their two termination vocabularies must be crosswalked before any pooled T2
number is quoted (C10).

Two by-products worth more than they look. The signature-to-entry-into-force gap is now measured
rather than assumed (C7). And 282 agreements were signed from 1946 and never entered force —
units with full administrative traces and no event, which is the specificity control U1 has
otherwise had no way to construct (C9).

## D-08 — one definition of "which columns are states", and the figure it had already spoiled
**2026-08-03.** Caught by `scripts/build_ledger.py` disagreeing with
`scripts/audit_corpus_scale.py` on a number both were meant to produce.

`audit_corpus_scale.py` carried its own list of the IGO file's non-state columns and it had
drifted from the one in `penumbra/crosswalk.py`: it omitted `dead`, `integrated`, `replaced`,
`sdate` and `deaddate`. So `dead` moving from 0 to 1 at a termination was counted as a state
acceding, and the accession figure came out **6,290** instead of **6,115** — 175 phantom
accessions, one per organisation that died in the era.

Three things worth recording rather than just fixing.

The defect is **two definitions of one thing**, not a typo, and the fix is that `IGO_META` now
lives in `penumbra/crosswalk.py` and is imported. This is the same class of error CLIQUEBAIT
documents in the benchmark it audits: five construction details that did not match the released
code, found only because someone recomputed them.

It was caught by **cross-checking two independent code paths against each other**, not by review.
The wrong number is entirely plausible — right order, right shape, wrong by 3 % — and no reading
of the script would have flagged it. `exits` was unaffected and matched at 901 in both paths,
which is itself the tell: `dead` goes 0 to 1 and never back, so only accessions could inflate.

The **frozen manifesto does not cite it.** §0's amendment record quotes ATOP's 52 alliances and 26
terminations and no accession count, so the pre-registration is unaffected and no clause needs
reinterpreting. The figure appeared in D-03's decision table and in LEDGER.md; both are corrected
in place with the old value named. The §11 decision does not turn on it — 6,115 is the same order
and the same conclusion — but the correction is recorded because the next quantity derived from it
would not have been so forgiving.

## D-09 — the synthetic testbed gets a back-dating axis, and it graded the estimator
**2026-08-03.** `penumbra/synthetic.py`, `penumbra/umbra.py`,
`scripts/calibrate_delta_star.py` → `results/delta_star_calibration.json`.

CLIQUEBAIT's generator has a leakage coefficient and measures at zero lag. PENUMBRA calibrates a
**horizon**, so the generator gains $\beta$: how many steps before an event its traces appear.
Leakage enters as a displacement of what $r^\star$ believes the membership to be — $r^\star$'s view
is the truth shifted $\beta$ steps earlier, which is §1's accession protocol signed before it takes
effect rather than an abstraction of it. The target follows from the definition and was fixed
before the run: traces exist for $\Delta \leq \beta$, so $\Delta^\star = \beta + 1$.

Two invariances, both inherited as hard constraints and both verified. **Density**: $r^\star$'s
density is identical across the whole $\alpha \times \beta$ grid, range $0.0$ to eight decimals.
**Completeness**: realised completeness equals $\alpha$ everywhere, maximum deviation 0.0004, with
the edge budget never clamped. The second is the one the design could have lost. Back-dating
enlarges the pool of eligible dyads, so a fixed budget split among all open windows would sample
each coalition more sparsely at higher $\beta$ and degrade the clique property — confounding
$\beta$ with the very thing `clique_contrast` measures. Defining $\alpha$ as completeness rather
than budget share keeps the axes orthogonal, and the budget is sized once from the worst-case year
over the whole sweep (1,568 dyads at $\beta \leq 10$, hence density 0.09) so that $\alpha = 1$ can
mean complete.

Three defects surfaced, in falling order of how badly they would have gone unnoticed.

**The band was a knife edge.** Set at the anchors' point estimate it returned "never reached" at
every $\beta$, on a corpus where the signal collapses exactly on cue. Bands are now derived from
sampling noise — a Clopper-Pearson upper limit for zero successes at the observed positive count,
and the null SD of AUC — so nothing is chosen by eye, which is what §5.1 demands.

**The anchors were structurally wrong**, and this is the finding worth the most. Relations with no
group mechanism sit at a clique rate of exactly zero; a relation that records the present honestly
still shows about 0.05. The band was an order of magnitude too tight and $\Delta^\star_{\text{lo}}$
overshot. Fixed by adding `r_current` — same construction, same completeness, $\beta = 0$ by
declaration. C17 carries the pre-specification this forces on real data.

**The anchors also have to be density-matched.** At $r^\star$ density 0.09 against anchors at 0.06,
$r^\star$ ranked top at every horizon on density alone and the sensitive bound never fired.
CLIQUEBAIT established that $\omega$ over-ranks dense relations; the clique rate inherits it.

Outcome: $\Delta^\star_{\text{lo}}$ recovers $\beta + 1$ in **6 of 6** settings. The upper bound
fires in 2 of 6 and is otherwise unreachable, which was flagged as a risk before any measurement
and is now demonstrated as a property of the definition. C18 fixes how P2 is read when that
happens, and the answer is not "falsified".

## D-10 — the provenance declaration §5.4 demands, and what reading it changed
**2026-08-03.** `scripts/parse_igo_provenance.py` → `results/igo_provenance.json`;
declaration in `PROVENANCE.md`.

PROTOCOL §1 must precede §2 and §3, so this ran before any real-data $\Delta^\star$. The v3 short
codebook carries the warning without the evidence — members are sometimes dated by accession or
signature, "these exceptions are listed below (see section IV)", and section IV is not in it. The
list exists only in the **v2.1** codebook, 93 pages of per-organisation notes. Parsed to exactly
the **495** records the codebook states, which is the check; two parse artefacts were sentences
inside notes opening with a year and a period and are named in the output rather than filtered
away.

**The finding is a negative one and it matters more than a positive would have.** Five of 495
organisations mention signature or accession dating. Reading all five: one back-dates membership
(the Oil Pollution Compensation Funds, "members coded according to first convention signed"), one
back-dates the founding only, one **explicitly refuses** to back-date (the Tropical Timber
Organization: treaties signed 1985, `formed` coded 1987), one is forward-dated, one is about
emanation status. So signature back-dating is not the mechanism by which a penumbra would appear in
the relation that carries $r^\star$ for 490 of 562 entities. If the penumbra is there it comes from
elsewhere, and if it is not, P1 is in trouble for a reason we now understand rather than a reason we
would have guessed at.

**Coverage disagrees with the documentation in both directions.** Over the 486 organisations in
both: 18 declare missing years the data does not carry as `-9`, and **45 carry `-9` in 205
organisation-years the documentation never mentions**. The second is the case PROTOCOL §1 is written
against, and it is the same defect class CLIQUEBAIT found in the benchmark it audited — undeclared
coverage, discovered only by recomputation. A further 48 of v3's 534 organisations have no notes at
all, having been added after v2.1.

**Dormancy is textual.** 16 organisations carry *inactive* or *dormant* in prose with no variable
recording it, which corroborates D-06 rather than softening it.

**C17's anchor list, as far as the evidence goes:** `trades`, `conflicts_with` and `votes_with`
outside 1964 are eligible — a reporting-year flow, a dispute onset and a roll-call cannot
anticipate an accession. `allies` is **undecided**, blocked on the unreachable ATOP codebook, so it
cannot serve as a declared anchor yet. `igo_comembership` is $r^\star$, not an anchor. The band is
fixed here, before the curve is computed, which is the only order in which either means anything.

## D-11 — U2 on real LEDGER, and the two performance fixes it needed first
**2026-08-03.** `scripts/run_u2.py` → `results/u2_real.json`; verdict in
`PENUMBRA-OUTCOMES.md` V1.

The first attempt ran for over two minutes on two horizons and was stopped rather than waited out,
because the cost was in two avoidable places: the negative sampler rebuilt a Python set of the
member list on every draw, and every candidate rebuilt the graph-index array behind its star of
dyads, once per relation per level. Both are now precomputed per entity-year. The UN carries 193
members, so those two lines were the difference between minutes and hours.

The optimisation is exact rather than approximate and was checked as such: a candidate group's
dyads decompose into the member-only dyads, shared by every candidate for the same entity-year and
therefore cacheable, plus the star from the acceding state, which is not. `phi_candidate` was
verified against the naive `phi` over 300 rows × 5 relations × 2 levels with **zero**
disagreements, before and after the change. A cache that is nearly right would have moved every
number in V1 by an unknown amount.

One reporting mistake worth recording so it is not repeated: the long runs were piped through
`tail`, which buffers, so no interim progress was visible and liveness could only be confirmed by
looking at the process. Long runs should not be piped.

## D-12 — U2 is reported at multiple probe capacities, because it can invent a penumbra
**2026-08-03.** Evidence and the capacity table are in `PENUMBRA-OUTCOMES.md` V1d.

The out-of-regime replication looked like it supported P2 where the primary regime falsified it: the
boosted probe decayed 0.143 across nine horizons against the primary regime's 0.024. The decay
turned out to scale with probe capacity -- 0.058, 0.116, 0.143 at 30/2, 100/2 and 300/3 trees and
depth -- while the linear probe stayed at 0.041. In the primary regime the same sweep gives
0.030, 0.031, 0.024: capacity-invariant, and matching the linear probe's 0.029.

The reason this is a protocol matter and not a tuning note is that the positive count necessarily
falls with horizon, since an event at t+D needs an origin at t. A high-capacity probe therefore
always overfits more at long horizons than at short ones and produces a decaying curve whatever
the leakage is. The confound is in the shape of the diagnostic, and it runs in the direction that
confirms the hypothesis being tested.

Every U2 figure is therefore reported at three or more capacities plus the linear probe, and a
decay that moves with capacity is reported as an artefact. This also bounds an inherited rule:
CLIQUEBAIT's "use a non-linear probe for D1" is sound at zero lag, where the sample does not
shrink, and becomes a penumbra generator when carried into a horizon-resolved setting without that
caveat.

## D-13 — the primary co-membership level is fixed at k = 25, declared before U1 runs
**2026-08-03, before any real-data $\Delta^\star$ exists.**

LEDGER.md §6.2 makes co-membership a weighted relation on a level ladder and says the primary level
must be fixed "on the synthetic testbed ... and never by matching a density to another relation's".
The synthetic testbed cannot do it yet: its $r^\star$ is binary, so it has no level structure to
calibrate against, and adding one is open work.

That leaves a real hazard. $\Delta^\star_{\text{lo}}$ will come out differently at different $k$, and
choosing $k$ after seeing which value gives which answer would be indistinguishable from choosing
the answer. At $k = 1$ the relation is saturated at density 0.995, so positives and negatives are
both cliques, the clique contrast is ~0, and $\Delta^\star_{\text{lo}}$ would come back as 1 and
falsify P1 for a reason that is purely an artefact of a binary reading.

**Rule, committed now:** the primary level is **$k = 25$**, the median number of shared
organisations over the analysis regime. It is a property of the relation's own weight distribution,
computed before any horizon curve existed (`LEDGER.md` §6.2 records the quantiles: 17 / 25 / 33 / 42),
and it is independent of every outcome. The full ladder (1, 17, 25, 33, 42) is reported as
sensitivity, and $\Delta^\star_{\text{lo}}(k)$ is reported as a curve, because how the leakage
horizon moves with a construction parameter is exactly the sensitivity CLIQUEBAIT's PROTOCOL §1
demands for threshold choices.

**P1's verdict is read at $k = 25$ and at no other level**, whatever the other levels show. If the
ladder disagrees sharply with itself that disagreement is the finding and is reported as one.

## D-14 — the negatives were not the declared risk set; V1 withdrawn
**2026-08-03.** Retraction written in `PENUMBRA-OUTCOMES.md` V0 **before** the corrected panel ran.

`accession_panel` sampled negatives by drawing (entity, year) uniformly and then a state. LEDGER.md
4.1 declares the risk set *within* a coalition-year, not across them. Measured at horizon 3:
positive groups averaged 66.4 members, negatives 18.2 -- a 3.7x gap that is structural, since
accessions happen in large active organisations while a uniformly drawn coalition-year is a small
one.

Both diagnostics were invalidated in the same way and in opposite-looking directions. U1's clique
contrast went NEGATIVE for the leaking relation, because a small group clears an all-dyads
condition far more easily than a large one, so the statistic measured size. U2's 0.87 became
uninterpretable, because `size` and `log_size` are in the feature set by the manifesto's own D1
specification and could separate the classes without any information about the candidate state.

Negatives are now drawn from the same (entity, year) as each positive: mean group size 66.4 against
66.4. `matched=False` is kept so the defect can be reproduced on purpose, since a size-confounded
negative stratum is itself worth reporting as a trap for anyone building this diagnostic.

Two things about how it was found. It was not caught by review or by the corpus validation suite,
which checks LEDGER rather than the audit built on it -- it was caught by the *sign* of a statistic
that had no business being negative. And the void verdict pointed in the direction the accumulated
evidence already favoured, which is exactly when a result is least likely to be questioned. The
retraction was written before the replacement numbers existed for that reason.

## D-15 — the two measurements that decided V2, and the one the manifesto does not specify
**2026-08-03.** `results/u2_matched.parquet`, `results/u2_d2_horizon.parquet`; verdict in
`PENUMBRA-OUTCOMES.md` V2 and V3.

**U2 with r* excluded, horizon by horizon.** The manifesto specifies U2 as one probe over all
relations, which cannot separate a decaying leak from ordinary forecasting difficulty -- both
produce a decaying curve, and difficulty is the null. Running the probe with and without r* does
separate them, and it is D2's horizon-resolved analogue. Measured: the anchors alone sit at
0.54-0.57 and decay 0.028, while r* adds 0.200 at horizon 1 falling to 0.095 at horizon 10. So
essentially all the graded signal is in r* and its contribution halves, which is neither
difficulty nor -- given the provenance -- an administrative shadow. This exclusion contrast is now
part of every U2 report.

**Clique power by group size.** The exact-clique contrast is 0.20-0.25 below twenty members, 0.047
at 21-40, 0.010 at 41-80 and identically 0.000 above eighty, where 2,056 of 5,639 positives live. A
90-member coalition has 4,005 dyads and a clique needs all of them, so the statistic is not weak
there, it is zero. The pooled 0.058 is a small-coalition subpopulation. This bounds the statistic
CLIQUEBAIT chose on the grounds that it "survived all three settings tested": none of those settings
had this size distribution, the protein benchmark's median complex being 3 against LEDGER's mean
positive stratum of 66. Clique contrasts are reported stratified by size from here on, with the
share of the corpus at zero power stated.

## D-16 — the likelihood was verified by closed-form tests, not by review
**2026-08-03.** `penumbra/hazard.py`, `scripts/test_hazard.py`.

Independent review of the interval-censored competing-risks derivation was attempted twice and both
workflows died on the session limit with nothing recoverable (237k and 279k subagent tokens, zero
findings). Subagents are unusable in this session, so the derivation was done directly and checked
against properties that must hold by algebra. That is a different guarantee from a reviewer, not a
weaker one: a failing property localises the error, whereas a reviewer might only doubt it.

Seven checks, all passing:

- the exact-event case equals pooled binary regression over entity-periods to 2.8e-14, which is the
  reduction section 7 asserts;
- an interval of width one reduces to the exact term exactly, which is the off-by-one check against
  the corpus convention t_L = y-1, t_R = y;
- the cause-specific interval term summed over causes equals S(t_L) - S(t_R) exactly, so the two
  branches of the likelihood agree;
- a constant hazard is recovered (0.1518 fitted against 0.1518 empirical, 0.15 true);
- a row preceding its entity's entry raises rather than being trimmed, because immortal time
  (section 9.1) in a trimmed panel looks correct and in a refused one gets investigated;
- the determinacy rule behaves at an origin, including the straddling case;
- events-per-parameter reproduces C8's bound -- 22 absorption events support zero covariates at ten
  per parameter, which is why P5 is tested on the collapsed contrast.

**Two rules the manifesto leaves open, decided here.** Interval censoring forces both and they share
one principle: assess only what is determined. At origin o an entity whose interval straddles o is
neither a positive nor a negative and is excluded with the count reported (`determined_at`), which
closes the section 9.2 rolling-origin hole. Calibration under interval censoring is assessed on the
same determined subset, with the undetermined share reported rather than imputed
(`calibration_at`), which is how section 9.3's demand for calibration as a primary metric becomes
implementable. Rule-assigned dates need nothing in the likelihood and everything in the evaluation:
a date assigned from ten years of later data cannot score a forecast made before it was knowable,
so those 103 terminations are excluded from rolling-origin evaluation rather than from estimation.

## D-17 — the likelihood is vectorised, and the rewrite is proved equal to the verified one
**2026-08-03.** `penumbra/hazard.py`, `scripts/test_hazard_fast.py`.

T1's unit is the (coalition, state) dyad and there are of order 10^5 of them, so the reference
implementation's Python loop over entities would need millions of iterations per L-BFGS gradient.
The rewrite is segment operations over rows sorted by (entity, period).

Replacing verified code with faster code is only safe if the two are shown to agree, so both value
and gradient are compared across six panel shapes exercising every branch -- one cause and several,
exact and interval events, with and without left truncation, and cause-unknown intervals -- plus a
check that a fit through the fast path is scored identically by the reference path. Worst
disagreement: 4.6e-13 on the likelihood, 2.3e-13 on the gradient. The closed-form checks of D-16
still pass through the new path.

## D-18 — T1 reports two AUCs, because one of them would repeat V0's mistake
**2026-08-03.** `scripts/run_t1_ladder.py`; results in `PENUMBRA-OUTCOMES.md` V5.

The first ladder run reported only the pooled AUC over the whole risk set at each origin, which gave
rung 2 a score of 0.79-0.91 -- above U2's density-only 0.766. Comparing those two would have been
the V0 error again with a better excuse: U2's negatives are matched within a coalition-year, while
the pooled T1 evaluation lets the model win on which coalitions grow and which states are joiners.

Both are now reported. The pooled metric is the right one for §4's forecasting question, which is
genuinely pooled. The within-coalition metric holds the coalition fixed and asks only which
candidate state accedes, which is the quantity comparable to U2 and to U1's contrasts. They differ
by about 0.25, and the gap is a result rather than a nuisance.

It also changes a ladder verdict. Rung 3's densities beat rung 2 by only +0.0096 pooled -- marginal
enough that an inattentive application of §7's rule might have dropped them -- but by +0.0393
within-coalition, four times larger, and in 16 of 16 cells. Node covariates answer which coalitions
grow; densities answer which state, for this coalition. Reporting a single number would have
obscured which question each rung was answering.

## D-19 — T2's covariates are pre-specified at four, because 36 was under-identified
**2026-08-03, before any cause-specific coefficient was read.** Evidence:
`hazard.events_per_parameter` on the T2 panel.

The T2 panel was first built with 36 covariates -- size, six node covariates in mean and standard
deviation, five relation densities, and missingness indicators. It fitted without complaint and the
fit is worthless: with 83 dissolution, 30 replaced and 20 absorbed events against 38 parameters per
cause, events per parameter are **2.18, 0.79 and 0.53**. At the conventional ten per parameter the
three causes support 6, 1 and 0 covariates. The 36-feature fit is not reported.

Reducing the feature set by looking at which covariates came out significant would be the garden of
forking paths, so the four are chosen on substantive grounds and named here before any coefficient
was inspected:

1. **log size** -- the most basic structural property of a coalition;
2. **internal co-membership density** at the D-13 primary level -- §5's own group-level statistic,
   and the cohesion measure the programme is about;
3. **mean member polity2** -- the standard regime-type covariate in this literature;
4. **standard deviation of member polity2** -- regime *heterogeneity*, which is the standard
   argument for why coalitions break up, and the covariate most likely to behave differently across
   causes, which is what P5 is about.

At four covariates plus intercept and baseline the collapsed model has 13.8 events per parameter for
dissolution and 8.3 for superseded, which is at or near the convention. The three-cause model is
still fitted and reported descriptively, and its absorption arm is explicitly labelled as
under-identified rather than presented as an estimate.

## D-20 — a labelling slip in a diagnostic script, caught and stated
**2026-08-03.** The focal-exclusion comparison script read `mod.coef_[0, 2]` as the co-membership
coefficient. The coefficient columns are [intercept, log_duration, log_size, phi, polity2_mean,
polity2_std], so index 2 is **log_size** and the column printed as `beta_phi` was log_size
throughout. The model was unaffected -- the preceding run printed the full table with proper column
names and phi is +0.255 there -- but the diagnostic's third column was mislabelled and would have
been quoted as a coefficient it is not.

Caught by the value: -0.402 in the "phi" column exactly matched log_size in the earlier table. The
loglik and AUC columns of that comparison are unaffected and are what V6 reports; the coefficient
column is not reported from that script at all.

Recorded because indexing a coefficient matrix by position rather than by name is the class of error
that produces a plausible number attached to the wrong variable, which no amount of reading the
output would reveal.

## D-21 — P6's verdict is reported as falsification AND reversal, because its wording covers only one
**2026-08-03.** `scripts/run_p6.py`; verdict in `PENUMBRA-OUTCOMES.md` V7.

P6 says it is "falsified if shortcut reliance and shift fragility are uncorrelated". At rho = -0.529,
p = 0.116 over ten models they are uncorrelated at any conventional level, so it is falsified. But the
spread is large -- 0.172 in reliance, 0.062 in fragility -- so this is not the immaterial case
CLIQUEBAIT's H5 lesson warns about, and the sign is negative: the two most shortcut-reliant models
perform BETTER out of regime than in it. P6's wording is silent on that case, which is simultaneously
a falsification and a reversal of the mechanism the manifesto assumes.

Both are reported. Folding the reversal into "uncorrelated" would discard the informative half, and
the verdict logic in the script has a branch for it that was written before the numbers existed.

The reversal is explained rather than left as a curiosity: co-membership density is 0.9704 in
1948-1963 against 0.9954 in 1965-2014, with 116 organisations per year against 273. The relation is
less saturated in the earlier regime, so density features carry more information there, which is
exactly where the density-only models improve.

That generalises into a finding about the diagnostic. **Shortcut reliance is not a property of a
model.** It depends on how saturated the leaking relation is in the regime the model is evaluated in,
and saturation drifts with the size of the institutional population. H4 in the prior programme and P6
here both treat a model-times-regime interaction as a model attribute, which is why neither could be
made to work.

## D-22 — the alliance r* verdict was rejected after the rule returned it
**2026-08-03.** `scripts/run_u1_alliance.py`; verdict in `PENUMBRA-OUTCOMES.md` V8.

The pre-specified rule returned Delta*_lo = 3 and Delta*_hi = 10 on the manifesto's original r*,
which reads as P1 holding and P2 falsified. Both were rejected, and the check that rejected them was
run before either was written down anywhere.

The clique contrast's standard error -- a difference of two proportions at 111-180 positives and a
clique rate near 3% -- is 0.012 to 0.017, the same magnitude as the contrast itself (0.014-0.032). No
horizon puts the contrast significantly above the band; the only |z| > 2 is at horizon 10 and is
negative, which is the in-band direction. And the contrast is not monotone: it falls, rises, falls,
rises. Delta*_lo = 3 is where two noise-floor series cross.

Power, concretely: separating a contrast of 0.03 from a band of 0.01 needs a standard error near
0.007, which is roughly 600 positives per horizon against the 111-180 available.

Recording this as a decision rather than only as a verdict, because the failure mode it avoids is the
one this project is about. The rule was pre-specified in D-13 and applied correctly; a pre-specified
rule applied to an underpowered sample still returns a number, and that number looked like the
programme's headline prediction finally holding. Accepting it would have been defensible on process
grounds and wrong on the evidence.

## D-23 — a consistency checker, because staleness bit three times
**2026-08-03.** `scripts/check_consistency.py`.

Three times in this programme a document has quoted a number the pipeline no longer produced: the
status header of `PENUMBRA-OUTCOMES.md` drifted twice, and 6,290 stood in two documents after the
audit was corrected to 6,115 (D-08). None was caught by reading. The last was caught only because a
second code path disagreed with the first.

The checker pairs each load-bearing claim with the artefact that produces it and fails when they
disagree, plus two cross-document agreement checks and a guard against the retracted 6,290
reappearing outside its correction note.

It earned its keep on the first run, and what it found is instructive: `results/ledger_summary.json`
still carried 10,528 events while `LEDGER.md` said 10,556. The **document** was right. After V4's
observer fix I ran `build_ledger.py --dry-run`, which validated and wrote nothing, and updated the
table by hand from the console output. So the source of truth was stale and the prose was current --
the reverse of the failure I was guarding against, and invisible to any check that trusts the results
files. Corrected by writing the corpus for real.

The other two failures were mine in the registry rather than in the documents: DESTA counts are
asserted in OUTCOMES and LEDGER, not in PROVENANCE, which states dating conventions rather than
counts. Fixed by correcting the pairing rather than padding the document, since a claim registered
against a document that never made it produces a failure that teaches nothing.

## D-24 — three performance guesses in a row, none of them measured first
**2026-08-03.** `scripts/run_p7.py`.

Recorded because it is the same failure this programme documents in other people's work, applied to
my own code rather than to a scientific claim.

The neural ladder was too slow, and I changed it three times without profiling.

1. **Negative subsampling in training.** Correct, and the right first move: the risk set is 0.3%
   positive so nearly every row re-teaches the same absence. Evaluation was pinned to the full risk
   set in the code so a later "optimisation" could not quietly reach it.
2. **Chunking for memory, with `retain_graph=True`.** The encoder is re-run after each optimiser
   step, so every chunk builds a fresh graph and retaining them held alive exactly the peak that
   chunking exists to bound. The fix reintroduced the problem it fixed.
3. **Chunking with the batch builder left inside the chunk loop.** Member arrays were rebuilt in
   Python per chunk and the 2.2M-row frame was rescanned per year: about 2.2M row-iterations per
   pass plus 110M comparisons. This turned a ten-minute budget into a timeout. Everything is now
   computed once per year and cached across epochs, and a chunk is a tensor slice.

One diagnosis did go the right way and is worth separating out: the CUDA out-of-memory was **not**
my code's footprint. Other processes on this machine held 6.6 of 8.2 GB, leaving 1.5. Checking the
device before redesigning avoided a pointless rewrite -- the 2009 snapshot's 59,361 rows and 1.23M
member-index elements are a reasonable load that simply did not fit in what was free.

The lesson is not about tensors. This project applies a strict rule to scientific claims -- V8
rejected a verdict the pre-specified rule had returned, because the standard error was the size of
the effect -- and I did not apply the same rule to statements about my own code. Three guesses cost
more than one profile would have.

## D-25 — the capacity confound was measured rather than argued about
**2026-08-03.** `scripts/run_p7.py --width`; results in `PENUMBRA-OUTCOMES.md` V9.

Section 7 matches capacity on depth, width and head. That does not equalise parameter count:
relation-specific weights cost parameters by construction, so rung 7 carries 1.9x rung 4's 54,849.
The ladder's gains rose monotonically with parameter count, which is exactly the shape a capacity
artefact would have, and exactly the confound CLIQUEBAIT found in the paper it audited -- a weak
baseline made the graph look worth 0.05-0.09 where a matched control gave 0.023.

So the control was widened until its parameter count matched each graph rung. Widths 96 and 128 give
80,993 and 109,185 parameters against rung 6's 78,849 and rung 7's 103,937.

The confound does not explain the gains. Doubling the control's parameters is worth **+0.0009**; the
control is saturated in capacity. Rung 6 keeps +0.0076 and rung 7 keeps +0.0245 against
parameter-matched controls.

Worth recording for a reason beyond P7: this is the first place an inherited CLIQUEBAIT rule has been
applied in full and *not* changed the answer. The rule is not redundant -- it fired hard in the prior
programme -- it simply does not trigger on this corpus. Reporting that as "we checked and it did not
matter" is different from not checking, and the difference is the whole point of a protocol.

One incompleteness, stated rather than smoothed: the width-128 control has four seed-runs across two
launches (0.8627, 0.8608, 0.8622, 0.8610) rather than a single clean three-seed run, because a third
seed hung and was not chased. The four values span 0.002, so the point estimate is not in doubt, but
the run is not as tidy as the others.

## D-26 — DESTA built, and §6's ground truth finally used as ground truth
**2026-08-04.** `penumbra/desta.py`, `scripts/validate_delta_star_desta.py`; verdict V10.

§6 called the signature-to-force gap the closest thing to ground truth outside synthetics and said it
should be exploited rather than merely noted. C7 measured it on 2026-08-03 and left it as a caveat
against P1. Using it as ground truth is what settles what eight verdicts could only circle, so the
`agreement` entity type deferred in LEDGER.md 1.1 was built after all.

**Crosswalk, on CLIQUEBAIT's rule.** 195 ISO numeric codes to 195 COW states, one-to-one, no
collisions. Nine parties are declared **non-COW and excluded with a reason** rather than force-matched
-- Cook Islands, Faroe Islands, Greenland, Hong Kong, Macao, Montserrat, Niue, Palestinian
Territories, Western Sahara. They sign trade agreements and are not states; mapping them onto a
metropole would attribute a territory's trade policy to another country. The builder raises rather
than returning a partial crosswalk.

**Two diagnosis notes worth keeping.** The crosswalk aborted on two parties and I diagnosed it as the
cp1252 encoding. That was half right: accent-stripping *was* a real latent bug -- normalising
"Cote d'Ivoire" deleted the circumflex instead of decomposing it, giving "ctedivoire" -- and fixing it
did not fix these two, because COW genuinely calls them "Ivory Coast" and "Sao Tome and Principe". A
correct fix for the wrong reason, then the actual reason. And one agreement has a gap of **-1**, in
force before signature; recorded as a source anomaly rather than clipped.

**What the ground truth showed, and it was not what §6 expected.** The back-dating is exact:
focal-only trace presence is 1.00 inside the coded gap and 0.00 outside it at every width, so
Delta* = gap + 1 precisely. The pooled relation-level density that UMBRA specifies sees almost none of
it -- contrast 0.102 against a truth of 1.000 -- because the focal agreement's back-dated dyads are
6.8% of a relation saturated by other agreements. The negative control on COW IGO gives beta = 0
directly, confirming PROVENANCE 2's reading from the coding rules.

The operation the manifesto lacks is the mirror of the one it has: 5.3 prescribes focal **exclusion**
to stop the focal group's edges standing in for the label, and detecting the penumbra needs focal
**isolation** of those same edges. Both are needed, for opposite purposes, and only one is in the
document.

## D-27 — UMBRA ships the missing operation, and the library disagreed with the script that found it
**2026-08-04.** `penumbra/graph.py::focal_only_weight`, `penumbra/umbra.py::trace_presence`.

V10 found that the manifesto specifies focal **exclusion** and never focal **isolation**, and that
without isolation the diagnostic cannot measure the quantity it exists to measure. Reporting that
without shipping the fix would leave section 10's deliverable -- UMBRA as a domain-general library --
carrying a known blind spot, so both operations are now exported with the reason attached to each.

Moving the measurement from an ad-hoc script into the library **changed the numbers**, and the library
was right. The script counted every (event, horizon) pair whether or not the entity existed at that
year, scoring the non-existent ones as trace-absent; `trace_presence` skips them, because asking
whether a state is on the record of an organisation that does not yet exist is not a question. The
divergence grows with horizon -- exactly where more entity-years fall outside the entity's life -- and
COW IGO's residual moves from 0.025 to 0.029. V10's conclusion is unchanged; its number is corrected.

The residual then explained itself. It rises from 0.024 at horizon 1 to 0.037 at horizon 8, which is
the signature of states that left and rejoined: a dyad already on the record before its recorded
accession is one whose earlier spell the single-event simplification discards. `count_recurrences`
puts recurrent accessions at 1.9 % from a computation sharing no code with this one. Two routes, the
same magnitude, and nothing left over that needs a story.

## D-28 — ATOP's phase structure, and a diagnostic that found a defect instead of a signal
**2026-08-04.** `penumbra/ledger.py::atop_membership_events`, `scripts/run_u1_isolation.py`.

The first corpus-wide focal-isolation run gave alliance accessions a trace presence of 0.458 one year
before the event, against organisation's 0.013. I had predicted the alliance curve would be degenerate,
since LEDGER takes ATOP membership and the accession date from the same `yrent` field, so the finding
contradicted the construction rather than merely surprising me.

The cause is that ATOP codes a member once per treaty **phase** (`phase`, 0-4). A member in two phases
has two `atop5_1m` rows with different `yrent`, `atop_membership` expands both, and the previous rule
emitted an accession for every row whose `yrent` postdated `begyr` -- so a founder of a multi-phase
treaty acquired an accession dated to the later phase. Of 481 events, **221 (45.9 %)** were that
artefact, against a measured presence of 0.458: the diagnostic was reading the defect back with nothing
left over.

The rule is now one accession per (treaty, member) at its **first** entry across phases, generated only
if that first entry postdates the treaty, with later rows treated as continuations and exits taken at
the last recorded exit. Alliance accessions in 1965-2014 fall from 336 to **177**.

Recorded as a decision rather than a silent fix because it changes a published count and because the
route by which it was found is the argument for D-27's operation: focal isolation asks a question whose
answer is known in advance -- is the member on the record before it joined? -- and the pooled statistic
section 5.1 specifies does not, which is why the defect had survived the validation suite, two independent
count audits and `check_consistency.py`.

## D-29 — four measurements in one script, because each invalidates the reading of the one before
**2026-08-04.** `scripts/run_u1_isolation.py` -> `results/u1_isolation.json`, `results/u1_isolation.log`.

SYNTHESIS section 6 named the corpus-wide focal-isolation curve as the one remaining measurement that could
move a non-identification. Taking it needed three further quantities, each forced by the last, and all
four now live in one script so the sequence cannot be run out of order or reported in part.

**A, unconditioned presence.** The reading it invites is wrong: `declared_resolution` decays
0.349 -> 0.249 -> 0.118 -> 0.045, which is the shape of a four-year penumbra, and I nearly recorded it
as the first real-data penumbra outside DESTA.

**B, conditioned on first entry.** The same curve is 0.142 at horizon 1 and **0.000 beyond**. The decay in A
was prior membership spells, and the confound *rises* with the horizon because reaching further back is
likelier to land inside an earlier spell -- 0.185 at horizon 1 to 0.330 at horizon 8 among recurrent
accessions, 0.0009 among first-time ones. `declared_resolution`'s recurrence rate is 30.7 % against
`exact`'s 6.2 %, so it loads onto exactly the stratum that looks like it has a penumbra. Conditioning on
first entry is now part of the definition of the statistic, not an option, and recurrence rate is reported
beside any $\Delta^\star$.

**C, the pooled relation on the same events.** Step from horizon 0: **0.984** isolated, **0.145** pooled,
against DESTA's 1.000 and 0.102. V10's factor of ten is a property of the diagnostic.

**D, every relation's matched contrast.** The decisive one, and it was not planned -- it exists because C's
pooled curve decays monotonically from 0.9917 to 0.757 and something had to say whether that shape is
event-related. It is not. `trades`, which cannot record an IGO accession, contrasts 0.264 at horizon 0 and
0.146 at horizon 8, retaining 55 % where $r^\star$ retains 48 %. Only `conflicts_with` is flat, and it is
the only relation without homophily content. $r^\star$ minus the strongest anchor falls below 0.01 at
horizon 5, so D-13's rule returns $\Delta^\star_{\text{lo}} \approx 5$ where focal isolation says 0.

Negatives are matched within (entity, year) at 2 per positive with seed 0, for V0's reason. The
declaration is in the script rather than chosen after seeing the curves: the same matching that V0's
retraction forced, reused unchanged.

## D-30 — V8 re-run on the corrected corpus returns an inverted interval, and that is the cleaner result
**2026-08-04.** `scripts/run_u1_alliance.py` -> `results/u1_alliance_primary.json`,
`results/u1_alliance_v11.log`.

V11 said any future run of the alliance test would use the corrected corpus. Run rather than asserted,
because the prediction attached to it -- that a 47 % smaller sample would strengthen a
noise-limitation finding -- is the kind that sounds safe and can still be wrong in its details.

It was right in direction and understated the result. The rule returns
$\Delta^\star_{\text{lo}} = 2$, $\Delta^\star_{\text{hi}} = 1$: the lower bound above the upper, on both
negative strata, identically. An inverted interval is the empty set, and reporting it needs no argument
about power at all -- where V8 had to reason from a standard error to reject its own "P1 HOLDS", the
corrected corpus simply fails to produce an interval.

What the smaller sample exposed is the arithmetic. The contrast is flat and non-monotone across the ten
horizons while the **band nearly triples**, 0.0169 to 0.0461, as positives fall 176 to 110. So
$\Delta^\star_{\text{lo}}$ is where a widening band overtakes a flat series, and it moved 3 -> 2 because
the sample shrank, not because anything about the horizon changed. Recorded because it is the strongest
available statement of the same finding: a $\Delta^\star$ that is a function of $n$ is not a horizon.

One by-product noted in V11 and not pursued: `igo_comembership` contrasts negatively on alliance groups
at every horizon with the group held fixed by matching, which is a substantive claim about alliance
formation that this programme is not positioned to make. A second -- `pta_signature` exceeding `pta_force`
by 0.0086 -- was **withdrawn in D-39**: those columns are present only because the loader globbed the
graph directory and absorbed the two PTA files V10 writes there.

Re-run again on corpus v3 after D-31: 59 alliance entities rather than 66, 1,500 alliance-years rather
than 1,572, median membership 5 rather than 4, and **every statistic identical to four decimals**. The
eight bilateral treaties D-31 removed had no later joiners, so they contributed neither positives nor
matched negatives. The inverted interval survives both fixes, which rules out its being an artefact of
a particular entity set.

## D-31 — a phase row is not a member, the second time
**2026-08-04.** `penumbra/ledger.py::atop_entities`, `scripts/quantify_atop_phase_defect.py`.

Found while making V11's numbers reproducible rather than by looking for it. The originally reported
45.9 % spurious share would not reconstruct from the raw files, and the residual was not a counting
error in either direction: `atop_entities` sized treaties with `groupby("atopid").size()`, which counts
**rows**, and ATOP writes one row per member per phase. A bilateral pact coded over two phases has four
rows and passes a `n_members >= 3` filter.

**8 of 80 alliance entities were bilateral treaties admitted this way**, each exactly two members over
two phases. `MIN_MEMBERS` is declared in LEDGER.md section 2 as COW IGO's own inclusion rule applied to
ATOP *for comparability*, so admitting bilateral treaties defeats the only reason the constant exists.
Fixed to `groupby("atopid").member.nunique()`.

Alliance entities 80 -> 72, corpus entities 573 -> **565**, exits 1,605 -> 1,589, events 10,355 ->
**10,331**. Accessions are unchanged at 8,062: those eight treaties have no later joiners, which is what
being bilateral and two-phase implies.

Two consequences worth separating. The **substantive** one is small -- eight of the 80 alliance entities,
contributing no accessions and 16 exits. The **methodological** one is not: 45.9 % was the product of
two overlapping defects and is therefore unreproducible, so V11 now reports 149 of 373 (40.0 %) on the
corrected entity set and records the original as superseded. A number that cannot be regenerated is not
a finding, and the attempt to regenerate it is what found the second defect. D-23 recorded the same
lesson from the opposite direction, where a stale summary file made a correct document look unverified.

## D-32 — the same root cause a third time, and the invariant that ends it
**2026-08-04.** `penumbra/ledger.py::atop_membership`, `penumbra/ledger.py::build`,
`scripts/build_ledger.py::validate`.

D-28 and D-31 were both instances of *a phase row is not a member*. Two instances of one root cause is
a reason to look for a third rather than to stop, so I searched the code base for row counts standing in
for entity counts. There was one, in the corpus itself.

`atop_membership` expands every phase row over its own year span and concatenates, and phases **overlap
in time**, so a member in two phases gets two rows for the same year. Measured: **596 duplicated
(entity, ccode, year) rows over 298 keys, all alliance**, and **162 of 17,582 (entity, year) cells**
whose row count exceeded their distinct-member count, by a mean factor of 1.36 and a maximum of 2.00.
Both `t1.py` and `t2.py` take group size as `.size()`, so those cells entered the ladder and the hazard
as coalitions up to twice their real size, through `log_size`.

Fixed by deduplicating in `atop_membership`, where the invariant belongs, rather than in each consumer.

**Three checks now enforce what four code paths had assumed.** `validate` asserts no duplicated
(entity, ccode, year) row; asserts group-size-by-rows equals group-size-by-distinct-members everywhere,
which is redundant by construction and kept because it is the form a consumer would write; and asserts
every entity has at least `MIN_MEMBERS` distinct members. A silent assumption held by several call sites
and checked by none is how all three defects survived.

**The third check failed immediately, on the source rather than on my code.** Three COW IGO entities do
not satisfy COW's own stated >= 3 members rule in the observed window: the **Regional Cooperation
Council** carries exactly one coded full member across 2008-2014 with 868 cells at -9, and two
pre-window bodies -- Intl Chemistry Office and Intl Office Public Hygiene -- carry none. This is C5's
failure mode, a coverage gap presenting as structure, and an entity with fewer than three members yields
no dyads and therefore no clique statistic, group density or co-membership edge. They are excluded by a
declared rule that names them in `_dropped`, not by an assertion that halts the build. Section 5.4 is why
the rule is checked rather than trusted: what a source records and what it advertises are different
facts, and this is the third time in this programme that reading the data has contradicted the
documentation.

Corpus v4: entities 565 -> **562** (490 organisations, 72 alliances), events 10,331 -> **10,328** (the
three lost events are the excluded entities' foundings), membership 505,701 -> 505,400. Accessions
unchanged at 8,062.

## D-33 — V6 had no script either, and writing one recovered two undocumented choices
**2026-08-04.** `scripts/run_t2_ladder.py` -> `results/t2_ladder.json`, `results/t2_focal.json`.

D-32 came from making V11 reproducible. The same audit applied to the rest of the results directory found
that **`t2_ladder.json` and `t2_focal.json` were written by an ad-hoc run no code path regenerates** --
which puts V6, one of the two verdicts that *hold*, in the position V11 was in. P4 rests on T2's
any-cause AUC and P5 on its cross-cause sign reversals, so both were resting on unreproducible numbers.

Reproducing them recovered two choices the original never recorded, each found by the reproduction
disagreeing:

**The baseline is `log`, not `linear`.** A linear baseline gives a duration coefficient of +0.002 where
the recorded table has +0.135. D-20's note that the coefficient columns are
`[intercept, log_duration, ...]` is what identified it -- only the log baseline produces that column.

**Discrimination is scored at the row level.** The natural entity-level alternative, $1 - S$ at each
entity's last observed period, returns **0.27**: an entity that terminates early has fewer rows and is
therefore evaluated over a shorter window, so cumulative event probability is *lower* for exactly the
entities that had events. It measures exposure length rather than risk and its output says nothing about
that. The row-level hazard AUC reproduces the recorded 0.614 to 0.612 on the changed corpus, which is
what established the definition.

Two defects in the artefacts, both fixed:

* `t2_focal.json`'s `beta_phi_*` keys held **log_size**. D-20 caught the positional-indexing slip and
  corrected the *document* -- V6 correctly reports $\phi = +0.255$ against log_size $= -0.402$ -- but
  the results file was never regenerated. Coefficients are now pulled by name from
  `meta["feature_names"]`, so that class of error cannot recur, and log_size is reported beside phi.
* The reversal detector scanned only the four covariates, which drops `log_duration` -- **one of the two
  reversals P5 is scored on**. V6 reports two reversals; a scan over covariates alone finds one. Fixed
  to scan every column except the intercept.

At level $k = 1$ the phi coefficient reaches ~40 on the logit scale, because co-membership density is
~0.995 for nearly every coalition-year (C15) and standardising a near-constant inflates its coefficient
without adding information. The sweep's log-likelihood and AUC columns are unaffected and are what V6
reports; the level-1 coefficient now carries an explicit `phi_coefficient_interpretable: false`.

On corpus v4: 527 coalitions, 16,067 coalition-years, 150 events (83 / 30 / 20 / 17 uncoded). **Every
sign, every reversal and every verdict is unchanged**; the largest coefficient move is phi's,
+0.255 -> +0.273. P4 and P5 hold on a corpus and a script that both now exist.

## D-34 — V10's construction check was reported as a measurement, and the correction strengthens it
**2026-08-04.** `scripts/validate_delta_star_desta.py` tests 3 and 4 ->
`results/desta_focal_only.json`, `results/igo_focal_only.json`.

Found by closing the same provenance gap D-32 and D-33 came from: `desta_focal_only.json` and
`igo_focal_only.json` were orphans, written by an ad-hoc run no code path regenerated, and V10 is the
capstone -- SYNTHESIS section 1 rests on it. Writing the script made the arithmetic explicit and one of
V10's two halves does not survive as stated.

**The step table is entailed by construction.** V10 reports focal isolation on DESTA as "the back-dating
is real and exact": presence 1.00 for horizon <= gap and 0.00 beyond, at every gap, contrast 1.000. The
focal relation admits the accession entry's dyads from its own `sig_year`, the event is dated at
`force_year`, and `gap` **is** `force_year - sig_year`. So presence at horizon d holds exactly when
d <= gap, with no data-dependent step anywhere, and the marginal curve is the gap distribution restated
-- `focal_only_by_horizon[d]` equals the share of events with gap >= d, which the script now asserts to
machine precision. The table cannot come out otherwise. Calling it a recovery of $\beta$ overstates it.

**The negative control is weaker than "two corpora, one with a penumbra and one without".** COW IGO
records **one** date per membership, so focal isolation has no second date to measure against and a zero
residual is entailed by the source's structure. V12 generalises this: focal isolation detects
back-dating only where a source codes two dates, which DESTA does and ATOP and COW IGO do not, so their
$\beta = 0$ is a property of their coding rather than a finding about the world.

**What survives, and it is the load-bearing half.** On the same corpus, at the same events, the pooled
density the manifesto specifies returns a contrast of **0.1023** against a focal-only truth of 1.000,
with the curve nearly flat -- 0.752 at horizon 0 to 0.621 at horizon 8 -- because the focal agreement's
back-dated dyads are 6.8 % of the relation. A forecaster reading signature-dated data at $t$ is exposed
to an edge `gap` years before the event; the diagnostic section 5.1 specifies recovers a tenth of it.
That is V10's conclusion, SYNTHESIS section 2(a), and none of it depends on the step table being a
measurement.

**And the programme's evidence that the estimator works was never V10.** It is C18: on synthetics the
generator sets $\beta$ and D-13's pre-specified rule returns $\beta + 1$ in 6 of 6 settings. Separating
the two removes a tautology from the argument and leaves the same conclusion resting on the two things
that do support it -- a synthetic calibration for the estimator and a real corpus for the blindness.

One thing the correction gains rather than loses. V10 accounted for COW IGO's 2.9 % residual by
recurrence and cross-checked it against `count_recurrences`' 1.9 %, calling them "two independent routes
to the same magnitude". The two statistics count different things -- dyads with a second recorded
accession against events whose state was on the record earlier -- and V12's conditioning gives the exact
decomposition instead: 7.71 % of events are recurrent and carry mean presence 0.2498, so
0.0771 x 0.2498 = 0.0193 against an observed residual of 0.0221, with first-time events contributing the
remaining 0.0008. The residual is recurrence, quantitatively, and conditioning on first entry removes it
to exactly zero.

## D-35 — an artefact carries its own provenance, because three verdicts did not
**2026-08-04.** `penumbra/provenance.py`, `scripts/check_consistency.py`, and every script that writes a
results file.

D-32, D-33 and D-34 have one shape. Each began with a results file no code path regenerated -- V11's
defect quantification, V6's T2 tables, V10's focal-isolation evidence -- and each time, writing the
script that should have produced it found a further defect: a third instance of the phase-row confusion,
a mislabelled coefficient key and a reversal detector scanning the wrong columns, and a construction
check reported as a measurement. The pattern is not that those three files were unlucky. It is that a
number in a JSON file with nothing attached to it cannot be audited, and an unauditable number in a
document reads exactly like an audited one.

So the fix is not a fourth audit. `write_result` stamps every artefact with the command that wrote it and
a three-integer corpus fingerprint, and `check_consistency.py` requires the `invocation` key -- a new
ad-hoc artefact now fails the check instead of waiting in `results/` to be cited.

Three details, each chosen against an alternative:

**No timestamp, no host, no git hash.** A timestamp changes on every rerun and turns a byte-identical
result into a diff, which is the opposite of what reproducibility is for. What actually disambiguates
two runs of the same command is the corpus they ran against, so `{entities, events, accessions}` is
recorded instead. This corpus went through four versions in one working day and every one of them would
otherwise have produced identically-named files.

**Attribution is read from the artefact, not from the script text.** The first version of the audit
tested whether a filename appeared anywhere under `scripts/`, and `p7_ctrl_w96` passed it because a
*comment* I had just written mentioned the name. A check satisfiable by prose is not a check.

**Reconstructed provenance is flagged as reconstructed.** `p7_ctrl_w96`'s invocation was recovered from
its own `width` and `rungs` fields rather than from a log, so it carries
`invocation_reconstructed: true` and the audit reports those separately. Recovered is not recorded.

The rewrite was mechanical and went wrong in the ordinary way: a regex turned
`p.write_text(json.dumps(X, indent=2))` into `write_result(p, X, indent=2))` across sixteen files,
leaving an unbalanced parenthesis in each. Fixed by matching parentheses properly rather than by
patching the regex, and every file re-parsed before anything was run.

## D-36 — left truncation was declared and not implemented, and P5 survives the fix
**2026-08-04.** `penumbra/t2.py::build_panel`, `scripts/run_t2_ladder.py` -> `results/t2_ladder.json`.

Found by working through LEDGER.md's open list rather than by a failure. Section 9.1 names left truncation
and immortal time; D-03 recorded that "left truncation binds hard, since entities founded before the
window enter under observation rather than at origin". The T2 panel set duration to 1 at the regime
start for every entity, so a coalition founded in 1900 and one founded in 1965 were both duration 1 in
1965.

**183 of 528 entities in the regime panel predate it**, with a median true age at 1965 of 13 years, a
mean of 19.7 and a maximum of 150. They carry **45.7 % of the coalition-years** and **39.1 % of the
terminations**. So the baseline hazard was estimated on a clock that was wrong for a third of the panel
and nearly half its exposure -- and `log_duration` is one of the two cross-cause sign reversals P5 is
scored on, which makes it the worst covariate in the model to get wrong.

`PeriodPanel.entry` exists for exactly this, is documented as "the last period BEFORE observation
begins", and was being passed zeros. Duration now runs from founding and `entry` is the age at which
observation starts, so the baseline is estimated on the true clock while the entity contributes only
observed periods. For an entity founded at or after the regime start the two clocks coincide and `entry`
is 0, which is the property that makes the change a no-op where it should be.

**The estimator was never the problem, and that is the uncomfortable part.** `test_hazard.py` and
`test_hazard_fast.py` both carry explicit *truncated* cases -- "2 causes, exact, truncated" and "3
causes, interval, truncated" -- and both agree with the closed form to 1e-13, while a separate check
asserts that immortal time is refused. The likelihood was written for left truncation, verified for it,
and had a test named after it. Every caller passed zeros. A test that exercises a capability proves the
capability exists; it says nothing about whether anything uses it, and no suite in this repository was
positioned to notice.

**P5 holds and V6's verdict does not move.** Both reversals survive: `log_duration` +0.095 against
-0.143, `phi_igo_comembership` +0.292 against -0.081. Any-cause AUC 0.6119 -> 0.6098. What changed is the
size of the duration effect, +0.137/-0.233 -> +0.095/-0.143 -- part of what read as duration dependence
was the misplaced baseline, which is the direction the error predicts.

One consequence worth recording separately. With the corrected clock `polity2_mean` came out -0.0925
against **+0.0006**, and a sign-only test counted that as a *third* reversal for P5. It is a rounding
artefact, not an effect. The detector now requires both sides to exceed a declared floor of 0.01 on the
logit scale for standardised covariates, and reports the below-floor flips separately so the choice is
visible rather than built in. A verdict scored on sign reversals needs a definition of reversal that a
coefficient of six ten-thousandths cannot satisfy.

## D-37 — "dyad time" was never defined against founding, and the ladder is invariant to which one you pick
**2026-08-04.** `penumbra/t1.py::_eligibility_clock`, `scripts/run_t1_ladder.py --clock` ->
`results/t1_ladder.json`, `results/t1_ladder_eligibility.json`.

D-36's audit applied to T1. `build_risk_set` set `dur = cumcount() + 1`, so every dyad starts at 1 in
the year it enters the *observed* risk set, and the docstring said "duration in dyad time" without
defining that against the coalition's founding. Measured on the 1965-2014 risk set: **19.9 %** of dyads
are truncated at the regime start, **41.2 %** of rows and **58.4 % of positive dyads** belong to
coalitions founded before it. Rung 1 is duration dependence alone and is the baseline every other rung is
scored against, so it is the worst place in the ladder for an undeclared clock.

Unlike D-36 this is a specification question rather than a defect, and the two clocks answer different
questions: `observed` is how long we have watched a dyad not accede, `eligibility` is how long the state
could have joined, starting at max(founding, the state's system entry, the window). So both are computed
and the default stays `observed`, because that is what V5 was measured on and moving a default silently
moves a published number.

**The rung ordering is invariant, which is what V5 actually claims:**

| | observed | eligibility |
|---|---|---|
| rung 2 - rung 1, pooled | +0.3191, 16/16 | +0.3333, 16/16 |
| rung 2 - rung 1, within | +0.0978, 16/16 | +0.1011, 15/16 |
| rung 3 - rung 2, pooled | +0.0089, 13/16 | +0.0084, 13/16 |
| rung 3 - rung 2, within | +0.0430, 15/16 | +0.0518, 15/16 |

Every rung beats the one below on both metrics under both clocks, and rung 3's within-coalition gain is
*larger* under the eligibility clock, so V5(b) -- relational features answering a different question from
node covariates -- is strengthened rather than threatened by the correction.

Two clocks that differ between tasks, stated rather than forced into agreement: T2's is the coalition's
**age**, known exactly from `founded`, so it runs unbounded to 150 years. T1's is the state's
**eligibility duration**, which needs a system-entry date the corpus does not carry before 1946, so it is
floored at the window and the correction is bounded at 19 years. Making them match would mean either
discarding T2's known founding dates or inventing pre-1946 state entries.

## D-38 — a glob, and the CUDA assert two indirections away from its cause
**2026-08-04.** `penumbra/neural.py::build_snapshots`, `scripts/run_p7.py`.

P7 died on `RuntimeError: CUDA error: device-side assert triggered` inside `RGCNConv`. The cause is nine
lines away and in a different file.

`build_snapshots` read its relations with `GRAPH.glob("edges_*.parquet")`. When
`validate_delta_star_desta.py` wrote `edges_pta_signature.parquet` and `edges_pta_force.parquet` into the
same directory -- which it does to build V10 -- those two files were silently pulled in. `RELATIONS` names
five, so `relation.map(rel_ix)` returned **NaN** for the PTA rows, `np.stack` cast NaN into an int64
edge-type tensor, and RGCN scattered on a garbage relation index. A NaN in an index array is the one bad
value that raises nothing where it is created; it raises on another device, later, in library code.

V9's P7 run predates the PTA files, so V9's numbers are unaffected and the glob was latently broken from
the moment V10 was measured. Nothing said so, because the only symptom is a crash in a rung that only
runs when someone runs P7.

Two changes. Relations are now read **by name** from `RELATIONS`, with a `FileNotFoundError` if a declared
relation has no file -- the failure a missing relation should produce. And unmapped endpoints or relations
raise instead of being cast: `pd.isna` is checked on each index array before `astype(np.int64)`.

The general shape is the one D-32 and D-35 keep producing: a set that should be **declared** was
**re-derived by pattern**, and the pattern picked up something a different script wrote. `data/graph/` is
shared between five scripts and a filename glob is an implicit contract between all of them.

## D-39 — the same glob in a second script, and there it added a leaking feature instead of crashing
**2026-08-04.** `scripts/run_u2.py::load`, `penumbra/t2.py::build_panel`.

D-38 fixed `neural.py`'s `GRAPH.glob("edges_*.parquet")` after it killed P7 with a CUDA assert. Grepping
for the pattern found two more call sites, and the one that did **not** crash is the dangerous one.

`run_u2.py::load` globs the same directory, and `run_u1.py` and `run_u1_alliance.py` import that loader.
So from the moment V10's DESTA validation wrote `edges_pta_signature.parquet` and
`edges_pta_force.parquet`, U2's probe gained four features -- `phi_pta_force_k1`,
`clique_pta_force_k1`, `phi_pta_signature_k1`, `clique_pta_signature_k1`. A v4 re-run reports **24
features where V1 and V2 were measured on 20**, and it reports them without complaint.

**`pta_signature` is deliberately back-dated.** It exists because V10 needed a relation carrying a
penumbra of known width, so it is the single worst feature that can be added to a shortcut probe by
accident: U2 measures how much of a model's discrimination comes from leakage, and the glob quietly handed
it a leaking feature. The direction is toward confirming P2's premise.

`penumbra/t2.py` globs too and was the least exposed: its features are built by looping over `RELATIONS`,
so the extra edges were loaded and ignored. That is exactly the reasoning to distrust -- "harmless because
something downstream filters it" is what was true of `run_u2.py` until `LEVELS` stopped being the only
gate. Both now read by name with a `FileNotFoundError` for a declared relation with no file.

**What this costs.** V1, V2 and their sub-verdicts were measured on the correct five relations -- they
predate the PTA files -- so the *published* numbers are sound, and it is the v4 re-run that was
contaminated. U1 and U2 are being re-run on the named set. V8's alliance table listed the PTA columns and
its band draws only on `['trades', 'conflicts_with', 'votes_with']`, so its $\Delta^\star$ is unaffected;
the observation V11 recorded in passing -- that `pta_signature` exceeds `pta_force` by 0.0086 -- was the
glob rather than a bonus finding, and is withdrawn.

Three scripts, one pattern, three different symptoms: a crash, four silent extra features, and a wasted
read. `data/graph/` is written by two scripts and read by four, and a filename glob is an implicit
contract among all six.

## D-40 — the risk-set cache was keyed on the regime and not on the corpus
**2026-08-04.** `penumbra/t1.py::build_risk_set`, `penumbra/t1.py::_corpus_fingerprint`.

`build_risk_set` caches to `t1_riskset_{lo}_{hi}.parquet` and returned it whenever the file existed. The
key is the regime; the *content* depends on the corpus. So a corpus rebuild left a stale risk set that
the next ladder, P6 or P7 run would consume in silence.

This was not hypothetical: the corpus went through four versions in one working day and the cache had to
be deleted by hand before each rebuild. It was deleted every time, which is luck rather than design --
forgetting once would have fitted the ladder to the previous corpus and produced a table with nothing
visibly wrong with it, against a document quoting the new entity counts.

The cache now carries a sibling `.corpus.json` holding the row counts of `membership`, `events` and
`entities`, and a mismatch rebuilds with a printed reason. Row counts are enough: none of D-28, D-31 or
D-32 left any of the three tables unchanged, and parquet keeps the count in its footer so the check costs
nothing.

The same shape as D-35 and D-38 from a third direction. There, a results file did not record what
produced it; here, a derived cache did not record what it was derived *from*. An artefact that cannot say
which inputs it came from cannot be checked against them, and every consumer of this one assumed it could.

## D-41 — two seeds said the heterogeneous encoder had stopped earning its parameters; four said otherwise
**2026-08-04.** `scripts/run_p7.py --seeds 0 1 2 3` -> `results/p7_s4.json`,
`results/p7_ctrl_w96_s4.json`, `results/p7_ctrl_w128_s4.json`.

V9's re-measurement on corpus v4 came in at two seeds -- the script's default, and, it turned out, what
the original run used despite the verdict saying three. Seed-matched against the parameter-matched
controls it read:

* rung 6 (78,849 params) vs MLP width 96 (80,993): **+0.0009**
* width alone, MLP 64 -> 96: **+0.0066**

Which says the heterogeneous encoder buys nothing its parameter count would not buy anyway, and that
widening the control is seven times more effective than message passing. That is a different verdict for
rung 6, and it would have joined rung 5 outside the headline.

**It was noise, and the tell was in the data already there.** Rung 6 has the widest seed-to-seed spread
in the ladder: sd **0.0065** over four seeds, against rung 7's 0.0019 and rung 4's 0.0023. A margin of
0.0121 cannot be resolved by two draws from a distribution that wide. At four seeds:

| | contribution | standard errors |
|---|---|---|
| rung 6 vs MLP w96 | **+0.0121** | 2.6 |
| rung 7 vs MLP w128 | **+0.0214** | 15 |
| width alone, 64 -> 96 | +0.0021 | 0.5 |
| width alone, 64 -> 128 | +0.0014 | 0.5 |

V9's ordering is restored and its original figures (+0.0076, +0.0245, +0.0009) were close to right.

Recorded rather than quietly corrected, because the underpowered reading is the one that **looked like a
finding**: "the relational encoder does not survive parameter matching" is a sharper, more publishable
sentence than "it does", and I had it written down before running more seeds. D-24 recorded three
performance guesses made without profiling; this is the same error in a statistic rather than in a
runtime, and the fix is the same one -- measure the variance before believing the difference.

Two consequences kept. Every parameter-matched margin now reports its seed spread, since such a margin is
a difference of two noisy means. And rung 5's characterisation still weakens on its own merits: -0.0009
over 48 cells, beating the control in exactly 24 of them, is **indistinguishable from a graph-free MLP**
rather than worse than one, which is what V9 claimed at -0.0076 on two seeds and corpus v1.

## D-42 — the same defect, in the prose written to report the defect
**2026-08-04.** `scripts/run_u1_isolation.py`, `results/u1_isolation.json`.

V12 quotes two numbers as its corpus-scale replication of V10: the step from horizon 0 to the mean beyond
it is **0.984** under focal isolation and **0.145** on the pooled relation, against DESTA's 1.000 and
0.102. Both were measured. Then the script was restructured to hold four measurements in one place, the
section producing them was dropped, and the verdict went on quoting them for several hours against an
artefact that no longer contained them.

That is exactly what D-35 exists to prevent, committed in the text reporting D-35, hours after writing
that "an unauditable number in a document reads exactly like an audited one". Found by re-verifying V12's
claims against its own artefact key by key rather than by anything noticing.

Restored and registered: the comparison is computed on the same rows both instruments see -- 52,305
positives at nine horizons -- and `check_consistency.py` now holds `focal_step` and `pooled_step`, so the
next restructuring fails the check instead of leaving the numbers hanging. They reproduce at 0.9844 and
0.1447.

The reason to record this rather than fix it quietly is that it bounds what the discipline achieves. Every
one of D-32 to D-41 was found by asking a question with an external answer; this one was found the same
way, by an author checking his own paragraph against the JSON. **Provenance stamping does not stop a claim
losing its source — it only makes the loss detectable.** The check is the mechanism, and the check has to
be extended each time a claim becomes load-bearing, which is a standing cost rather than a solved problem.

## D-43 — the second domain, and it falsified one of my own claims
**2026-08-04.** `scripts/run_second_domain.py` -> `results/second_domain_thr400.json`,
`results/second_domain_thr150.json`; verdict in `PENUMBRA-OUTCOMES.md` V13.

SYNTHESIS named this the highest-value remaining work and the reason was risk, not curiosity: three of the
ten failure modes the paper rests on are claims about **any** curated group corpus and all three had been
measured on one. CLIQUEBAIT's protein benchmark is the adversarial case because its size distribution is
the opposite of LEDGER's -- median complex size 3 against LEDGER's mean positive stratum of 66.

Three design choices, each made before a number was read.

**The statistics come from the pinned library.** `vendor/cliquebait/diagnostics.LeakageAudit` computes phi
and the clique contrast, and its `Group` already defaults to a `'__static__'` time, so the timeless case
needed no adaptation. Reimplementing them would have made any difference between domains
uninterpretable -- it could always have been the implementation.

**$r^\star$ and the anchors were declared from what each STRING channel records**, in the script's
docstring, before running it. `database` imports CORUM and ComplexPortal, which *are* the label source, so
it is $r^\star$ by the same logic that makes `igo_comembership` T1's leaking relation. `textmining` and
`experiments` were declared **contaminated and therefore ineligible as anchors**, because the first reads
papers describing complexes and the second covers co-immunoprecipitation, which detects them. Anchors:
coexpression, coexpression_transferred, fusion, cooccurence, homology.

**Both STRING thresholds were run**, 400 and 150, because a five-fold change in edge count is the cheapest
available robustness check on a density-sensitive statistic.

**(d) is falsified and the restatement is the useful part.** It claimed size and sample never come out
favourable together in a curated group corpus. Here they do: 1,399 positives at 2-3 members with a
contrast of 0.4124 against a negative clique rate of 0.0000. The trade-off is a property of a corpus whose
group size **correlates with entity type when the small-size type is rare** -- LEDGER exactly, with 59
alliances at median 5 carrying 177 events against numerous large organisations. Generalising from LEDGER's
composition to group corpora as such was the error, and it is mine rather than the manifesto's: (d) is not
in the pre-registration, it is one of the findings this programme added.

**(h) narrows for a reason that can be named.** $r^\star$ 0.4240 against a strongest anchor of 0.0165,
residual +0.4075. In IR, trade, UNGA voting and co-membership all express one latent thing -- which states
are close to which -- so the band subtracts almost nothing. mRNA co-expression and gene fusion bear no such
relation to a curator's complex boundaries. (h) is about the IR corpus.

**And the first positive result about the method.** The three channels declared contaminated *in advance*
ranked first, second and third on clique contrast -- 0.4579, 0.4240, 0.3075 -- above every anchor at
<= 0.0165, with `textmining` scoring above $r^\star$ itself. Section 5.4 asserts that no statistic separates
leakage from signal and that the verdict needs the coding rules read; the reading was done first, in
writing, and the statistic then put exactly those three on top. Every previous verdict in this programme
found something that does not work. This one found something that does.

Recorded with the falsification stated first, because a second domain that confirms everything is a
second domain that was not adversarial enough, and the value of this run is the claim it broke.

## D-44 — the manuscript consistency pass, and a claim that was false at the level a reader would assume
**2026-08-04.** `scripts/check_paper.py`, `scripts/clique_by_size.py` -> `results/clique_by_size.json`.

The manuscript restates figures in compressed form, so a value can be correct in `PENUMBRA-OUTCOMES.md`
and wrong there, and it was drafted after four corpus rebuilds. A dedicated checking pass found five
problems, four of them stale numbers and one a specification gap that matters more.

**Four values were from corpus v1.** Median group size by type was given as 4 alliances and 51
organisations against v4's **5** and **16**; the positive strata's mean as 66 against **73.5**; and the
share of events in groups above eighty members as 36 percent against **41.1 percent**. The "51" was not
a stale median at all but a different quantity, the median size of the group an accession enters, which
is 60. The manuscript's table labelled both as "median group size", so it now reports the two rows
separately.

**The level was lost in compression, and the size dependence reverses without it.** V3 states its
conditions in full: "clique rate at $k = 25$ by group size, horizon 3, matched panel". SYNTHESIS section 2(c)
and the manuscript both dropped the level when summarising it as "0.20 to 0.25 below twenty members and
identically 0.000 above eighty". So the defect is in the summary, not the measurement, and the attribution
matters: V3 is correct and complete as written.

Two further differences make the re-measurement a companion rather than a reproduction. It is taken at the
**event year** rather than at horizon 3, because corpus B has no time axis and the two domains have to be
compared at the same lead time, and it uses finer size bins. Measured that way on v4 at $k = 25$ the
contrast runs 0.5833, 0.3617, 0.3391, 0.2437, 0.0521 and **0.0000**, with the positive clique rate itself
zero above eighty: the same shape as V3's 0.196, 0.249, 0.205, 0.047, 0.010, 0.000, at different levels
because the cut is different.
At $k = 1$ the same statistic on the same corpus **rises** with size, 0.0625 to **0.4778**, because
co-membership at $k = 1$ has density 0.9954 and both classes are near-cliques, so the contrast comes
from the negative rate falling with size rather than the positive rate holding. A summary of a
clique-based statistic that drops its level is false at the level a reader would assume, and mechanisms
(b) and (c) of the paper interact rather than standing separately.

**A figure specification carried an unmeasured number.** Figure 6 overlays the two corpora and its
drawing instructions said "roughly 0.22 in the 11 to 20 bin" for corpus A. Both series are now computed
by one script, which is what makes the overlay a comparison, and the levels differ by necessity: corpus
A at $k = 25$ because its relation is weighted and degenerate at $k = 1$, corpus B at $k = 1$ because its
channels are binary. That difference is now stated in the paper rather than left for a reader to notice.

**One framing overstated what the corpus can show, and Section 9 already contradicted it.** Section 6.3
read "under focal isolation the corpus's back-dating is zero", presented as a measurement, while the
threats section correctly said that a register coding one date returns zero by entailment. Corpus A codes
one date and derives the event from a transition in the same field, so that zero is a construction check
in the same sense as Section 6.2's step table. What survives, and is what the section now claims, is that
the focal record carries nothing past one period while the pooled statistic still reports 0.1490 after
eight, a factor of 6.8 on the step from zero lead time. The declared-resolution stratum's 0.1419 at one
period is a genuine measured width and is the only place this register demonstrably reaches past the
event.

`check_paper.py` now enforces 43 numeric claims against their artefacts, six retired phrases, the
250-word single-paragraph abstract, sequential figure and table numbering, and that every figure and
table is cited. A deliberate corruption test showed the first version of the numeric check was too weak:
it verified that a value appears somewhere, so a count stated in three places could be stale in one and
still pass. Context-anchored patterns now require every occurrence of a quantity to match, and
corrupting one of three occurrences fails the check.

## D-45 — the double check, and mechanism (e) does not survive the panel V0 corrected
**2026-08-04.** `scripts/paper_support.py`, `scripts/run_u2_capacity.py`,
`scripts/check_paper.py` -> `results/paper_support.json`, `results/u2_capacity_replication.json`.

Re-running the checks I had just written would have been circular, so the second pass asked a different
question: **what fraction of the manuscript's numbers does the checker actually cover, and does any
number have no source at all?** The answer to the first was 43 of 293 distinct numeric tokens, about 15
percent. The answer to the second found the substantive problem.

**Fourteen asserted figures existed only in prose.** Every one verified when recomputed -- the two
regimes' densities 0.9704 and 0.9954 with 116 and 273 organisations per year, the left-truncation audit's
183 of 528 and 45.7 percent, the 162 inflated group-years, the 39.4 percent share of gaps at two or more,
and the ladder and architecture aggregates -- but a verified number that lives only in a sentence is
unauditable from the next edit onward. `paper_support.py` now computes them and the checker registers
them, taking coverage from 43 to 76 claims and the unsourced-token count from 32 to 17, of which all 17
are reference years, figure axis bounds, or arithmetic stated in the text.

**One counting convention was wrong in four places.** "596 duplicated membership rows" doubles the
excess: 298 rows are redundant and 596 stand in duplicate pairs. Corrected in the manuscript,
`SYNTHESIS.md`, `PENUMBRA-OUTCOMES.md` and both code comments, and the artefact now reports both
conventions with the difference named.

**And mechanism (e) does not survive.** Its figures, a decay of 0.058 at 30 trees against 0.143 at 300
with a linear probe at 0.041, traced to `u2_real_replication.json`, which carries neither an invocation
nor a corpus fingerprint -- it predates D-35's stamping and is the panel **V0 retracted**, where
negatives were drawn across group periods rather than within them. V1d's own header says "mechanism
stands, numbers void", and the manuscript had quoted the void numbers.

Recomputed with matched negatives on the same regime, the claim fails:

| capacity | decay, old panel | decay, matched panel |
|---|---|---|
| 30 trees, depth 2 | 0.0575 | **0.2160** |
| 300 trees, depth 3 | 0.1434 | **0.2686** |
| ratio | 2.49 | **1.24** |
| linear probe | 0.0411 | **0.2597** |

The linear probe decays 0.2597, between the two boosted extremes. A decay present at every capacity
including linear is not a capacity artefact, so on this corpus probe capacity is not what produces the
decaying curve. The a priori concern is untouched, since the positive count really does fall from 1,061
to 508 across the lead-time range, and (e) is now stated as sound in principle and not demonstrated
here. Table 8's status for it changes from "general, property of the probe" to "sound in principle, not
demonstrated on this corpus".

Two things worth keeping. The practical recommendation attached to (e), report a linear probe beside any
non-linear one, is what settled the question, and it settled it **against** the mechanism it was
introduced to support. And the reason this survived the first consistency pass is that the first pass
checked whether a value appears somewhere rather than whether every occurrence is right, and checked
only values I had thought to register; a corruption test exposed the first weakness and a coverage audit
the second. A checker's coverage is itself a number that should be reported.


## D-46 — an outside review of the manuscript, and four of its ten blockers were real errors
**2026-08-24.** `penumbra_revizyon_plani.md`, `scripts/quantify_focal_share.py`,
`scripts/corpus_b_negatives.py`, `scripts/audit_upper_bound.py` ->
`results/focal_share.json`, `results/corpus_b_negatives_thr400.json`,
`results/upper_bound_audit.json`.

The manuscript went out for an external read and came back with ten items marked as blocking. Checking
each against the artefacts rather than against memory is the only way to tell a reviewer's inference
from a defect, and the split was four to six.

**Four were errors.**

*The 6.8 percent travelled between corpora.* Section 5.3 derives it from the PTA register, 13,966 of
204,747 edge-years, and Section 6.3 and mechanism (b) then quoted it for corpus A, whose relation,
dating convention and density are all different. No such figure had ever been computed for corpus A.
Computed now, and the level decides it by a factor of three hundred: of the 474,034 candidate-to-member
dyads the pooled statistic reads as present at k = 1, **117** are present only through the focal entity,
0.02 percent; at the declared primary level k = 25 it is 15,059 of 230,707, **6.5 percent**. Co-membership
weights count shared organisations, so a dyad read at level k is present only through the focal entity
exactly when its weight equals k, and the decomposition is exact rather than estimated. The saturation
argument is stronger with the real numbers than it was with the borrowed one, and the coincidence that
6.5 sits next to 6.8 is a coincidence.

*Figure 3 panel A drew a decline that is not in the data.* The five step functions were staggered
14 pixels apart so they would not overplot, and on an axis where 1.0 is at y = 140 and 0.0 at y = 540 a
14-pixel stagger is 0.035. The reviewer read presence declining from 1.00 to 0.86 as the coded gap
widens, which is exactly what the figure showed and the opposite of what the artefact says: every
per-gap curve is 1.0 inside its gap and 0.0 outside, at every gap. Fixed in the `.drawio` source, and
the figure specification now forbids the offset in as many words, because nothing is lost by removing it:
the five lines differ in where they drop, not in how high they run. **The exported `.svg` and any
downstream `.docx` must be regenerated from the corrected source; the rendered artefacts still carry the
stagger.**

*The upper bound's firing count was wrong in the text and the figure named the wrong settings.* Section
6.1 said the bound fired in 2 of 6 synthetic settings and Figure 2's specification said it exists at
beta = 0 and beta = 5. The artefact says **3 of 6**, at beta = 0, 1 and 2, and it does not exist at
beta = 5. The recomputation confirms that the pre-edit rule and the stored bound agree in all six
settings, so this was a transcription error and not a code change. Neither number was registered in
`check_paper.py`; both are now.

*Table 5 named the wrong statistic.* Its caption said "matched clique contrast" for six years. The code
computes the difference in the mean share of the candidate's dyads into the existing members that the
relation carries -- a density, not a clique rate. The numbers were right, the label was wrong, and the
distinction is load bearing precisely because Section 6.4 spends two pages on how differently the two
behave. This is D-20's class of defect and it survived four consistency passes because a caption is
prose and the checker checks numbers.

**Six were inferences from an under-specified text**, and each of them says the text needed the
sentence rather than that the number was wrong: the "0.00000000" density range is exactly zero because
the edge budget is a fixed integer count, so the honest form is "exactly" and not a threshold; the
0.0000 negative clique rate in corpus B is what independent sampling predicts, expected count two
millionths, and the negatives are demonstrably not edge-excluded because their mean density sits at the
relation's own; the "same factor of roughly ten" is two observations 44 percent apart; and so on. All are
now stated in the manuscript.

The general lesson is the one Section 8 already argues, arriving from a new direction. Every one of the
four real errors is a **claim-to-artefact mismatch of a kind an internal checker cannot see**: a figure
that draws what the data do not say, a caption that names the wrong statistic, a number quoted for the
wrong corpus, and a count transcribed wrongly into prose. `check_paper.py` tested whether registered
values appear in the text. It could not test whether the text attributes them to the right object. Four
questions with externally checkable answers found nine defects; one outside reader found four more, and
the four are of a class the questions do not reach.

## D-47 — homophily is now a dial, and the identification claim is a slope rather than a sentence
**2026-08-24.** `penumbra/synthetic.py` (`generate_parametric`),
`scripts/run_synthetic_homophily.py` -> `results/synthetic_homophily.json`.

Section 6.3's deepest claim was that a trace of the event and a persistent similarity to the members
enter a pooled contrast identically, so no such contrast separates them. It was argued, not measured,
and it was argued on the one corpus where the trace is the unknown. The generator that could have
measured it had no homophily axis: its background was always drawn by latent proximity and its acceding
entities were always the group's nearest non-members, so there was nothing to vary.

`generate_parametric` adds four controls and leaves `generate` byte-identical, so Table 3's calibration
cannot move. Homophily h is an exponent on latent similarity in the edge background, in the founding
membership and in the pool the joiners come from; at h = 0 every draw is uniform. The width can be
redrawn per event from a distribution. A share of coded dates can be displaced from the true ones. And
the anchors can be drawn from the same latent trajectory as the target relation or from an independent
one. Two membership registers are emitted rather than one, because U1 needs the honest register -- a
back-dated one would drop the leaking rows as ineligible, the candidate already being a member there --
and focal isolation needs the recorded one. That pairing is the PTA situation reproduced in a setting
where the truth is set.

Six homophily settings against six widths in each of two anchor regimes, 72 corpora, four estimators
graded against beta + 1. Two summaries: mean error, and the least-squares slope of the estimate on the
true width, where 1 means the estimator tracks the truth and 0 means its output is unrelated to what it
estimates.

| estimator | h up to 1 | h = 2 | h = 3 and above |
|---|---|---|---|
| focal isolation | 0.00 / 1.00 | 0.00 / 1.00 | 0.00 / 1.00 |
| lower bound, clique contrast | 0.00 / 1.00 | 0.00 / 1.00 | 0.00 / 1.00 |
| residual rule, shared anchors | 0.00 / 1.00 | 0.00 / 1.00 | 0.00 / 1.00 |
| residual rule, independent anchors | 0.00 / 1.00 | +2.00 / +0.54 | +5.33 / -0.03 |
| unbanded rule | 0.00 / 1.00 | +4.33 / -0.03 | +5.50 / 0.00 |

Four findings, and one of them reverses something I wrote.

**Homophily alone destroys identification in the pooled statistic.** With no band, the estimate goes from
exact at h = 1 to a constant at h = 3, reporting the end of the examined range at every width. Nothing
changed but how strongly latently close entities are tied to one another. The instrument reads that
closeness as back-dating.

**The band repairs it only when the anchors share the target relation's structure, which is the opposite
of what mechanism (h) said.** I had held that the band fails *because* corpus A's anchors express the
same latent quantity as its target relation. The controlled version says shared structure is what lets
the band subtract the homophily and independent structure is what leaves it in. Corpus B is the
independent case and the only reason its residual of 0.4075 is not a phantom horizon is that corpus B
has no time axis. Mechanism (h) restated in the manuscript, with the reversal marked.

**Focal isolation is unbiased in homophily at every setting in both regimes.** 0.00 / 1.00 in all twelve
cells. It reads the group's own record, and similarity does not put a candidate on a record.

**Saturation and homophily are one mechanism seen from two sides.** The clique-contrast lower bound is
exact everywhere above, which is a narrow result rather than a robust one: a clique needs every dyad, so
at density 0.12 homophily cannot complete one. At h = 3 and width 2 the bound is exact at density 0.12,
does not fire inside eight periods at 0.50, and overshoots by two at 0.90; at h = 0 it is exact at all
three. Corpus A's target relation has density 0.9954 and its lower bound does not fire inside ten
periods at the primary level. Mechanisms (b) and (h) are not two corpus-specific findings; saturation is
the condition under which homophily breaks the clique statistic.

Three side results. The negative control at h = 0, beta = 0 returns the correct value from every
estimator: no false positive, which the manuscript had no number for. Under a width redrawn from the PTA
register's own coded gaps, focal isolation's zero rule returns the realised maximum plus one and its
half rule returns the realised median plus one, in all twelve settings -- so under a spread width the
estimand is a **choice**, and the choice has to be reported rather than made silently. And displacing a
tenth of coded dates one period late puts focal isolation's presence at 0.0667 at one period and zero
beyond, three tenths at 0.3000; corpus A's declared-resolution stratum reads 0.1419, which is about one
event in seven, and that is a quantitative bridge between the synthetic testbed and the one place in
corpus A where back-dating is measured rather than entailed.

## D-48 — the upper bound repaired, and the repair is the lower bound wearing a hat
**2026-08-24.** `penumbra/umbra.py` (`delta_star(upper_rule=...)`),
`scripts/audit_upper_bound.py` -> `results/upper_bound_audit.json`.

The suite was sold as an interval estimator and the abstract said so. The upper bound required r-star to
lose top rank on clique contrast **and** have its single-feature discrimination enter the band. The rank
condition is what blocks it, so the obvious repair is to drop it and keep the band crossing. Both rules
now exist behind one keyword, computed from the same curve so neither is graded on data the other was
not, and the pre-specified rule stays the default because a rule is not improved by being changed after
seeing that it failed.

The repair works and buys nothing.

| | pre-specified | band crossing only |
|---|---|---|
| synthetic, 6 settings | fires in 3 | fires in 6 |
| synthetic, 72-cell grid | fires in 20 | fires in 72 |
| coincides with the lower bound | -- | **72 of 72** |
| corpus A, primary level k = 25 | never fires | fires at 1, lower bound never fires |
| corpus A, k = 42 | 4 | **1, below the lower bound** |

An upper bound that equals the lower bound in every cell is not a second statistic, it is the first one
relabelled, and the bracket it forms has width zero. Worse, on corpus A the two statistics disagree in
the direction the design forbids: at the primary level the clique contrast sits **outside** its band at
every lead time from one to ten, so the specific statistic calls the relation distinguishable
everywhere, while the single-feature AUC sits **inside** its band at every one of them, so the sensitive
statistic calls it indistinguishable everywhere. The premise of the bracket is that one declares the
horizon closed early and the other late. They do the opposite.

So the interval is withdrawn and the estimand is a lower bound. The definition stays in print because a
rule that failed is evidence about the design, and because the alternative -- quietly deleting a
pre-registered rule that did not work -- is the thing pre-registration exists to prevent. Section 4,
Section 6.1.1, Section 9, the abstract, the highlights and the contribution list all move to lower-bound
language.

## D-49 — the second implementation, and what it found was a gap in the prose
**2026-08-24.** `penumbra/reference.py`, `scripts/verify_reference_density.py` ->
`results/reference_density.json`.

Section 9's first threat was that group density and the clique contrast were computed by one
implementation across all four testbeds. The survival likelihood has a slow reference checked against
closed forms to 1e-13; the density code had nothing.

`penumbra/reference.py` is written from Section 3's definitions and shares nothing with `umbra`. Where
`umbra` packs each dyad into one int64, sorts per (relation, year) and answers membership by
`searchsorted`, the reference stores a dict of tuples. Where `umbra` decomposes a candidate group into a
cached member-only count plus a star -- the optimisation most able to be subtly wrong -- the reference
enumerates every pair with `itertools.combinations` and caches nothing. It does not import numpy.

Exact agreement everywhere: 74,425 densities on the synthetic testbed, 784,585 star densities behind
Table 5, 39,582 candidate-group densities behind Table 6, and 101,600 on corpus B, where the pinned
CLIQUEBAIT library agrees exactly as a third implementation. Table 3's calibration was re-derived end to
end through the reference and returns the known width in 6 of 6 settings with bounds identical to
`umbra`'s. Corpus B had never been through `umbra` at all, its node ids being strings; relabelling the
accessions 0, 1, 2 is a bijection that changes no dyad, so all three implementations now compute that
table.

**The disagreement it did find was in the specification, not in the arithmetic.** The reference read
"level 1" literally, as weight at least one. Co-membership's weights count shared organisations and are
integers, so nothing changes there; trade flows carry log volumes from -3.98 to 3.54 and voting
agreement lies strictly inside the unit interval, so the literal filter empties one relation and
discards half of another. The two implementations disagreed by exactly 1.0 on those two stars, and by
0.1779 on the published Table 5. `umbra` was right: level 1 means presence, and the ladder is defined
for the integer-weighted target relation only. The prose never said so. Section 4 now does.

That is the outcome worth recording. A second implementation is usually justified as insurance against
arithmetic error, and it found none. What it actually tested was whether the specification had ever been
written down clearly enough for someone to build the thing twice, and the answer was no in one place.
Both implementations were written by the same people from the same prose, which is exactly why the gap
it found was a gap in the prose -- and why this narrows Section 9's exposure without removing it.

## D-50 — intervals on everything, and the five-period phantom is not a width
**2026-08-24.** `scripts/bootstrap_diagnostics.py` -> `results/bootstrap_diagnostics.json`.

A paper about a measuring instrument had no uncertainty on any headline magnitude. The task results
bootstrap over the 464 membership equivalence families; the diagnostics did not. The resampling unit was
already declared, so this was 300 lines and no new decisions: compute each row-level frame once, then
resample clusters over the stored rows, because every statistic here is a mean or a threshold crossing
of means and recomputing the graph statistics per replicate would multiply the cost of the paper by a
thousand and change no number. 1,000 replicates, percentile intervals, corpus A by family, corpus B by
complex, PTA by agreement, the synthetic testbed by coalition.

Three results the point estimates were hiding.

**The target relation and an anchor that cannot record the event are indistinguishable at eight
periods.** Co-membership 0.1490 with interval 0.1160 to 0.1768; trade flows 0.1463 with 0.1161 to
0.1755. At zero lead time they are separated. By the far end of the range the diagnostic examines, they
are not, and that is visible only with intervals.

**The five-period phantom is real in most samples and its width is not identified.** The residual first
falls below 0.01 at lead time 5 on the point estimate. Across replicates: median 4, 95 percent interval
0 to 7, and it never crossed inside eight periods in **222 of 1,000**. In **133** replicates the
residual was already below the threshold at zero lead time, meaning no phantom at all. The mode is 5 at
261 and the next is 4 at 201. "The pre-specified rule returns about five periods" was a number without
an interval, and with one it is a mode of a distribution spanning the whole examined range. This is
worse for the instrument than the point estimate was, which is the right direction for an honest
interval to move a claim about an instrument.

**The two corpora's ratios are not distinguishable, and that is not a rescue.** Corpus A's focal step
over pooled step is 6.80, interval 4.74 to 10.61; the PTA register's is 9.77, interval 8.78 to 11.05,
the numerator there being exactly 1 by entailment so the interval is the denominator's alone. The
intervals overlap, so the manuscript cannot claim the two ratios differ. It also cannot claim they are
the same factor, which is what the retired sentence did: two observations 44 percent apart with no
mechanism forcing a value, and an interval wide enough to contain both, support "close to an order of
magnitude, corpus specific" and nothing stronger.

Two smaller ones. Table 6's largest entry, 0.5833 on 24 events, has interval 0.3148 to 0.8096, which
overlaps the next bin's on 47 events; the peak at the smallest group sizes is not resolved, and Figure 6
must not be drawn as though it were. That works for mechanism (d) rather than against it, since (d) is
precisely the claim that where the statistic has power the sample is too small. And Table 3's six ticks
survive resampling unevenly: the rule lands on the target in 100 percent of replicates at beta = 0 and
1, 91 and 92 percent at 2 and 3, **67 percent at 4**, and 92 percent at 5, and it never undershoots at
any setting. An estimator that errs only upward is the right error profile for a lower bound; that it
errs at all on 90 events belongs beside the six ticks.

The structural zeros come through resampling as exact zeros with zero-width intervals, which is the one
place a flat interval is the correct answer rather than a missing one.

## D-51 — every corpus B density was exactly twice its value, and the checker had never been told
**2026-08-24.** `scripts/run_second_domain.py`, `scripts/check_paper.py` ->
`results/second_domain_thr400.json`, `results/second_domain_thr150.json`.

Found while writing the corpus B negative-sampling audit for D-46, and not by looking for it. Two
scripts computed a density for the same relation and disagreed: `corpus_b_negatives.py` said the
curated-register channel sits at 0.001153 and `second_domain.py` said 0.002305. The ratio is 2.0000.

STRING ships both directions of every interaction. The benchmark builder's own log says so, in as many
words, when it reports the channel edge counts. `run_second_domain.py` then computed

    dens = e.groupby("relation").size() / (n * (n - 1) / 2)

which divides a **directed row count** by an **unordered dyad count**. Every corpus B density it has
ever reported is twice its value, in all twelve channels at both thresholds, ratio 2.0000 to 2.0000 with
no self-loops to complicate it.

| | as reported | correct |
|---|---|---|
| target relation, threshold 400 | 0.0023 | **0.001153** |
| densest channel, threshold 400 | 0.0038 | **0.001887** |
| factor against LEDGER's 0.9954 | 431 | **864** |

Corrected in the script, in `results/`, in the manuscript's Table 2 and Section 6.4, in mechanism (b),
in `PENUMBRA-OUTCOMES.md` and in `SYNTHESIS.md`. The script now reports the directed count beside the
undirected one so the factor of two is visible rather than implicit, and the artefact carries the
convention as a note.

Four things worth recording.

**The verdict is untouched and stronger.** (b) says coalition relations saturate and protein relations
do not. Halving a density that was already three orders of magnitude below saturation cannot change
that, and the cross-domain factor doubles from 431 to 864. A defect that moves a headline number and
leaves the conclusion intact is the easiest kind to leave in place, which is why it lasted.

**`phi` was never affected**, which is why nothing else moved. Every clique contrast, every residual and
every figure in Section 6.4 comes from `LeakageAudit.densities()`, which builds a dyad key set and
therefore collapses the duplicate directions. D-49's reference implementation agreed with it exactly on
all 101,600 values. The defect lived only in the summary table, which is the one number in that script
that nothing else recomputes.

**None of the three affected numbers was registered in `check_paper.py`.** The checker held 76 claims
about this manuscript and a density that appears in a table row and in a mechanism statement was not one
of them. Registered now, with the density, the maximum and the ratio all read from the artefact. The
lesson is the coverage lesson of D-45 arriving a second time: a checker's value is bounded by what it
was told to check, and the tokens it does not cover are exactly where a defect can sit for months.

**It was found by computing the same quantity twice for a different reason.** The audit that found it
was written to answer a reviewer's question about negative sampling, not to check a density. That is the
fourth of Section 8's four questions in a form the section does not state: *what happens if two code
paths compute the same number?* The existing four ask what produced an artefact, what it derives from,
whether anything calls it, and how much it moves under a nuisance change. None of them catches a number
that is consistently, reproducibly, provenance-stamped wrong. Two independent computations do, and that
is the same argument D-49 makes for the density code, arriving from a defect rather than from a threat.

## D-52 — auditing the revision, and the revision that added the intervals shipped two numbers without one
**2026-08-24.** `penumbra/synthetic.py`, `scripts/run_synthetic_homophily.py`,
`scripts/bootstrap_diagnostics.py`, `scripts/check_paper.py` ->
`results/synthetic_homophily.json`, `results/bootstrap_diagnostics.json`.

D-46 to D-51 were the revision. This is the audit **of** the revision, run on the same terms, and it is
recorded because the audit found five things and four of them were mine.

**Two numbers I introduced lived only in prose.** Section 5.2's new paragraph justified the parametric
generator's density constant with a measured worst case, "peaks at 1,794 eligible dyads of 19,900
pairs". Both figures came from an exploratory run and neither was in any artefact. That is D-45's defect
exactly, committed in the text written to report the revision, and it took the same coverage sweep to
find it: 366 distinct numeric tokens in the running text, 350 derivable from `results/`, sixteen orphans
of which eleven are reference years. `generate_parametric` now records the eligible-dyad count per year,
`run_synthetic_homophily.budget_headroom()` measures the peak across the widest settings used, and both
values are registered. Coverage is 96 percent against the 15 percent D-45 measured.

**One headline magnitude still had no interval after the pass that added intervals.** Section 6.3's
declared-resolution width, 0.1419, is the paper's only positive field measurement of a leakage horizon
on corpus A, and D-50 gave intervals to everything around it and not to it. Added as a sixth bootstrap
pass, clustered on families like the rest:

| stratum | events at one period | families | presence at one period |
|---|---|---|---|
| declared resolution | 310 | 42 | **0.1419 [0.0678, 0.2395]** |
| exact | 7,084 | 328 | 0.0 [0.0, 0.0] |

The interval spans a factor of three and a half, which matters for how the finding is stated: the
**width** is one period and the **share** of events carrying it is anything between one in fifteen and
one in four. The exact stratum's zero-width interval beside it is what an entailment looks like next to
a measurement, and putting the two rows together says more than either does alone.

**The inverted interval was not new, and the manuscript nearly claimed it was.** D-48 reports that
$\Delta^\star_{\text{lo}}$ can exceed $\Delta^\star_{\text{hi}}$ on corpus A. V8 and D-30 already
reported exactly that on the alliance subcorpus, on a superseded build, and attributed it to power: the
stratum had lost 47 percent of its positives and a bound that moves with the sample looks like a sample
problem. It was not one. The same inversion is present on the current corpus, in the organisation
stratum, at full sample, and the synthetic grid puts the repaired bound *on* the lower bound in all 72
cells. Three cuts, two corpus builds, one failure: that is a property of the two statistics and the
manuscript now says so, crediting the earlier observation rather than rediscovering it. Reading one's
own back catalogue is cheaper than the measurement that would establish the same thing.

**Two programme documents were left quoting a number the manuscript had corrected.**
`PENUMBRA-OUTCOMES.md` still said the upper bound fired in 2 of 6 settings after D-46 had established
three, and both it and `SYNTHESIS.md` carried the doubled corpus B densities until D-51 reached them.
The manuscript has a checker and the reconciliation documents have a different one, and neither of them
checks the *other* document's prose against the artefact. Corrected in both, with the prior value and
the correcting decision named in place, which is this project's convention and the only reason the drift
is visible at all.

**And the checker caught me.** Editing `PENUMBRA-OUTCOMES.md` through a shell heredoc put a raw control
byte where a LaTeX escape was meant, `$\beta$` becoming a backspace. `check_consistency.py` has a rule
for exactly that, added the first time it happened, and it failed the run within seconds. A byte-level
check on a document nobody executes earns its place: the file would have rendered as `$eta = 0$` and
read as a typo rather than as corruption.

The transferable point is short. A revision is work, so it needs the audit that work needs, and the fact
that the revision's own subject was measurement discipline bought no exemption whatsoever. Three of the
four defects above are in text written to describe how carefully the numbers had been checked.

## D-53 — the figures are drawn from the artefacts, because a checker cannot read a drawing
**2026-08-24.** `penumbra/figures.py`, `scripts/build_figures.py`, `scripts/build_paper.py`,
`scripts/check_paper.py` -> `results/figures.json`, `paper/Figures/figure-1..7.{svg,pdf,png}`.

D-46 found four defects by external read and two of them were in figures: panel A of Figure 3 drew a
decline the data do not contain, and Figure 2's upper-bound row named the wrong two settings. Neither
was reachable by anything we had. `check_paper.py` compares a number in the text against the artefact
it came from; a diagram is not text, and the numbers in these diagrams had been typed in by hand.

So the figures are now drawn from `results/` by a script. Seven figures, one function each, every
series read from an artefact rather than transcribed. The two defects above cannot recur in the class
they belong to: there is no second copy of a series to disagree with the first.

**What this closes, beyond the two defects.** The manuscript's data availability statement has always
said that every reported figure is regenerated by a named script. That was true of the *numbers* and
not of the figures, which were drawn by hand in a diagram editor. It is now true as written.

**What it also fixed, found while drawing.** Reading each figure back as an image after rendering it
caught a class of problem the specifications could not: labels that collide, an inset that covers the
encoder it describes, a rotated annotation running the height of two tiers, and five identical step
functions overplotted into one. None of these is a data error and all of them would have reached a
reader. The specifications had been written carefully and none of them predicted a collision, because
a specification describes what to draw and not what the drawing then looks like.

**The manuscript is 3,300 words shorter.** The specifications were drawing briefs sitting in the body
text, and they were always going to be removed before submission; they now live as the docstring of
the function that draws each figure, which is where a drawing brief belongs. Section 6.5's reviewers
will still say the paper reads like three papers, but it is no longer three papers plus a set of
instructions to an illustrator.

**Three formats, and each has a job.** `.svg` is what the manuscript references and what Word 2016
and later render through the `svgBlip` extension; `.pdf` is what an Elsevier submission wants; `.png`
is the raster fallback. That last one is not decorative. Pandoc writes the picture with `svgBlip` and
**no `r:embed` on the blip itself**, so a reader without SVG support gets nothing at all, and
`build_paper.py` now injects the PNG beside each SVG the way Word's own insert does. The authors'
earlier document pairs them the same way, which is how we knew what the target looked like.

**Two build defects surfaced in the process, both of the silent-success kind.** Pandoc resolves
relative image paths against the working directory rather than the source file, so the first build
after the change produced a clean document with **zero** figures in it and reported success.
`build_paper.py` now passes a resource path and, more to the point, fails when the number of images in
the document is below the number of figure captions. And `check_paper.py`'s old rule that every value
in a figure specification be derivable from an artefact became vacuous the moment the specifications
left the manuscript; it is replaced by a rule that every referenced image exists, was recorded as
built by the generator, and that no figure the generator produces goes unreferenced.

The transferable point is the one D-51 made from a different direction. A check is worth what its
coverage is, and the coverage gap that mattered here was not a number nobody registered: it was an
entire artefact class, the figures, that no check could reach at all. The fix was not a better checker.
It was removing the second copy.
