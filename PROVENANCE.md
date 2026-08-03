# Provenance, per relation and per event source

§5.4 requires this and says it is load-bearing rather than boilerplate: *"For each relation, the
paper must state what the source records as the start date: signature, ratification, entry into
force, or first observed activity."* PROTOCOL §1 puts it before everything else and adds that
coverage must be verified against the **materialised** artefact, not the documentation.

Nothing here is a statistic. The whole point of §5.4 is that no statistic can settle it — a
genuine precursor and an administrative back-dating produce the same edge — so the verdict comes
from reading the coding rules. What the automated diagnostics do is decide which relations to read
about first.

Evidence: `scripts/parse_igo_provenance.py` → `results/igo_provenance.json`,
`scripts/build_graph.py` → `results/graph_coverage.json`,
`scripts/audit_corpus_scale.py` → `results/corpus_scale.json`.

---

## 1. What each relation records as its date

| relation | source | date the record carries | back-dating risk |
|---|---|---|---|
| `igo_comembership` | COW IGO v3 membership | **first year the organisation functions**; members by year of entry, with 5 documented exceptions | **low, and measured — see §2** |
| `allies` | ATOP v5.1 defence pacts | treaty in force: `begyr/begmo/begday`, member `yrent` | **unverified** — codebook unreachable, see §4 |
| `trades` | IMF IMTS/DOTS | reporting year of the trade flow | none: a flow is not an event |
| `votes_with` | UNGA ideal points, k-NN k=30 | calendar year of the roll-call session | none, but see the 1964 hole |
| `conflicts_with` | COW MID 5.0 | dispute onset year | none |

## 2. COW IGO does not systematically back-date, and this was read rather than assumed

The v3 short codebook contains the warning and not the evidence: *"we begin to code an IGO by
identifying the first year in which the organization functions. In some cases, individual members
are listed by year of accession or signature. These exceptions are listed below (see section IV)"*
— and it omits section IV. **The exceptions list exists only in the v2.1 codebook**, 93 pages of
per-organisation notes, which is why it had to be found rather than looked up.

Parsed: **495 records, exactly the 495 the codebook states.** Of these, **5** mention signature or
accession dating, and reading all five is the whole verdict:

| ionum | organisation | what the note says | direction |
|---|---|---|---|
| 2950 | International Oil Pollution Compensation Funds | "Members coded according to first convention signed" | **back-dated** |
| 290 | ASECNA | "subsequent listings suggest it was formed when a convention was signed" | founding back-dated, members not |
| 3190 | International Tropical Timber Organization | "Treaties signed in 1985, no organization until 1987" — and `formed` is coded **1987** | **explicitly refuses to back-date** |
| 3440 | Latin Union | founded 1954 on signature, but "membership is coded only for 1983 onward" | **forward**-dated |
| 3400 | Latin American Educational Film Institute | emanation status, not dating | not a dating case |

So the page-5 caveat describes a handful of cases, one organisation back-dates membership, and one
explicitly declines to. **Signature back-dating is not the mechanism by which the penumbra would
appear in this corpus.** That is a substantive finding and it bears directly on P1: if the relation
carrying $r^\star$ for 493 of 573 entities does not anticipate, the penumbra for organisation
entities has to come from somewhere else or be narrow.

Two other mechanisms displace dates in this source and neither is signature back-dating:

- **The ten-year plenary rule.** An organisation is dead once ten consecutive years have passed
  without a plenary session, so 103 of 157 terminations carry a date assigned from data up to a
  decade later. This is §9.7's category and it moves the timestamp *forward* in knowability while
  leaving it *early* in the record — the opposite displacement from a penumbra.
- **Pre-1965 imputation.** 1,388 organisation-years, none after 1964, block-resolved onto the
  Wallace-Singer five-year grid. A width, not an anticipation.

## 3. Coverage: the documentation and the data disagree in both directions

486 organisations appear in both v2.1's notes and v3's data. Cross-checking the declared
missing-data years against the materialised `-9` cells:

| | organisations | organisation-years |
|---|---|---|
| declared missing, **not** `-9` in the data | 18 | 80 |
| `-9` in the data, **not** declared | **45** | **205** |

The second row is what PROTOCOL §1 exists for. The largest undeclared gaps are the Commonwealth
Telecommunications Board (24 years), the Commonwealth Air Transport Council (16), the International
Chemistry Office (11), the Arab Industrial Development and Mining Organization (10) and the
International Commission of Agricultural Industries (10).

**48 of v3's 534 organisations have no provenance notes at all**, because they were added after
v2.1. Nine organisations in the notes are absent from v3. Both lists are in
`results/igo_provenance.json`; neither is dropped silently.

**Dormancy is textual, not coded.** 16 organisations carry *inactive* or *dormant* in their notes
while no variable records it, which is what §4's corrected T2 says: dormancy is what death *means*
in this source, through the ten-year rule, rather than a cause beside it.

## 4. What remains unread, and what that blocks

**ATOP's codebook is unreachable.** `atopdata.org` refuses the TLS handshake from this network, as
CLIQUEBAIT also found. Three consequences, each stated rather than worked around:

1. `termmode` and `termcaus` cannot be interpreted, so ATOP terminations enter LEDGER as events
   without causes and T2's competing risks rest on COW IGO alone (LEDGER.md §2.2).
2. Whether `allies` dates a pact from signature, ratification or entry into force is **unverified**.
   `begyr/begmo/begday` and `yrent` are day-resolved, which is consistent with a legal date rather
   than a coding convention, but consistency is not evidence. Until it is read, the alliance
   relation cannot serve as a declared non-back-dating anchor for the C17 band.
3. CLIQUEBAIT's construction choice — defence pacts only — is documented in its own FINDINGS §4 and
   is inherited unchanged, so that part needs no re-reading.

**The 1964 `votes_with` hole.** Zero edges, the only such year in 1946–2016, confirmed in
CLIQUEBAIT's own rebuilt snapshot. The probable cause is that the nineteenth General Assembly
session took no recorded votes during the Article 19 crisis. **Unverified against the ideal-point
release's own documentation.** The handling does not depend on it — 1964 is its own coverage regime
either way — but this paragraph does.

## 5. The C17 anchor declaration, as far as it can go now

C17 requires the non-leaking band to be anchored on a relation **known from the coding rules** to
record without back-dating, not merely believed not to leak. On the evidence above:

| relation | eligible as a band anchor | why |
|---|---|---|
| `trades` | **yes** | a reporting-year flow cannot anticipate an event |
| `conflicts_with` | **yes** | dispute onset, no accession process to record early |
| `votes_with` | **yes**, outside 1964 | a roll-call happens or it does not |
| `igo_comembership` | **as $r^\star$, not as an anchor** | it is built from the label source; §2 shows it does not systematically anticipate, which is a finding about $r^\star$ rather than a licence to use it as a reference |
| `allies` | **undecided** | blocked on the ATOP codebook, §4 |

Anchors for the first real-data $\Delta^\star$: `trades`, `conflicts_with`, `votes_with`. Recorded
so that the band is fixed before the curve is computed, which is the only order in which either
means anything.
