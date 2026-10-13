# -*- coding: utf-8 -*-
"""RESS manuscript, part B2: Results 6.5 to 6.8."""
# ------------------------------------------------------------------------------------------------ 6.5
HD("6.5 Aleatory and epistemic contributions to unsafe-release risk", 2)
SM = R5["decomposition"]["structural_models"]
D2, D5, D1, DB = DEC["by_policy"]["P2_quality"], DEC["by_policy"]["P5_robust_theta_struct"], DEC["by_policy"]["P1_fixed"], DEC["by_policy"]["B2_1d_framework"]
P("Figure 6 and Supplementary Table S4 separate the two kinds of uncertainty for %d parameter draws crossed with the five structural models (%d networks of %d corridors, %s km each, per cell). "
  "Within a structural model the unsafe-release probability of the sensor-quality-adjusted policy P2 has a mean between %s%% (L2) and %s%% (L4); the between-network (aleatory) standard deviation is %s to %s percentage points, "
  "and the standard deviation of the mean across parameter draws (epistemic) is %s to %s percentage points. The epistemic share of the variance is %s to %s%% for P2, %s to %s%% for P5, %s to %s%% for the 1D framework and %s to %s%% for P1. "
  "Parameter uncertainty therefore dominates the variability of the unsafe-release probability once a network is large enough for the network-to-network variation to average out; more simulated networks would not reduce it, and only knowledge of the parameters would. "
  "The aleatory share is a property of the network size used and would be larger for shorter networks. For P1, the share falls to %s and %s%% for the two geometries with a parallel utility: there the failure is set by the structure and is nearly insensitive to the parameters (the mean is %s%% and %s%% across the whole parameter envelope)." % (
      DEC["n_theta_draws"], DEC["blocks_per_cell"], DEC["network_size_corridors"], "%.0f" % (DEC["network_size_corridors"] * 0.5),
      "%.1f" % (100 * min(D2[m]["mean_P_F"] for m in SM)), "%.1f" % (100 * max(D2[m]["mean_P_F"] for m in SM)),
      "%.2f" % (100 * min(D2[m]["sd_within_network"] for m in SM)), "%.2f" % (100 * max(D2[m]["sd_within_network"] for m in SM)), "%.2f" % (100 * min(D2[m]["sd_between_theta"] for m in SM)), "%.2f" % (100 * max(D2[m]["sd_between_theta"] for m in SM)),
      "%.0f" % (100 * min(ES["P2_quality"])), "%.0f" % (100 * max(ES["P2_quality"])), "%.0f" % (100 * min(ES["P5_robust_theta_struct"])), "%.0f" % (100 * max(ES["P5_robust_theta_struct"])),
      "%.0f" % (100 * min(ES["B2_1d_framework"])), "%.0f" % (100 * max(ES["B2_1d_framework"])), "%.0f" % (100 * min(ES["P1_fixed"])), "%.0f" % (100 * max(ES["P1_fixed"])),
      "%.0f" % (100 * D1[SM[3]]["epistemic_share"]), "%.0f" % (100 * D1[SM[4]]["epistemic_share"]), "%.1f" % (100 * D1[SM[3]]["mean_P_F"]), "%.1f" % (100 * D1[SM[4]]["mean_P_F"])), align="justify")
FIGX(doc, os.path.join(FIG5, "fig26_aleatory_epistemic.png"), 6.5, "**Fig. 6.** Aleatory and epistemic contributions to unsafe-release risk. (a) Share of the variance of the unsafe-release probability of a simulated network (490 corridors) that is epistemic (variation of the expected value across 40 parameter draws, dark; 95% bootstrap interval) and aleatory (variation between independent networks of the same draw, light), per structural model and for P2, P5 and the 1D framework. "
         "(b) Distribution of the unsafe-release probability over the parameter draws (boxes: quartiles; whiskers: 5th to 95th percentile; triangle: maximum; the structural models are scenarios and are not averaged).", alt="Aleatory and epistemic contributions")
