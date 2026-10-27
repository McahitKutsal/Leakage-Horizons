## 7. Results

The results run from the testbed, where the width is a parameter we set, to two field corpora, where it is a property of a register we did not build. They end at what the horizon costs a model trained across it.

### 7.1 Calibration against a width the generator sets

Table 3 reports the pre-specified rule at six settings of the back-dating parameter. The estimand implied by the definition is $\beta + 1$: traces are present for $\Delta \leq \beta$, so the smallest trace-free lead time is one period beyond.

| Width regime | Target | $\widehat{\Delta}^{\star}$ | On target | Replicates on target | 95 percent interval |
|---|---|---|---|---|---|
| sharp, $\beta = 0$ | 1 | 1 | yes | 100 percent | 1 to 1 |
| sharp, $\beta = 1$ | 2 | 2 | yes | 100 percent | 2 to 2 |
| sharp, $\beta = 2$ | 3 | 3 | yes | 91 percent | 3 to 5 |
| sharp, $\beta = 3$ | 4 | 4 | yes | 92 percent | 4 to 6 |
| sharp, $\beta = 4$ | 5 | 5 | yes | 67 percent | 5 to 7 |
| sharp, $\beta = 5$ | 6 | 6 | yes | 92 percent | 6 to 8 |
| trade-register gaps, against the realised maximum of 4 | 5 | 5 | yes | not resampled | |
| trade-register gaps, against the realised median of 1 | 2 | 5 | no, high by three | not resampled | |

**Table 3.** Calibration against a known back-dating width. Primary comparison stratum, 90 accession events per setting; the last two columns resample coalitions over 1,000 replicates.

The estimate lands on the target in **6 of 6** settings, and Figure 3 plots the six against the target line. At $\beta = 4$ the rule returns the target in two replicates of three and overshoots by one or two in the rest. It never undershoots, in any replicate, at any setting.

Both halves of that matter. Read as a lower bound, the rule fails 33 percent of the time at $\beta = 4$, and a bound that comes back above the quantity it bounds is wrong rather than cautious. Read as a conservative estimate under the asymmetry of Section 4.2, the same number is a 67 percent coverage rate with every miss on the side that discards data. One cell is a negative control: at homophily $h = 0$ and $\beta = 0$ there is nothing to find, and all four estimators return the correct value of 1.

The interval's upper end is not identified, and the obvious repair does not repair it. As specified it fired in 3 of 6 settings and was unreachable in the rest, because it requires $r^{\star}$ to lose top rank and a structurally similar anchor keeps contesting that position. Dropping the rank condition makes it fire in 72 of 72 cells of the wider grid and land on $\widehat{\Delta}^{\star}$ in every one, so the interval it forms has width zero. The failure survives a corpus rebuild, a change of stratum and a change of sample size, so it is a property of the two statistics and not of a sample. We report **instrumental non-identification of the upper end** and withdraw the interval.

[FIGURE 2]

**Figure 3.** How the estimate is formed, and that it lands on the target six times out of six. Synthetic testbed, six settings of the back-dating width, 200 nodes and 90 accession events per setting, clique contrast at level $k = 1$ on the never-event stratum, lead times 1 to 8.

### 7.2 Homophily against back-dating: a measured identification failure

Section 2.4 states that a pooled contrast sums an administrative trace and a persistent similarity, and that no contrast of that form separates them. On a field corpus the claim cannot be tested, because the trace is the unknown. On the generator it can: the width is set, **homophily** — the tendency of similar entities to be tied — is a dial, and an estimator's error is a function of that dial. We sweep six homophily settings against six widths in each of two anchor regimes, 72 corpora, and grade four estimators against the target $\beta + 1$.

Each cell of Table 4 gives three numbers: the mean error across the six widths, the least-squares slope of the estimate on the true width, and the number of widths censored at the top of the examined range. A slope of 1 means the estimator tracks the truth; a slope of 0 means its output is unrelated to the quantity it estimates. An estimate may be biased and still informative; an estimate with slope 0 is not.

| Anchors | $h$ | Focal isolation | Clique estimate | Residual rule | Unbanded rule |
|---|---|---|---|---|---|
| share the latent space | 0.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 |
| | 0.5 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 |
| | 1.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 |
| | 2.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | +4.33 / −0.03 / 4 |
| | 3.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | +5.50 / 0.00 / 6 |
| | 4.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | +5.50 / 0.00 / 6 |
| independent | 0.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 |
| | 0.5 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 |
| | 1.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 |
| | 2.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | +2.00 / +0.54 / 1 | +4.33 / −0.03 / 4 |
| | 3.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | +5.33 / −0.03 / 6 | +5.50 / 0.00 / 6 |
| | 4.0 | 0.00 / 1.00 / 0 | 0.00 / 1.00 / 0 | +5.50 / 0.00 / 6 | +5.50 / 0.00 / 6 |

**Table 4.** Identification. Mean error / slope on the true width / censored widths, per estimator and homophily setting, in each anchor regime.

Read the last column down. Up to $h = 1$ the unbanded rule is exact. At $h = 2$ its mean error is four and a third periods and its slope has collapsed to $-0.03$. At $h = 3$ and above it reports the largest lead time examined at every one of the six widths, so its output is a constant. Nothing about the corpus changed except how strongly entities close in the latent space are tied. The instrument reads that closeness as back-dating.

A constant at the top of a range is a fact about the range as well as the estimator, so we reran the collapsed cells over lead times to twenty. The estimates move with the range, which confirms the censoring, but the dependence on the truth does not come back: at $h = 3$ both the unbanded rule and the residual rule with independent anchors return a slope of $-1.09$, the latter with nothing censored. A wider range therefore turns a slope of zero into a slope of about minus one. The censored zero understated the failure; it did not manufacture it. Every cell whose slope is 1.00 has censoring zero, and rerunning those cells over the wider range returns the identical six estimates.

Homophily is one word for several mechanisms, so we reran the grid under a bounded logistic kernel and under a block kernel that discards latent distance for discrete latent communities. The three collapse at different values of $h$, which is a failure of comparability rather than kernel dependence, since each concentrates edge weight differently at the same value. We therefore report the collapse against a quantity a field corpus also has: the strongest anchor's clique contrast at level 1 on the never-event stratum, read at one period. On that scale the two kernels that reach the collapse agree about where it is. The unbanded rule loses the truth at an anchor clique contrast of **0.0152** under the power kernel and **0.0186** under the block kernel, a difference of about a fifth between mechanisms sharing no functional form. The logistic kernel never exceeds 0.0063 at any $h$ we swept, so it fails to reach the concentration at which the collapse happens rather than resisting it.

Corpus A's strongest anchor, trade flows, has a clique contrast of **0.0259** at the same level and lead time, so the corpus sits above both thresholds. It is worth being exact about what that carries. It does not show that corpus A's phantom horizon is *caused* by homophily, because the trace there is unknown. It shows that the regime in which the pooled statistic provably loses identification is not an extrapolation past anything real.

Focal isolation, by contrast, is unbiased in homophily everywhere: its column reads 0.00 / 1.00 in all twelve cells. It reads the group's own record, and no amount of similarity between a candidate and the members puts that candidate on that record. Robustness to seed, range and kernel is reported in the supplementary material, as is a calibration of dating noise that reproduces corpus A's declared-resolution stratum from the other direction.
