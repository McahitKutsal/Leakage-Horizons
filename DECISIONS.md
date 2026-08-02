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
| accessions | 335 multilateral | **6,290** |
| terminations | **26** multilateral | 135 candidates |
| exits | 756 member-level | 901 |

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

Unverified and open: `death_candidates_in_era` is last-observed-year, not COW's coded
dead/dormant status. The unit-level file has not been checked and must be before any T2 number
is quoted.

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
