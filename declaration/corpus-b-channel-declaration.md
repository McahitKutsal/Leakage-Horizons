# Corpus B channel declaration

**Status: not timestamped.** This text assigns the ten STRING channels to target,
contaminated and anchor. It was written in the analysis script's docstring before that
script was run, which is our account of the order and is not corroborated by version
control: the script was not committed before it was run, and the pre-registration in
`pre-registration.md` does not name the channels. A reader is entitled to treat the
prospective reading of Section 6.6 as our word about our own procedure. What is
checkable is the content and the result: the assignment below is the one the released
code uses, and the ranking it predicts is reproducible from that code.

Reproduced verbatim from the docstring of `scripts/run_second_domain.py`:

```
The second domain: are SYNTHESIS section 2's (b), (c), (d) and (h) general or particular?

Three of the ten failure modes the paper rests on are claims about **any** curated group corpus, and all
three were measured on one. That is the largest remaining risk to the contribution, and CLIQUEBAIT's
protein benchmark is the adversarial test rather than a confirmation run, because its size distribution is
the **opposite** of LEDGER's: 2,540 complexes with a median of 3 members and 1.6 % above twenty, against
LEDGER's positive strata averaging 66 with 36 % above eighty.

**The statistics come from the pinned CLIQUEBAIT library, not from a reimplementation.** `LeakageAudit`
computes $\phi_r(S)$ and the clique contrast $P(\phi = 1 \mid \text{pos}) - P(\phi = 1 \mid \text{neg})$,
which is the statistic (c) and (h) are about, and its `Group` already carries a `'__static__'` time, so
the timeless case needs no adaptation. Only the size stratification is PENUMBRA's own (V3).

What each claim predicts here, written before the numbers:

**(b) a saturating relation hides the shadow.** Says coalition relations saturate — IGO co-membership has
density 0.995. If the protein relations are far from saturated, (b) is a claim about *coalition* relations
specifically, which is what it says, and the benchmark confirms the scope rather than the claim.

**(c) the exact-clique statistic is structurally zero on large groups.** Predicts the contrast has
*power* here, since 98 % of complexes are under twenty members and V3 measured 0.20-0.25 in that range.
**Falsified if the contrast is near zero on small protein complexes too** -- that would mean (c)'s
mechanism is not size.

**(d) there is no subpopulation where both problems go away.** The strongest test, and the one that can
break. This corpus has 2,540 positives *and* a median size of 3 -- size and sample favourable at once,
which LEDGER never offers. **If the contrast separates cleanly from its band here, (d) is false as
stated** and has to be restated as a property of coalition corpora rather than of curated group corpora.

**(h) the band cannot subtract homophily.** Testable only in its zero-lag form: do relations that cannot
record complex membership show the same contrast as the one that does? The horizon-resolved form does not
transfer -- this benchmark has no time axis, so there is no penumbra here and none is looked for.

$r^\star$ and the anchors are declared from what each STRING channel records, before any number is read,
which is section 5.4 applied to a new domain:

* $r^\star$ = **`database`** (and `database_transferred`). STRING's database channel imports CORUM and
  ComplexPortal -- the label source itself. Exactly analogous to `igo_comembership` being built from the
  file that supplies T1's labels: it leaks by construction, and that is the object of study.
* **Contaminated, and therefore not anchors**: `textmining` reads papers that describe complexes, and
  `experiments` covers co-immunoprecipitation and affinity purification, which *detect* complexes. Both
  can carry the label through a route that is not the database channel.
* **Anchors** = `coexpression`, `coexpression_transferred`, `fusion`, `cooccurence`, `homology`. mRNA
  correlation, gene-fusion events, phylogenetic co-occurrence and sequence similarity cannot record a
  curator's decision that a set of proteins forms a complex.

Negative strata are reported separately because V0 was retracted for pooling them: this benchmark ships
`random` and `hard` negatives and their group sizes are already matched to the positives (median 3, mean
5.1 on both sides), so the defect V0 records cannot arise here.

    python scripts/run_second_domain.py
    python scripts/run_second_domain.py --threshold 150
```
