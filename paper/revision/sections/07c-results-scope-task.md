### 7.6 A scope test on the inverse size distribution

Three mechanisms in Section 8 are claims about any curated group corpus, and a fourth, saturation, is a claim whose scope a second domain can settle. We test all four on corpus B, whose size distribution is the inverse of corpus A's. Every statistic is computed by the same pinned implementation, so a difference between domains cannot be an implementation difference.

| Members | 2 to 3 | 4 to 5 | 6 to 10 | 11 to 20 | 21 to 80 | 81 and above |
|---|---|---|---|---|---|---|
| Corpus B positives | 1,399 | 641 | 321 | 142 | 34 | 3 |
| Corpus B contrast, $k = 1$ | 0.4124 | 0.4665 | 0.4455 | 0.3662 | 0.1765 | 0.0000 |
| Corpus B negative cliques | 0 of 1,399 | 0 of 641 | 0 of 321 | 0 of 142 | 0 of 34 | 0 of 3 |
| Corpus A positives | 24 | 47 | 289 | 751 | 2,801 | 2,685 |
| Corpus A contrast, $k = 25$ | 0.5833 | 0.3617 | 0.3391 | 0.2437 | 0.0521 | 0.0000 |
| Corpus A contrast, $k = 1$ | 0.0625 | 0.1809 | 0.1972 | 0.1911 | 0.2387 | 0.4778 |

**Table 7.** Clique contrast by group size, both corpora, with matched or random negatives respectively. Full 95 percent intervals are in the supplementary material.

The size dependence of the clique statistic generalises. Both corpora decay with size and both are identically zero above eighty members, in domains sharing no entities, no relations and — for corpus B — no time axis. The two sample opposite ends of the range: 5,486 of corpus A's 6,597 events fall in groups above twenty members, against 1,399 of corpus B's 2,540 complexes at three members or fewer. The series share a shape and not a level, and we do not compare heights, because they are read at different levels of the ladder. These are two decreasing functions read at two levels, not one function traced twice, which is what Figure 8 draws.

A zero negative clique rate is what a correct sampler produces, not evidence about it: a clique on $n$ members needs all $\binom{n}{2}$ dyads and the curated-register channel has density 0.00115, so the expected count over the smallest bin's negatives is two millionths of a group. What does carry information is the hard stratum, which keeps most of a real complex and swaps two members out; there the smallest bin yields 9 cliques of 2,798 negatives at a contrast of 0.4092, against the random stratum's 0.4124. The last row of Table 7 is then the one to read against the two above it, because at a level where the target relation is saturated the size dependence *reverses*, rising with group size instead of falling. A claim about clique-based statistics that does not name its level is false at the level a reader would assume.

Three claims change status here. One is **falsified and restated**: we had claimed that group size and sample size trade off in any curated group corpus, so that no subpopulation offers both, yet corpus B offers 1,399 positives at two to three members with a contrast of 0.4124 and a negative clique rate of 0.0000. The trade-off holds only where group size correlates with entity type and the small-size type is rare, which is corpus A exactly. One **narrows, and the controlled test reverses its explanation**: the finding that the anchors carry the same homophily as the target relation does not transfer, since on corpus B the target relation contrasts 0.4240 against a strongest anchor of 0.0165, leaving a residual of 0.4075 with the remaining anchors flat. In international relations, trade, voting agreement and co-membership express one latent quantity, so subtracting one from another removes almost nothing, whereas messenger RNA co-expression bears no such relation to a curator's complex boundaries. Corpus B is therefore the independent-anchor case of Section 7.2, and the only reason its residual is not a phantom horizon is that it has no time axis for one to live on. One is **confirmed in scope**: no relation in corpus B exceeds density 0.001887 against corpus A's 0.9954, so nothing here saturates.

Finally, a documentary reading placed the leaking channels. The three channels declared contaminated on documentary grounds came out ranked first, second and third on clique contrast, at 0.4579, 0.4240 and 0.3075, above every declared anchor at 0.0165 or below. Whether that is a *prospective* test depends on an ordering the repository cannot confirm, for the reason Section 6.1 gives. What a reader can take without trusting our account is weaker and still worth having: a documentary reading of ten channels is consistent with a ranking it did not use, and the procedure is cheap enough for anyone to run prospectively.