P("The envelope of results across structural models is the scenario analysis of Eq. 7. For P2 the mean unsafe-release probability across parameter draws is %s%% for the matched geometry and %s%% for a parallel utility and a branch, a factor of %.0f; the 95th percentile and the maximum over the draws in the worst structure are %s%% and %s%%, "
  "and the maximum conditional risk is %s%%. For the robust policy P5 the corresponding means are %s%% and %s%%, a factor of %.1f, and the maximum over all 200 parameter-by-structure cells is %s%% (conditional risk %s%%). "
  "The quantity that the structural models change most is therefore the unsafe-release probability of the nominal policy, and the robust policy narrows the envelope at the price of released coverage (%s to %s%% on average against %s to %s%% for P2). "
  "No probability has been given to the structural models, so no single risk number is claimed; the ranges are the result." % (
      "%.1f" % (100 * D2[SM[0]]["mean_P_F"]), "%.1f" % (100 * D2[SM[4]]["mean_P_F"]), D2[SM[4]]["mean_P_F"] / D2[SM[0]]["mean_P_F"], "%.1f" % (100 * D2[SM[4]]["P_F_theta_quantiles"][4]), "%.1f" % (100 * max(D2[m]["P_F_theta_max"] for m in SM)),
      "%.0f" % (100 * max(D2[m]["cond_risk_theta_max"] for m in SM)), "%.2f" % (100 * D5[SM[0]]["mean_P_F"]), "%.2f" % (100 * D5[SM[4]]["mean_P_F"]), D5[SM[4]]["mean_P_F"] / D5[SM[0]]["mean_P_F"], "%.1f" % (100 * max(D5[m]["P_F_theta_max"] for m in SM)),
      "%.1f" % (100 * max(D5[m]["cond_risk_theta_max"] for m in SM)), "%.0f" % (100 * min(D5[m]["coverage_mean"] for m in SM)), "%.0f" % (100 * max(D5[m]["coverage_mean"] for m in SM)), "%.0f" % (100 * min(D2[m]["coverage_mean"] for m in SM)), "%.0f" % (100 * max(D2[m]["coverage_mean"] for m in SM))), align="justify")

# ------------------------------------------------------------------------------------------------ 6.6
HD("6.6 Ablation and verification prioritisation", 2)
AB = ST["ablation_equal_coverage"]


def ab(n, k):
    e = AB[n][k]["op"]["diff_vs_full"]
    return "%+.1f" % (100 * e[0])


P("Removing one component of the robust policy at a time and comparing the conditional risk at equal released coverage (Fig. 7; Supplementary Table S3) shows that every component matters in some conditions and none matters everywhere. "
  "In the matched baseline all removals change the risk by at most %.1f percentage points at the released coverage of P5 (%s%%, where the full policy has a risk of %s%%). Removing sensor-health information raises the risk by %s points with mixed health, %s points when the GPR has failed and is flagged and %s points in the combined scenario; "
  "removing structural uncertainty raises it by %s, %s and %s points in the geometries C, G3 and G4 and by %s points in the common-cause scenario; removing spatial continuity raises it by %s points with unseen soils and %s points when the GPR has failed and is flagged; "
  "removing parameter uncertainty raises it by %s points with unseen soils; and falling back to the nominal ranking (no robustness, the ranking of P2) raises it by %s to %s points in the mismatch and common-cause scenarios. "
  "Two removals have the opposite sign: without sensor-health information the risk falls by %s points in the common-cause scenario and %s points with unseen soils, and without the capability thresholds it falls by %s and %s points, "
  "so that, at equal coverage, these components cost reliability in those conditions. We have no tested explanation; the thresholds and the health flags also move segments between the released and unverified sets, and in conditions where the flags and the reference check are themselves wrong they can promote a poor ranking. The result should be read as a limit of the design and not as an argument for removing the components, which are what produce the large gains in Section 6.2." % (
      np.ceil(10 * max(abs(100 * AB["baseline"][k]["op"]["diff_vs_full"][0]) for k in W5.ABLATION[1:])) / 10, "%.0f" % (100 * AB["baseline"]["_operating_point"]["coverage_of_full_policy"]), "%.2f" % (100 * AB["baseline"]["full"]["op"]["risk"][0]),
      ab("mixed_health", "no_sensor_health"), ab("A_gpr_failed_flagged", "no_sensor_health"), ab("combined", "no_sensor_health"),
      ab("C_em_degraded_wrong_geometry", "no_structural_uncertainty"), ab("G3_parallel", "no_structural_uncertainty"), ab("G4_parallel_branch", "no_structural_uncertainty"), ab("D_common_cause", "no_structural_uncertainty"),
      ab("ood_soils_check", "no_spatial_continuity"), ab("A_gpr_failed_flagged", "no_spatial_continuity"), ab("ood_soils_check", "no_parameter_uncertainty"),
      min(float(ab(n, "no_robustness")) for n in ("C_em_degraded_wrong_geometry", "D_common_cause", "G3_parallel", "G4_parallel_branch")), max(float(ab(n, "no_robustness")) for n in ("C_em_degraded_wrong_geometry", "D_common_cause", "G3_parallel", "G4_parallel_branch")),
      ab("D_common_cause", "no_sensor_health").lstrip("+-"), ab("ood_soils_check", "no_sensor_health").lstrip("+-"), ab("D_common_cause", "no_capability_thresholds").lstrip("+-"), ab("ood_soils_check", "no_capability_thresholds").lstrip("+-")), align="justify")
