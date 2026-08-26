r"""Every number the manuscript asserts must match the artefact it came from.

`check_consistency.py` does this for the reconciliation documents. The manuscript needs its own pass for
two reasons: it restates figures in compressed form, so a value can be right in `PENUMBRA-OUTCOMES.md`
and wrong here, and it was written after four corpus rebuilds, so any figure carried over from an
earlier draft is stale until checked.

Writing this found four stale values and one specification gap that a read-through had missed: the
median group sizes and the share of events in groups above eighty members were all from corpus v1, and
the clique contrast claim named no level, which matters because the size dependence reverses between
$k = 1$ and $k = 25$ (D-44).

Checks are of three kinds:

* **numeric**, a formatted value from a results file that must appear verbatim in the manuscript;
* **structural**, one paragraph per abstract, every figure and table cited in the text, sequential
  numbering with no gaps;
* **textual**, phrases retired by a correction that must not reappear.

    python scripts/check_paper.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "penumbra-kbs.md"
RESULTS = ROOT / "results"


def load(name: str):
    p = RESULTS / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def dig(obj, path: str):
    """Walk a dotted path. A segment wrapped in brackets is one key even if it contains dots.

    Some artefact keys are themselves decimals -- the identification grid is keyed by homophily
    setting, `h=0.5` -- so a plain split on the separator would look for a key `h=0` inside a
    dictionary that has none. Write those as `summary.regime.[h=0.5].estimator.field`.
    """
    # Split on the separator first, then rejoin any run that a caller wrapped in brackets. Doing it
    # in this order matters: several artefact keys are pandas interval labels such as `(80, 10000]`,
    # whose closing bracket would unbalance a character-by-character depth counter and silently stop
    # the split. An earlier version of this function did exactly that and quietly skipped four checks.
    raw = path.split(".")
    parts, pending = [], None
    for seg in raw:
        if pending is not None:
            pending.append(seg)
            if seg.endswith("]"):
                joined = ".".join(pending)
                parts.append(joined[1:-1])
                pending = None
            continue
        if seg.startswith("[") and not seg.endswith("]"):
            pending = [seg]
            continue
        if seg.startswith("[") and seg.endswith("]"):
            parts.append(seg[1:-1])
            continue
        parts.append(seg)
    if pending is not None:                     # unterminated escape: treat it literally
        parts.extend(pending)

    cur = obj
    for part in parts:
        if cur is None:
            return None
        cur = cur[int(part)] if isinstance(cur, list) else cur.get(part)
    return cur


# (results file, dotted path, formatter) -> the string that must appear in the manuscript
NUMERIC = [
    ("ledger_summary.json", "entities.total", lambda v: f"{v}"),
    ("ledger_summary.json", "events.total", lambda v: f"{v:,}"),
    ("ledger_summary.json", "events.by_type.accession", lambda v: f"{v:,}"),
    ("ledger_summary.json", "events.by_type.exit", lambda v: f"{v:,}"),
    ("ledger_summary.json", "events.by_type.termination", lambda v: f"{v}"),
    ("ledger_summary.json", "events.by_dating_stratum.exact", lambda v: f"{v:,}"),
    ("ledger_summary.json", "events.by_dating_stratum.declared_resolution", lambda v: f"{v}"),
    ("ledger_summary.json", "membership.rows", lambda v: f"{v:,}"),
    ("ledger_summary.json", "entities.families", lambda v: f"{v}"),

    ("u1_isolation.json", "matched_contrast.focal_step", lambda v: f"{v:.4f}"),
    ("u1_isolation.json", "matched_contrast.pooled_step", lambda v: f"{v:.4f}"),
    ("u1_isolation.json", "matched_contrast.n_positives", lambda v: f"{v:,}"),
    ("u1_isolation.json", "matched_contrast.contrast.igo_comembership.0", lambda v: f"{v:.3f}"),
    ("u1_isolation.json", "matched_contrast.contrast.igo_comembership.8", lambda v: f"{v:.3f}"),
    ("u1_isolation.json", "matched_contrast.contrast.trades.8", lambda v: f"{v:.4f}"),
    ("u1_isolation.json", "first_entry_by_dating_stratum.exact.n_events", lambda v: f"{v:,}"),
    ("u1_isolation.json", "first_entry_by_dating_stratum.declared_resolution.curve.1",
     lambda v: f"{v:.4f}"),

    ("desta_delta_star.json", "n_accession_events", lambda v: f"{v}"),
    ("desta_delta_star.json", "test1_trace_presence.contrast", lambda v: f"{v:.4f}"),
    ("desta_delta_star.json", "test1_trace_presence.share_present_by_horizon.0",
     lambda v: f"{v:.4f}"),
    ("desta_delta_star.json", "test1_trace_presence.share_present_by_horizon.8",
     lambda v: f"{v:.4f}"),
    ("desta_delta_star.json", "n_edge_years_signature", lambda v: f"{v:,}"),
    ("desta_delta_star.json", "n_edge_years_force", lambda v: f"{v:,}"),

    ("second_domain_thr400.json", "size_profile.n_positive", lambda v: f"{v:,}"),
    ("second_domain_thr400.json", "size_profile.median", lambda v: f"{v}"),
    ("second_domain_thr400.json", "size_profile.mean", lambda v: f"{v}"),
    ("second_domain_thr400.json", "size_profile.max", lambda v: f"{v}"),
    ("second_domain_thr400.json", "r_star_minus_best_anchor.random.residual",
     lambda v: f"{v:.4f}"),
    ("second_domain_thr400.json", "r_star_minus_best_anchor.hard.residual", lambda v: f"{v:.4f}"),
    # Registered after D-51: every corpus B density in the manuscript was twice its value for six
    # months because a directed row count was divided by an unordered dyad count, and none of the three
    # affected numbers was registered here. A density that appears in a table and in a mechanism
    # statement is a claim, so it is checked like one.
    ("second_domain_thr400.json", "target_relation_density", lambda v: f"{v:.6f}"),
    ("second_domain_thr400.json", "highest_relation_density", lambda v: f"{v:.6f}"),
    ("second_domain_thr400.json", "saturation_ratio_against_corpus_a", lambda v: f"{v:.0f}"),

    ("clique_by_size.json", "corpus_a.k=25.(80, 10000].clique_contrast", lambda v: f"{v:.4f}"),
    ("clique_by_size.json", "corpus_a.k=25.(1, 3].clique_contrast", lambda v: f"{v:.4f}"),
    ("clique_by_size.json", "corpus_a.k=1.(80, 10000].clique_contrast", lambda v: f"{v:.4f}"),
    ("clique_by_size.json", "corpus_b.k=1.(3, 5].clique_contrast", lambda v: f"{v:.4f}"),

    ("p6.json", "spearman_rho", lambda v: f"{v:.3f}"),
    ("p6.json", "p_value", lambda v: f"{v:.4f}"),
    # The spreads are the CLIQUEBAIT H5 lesson applied here: a rank correlation over a range too small
    # to matter is immaterial however significant it looks, so the range is a claim too.
    ("p6.json", "reliance_spread", lambda v: f"{v:.4f}"),
    ("p6.json", "fragility_spread", lambda v: f"{v:.4f}"),

    ("t2_ladder.json", "focal_False.n_entities", lambda v: f"{v}"),
    ("t2_ladder.json", "focal_False.n_rows", lambda v: f"{v:,}"),
    ("t2_ladder.json", "focal_False.auc_any", lambda v: f"{v:.3f}"),

    ("t1_ladder.json", "fits.1.n_rows", lambda v: f"{v:,}"),
    ("t1_ladder.json", "fits.1.n_events", lambda v: f"{v:,}"),

    ("p7_s4.json", "n_parameters.7", lambda v: f"{v:,}"),
    ("p7_s4.json", "n_parameters.6", lambda v: f"{v:,}"),
    ("p7_ctrl_w128_s4.json", "n_parameters.4", lambda v: f"{v:,}"),

    # -- figures the manuscript asserts that no other script computed until D-45 --
    ("paper_support.json", "regime_saturation.early.mean_density", lambda v: f"{v:.4f}"),
    ("paper_support.json", "regime_saturation.primary.mean_density", lambda v: f"{v:.4f}"),
    ("paper_support.json", "regime_saturation.early.organisations_per_year", lambda v: f"{v}"),
    ("paper_support.json", "regime_saturation.primary.organisations_per_year", lambda v: f"{v}"),
    ("paper_support.json", "left_truncation.entities_in_panel", lambda v: f"{v}"),
    ("paper_support.json", "left_truncation.predating_the_window", lambda v: f"{v}"),
    ("paper_support.json", "left_truncation.median_true_age_at_window_start", lambda v: f"{v}"),
    ("paper_support.json", "left_truncation.max_true_age_at_window_start", lambda v: f"{v}"),
    ("paper_support.json", "left_truncation.share_of_group_years", lambda v: f"{v * 100:.1f}"),
    ("paper_support.json", "duplicate_membership_rows.redundant_rows", lambda v: f"{v}"),
    ("paper_support.json", "duplicate_membership_rows.rows_in_duplicate_pairs", lambda v: f"{v}"),
    ("paper_support.json", "duplicate_membership_rows.inflated_group_years", lambda v: f"{v}"),
    ("paper_support.json", "coded_gap_share.share_gap_at_least_2", lambda v: f"{v * 100:.1f}"),
    ("paper_support.json", "derived_aggregates.rung3_minus_rung2_pooled", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung3_minus_rung2_within", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung3_minus_rung2_within_eligibility_clock",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung4_mean_auc", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung5_mean_auc", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung6_mean_auc", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung7_mean_auc", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung6_sd_over_seeds", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung7_sd_over_seeds", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.mlp_w96_mean_auc", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.mlp_w128_mean_auc", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung6_minus_mlp_w96", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.rung7_minus_mlp_w128", lambda v: f"{v:.4f}"),
    ("paper_support.json", "derived_aggregates.width_64_to_128", lambda v: f"{v:.4f}"),

    # -- mechanism (e), recomputed on the matched panel after its published figures were traced to
    #    the retracted one (D-45) --
    ("u2_capacity_replication.json", "capacities.0.decay", lambda v: f"{v:.4f}"),
    ("u2_capacity_replication.json", "capacities.2.decay", lambda v: f"{v:.4f}"),
    ("u2_capacity_replication.json", "decay_linear_mean", lambda v: f"{v:.4f}"),
    ("u2_capacity_replication.json", "decay_ratio", lambda v: f"{v:.2f}"),
    ("u2_capacity_replication.json", "capacities.0.n_pos_at_first", lambda v: f"{v:,}"),
    ("u2_capacity_replication.json", "capacities.0.n_pos_at_last", lambda v: f"{v}"),

    # -- revision: the focal contribution computed on corpus A rather than carried from the trade
    #    register, which had the same 6.8 percent standing for two different quantities (item 1.3) --
    ("focal_share.json", "pta.back_dated_increment", lambda v: f"{v:,}"),
    ("focal_share.json", "pta.dyad_years_only_in_signature", lambda v: f"{v:,}"),
    ("focal_share.json", "corpus_a.star_local.k=1.dyads_read_as_present", lambda v: f"{v:,}"),
    ("focal_share.json", "corpus_a.star_local.k=1.dyads_present_only_through_the_focal_entity",
     lambda v: f"{v}"),
    ("focal_share.json", "corpus_a.star_local.k=25.dyads_read_as_present", lambda v: f"{v:,}"),
    ("focal_share.json", "corpus_a.star_local.k=25.dyads_present_only_through_the_focal_entity",
     lambda v: f"{v:,}"),
    ("focal_share.json", "corpus_a.star_local.k=25.focal_share_of_what_the_statistic_reads",
     lambda v: f"{v * 100:.1f}"),

    # -- revision: corpus B's negatives, so a zero rate is a counted zero (item 1.5) --
    ("corpus_b_negatives_thr400.json", "target_relation_density", lambda v: f"{v:.5f}"),
    ("corpus_b_negatives_thr400.json", "exclusion_test.mean_phi_random_negatives",
     lambda v: f"{v:.5f}"),
    ("corpus_b_negatives_thr400.json", "by_stratum.hard.(1, 3].negative_cliques", lambda v: f"{v}"),
    ("corpus_b_negatives_thr400.json", "by_stratum.hard.(1, 3].n_neg", lambda v: f"{v:,}"),
    ("corpus_b_negatives_thr400.json", "by_stratum.hard.(1, 3].clique_contrast",
     lambda v: f"{v:.4f}"),

    # -- revision: the second implementation of the density code (item 2.7) --
    ("reference_density.json", "synthetic.phi.n_values", lambda v: f"{v:,}"),
    ("reference_density.json", "corpus_a_table_3.star.n_values", lambda v: f"{v:,}"),
    ("reference_density.json", "corpus_a_table_4.phi.n_values", lambda v: f"{v:,}"),
    ("reference_density.json", "corpus_b_table_4.umbra_vs_reference.n_values", lambda v: f"{v:,}"),

    # -- revision: the upper bound, both definitions (item 2.4) --
    ("upper_bound_audit.json", "synthetic.pre_specified_rule_fires_in", lambda v: f"{v}"),
    ("synthetic_homophily.json", "upper_bound.cells", lambda v: f"{v}"),
    ("synthetic_homophily.json", "upper_bound.rank_and_band_fired", lambda v: f"{v}"),

    # -- revision: the identification grid and its side experiments (items 2.2, 2.3, 2.10) --
    ("synthetic_homophily.json",
     "summary.anchors_independent.[h=3.0].residual_rule.mean_error", lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json",
     "summary.anchors_independent.[h=2.0].residual_rule.slope_on_beta", lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json",
     "summary.anchors_share_latent_space.[h=2.0].unbanded_rule.mean_error", lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json", "dating_noise.1.focal_curve.1", lambda v: f"{v:.4f}"),
    ("synthetic_homophily.json", "dating_noise.2.focal_curve.1", lambda v: f"{v:.4f}"),

    # -- revision: an interval on every headline magnitude (item 2.1) --
    ("bootstrap_diagnostics.json", "replicates", lambda v: f"{v:,}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.contrast.igo_comembership.0.lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.contrast.igo_comembership.0.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.contrast.igo_comembership.8.lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.contrast.igo_comembership.8.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.contrast.trades.8.lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.contrast.trades.8.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.contrast.conflicts_with.8.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.residual_crossing_lead_time.replicates_where_it_fired",
     lambda v: f"{v}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.residual_crossing_lead_time.replicates_where_it_never_fired",
     lambda v: f"{v}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.residual_crossing_lead_time.distribution.5", lambda v: f"{v}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.residual_crossing_lead_time.distribution.4", lambda v: f"{v}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.residual_crossing_lead_time.distribution.0", lambda v: f"{v}"),
    ("bootstrap_diagnostics.json", "table_3_and_the_two_steps.focal_step.lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json", "table_3_and_the_two_steps.focal_step.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json", "table_3_and_the_two_steps.pooled_step.lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json", "table_3_and_the_two_steps.pooled_step.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.focal_over_pooled.point", lambda v: f"{v:.2f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.focal_over_pooled.lo", lambda v: f"{v:.2f}"),
    ("bootstrap_diagnostics.json",
     "table_3_and_the_two_steps.focal_over_pooled.hi", lambda v: f"{v:.2f}"),
    ("bootstrap_diagnostics.json", "pta_contrast.contrast.lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json", "pta_contrast.contrast.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json", "pta_contrast.focal_over_pooled.point", lambda v: f"{v:.2f}"),
    ("bootstrap_diagnostics.json", "pta_contrast.focal_over_pooled.lo", lambda v: f"{v:.2f}"),
    ("bootstrap_diagnostics.json", "pta_contrast.focal_over_pooled.hi", lambda v: f"{v:.2f}"),
    ("bootstrap_diagnostics.json",
     "clique_contrast_by_size.corpus_a.k=25.(1, 3].lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "clique_contrast_by_size.corpus_a.k=25.(1, 3].hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "clique_contrast_by_size.corpus_b.k=1.(20, 80].lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "synthetic_calibration.4.share_on_target", lambda v: f"{v * 100:.0f}"),
    # The declared-resolution width is the only positive field measurement of a horizon in corpus A, so
    # its interval is a headline magnitude rather than a supporting one.
    ("bootstrap_diagnostics.json",
     "declared_resolution_width.declared_resolution.presence_at_1.lo", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "declared_resolution_width.declared_resolution.presence_at_1.hi", lambda v: f"{v:.4f}"),
    ("bootstrap_diagnostics.json",
     "declared_resolution_width.declared_resolution.n_clusters", lambda v: f"{v}"),
    ("bootstrap_diagnostics.json",
     "declared_resolution_width.exact.n_events_at_lead_time_1", lambda v: f"{v:,}"),
    # The generator's edge budget: the peak eligible-dyad count justifies the density constant, and it
    # lived only in a comment and in the manuscript's prose until this entry existed.
    ("synthetic_homophily.json",
     "budget_headroom.worst_case.peak_eligible_backdated_dyads", lambda v: f"{v:,}"),
    ("synthetic_homophily.json", "budget_headroom.n_pairs", lambda v: f"{v:,}"),

    # -- revision 2: the censoring column behind every slope in Table 4, and the range audit that
    #    settles the censored cells. A slope of zero and a range too narrow to hold the estimator look
    #    identical without these, which is the objection they answer. --
    ("synthetic_homophily.json",
     "summary.anchors_independent.[h=2.0].residual_rule.censored", lambda v: f"{v}"),
    ("synthetic_homophily.json",
     "summary.anchors_independent.[h=3.0].residual_rule.censored", lambda v: f"{v}"),
    ("synthetic_homophily.json",
     "summary.anchors_share_latent_space.[h=2.0].unbanded_rule.censored", lambda v: f"{v}"),
    ("synthetic_homophily.json",
     "summary.anchors_share_latent_space.[h=2.0].unbanded_rule.slope_on_beta_uncensored",
     lambda v: f"{v:+.2f}"),
    ("synthetic_homophily.json",
     "range_audit.anchors_independent.[h=3.0].unbanded_rule.wide_slope", lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json",
     "range_audit.anchors_independent.[h=4.0].unbanded_rule.wide_slope", lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json",
     "range_audit.anchors_independent.[h=3.0].unbanded_rule.wide_max_lead_time",
     lambda v: f"{v}"),
    # -- and the seed pass on the transition rows, because one corpus per cell is not an interval --
    ("synthetic_homophily.json",
     "seed_replication.anchors_independent.[h=2.0].over_seeds.residual_rule.slope_mean",
     lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json",
     "seed_replication.anchors_independent.[h=2.0].over_seeds.residual_rule.slope_min",
     lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json",
     "seed_replication.anchors_share_latent_space.[h=3.0].over_seeds.delta_star_lo.slope_mean",
     lambda v: f"{v:.2f}"),
    ("synthetic_homophily.json",
     "seed_replication.anchors_share_latent_space.[h=3.0].over_seeds.delta_star_lo.slope_min",
     lambda v: f"{v:.2f}"),

    # -- revision 2: the whole grid at three seeds under three homophily kernels. The two columns the
    #    argument rests on have to be seed-invariant for Table 4's single-seed cells to be readable, so
    #    the thresholds and the collapse points are registered rather than described. --
    ("synthetic_homophily.json",
     "form_and_seed_robustness.power.anchors_independent.collapse_threshold.residual_rule.min",
     lambda v: f"{v}"),
    ("synthetic_homophily.json",
     "form_and_seed_robustness.power.anchors_independent.collapse_threshold.unbanded_rule.min",
     lambda v: f"{v}"),
    ("synthetic_homophily.json",
     "form_and_seed_robustness.block.anchors_share_latent_space.collapse_threshold.unbanded_rule.min",
     lambda v: f"{v}"),

    # -- revision 2: the collapse reported on a scale corpus A also has. These four numbers are the
    #    bridge between the generator and the field, so each is registered rather than described. --
    ("homophily_scale.json", "collapse_threshold_in_anchor_contrast.power.unbanded_rule",
     lambda v: f"{v:.4f}"),
    ("homophily_scale.json", "collapse_threshold_in_anchor_contrast.block.unbanded_rule",
     lambda v: f"{v:.4f}"),
    ("homophily_scale.json", "summary.logistic.[h=4.0].anchor_contrast_mean",
     lambda v: f"{v:.4f}"),
    ("homophily_scale.json", "corpus_a_reference.strongest_anchor", lambda v: f"{v:.4f}"),
    ("homophily_scale.json", "corpus_a_reference.per_relation.trades", lambda v: f"{v:.4f}"),

    # -- revision 2: Section 6.3, whether the focal record is the only place back-dating lives --
    ("co_backdating.json", "summary.[mixed,share=0.5].mean_gap_focal_group_only",
     lambda v: f"{v:.2f}"),
    ("co_backdating.json", "summary.[mixed,share=0.25].mean_gap_focal_group_only",
     lambda v: f"{v:.2f}"),
    ("co_backdating.json", "summary.[mixed,share=0.1].mean_gap_focal_group_only",
     lambda v: f"{v:.2f}"),
    ("co_backdating.json", "summary.[mixed,share=0.5].mean_gap_every_register",
     lambda v: f"{v:.2f}"),
    ("co_backdating.json", "summary.[mixed,share=0.5].max_gap_focal_group_only", lambda v: f"{v}"),
    ("co_backdating.json", "ambient_off_focal.mean_reach_positives", lambda v: f"{v:.4f}"),
    ("co_backdating.json", "ambient_off_focal.mean_reach_negatives", lambda v: f"{v:.4f}"),
    ("co_backdating.json", "ambient_off_focal.share_positives", lambda v: f"{v:.4f}"),
    ("co_backdating.json", "ambient_off_focal.share_negatives", lambda v: f"{v:.4f}"),
    ("co_backdating.json", "budget_headroom.peak_eligible_backdated_dyads", lambda v: f"{v:,}"),
    ("co_backdating.json", "budget_headroom.n_pairs", lambda v: f"{v:,}"),
    ("co_backdating.json", "budget_headroom.density_chosen", lambda v: f"{v}"),
    ("co_backdating.json", "invariance.smallest_budget_headroom", lambda v: f"{v}"),

    # -- revision 2: why no stratum of corpus A supports both instruments as measurements. The three
    #    numbers behind that claim are registered, because it is the claim an outside read said the
    #    paper needed and could not have. --
    ("both_instruments.json", "stratum_windows.declared_resolution.n_accessions", lambda v: f"{v}"),
    ("both_instruments.json", "stratum_windows.declared_resolution.last_year", lambda v: f"{v}"),
    ("both_instruments.json",
     "stratum_windows.declared_resolution.lead_times_reachable_inside_the_window",
     lambda v: f"{v}"),
    ("both_instruments.json",
     "by_stratum.declared_resolution.share_of_rows_read_before_the_window",
     lambda v: f"{v * 100:.0f}"),

    # -- revision 2: the filter chain, which is where three pairs of counts an outside read flagged
    #    are separated. Each of the six numbers is registered so the flow cannot drift from the code. --
    ("filter_chain.json", "groups.overlapping_the_window_on_entity_dates", lambda v: f"{v}"),
    ("filter_chain.json", "groups.estimated_in_the_termination_panel", lambda v: f"{v}"),
    ("filter_chain.json", "accessions.accession_events_in_the_window", lambda v: f"{v:,}"),
    ("filter_chain.json", "accessions.event_dyads_in_the_window", lambda v: f"{v:,}"),
    ("filter_chain.json", "accessions.repeat_accessions_collapsed", lambda v: f"{v}"),
    ("filter_chain.json", "accessions.dyads_with_more_than_one_accession", lambda v: f"{v}"),
    ("filter_chain.json", "focal_isolation.exact.first_entry_at_lead_time_0", lambda v: f"{v:,}"),
    ("filter_chain.json", "focal_isolation.exact.first_entry_at_lead_time_1", lambda v: f"{v:,}"),
    ("filter_chain.json", "focal_isolation.exact.lost_between_lead_time_0_and_1", lambda v: f"{v}"),
    ("filter_chain.json", "focal_isolation.declared_resolution.first_entry_at_lead_time_1",
     lambda v: f"{v}"),
    ("filter_chain.json", "terminations.in_the_window", lambda v: f"{v}"),
    ("filter_chain.json", "terminations.events_in_the_estimated_panel", lambda v: f"{v}"),

    # -- revision 2: the architecture comparison at ten seeds, where one verdict changed --
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.rung4_mean_auc",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.rung5_mean_auc",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.rung6_mean_auc",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.rung7_mean_auc",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.mlp_w96_mean_auc",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.mlp_w128_mean_auc",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.rung5_sd_over_seeds",
     lambda v: f"{v:.4f}"),
    ("paper_support.json", "architecture_by_seed_count.ten_seeds.rung6_sd_over_seeds",
     lambda v: f"{v:.4f}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.relation_specific_vs_w96.margin", lambda v: f"{v:.4f}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.relation_specific_vs_w96.cells_won", lambda v: f"{v}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.temporal_vs_w128.margin", lambda v: f"{v:.4f}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.temporal_vs_w128.cells_won", lambda v: f"{v}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.homogeneous_vs_w64.margin", lambda v: f"{v:.4f}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.homogeneous_vs_w64.cells_won", lambda v: f"{v}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.gain_by_lead_time_over_width_64.7.1",
     lambda v: f"{v:.4f}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.gain_by_lead_time_over_width_64.7.10",
     lambda v: f"{v:.4f}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.gain_by_lead_time_over_width_64.6.1",
     lambda v: f"{v:.4f}"),
    ("paper_support.json",
     "architecture_by_seed_count.ten_seeds.gain_by_lead_time_over_width_64.6.10",
     lambda v: f"{v:.4f}"),
]

# Phrases a correction retired. Each must be absent.
RETIRED = [
    # Retired by a decision rather than by a measurement: the manuscript was written for
    # Knowledge-Based Systems and opened by calling the thing a knowledge-based system. The
    # journal changed, and the phrase names a tradition this paper is not in. The three
    # "Knowledge" strings that remain are journal names in the reference list.
    ("knowledge-based system", "the paper is not about knowledge-based systems"),
    ("51 organisations", "median organisation size was 16 on corpus v4, not 51 (D-44)"),
    ("mean positive stratum of 66", "the mean is 73.5 on corpus v4 (D-44)"),
    ("0.20 to 0.25 below twenty", "the range is 0.24 to 0.58 at k=25 on corpus v4 (D-44)"),
    ("36 percent of corpus A's positives", "the share above eighty members is 41.1 percent (D-44)"),
    ("roughly 0.22", "a figure specification must not carry an unmeasured value (D-44)"),
    ("4 alliances, 51", "stale median group sizes (D-44)"),
    ("0.058 to 0.143", "mechanism (e)'s figures came from the panel V0 retracted (D-45)"),
    ("linear probe holds at 0.041", "same retracted panel (D-45)"),

    # -- retired by the revision. Each of these was true of an earlier draft and is now wrong, and a
    #    substring search is the only check that catches a sentence coming back from an old copy. --
    ("the same factor of roughly ten",
     "the two ratios are 9.8 and 6.8 and are reported separately; no mechanism forces one value"),
    ("Together they trace one function across the full range",
     "the two corpora are read at different levels, so their heights are not comparable"),
    ("fired in 2 of 6 settings",
     "the pre-specified upper bound fires in 3 of 6, at beta 0, 1 and 2"),
    ("at $\\beta = 0$ and $\\beta = 5$",
     "Figure 2's upper-bound row named the wrong settings; it exists at beta 0, 1 and 2"),
    ("density range across the grid is 0.00000000",
     "the range is exactly zero because the edge budget is a fixed integer count"),
    ("estimating it as a bracketed interval",
     "the interval is withdrawn; the upper bound is not identified (item 2.4)"),
    ("The author declares", "the manuscript has six authors"),
    ("found by the author auditing the author's own work", "the manuscript has six authors"),
    ("the focal contribution is 6.8 percent of a relation whose density is 0.9954",
     "6.8 percent is the trade register's increment; corpus A's own share is 0.02 and 6.5 percent"),
    ("Co-membership has density 0.9954, so almost every pair of states shares something, and the "
     "focal contribution is 6.8 percent of the relation",
     "same figure carried between corpora (item 1.3)"),

    # -- retired by the second revision. Each was true of the version an outside read examined. --
    ("and nothing else",
     "Section 3.3's claim holds under one dating convention and fails under mixed ones (6.3)"),
    ("recovers a tenth",
     "the numerator is a probability and the denominator a density contrast; the claim is now the "
     "6.8 percent share (6.4)"),
    ("An estimator that errs only upward is the right error profile for a lower bound",
     "a lower bound that exceeds what it bounds has failed; 3.2 states the loss instead"),
    ("Replication on the inverse size distribution",
     "corpus B has no time axis and cannot replicate a result about lead time; it is a scope test"),
    ("it is indistinguishable from a multilayer perceptron rather than worse than one",
     "at ten seeds the homogeneous encoder is worse than its capacity-matched control at 3.7 sigma"),
    ("carries no information about the truth whatever",
     "the claim has to be relative to the examined range; the range audit is what settles it"),
    ("Ten ways a leakage diagnostic misreports and test four",
     "the count is ten demonstrated and one not demonstrated"),
    ("M. R. Bailey", "the author is M. A. Bailey"),
    ("R. W. Frank", "the author is R. W. McManus; the entry was a reference-manager collision"),
    ("protein-protein association networks with increased coverage",
     "the corpus is built from STRING v12.0, whose release note is the 2023 article"),
    ("CORUM: the comprehensive resource of mammalian protein complexes",
     "the corpus is built from CORUM release 5.3, whose release note is the 2024 article"),
    ("Complex Portal 2018", "the corpus is built from the current release, whose note is the 2022 "
                            "article"),
]

FORBIDDEN_CHARS = {"em dash": "—", "en dash": "–", "minus sign": "−"}
ABSTRACT_MAX_WORDS = 250
ABSTRACT_MAX_NUMBERS = 6

# The figure specifications carry the series a reader will plot, roughly 270 numeric tokens, and a wrong
# value there reaches the figure and then the reader. They are not covered by NUMERIC, which registers
# named claims, so every value in them is required to be derivable from some artefact instead. An earlier
# version of a specification carried "roughly 0.22", an unmeasured value, which is what this catches.
#
# Exempt: axis bounds, which are drawing choices rather than data, and arithmetic the running text states
# and derives in place.
SPEC_EXEMPT = {"50,000", "115,000", "13,966"}

# Substring search answers "does the right value appear somewhere", not "is every occurrence right",
# and a manuscript that states a count in three places can be stale in one of them and still pass. A
# deliberate corruption test confirmed exactly that. These patterns anchor a quantity to the words
# around it and require **every** match to equal the artefact value.
#
# `unit` is matched after the number, so "562 entities" is checked wherever it appears. Units whose
# number legitimately varies by context, "events" for instance, which is used for the corpus total and
# for per stratum counts, are unsuitable and are left out rather than special cased.
ANCHORED = [
    (r"([\d][\d,]*)\s+entities\b", "ledger_summary.json", "entities.total"),
    (r"([\d][\d,]*)\s+accessions\b", "ledger_summary.json", "events.by_type.accession"),
    (r"([\d][\d,]*)\s+exits\b", "ledger_summary.json", "events.by_type.exit"),
    (r"([\d][\d,]*)\s+terminations\b", "ledger_summary.json", "events.by_type.termination"),
    (r"([\d][\d,]*)\s+complexes\b", "second_domain_thr400.json", "size_profile.n_positive"),
    (r"([\d][\d,]*)\s+proteins\b", "second_domain_thr400.json", "n_proteins"),
]


def main() -> int:
    text = PAPER.read_text(encoding="utf-8")
    cmp_text = text.replace("−", "-")
    fails, skipped = [], []

    for src, path, fmt in NUMERIC:
        obj = load(src)
        if obj is None:
            skipped.append(f"{src} missing")
            continue
        val = dig(obj, path)
        if val is None:
            skipped.append(f"{src}:{path} absent")
            continue
        want = fmt(val)
        if want not in cmp_text:
            fails.append(f"manuscript does not contain {want!r} from {src}:{path}")

    derivable = set()
    for f in sorted(RESULTS.glob("*.json")):
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue

        def collect(o):
            if isinstance(o, dict):
                for v in o.values():
                    collect(v)
            elif isinstance(o, list):
                for v in o:
                    collect(v)
            elif isinstance(o, (int, float)) and not isinstance(o, bool):
                x = float(o)
                # One provenance artefact carries NaN, and `int(nan)` raises rather than returning
                # anything, so a bare `x == int(x)` test crashes the whole audit on a value that
                # cannot appear in a figure anyway.
                if not math.isfinite(x):
                    return
                for fmt in (f"{x:g}", f"{x:.1f}", f"{x:.2f}", f"{x:.3f}", f"{x:.4f}",
                            f"{int(x):,}" if x == int(x) else "",
                            f"{abs(x):.3f}", f"{abs(x):.4f}",
                            f"{abs(x) * 100:.1f}", f"{abs(x) * 100:.2f}"):
                    if fmt:
                        derivable.add(fmt.lstrip("+"))
        collect(obj)

    # The figures used to be specifications in the manuscript, listing every series a reader would
    # plot, and this check required each of those values to be derivable from an artefact. The figures
    # are now drawn from the artefacts by `scripts/build_figures.py`, so the values cannot disagree by
    # construction and the check moves to the thing that can still go wrong: a manuscript referring to
    # an image that was never built, or built by something other than the generator.
    refs = re.findall(r"!\[[^\]]*\]\((Figures/figure-(\d+)\.svg)\)", text)
    built = load("figures.json") or {}
    built_stems = {v.get("stem") for v in (built.get("figures") or {}).values()}
    for rel, n in refs:
        path = PAPER.parent / rel
        if not path.exists():
            fails.append(f"figure {n} is referenced but {rel} does not exist")
        elif f"figure-{n}" not in built_stems:
            fails.append(f"{rel} exists but results/figures.json does not record building it")
    if refs:
        # Every figure the generator produces should be used, or it is dead output.
        unused = sorted(built_stems - {f"figure-{n}" for _r, n in refs})
        if unused:
            fails.append(f"figures built but never referenced: {unused}")
    # Blockquotes were once figure drawing briefs and this check refused all of them. The manuscript
    # now uses the same syntax for two deliberate definition boxes, so the check becomes a whitelist:
    # a blockquote is allowed if its first line is one of the declared box openers, and any other
    # blockquote still fails, which is what keeps a drawing brief from creeping back in.
    ALLOWED_BOXES = [
        "**The level ladder, stated as a convention.**",
        "**Six questions with checkable answers.**",
    ]
    blocks, cur = [], []
    for line in text.splitlines():
        if line.startswith(">"):
            cur.append(line)
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    for b in blocks:
        head = b[0].lstrip("> ").strip()
        if not any(head.startswith(a) for a in ALLOWED_BOXES):
            fails.append(f"undeclared blockquote in the manuscript, starting {head[:60]!r}; a "
                         f"drawing brief belongs in scripts/build_figures.py and a definition box "
                         f"has to be declared in check_paper.ALLOWED_BOXES")
    for a in ALLOWED_BOXES:
        if not any(b[0].lstrip("> ").strip().startswith(a) for b in blocks):
            fails.append(f"declared box absent from the manuscript: {a}")

    for pattern, src, path in ANCHORED:
        obj = load(src)
        val = dig(obj, path) if obj else None
        if val is None:
            skipped.append(f"{src}:{path} absent, cannot anchor {pattern}")
            continue
        want = f"{val:,}"
        found = re.findall(pattern, text)
        if not found:
            skipped.append(f"no occurrence of {pattern} to anchor")
            continue
        wrong = sorted({f for f in found if f not in (want, str(val))})
        if wrong:
            fails.append(f"{pattern}: expected {want} from {src}:{path}, also found {wrong}")

    # Every section a sentence points at must exist. Two renumberings during this revision moved
    # eleven headings and thirty-eight references, and a stale "Section 6.3" reads as a correct
    # sentence about the wrong object, which is precisely the claim-to-artefact class Section 9 says
    # no check reaches. This one reaches the part of it that is mechanical.
    heads = set()
    for m in re.finditer(r"^#{2,4} (\d+(?:\.\d+)?)[. ]", text, re.M):
        heads.add(m.group(1))
    for m in re.finditer(r"^## Appendix ([A-Z])\.", text, re.M):
        heads.add(f"Appendix {m.group(1)}")
    cited = set()
    for m in re.finditer(r"Sections? (\d+(?:\.\d+)?)(?: and (\d+(?:\.\d+)?))?", text):
        cited.add(m.group(1))
        if m.group(2):
            cited.add(m.group(2))
    for m in re.finditer(r"Appendix ([A-Z])\b", text):
        cited.add(f"Appendix {m.group(1)}")
    dangling = sorted(cited - heads, key=str)
    if dangling:
        fails.append(f"sections referenced but absent: {dangling} (headings present: "
                     f"{sorted(heads, key=str)})")
    # And the reverse, for a section nothing points at, which after a restructure usually means a
    # reference was rewritten to the wrong number rather than that the section is unnecessary.
    body_only = {h for h in heads if "." in h}
    orphan = sorted(body_only - cited, key=str)
    if orphan:
        skipped.append(f"subsections nothing refers to: {orphan}")

    for phrase, why in RETIRED:
        if phrase in text:
            fails.append(f"retired phrase present: {phrase!r} ({why})")

    for name, ch in FORBIDDEN_CHARS.items():
        if ch in text:
            fails.append(f"{name} present in the manuscript")

    blank = chr(10) + chr(10)
    m = re.search("## Abstract" + blank + "(.*?)" + blank + re.escape("**Keywords"), text, re.S)
    if m is None:
        fails.append("abstract not found")
    else:
        body = m.group(1)
        if body.count(blank):
            fails.append("the abstract is more than one paragraph")
        if len(body.split()) > ABSTRACT_MAX_WORDS:
            fails.append(f"abstract is {len(body.split())} words, limit {ABSTRACT_MAX_WORDS}")

    # Sequential numbering, and every figure and table cited somewhere in the running text.
    for kind in ("Figure", "Table"):
        caps = [int(x) for x in re.findall(rf"\*\*{kind} (\d+)\.", text)]
        if caps != list(range(1, len(caps) + 1)):
            fails.append(f"{kind} captions are not sequential from 1: {caps}")
        refs = {int(x) for x in re.findall(rf"(?<!\*\*){kind} (\d+)", text)}
        missing = set(caps) - refs
        if missing:
            fails.append(f"{kind}(s) never cited in the text: {sorted(missing)}")

    # The third external reading said the abstract was nearly unreadable: ten numeric tokens in
    # eleven sentences, and 6.8 standing for a percentage in one and a ratio in another. A number in
    # an abstract has to mean something to someone who has not read the paper, and the same digits
    # meaning two things is the case where it means less than nothing. Checked here rather than left
    # to a reader, and the same for the revision tags, which belong to Appendix B and not to the body.
    if m is not None:
        nums = re.findall(r"\b\d[\d.]*\b", m.group(1))
        if len(nums) > ABSTRACT_MAX_NUMBERS:
            fails.append(f"the abstract carries {len(nums)} numeric tokens, "
                         f"{ABSTRACT_MAX_NUMBERS} is the limit: {nums}")
        twice = sorted({n for n in nums if nums.count(n) > 1})
        if twice:
            fails.append(f"a number appears more than once in the abstract: {twice}")

    if "\n## Appendix B" in text:
        body_only = text[:text.index("\n## Appendix B")]
        tags = re.findall(r"\(R\d+(?:\s*,\s*R\d+)*\)", body_only)
        if tags:
            fails.append(f"{len(tags)} revision tag(s) in the body, which belong to Appendix B: "
                         f"{sorted(set(tags))[:5]}")

    # The byline and the contribution statement have to name the same people. An outside reader found
    # this before any check did, and called it ironic in a paper about auditing: the title page listed
    # four authors and the statement six. It is the same claim-to-artefact class as the rest, with the
    # artefact being another part of the same document.
    head = text[:text.index("\n<sup>1</sup>")] if "\n<sup>1</sup>" in text else ""
    byline = set(re.findall(r"\*\*([^*]+)\*\*<sup>", head))
    if "## CRediT" in text:
        block = text[text.index("## CRediT"):]
        block = block[:block.index("\n## ")] if "\n## " in block else block
        credit = {n for n in re.findall(r"\*\*([^*]+):\*\*", block)
                  if "does not claim" not in n}
        if not byline:
            fails.append("no byline found, so it cannot be compared with the contribution statement")
        elif byline != credit:
            only_c = sorted(credit - byline)
            only_b = sorted(byline - credit)
            if only_c:
                fails.append(f"named in the contribution statement and not on the byline: {only_c}")
            if only_b:
                fails.append(f"on the byline and absent from the contribution statement: {only_b}")

    # A named work has to cite the entry that carries the name. The manuscript said "REFORMS [3]" in
    # Section 9 where 3 is the other Kapoor paper: the sentence was written after the bibliography was
    # renumbered by key, and the number, which had been typed by hand, was never remapped. Every check
    # above passed on it, because each one reads a number and none reads what the number points at.
    if "\n## References" not in text:
        skipped.append("no reference list, so nothing checks what the citations point at")
    else:
        head = text.index("\n## References")
        tail = text.index("\n## ", head + 5)
        entries = {int(m.group(1)): m.group(2)
                   for m in re.finditer(r"^(\d+)\. (.+)$", text[head:tail], re.M)}
        body = text[:head]
        # An acronym a reference names is checkable: REFORMS, CORUM, STRING, DESTA, ATOP.
        homes: dict[str, set] = {}
        for n, entry in entries.items():
            for acr in re.findall(r"\b([A-Z]{4,})\b", entry):
                homes.setdefault(acr, set()).add(n)
        for acr, where in sorted(homes.items()):
            for m in re.finditer(re.escape(acr) + r" \[([\d,\s]+)\]", body):
                cited = {int(x) for x in re.split(r",\s*", m.group(1))}
                if not cited & where:
                    fails.append(f"{acr} cites {sorted(cited)}, and the entry that names it is "
                                 f"{sorted(where)}")
        # So is a surname printed in front of the number, when the citation is written as one.
        for m in re.finditer(r"\b([A-Z][a-z]{3,})(?: et al\.| and [A-Z][a-z]{3,}) \[(\d+)\]", body):
            surname, n = m.group(1), int(m.group(2))
            if n in entries and surname.lower() not in entries[n].lower():
                fails.append(f"{surname} cites [{n}], whose authors are "
                             f"{entries[n].split('.')[0]!r}")
        if not homes:
            skipped.append("no acronym in any reference title, so citation targets are unchecked")

    for s in skipped:
        print(f"  skip  {s}")
    for f in fails:
        # A failure naming an author crashed this on a console that cannot encode a Turkish letter, so
        # the check fired and the message never arrived. A checker that dies while reporting is worse
        # than one that reports approximately.
        try:
            print(f"  FAIL  {f}")
        except UnicodeEncodeError:
            print("  FAIL  " + f.encode("ascii", "backslashreplace").decode("ascii"))
    print()
    if fails:
        print(f"{len(fails)} problem(s) in the manuscript.")
        return 1
    print(f"ok: {len(NUMERIC)} numeric claims match their artefacts; "
          f"{len(RETIRED)} retired phrases absent; structure checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