[FIGURE 7]

**Figure 8.** The same shape in two domains, read at two levels, and a reversal when the relation saturates. Clique contrast against group size in six bins, at zero lead time in both corpora.

### 7.7 What the horizon costs a forecaster

A reader will reasonably ask whether the underlying prediction problem is tractable at all. Table 8 gives the accession task: a dyad-level discrete-time hazard over 2,197,744 candidate periods with 6,501 event dyads, evaluated at four rolling origins and four lead times with a cluster bootstrap over families.

| Rung | Features | Pooled AUC | Within-group AUC | Calibration slope |
|---|---|---|---|---|
| 1, duration only | 1 | 0.476 to 0.715 | 0.461 to 0.524 | −0.13 to 1.03 |
| 2, plus node covariates | 22 | 0.794 to 0.911 | 0.527 to 0.632 | 0.67 to 1.02 |
| 3, plus relational densities | 34 | 0.798 to 0.915 | 0.566 to 0.688 | 0.65 to 0.96, mean 0.83 |

**Table 8.** Accession task, corpus A. Each rung must beat the one below on both metrics.

The two discrimination metrics differ by about 0.25, and that gap is a finding rather than a nuisance. Pooled, the model scores 0.798 to 0.915; holding the group fixed and asking only which candidate accedes, it scores 0.566 to 0.688. Most of the pooled discrimination is therefore between-group and between-entity structure: which groups grow, and which entities join things in general. A reader who wants to know whether the model picks the right candidate is reading the wrong number. Relational densities add 0.0089 pooled and 0.0430 within-group, nearly five times more once the group is held fixed. A second task, the termination of a group, is in the supplementary material; its cause-specific discrimination of 0.628 and 0.559 shows that the tractability question does not transfer.

Table 9 gives the architectural comparison, and Figure 9 plots it against parameter count.

| Encoder | Parameters | Mean AUC, 4 seeds | SD, 4 seeds | Mean AUC, 10 seeds | SD, 10 seeds |
|---|---|---|---|---|---|
| Graph-free MLP, width 64 | 54,849 | 0.8602 | 0.0023 | 0.8623 | 0.0042 |
| Graph-free MLP, width 96 | 80,993 | 0.8623 | 0.0064 | 0.8644 | 0.0056 |
| Graph-free MLP, width 128 | 109,185 | 0.8616 | 0.0020 | 0.8630 | 0.0033 |
| Homogeneous message passing | 59,649 | 0.8593 | 0.0029 | 0.8532 | 0.0066 |
| Relation-specific message passing | 78,849 | 0.8744 | 0.0065 | 0.8743 | 0.0043 |
| Temporal encoder over the graph history | 103,937 | 0.8830 | 0.0019 | 0.8822 | 0.0031 |

**Table 9.** Architectural comparison, corpus A. Mean pooled AUC and seed standard deviation, at four seeds and at ten.

Two margins survive and one changes sign in significance. The relation-specific encoder beats its parameter-matched control by 0.0100 at ten seeds against 0.0121 at four, so the margin shrinks while its significance rises from 2.7 standard errors to 4.5. The temporal encoder beats its control by 0.0192 at ten seeds, 13.4 standard errors. Widening the graph-free control buys 0.0014 from width 64 to 128 at four seeds and 0.0007 at ten, non-monotone at both counts, so neither gain is capacity. The homogeneous encoder is worse than its control, and at four seeds it did not look it: its margin was $-0.0009$, half a standard error, winning exactly 24 of 48 cells, whereas at ten seeds it is $-0.0091$, 3.7 standard errors, winning 25 of 120.

One pattern bears directly on the horizon argument. The graph's contribution is largest at the shortest lead time and erodes with distance: over the width-64 rung the temporal encoder gains 0.0227 at one period against 0.0202 at ten, and the relation-specific one 0.0178 against 0.0095. This reverses the rationale usually offered for relational features at long horizons, namely that structure should matter more as covariates go stale. It is what the horizon argument predicts: relational features derived from a register are worth most exactly where that register's dating conventions make them least trustworthy.

[FIGURE 8]

**Figure 9.** Message passing against a capacity-matched control, with the seed spread that settled it. Corpus A accession task, mean pooled AUC over ten seeds against parameter count, six encoders, with the seed standard deviation as the error bar.