FIGX(doc, os.path.join(FIG5, "fig27_ablation.png"), 6.4, "**Fig. 7.** Ablation at equal released coverage: change in the conditional risk P(U | A), in percentage points (symmetric logarithmic axis), when one component of the robust policy P5 is removed, in seven scenarios. The coverage c is that of the full policy in the scenario; bars are means with 95% t-intervals over 10 networks.", alt="Ablation")
vb, vo = SCN["baseline"]["verification"], SCN["ood_soils_check"]["verification"]
P("**Verification prioritisation.** The segments that P5 leaves unverified (%s%% of the corridor in the baseline, %s%% with unseen soils) are the candidates for trial pits. With a budget of pits equal to 5%% of all segments, pits placed on the lowest-probability segments first clear %s%% of the corridor in the baseline, "
  "pits ranked by value of information %s%% and pits placed at random %s%%; with unseen soils the figures are %s%%, %s%% and %s%% (Supplementary Fig. S1). Verification does not change the risk of the segments already released; it converts unverified segments into released ones at no risk if the pit is reliable. "
  "Prioritising by probability clears as many or more segments per pit as ranking by the value of information in almost every case (the exception is the smallest budget in the baseline); the value-of-information ranking is designed to minimise expected cost, not to maximise coverage, and with the assumed costs the two are close. Both are clearly better than random placement." % (
      "%.0f" % (100 * vb["unverified_share"]), "%.0f" % (100 * vo["unverified_share"]), "%.1f" % (100 * vb["lowest_probability"][1]), "%.1f" % (100 * vb["highest_voi"][1]), "%.1f" % (100 * vb["random"][1]),
      "%.1f" % (100 * vo["lowest_probability"][1]), "%.1f" % (100 * vo["highest_voi"][1]), "%.1f" % (100 * vo["random"][1])), align="justify")
FIGX(doc, os.path.join(FIG5, "fig29_verification_prioritisation.png"), 6.4, "**Fig. S1.** Share of the corridor cleared by trial pits against the pit budget (share of all segments) for three allocation orders, among the segments left unverified by P5.", alt="Verification prioritisation")

# ------------------------------------------------------------------------------------------------ 6.7
HD("6.7 Reliability sensitivity and dominant failure drivers", 2)
GN = [p["label"] for p in GSA["parameters"]]
GS = R5["gsa"]["sobol"]


def top(p, resp, k=3):
    s = GS[p][resp]
    o = np.argsort(-np.array(s["ST"]))[:k]
    return ", ".join("%s (%.2f)" % (GN[i].split(" (")[0].lower(), s["ST"][i]) for i in o)


