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
the relation that carries $r^\star$ for 493 of 573 entities. If the penumbra is there it comes from
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
