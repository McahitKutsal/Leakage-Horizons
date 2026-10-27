# Supplementary material

## Leakage horizons in group membership prediction: why pooled density diagnostics cannot measure them, and what can

This document holds four things the main text points at and does not print: the second forecasting task, the full robustness grid behind the identification result, the complete interval estimates for the clique contrast by group size, and the filter chains that separate one reported count in the coalition corpus from another. Section numbers of the form S1, S2 and so on are this document's; plain section numbers refer to the main text.

## S1. The termination task

This task concerns the substantive problem, the survival of international organisations, and not the measuring instrument the paper is about, which is why it is reported here. Two of its features are methodological and belong on the record.

The interval formulation is mandatory and not optional. The register's own coding rule declares an organisation defunct after ten consecutive years without a plenary session, so the event is known to have happened inside a window and not at a date. We therefore use a likelihood contribution of the form $S(t_{L}) - S(t_{R})$ over entity periods: a discrete-time competing-risks hazard with interval-censored event times, in the cause-specific form (Allison, 1982; Prentice et al., 1978; Finkelstein, 1986).

Thirty events whose cause the source does not state enter through the likelihood's cause-unknown branch. They are neither dropped nor assigned a cause.

Table S1 gives the task over 527 groups and 16,067 group periods with 150 events. Both counts are the estimated panel's and not the corpus's: 528 groups have an observation interval overlapping the window and 527 contribute a period to the likelihood. The one difference is a group with no active membership row inside the window, and that same group carries one of the 151 coded terminations inside the window, which is why the panel scores 150. Section S4 gives the chain.

| Covariate | Dissolution | Superseded |
|---|---|---|
| Log duration | +0.095 | −0.143 |
| Log size | −0.392 | −0.120 |
| Internal cohesion | +0.292 | −0.081 |
| Mean regime type | −0.093 | +0.001 |
| Regime heterogeneity | −0.109 | −0.070 |

**Table S1.** Termination task, corpus A. Cause-specific coefficients, standardised covariates, logit scale.

Two covariates reverse sign between the two causes, log duration and internal cohesion, so a pooled model would average both reversals toward zero. Duration reads cleanly: old groups fade while young ones are replaced or merged. A reversal is counted only when both coefficients exceed 0.01 in absolute value, since a sign flip at 0.001 is a rounding artefact and not an effect.

Any-cause discrimination is 0.610; cause-specific discrimination is 0.628 for dissolution and 0.559 for supersession. That is the comparison Section 7.7 draws against the accession task's pooled 0.798 to 0.915, and it is why termination is the harder problem on the comparable metric.
