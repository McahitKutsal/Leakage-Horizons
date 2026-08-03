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