P("Figure 8 ranks the eight parameters by their total-order Sobol index for the unsafe-release probability and the conditional risk (Latin hypercube design of %d points; surrogate hold-out R² between %.2f and %.2f). "
  "The ranking depends on the policy, and that is the main result. For the quality-adjusted policy P2 the unsafe-release probability is dominated by the share of corridors with a parallel utility and a branch (total index %.2f; ranked first in %.0f%% of the bootstrap refits), then soil attenuation (%.2f) and the utility loss hazard (%.2f). "
  "For the robust policy P5 the structural share nearly disappears (%.2f) and the unsafe-release probability is driven by undetected sensor failure: the failure prevalence (%.2f; first in %.0f%% of the refits) and the probability that a failed sensor is flagged (%.2f). "
  "For its conditional risk the largest contribution is lateral shifting (%.2f), then failure prevalence (%.2f). The 1D framework and the fixed-threshold policy P1 are driven by soil attenuation (%.2f and %.2f), that is, by the sensor parameters, as is expected of policies with no mechanism that detects a parameter mismatch. "
  "The sum of first-order indices is %.2f to %.2f, so interactions are modest (the sum above one for P1 shows the estimation error of the surrogate). The top-ranked parameter is stable under refitting for P2 and the 1D framework (Kendall τ of the total-order ranking against refits: mean %.2f to %.2f); the lower ranks are not, and are not interpreted. "
  "The caveat of Section 5.5 applies: the parameters were sampled independently, whereas soil, sensor and model error may be correlated." % (
      GSA["n_points"], min(GS[p][r_]["r2_holdout"] for p in GS for r_ in GS[p]), max(GS[p][r_]["r2_holdout"] for p in GS for r_ in GS[p]),
      GS["P2_quality"]["P_F"]["ST"][5], 100 * GS["P2_quality"]["P_F"]["share_ranked_first"][5], GS["P2_quality"]["P_F"]["ST"][0], GS["P2_quality"]["P_F"]["ST"][7],
      GS["P5_robust_theta_struct"]["P_F"]["ST"][5], GS["P5_robust_theta_struct"]["P_F"]["ST"][3], 100 * GS["P5_robust_theta_struct"]["P_F"]["share_ranked_first"][3], GS["P5_robust_theta_struct"]["P_F"]["ST"][2],
      GS["P5_robust_theta_struct"]["cond_risk"]["ST"][4], GS["P5_robust_theta_struct"]["cond_risk"]["ST"][3], GS["B2_1d_framework"]["P_F"]["ST"][0], GS["P1_fixed"]["P_F"]["ST"][0],
      min(GS[p][r_]["sum_S1"] for p in GS for r_ in GS[p]), max(GS[p][r_]["sum_S1"] for p in GS for r_ in GS[p]),
      min(GS[p]["P_F"]["kendall_tau_vs_base"][0] for p in ("P2_quality", "B2_1d_framework")), max(GS[p]["P_F"]["kendall_tau_vs_base"][0] for p in ("P2_quality", "B2_1d_framework"))), align="justify")
FIGX(doc, os.path.join(FIG5, "fig28_global_sensitivity.png"), 6.5, "**Fig. 8.** Global sensitivity of the unsafe-release probability P(F) (a) and of the conditional risk P(U | A) (b) for three policies: total-order Sobol indices (bars; 95% bootstrap intervals over 60 refits of the surrogate) and first-order indices (circles), from a 320-point Latin hypercube design. The hold-out R² of each surrogate is shown above the panel.", alt="Global sensitivity")

