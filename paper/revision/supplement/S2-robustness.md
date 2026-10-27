## S2. The full robustness grid behind the identification result

Section 7.2 reports that the pooled statistic's slope on the true width collapses as homophily concentrates, and summarises four passes that answer what one seed, one range and one kernel cannot. Table S2 gives every pass.

The first pass reruns the entire grid under three homophily kernels and reports where each one breaks the unbanded rule, on a scale a field corpus also has: the strongest anchor's clique contrast at level 1 on the never-event stratum, read at one period. The second reruns the whole grid at three seeds and reports the largest per-seed spread of the slope any homophily setting produces. The third takes five seeds on the transition rows, where an estimator is neither exact nor fully collapsed. The fourth reruns the collapsed cells over lead times to twenty, two and a half times the original range.

| Pass | Cell | Estimator | Result |
|---|---|---|---|
| three kernels | whole grid, power kernel | unbanded rule | collapses between $h = 2$ and 3, at an anchor clique contrast of 0.0152 |
| three kernels | whole grid, block kernel | unbanded rule | collapses between $h = 1$ and 2, at an anchor clique contrast of 0.0186 |
| three kernels | whole grid, logistic kernel | unbanded rule | never inside the range, and never exceeds an anchor contrast of 0.0063, below both thresholds |
| three kernels | whole grid, all three | focal isolation, clique estimate | slope 1.00 throughout, in both anchor regimes |
| reference | corpus A, strongest anchor | none, this is the field value | anchor clique contrast 0.0259 at level 1 and one period, above both thresholds |
| three seeds, whole grid | all 36 settings, shared anchors | focal isolation, clique estimate, residual rule | slope 1.00 at every setting and every seed; largest spread 0.000 |
| three seeds, whole grid | all 36 settings, independent anchors | focal isolation, clique estimate | slope 1.00 at every setting and every seed; largest spread 0.000 |
| three seeds, whole grid | independent anchors | residual rule | largest spread 0.273, at $h = 3$ |
| three seeds, whole grid | both regimes | unbanded rule | largest spread 0.786, at $h = 2$, which is the transition |
| five seeds | $h = 1$, both regimes | all four | slope 1.00, spread 0.00, every seed exact |
| five seeds | $h = 2$, shared anchors | residual rule | slope 1.00, spread 0.00, every seed exact |
| five seeds | $h = 2$, independent | residual rule | slope 0.88, range 0.54 to 1.00, SD 0.20; mean error +0.43, range 0.00 to +2.00 |
| five seeds | $h = 2$, both regimes | unbanded rule | slope 0.87, range −0.03 to +1.51, SD 0.56 |
| five seeds | $h = 3$, both regimes | clique estimate | slope 0.97, range 0.86 to 1.00, SD 0.06; mean error +0.03 |
| five seeds | $h = 3$, independent | residual rule | slope 0.14, range −0.03 to +0.46, SD 0.22; mean error +4.67 |
| five seeds | $h = 3$, both regimes | unbanded rule | slope 0.08, range −0.03 to +0.43, SD 0.20; mean error +5.30 |
| wider range | $h = 3$, independent | residual rule | 9,9,9,8,9,9 to 20: 17,19,11,8,14,13; slope −0.03 to −1.09; censored 6 to 0 |
| wider range | $h = 3$, both regimes | unbanded rule | 9,9,9,9,9,9 to 20: 21,19,11,18,19,12; slope 0.00 to −1.09; censored 6 to 1 |
| wider range | $h = 4$, independent | residual rule | 9,9,9,9,9,9 to 20: 19,21,21,17,19,16; slope 0.00 to −0.71; censored 6 to 2 |
| wider range | $h = 4$, both regimes | unbanded rule | 9,9,9,9,9,9 to 20: 21,21,21,17,21,16; slope 0.00 to −0.83; censored 6 to 4 |
| wider range | every uncensored cell | clique estimate, shared residual | 1,2,3,4,5,6 at both ranges; unchanged |

**Table S2.** The four passes that answer what one seed, one range and one kernel cannot.

Two readings of this table carry the argument of Section 7.2. The seed variance is confined to the cells that are collapsing, which is where variance belongs, and the five-seed pass moves two entries without reversing a sign or moving an estimator across the boundary between tracking the truth and not tracking it. And widening the range moves the censored cells while leaving the uncensored ones untouched, which is what it should do if censoring is what the column says it is.

## S3. Interval estimates for the clique contrast by group size

Table 7 of the main text prints point estimates. Table S3 adds the 95 percent intervals, from 1,000 bootstrap replicates. Corpus A resamples membership equivalence families; corpus B resamples complexes, which keeps a positive and the negatives generated from it in the same replicate.

| Members | 2 to 3 | 4 to 5 | 6 to 10 | 11 to 20 | 21 to 80 | 81 and above |
|---|---|---|---|---|---|---|
| Corpus B positives | 1,399 | 641 | 321 | 142 | 34 | 3 |
| Corpus B contrast, $k = 1$ | 0.4124 [0.3855, 0.4386] | 0.4665 [0.4297, 0.5066] | 0.4455 [0.3941, 0.4982] | 0.3662 [0.2889, 0.4516] | 0.1765 [0.0571, 0.3104] | 0.0000 |
| Corpus B negative cliques, count | 0 of 1,399 | 0 of 641 | 0 of 321 | 0 of 142 | 0 of 34 | 0 of 3 |
| Corpus B expected negative cliques, independent sampling | 2.1 × 10⁻⁶ | 1.0 × 10⁻¹⁵ | 7.5 × 10⁻⁴³ | 5.4 × 10⁻¹⁶¹ | 0 | 0 |
| Corpus A positives | 24 | 47 | 289 | 751 | 2,801 | 2,685 |
| Corpus A contrast, $k = 25$ | 0.5833 [0.3148, 0.8096] | 0.3617 [0.2211, 0.5083] | 0.3391 [0.2451, 0.4322] | 0.2437 [0.1781, 0.3151] | 0.0521 [0.0323, 0.0755] | 0.0000 |
| Corpus A contrast, $k = 1$ | 0.0625 [0.0000, 0.1250] | 0.1809 [0.0980, 0.2675] | 0.1972 [0.1597, 0.2372] | 0.1911 [0.1576, 0.2207] | 0.2387 [0.2018, 0.2740] | 0.4778 [0.3622, 0.5754] |

**Table S3.** Clique contrast by group size with 95 percent intervals, both corpora.

The small bins are small and their intervals say so. Corpus A's largest entry, 0.5833 at two to three members, rests on 24 events with an interval of 0.3148 to 0.8096 that overlaps the next bin's, so the apparent peak at the smallest sizes is not resolved. That is mechanism M7 measured: the subpopulation where the statistic has power is the one with too few events. Corpus B's smallest bins carry 1,399 and 641 positives with intervals a twentieth as wide, which is the same mechanism seen from the side where it does not bind.