# ------------------------------------------------------------------------------------------------ 6.8
HD("6.8 Sensor health and unseen soils in the lateral-tracking model", 2)
P("Two results of the version 1.1 experiments, obtained with the lateral tracker with three passes and used in earlier versions, belong in the reliability argument. With mixed sensor health and the assumed diagnostic (Fig. 9), sensor-health awareness lowers the false clearance of the lateral tracker from %s%% (version 1.0 filter) to %s%%, at an unverified share of %s%% against %s%%; the same conclusion holds in the present policies (P2 %s%% against %s%% for the 1D framework). "
  "With unseen soils (Fig. 10) the lateral tracker has a false clearance of %s%% without the on-site reference check and %s%% with it, at an unverified share of %s%%; the reference check flags %s%% of the corridors in the unseen soils and %s%% in the seen soils. "
  "In both cases the gain depends on a diagnostic or a check whose sensitivity is assumed (0.90 for a failed sensor, a binomial test with α = 0.01), and neither addresses a degradation that the diagnostic cannot see." % (
      sm4("mixed_health_realistic_diagnostic", "continuity_1d", "false_clearance"), sm4("mixed_health_realistic_diagnostic", "proposed_3pass", "false_clearance"), sm4("mixed_health_realistic_diagnostic", "proposed_3pass", "unverified", 0), sm4("mixed_health_realistic_diagnostic", "continuity_1d", "unverified", 0),
      q("mixed_health", "P2"), q("mixed_health", "B2"), sm4("ood_soils_no_guard", "proposed_3pass", "false_clearance"), sm4("ood_soils", "proposed_3pass", "false_clearance"), sm4("ood_soils", "proposed_3pass", "unverified", 0),
      pc(SC4["ood_soils"]["reference_check_flag_share"], 0), pc(SC4["baseline_with_reference_check"]["reference_check_flag_share"], 1)), align="justify")
FIGX(doc, os.path.join(K.FIG4, "fig14_sensor_health.png"), 6.3, "**Fig. 9.** Classification under sensor degradation and failure (version 1.1 experiment): (a) false clearance among released segments, (b) unverified share, (c) sensitivity among decided segments.", alt="Sensor health scenarios")
FIGX(doc, os.path.join(K.FIG4, "fig17_out_of_distribution.png"), 6.3, "**Fig. 10.** Seen and unseen soils with and without the on-site reference check (version 1.1 experiment): (a) false clearance, (b) unverified share, (c) calibration error.", alt="Unseen soils")
# supplementary figures carried over from the earlier versions
FIGX(doc, os.path.join(K.FIG4, "fig13_lateral_robustness.png"), 6.4, "**Fig. S3.** Robustness to lateral displacement of the utility: false-alarm rate, false clearance, calibration error and lateral accuracy against the number of lateral shifts per 100 m (version 1.1 experiment).", alt="Lateral robustness")
FIGX(doc, os.path.join(K.FIG4, "fig08_equal_coverage.png"), 6.4, "**Fig. S4.** Clearance at equal coverage in the version 1.1 experiment: modelled intersections per km against released coverage, in the matched model and with half of the losses as lateral shifts, equal-risk coverage and cost.", alt="Equal coverage")
FIGX(doc, os.path.join(K.FIG4, "fig16_model_comparison.png"), 6.3, "**Fig. S5.** False clearance and unverified share for five models in twelve scenarios (version 1.1 experiment).", alt="Model comparison")
FIGX(doc, os.path.join(K.FIG4, "fig15_capability_zones.png"), 6.3, "**Fig. S6.** Capability zones by soil, utility and depth (closed form).", alt="Capability zones")
FIGX(doc, os.path.join(K.FIG4, "fig21_parameter_envelope.png"), 6.2, "**Fig. S7.** Parameter-uncertainty envelope of version 1.2: false clearance of three methods over parameter draws, true sensor-blind share and the proposed layer against the version 1.0 filter.", alt="Parameter envelope")
FIGX(doc, os.path.join(K.FIG4, "fig18_value_of_information.png"), 6.3, "**Fig. S8.** Value of information (version 1.1): change in total cost against the pit budget for three allocation rules and three holding costs.", alt="Value of information")
FIGX(doc, os.path.join(K.FIG, "fig02_detectability_depth.png"), 6.3, "**Fig. S9.** Fused signal detection probability (dual-band GPR and EM) against depth for each soil and utility type (closed form).", alt="Detectability")
FIGX(doc, os.path.join(K.FIG, "fig04_ablation.png"), 6.3, "**Fig. S10.** Detection and classification performance of the compared methods of version 1.0 in sensor-visible cells and in all cells.", alt="Version 1.0 baselines")
FIGX(doc, os.path.join(K.FIG, "fig06_calibration.png"), 6.3, "**Fig. S11.** Calibration of the version 1.0 framework: reliability curves, distribution of probabilities and an isotonic recalibration.", alt="Calibration")
