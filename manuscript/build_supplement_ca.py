# -*- coding: utf-8 -*-
"""Supplementary Material for the RESS manuscript (version 1.3).   python build_supplement_ress.py -> out/Supplementary_Material_CA.docx"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import docx_helpers as H  # noqa: E402
import common_ress as K  # noqa: E402
from common_ress import R, R4, R5, SW, PP  # noqa: E402

sys.path.insert(0, K.ROOT)
import SubSurface_v5 as W5  # noqa: E402

H.AUTO_MATH = False
doc = H.new_document(size=10, line=1.15)
ST = R5["scenario_study"]
SCN = ST["scenarios"]
SC4 = R4["scenarios"]
LAB4 = {"em_only": "EM only", "gpr_only": "GPR only (dual band)", "fusion": "Per-segment GPR + EM fusion", "continuity_1d": "v1.0 continuity filter, one pass", "continuity_1d_3rep": "v1.0 filter, three repeat passes",
        "proposed_1pass": "Proposed, one pass", "proposed_3pass": "Proposed, three parallel passes"}
SCLAB = {n: sc["label"] for n, sc in SCN.items()}


def f(v, d=1, scale=100.0):
    if v is None or v[0] is None:
        return "n/a"
    if len(v) < 3 or v[1] is None or v[2] is None:
        return ("%." + str(d) + "f") % (scale * v[0])
    return ("%." + str(d) + "f (%." + str(d) + "f to %." + str(d) + "f)") % (scale * v[0], scale * v[1], scale * v[2])


TITLE = "Change-Aware Reliability-Gated Sensor Fusion: Risk-Bounded Decisions Under Infrastructure Modifications and Model Uncertainty"
H.para(doc, "**Supplementary Material**", size=14, space_after=2)
H.para(doc, TITLE, size=10.5, space_after=2)
H.para(doc, "Software https://doi.org/%s; preprint https://doi.org/%s. All values are simulation results under stated assumptions; intervals are 95%% cluster-bootstrap percentile intervals over corridors (stratified by soil-by-utility cell) unless stated; "
            "curve statistics use 95%% t-intervals over independent simulated networks." % (SW, PP), size=9, space_after=8)

# ------------------------------------------------------------------------------------------------ S1 policies by scenario
H.heading(doc, "S1. Survey evidence layer: policies and baselines in every scenario", 1)
H.para(doc, "Percentages. P(F) = unsafe-release probability, P(U|A) = conditional false-clearance risk, P(A) = release coverage, unverified = share of all segments, cost = expected loss per km under the scenario cost assumptions (US$ thousand, per km of corridor). "
            "Policy definitions are in Table 3 of the manuscript. The calibrated-abstention levels were fitted on separate baseline networks (isotonic calibration, calibrated probability of a utility at most %.0f%%)." % (100 * ST["alpha_target"]), size=9)
pols = [p for p in W5.POLICIES if p in next(iter(SCN.values()))["policies"]]
for n, rec in SCN.items():
    H.heading(doc, "%s: %s" % (n.replace("_", " "), rec["label"]), 3)
    rows = [["Policy", "P(F)", "P(U|A)", "P(A)", "Unverified", "Cost (k$/km)"]]
    for p in pols:
        d = rec["policies"][p]
        rows.append([W5.POLICY_LABEL[p], f(d["P_F"], 2), f(d["cond_risk"], 2), f(d["coverage"]), f(d["unverified"]), f(d["cost_per_km"], 0, 1e-3)])
    H.table(doc, rows, widths=[3.0, 0.9, 0.9, 0.9, 0.8, 0.9], size=6.8)
    z = rec["zone_share"]
    H.para(doc, "Capability zones A/B/C: %.2f / %.2f / %.2f; reference check flagged %.1f%% of corridors; mean upper bound minus nominal probability %.3f; unsafe mass attributed (P2): %s." % (
        z[0], z[1], z[2], 100 * rec["guard_flag_share"], rec["robust_minus_nominal_probability"],
        ", ".join("%s %.0f%%" % (k.replace("_", " "), 100 * v) for k, v in rec["attribution"].get("P2_quality", {}).items() if v > 0.005) or "none"), size=8)

# ------------------------------------------------------------------------------------------------ S2 dominance
H.heading(doc, "S2. Dominance of reliability–coverage curves", 1)
H.para(doc, "For each pair, the share of the common released-coverage range in which the first score has a significantly lower conditional risk (95% t-interval of the paired difference over 10 networks below zero), a significantly higher risk, or no significant difference; "
            "'nowhere worse' states that the first score is never significantly worse over the range. Coverage range: the coverages both scores can reach.", size=9)
rows = [["Scenario", "Pair (A vs B)", "A better", "B better", "Indistinguishable", "Nowhere worse", "Range"]]
for n in SCN:
    for pair, d in ST["dominance"][n].items():
        a, b = pair.split("_vs_")
        rng = d["coverage_range"]
        rows.append([n.replace("_", " "), "%s vs %s" % (a, b), "%.0f%%" % (100 * d["share_A_better"]), "%.0f%%" % (100 * d["share_B_better"]), "%.0f%%" % (100 * d["share_indistinguishable"]),
                     "yes" if d["A_dominates_everywhere"] else "no", "n/a" if not rng else "%.0f%%–%.0f%%" % (100 * rng[0], 100 * rng[1])])
H.table(doc, rows, widths=[1.5, 1.8, 0.7, 0.7, 1.0, 0.8, 0.9], size=6.5)

# ------------------------------------------------------------------------------------------------ S3 ablation
H.heading(doc, "S3. Ablation at equal released coverage", 1)
H.para(doc, "Conditional risk P(U|A) in percent (mean and 95% half-width over 10 networks) for the full policy P5 and with one component removed, at 10%, 20%, 30% and 40% released coverage and at the released coverage of P5 in the scenario (op). n/a: the variant cannot release that coverage.", size=9)
AB = ST["ablation_equal_coverage"]
for n in SCN:
    op = AB[n]["_operating_point"]
    H.heading(doc, "%s (operating point: %.0f%% released)" % (n.replace("_", " "), 100 * op["coverage_of_full_policy"]), 3)
    rows = [["Variant", "10%", "20%", "30%", "40%", "op", "op: difference to full (points)"]]
    for k in W5.ABLATION:
        row = [k.replace("_", " ")]
        for c in ("0.1", "0.2", "0.3", "0.4", "op"):
            e = AB[n][k][c]
            row.append("n/a" if not e["reachable"] or e["risk"][0] is None else "%.2f (%.2f)" % (100 * e["risk"][0], 100 * (e["risk"][1] or 0)))
        e = AB[n][k]["op"]
        row.append("n/a" if e["diff_vs_full"][0] is None else "%+.2f (%.2f)" % (100 * e["diff_vs_full"][0], 100 * (e["diff_vs_full"][1] or 0)))
        rows.append(row)
    H.table(doc, rows, widths=[1.6, 0.8, 0.8, 0.8, 0.8, 0.8, 1.4], size=6.8)

# ------------------------------------------------------------------------------------------------ S4 decomposition
H.heading(doc, "S4. Aleatory and epistemic decomposition", 1)
D = R5["decomposition"]
H.para(doc, "Per policy and structural model (scenario, not weighted): mean unsafe-release probability P(F); standard deviation within a (parameter draw, structural model) cell across independent networks of %d corridors (aleatory) and across parameter draws (epistemic, corrected for sampling variance); "
            "epistemic share of variance with its 95%% bootstrap interval over parameter draws; 5th, 50th and 95th percentile and maximum of P(F) over the %d parameter draws; mean coverage." % (D["network_size_corridors"], D["n_theta_draws"]), size=9)
for p, ent in D["by_policy"].items():
    H.heading(doc, W5.POLICY_LABEL[p], 3)
    rows = [["Structural model", "mean P(F) %", "SD aleatory", "SD epistemic", "Epistemic share", "P(F) q05 / q50 / q95 / max %", "P(U|A) max %", "Coverage %"]]
    for m, v in ent.items():
        q = v["P_F_theta_quantiles"]
        rows.append([m, "%.2f" % (100 * v["mean_P_F"]), "%.2f" % (100 * v["sd_within_network"]), "%.2f" % (100 * v["sd_between_theta"]),
                     "n/a" if v["epistemic_share"] is None else "%.0f%% (%.0f–%.0f)" % (100 * v["epistemic_share"], 100 * v["epistemic_share_ci"][0], 100 * v["epistemic_share_ci"][1]),
                     "%.2f / %.2f / %.2f / %.2f" % (100 * q[0], 100 * q[2], 100 * q[4], 100 * v["P_F_theta_max"]), "%.1f" % (100 * v["cond_risk_theta_max"]), "%.0f" % (100 * v["coverage_mean"])])
    H.table(doc, rows, widths=[1.6, 0.7, 0.7, 0.7, 1.0, 1.5, 0.7, 0.6], size=6.5)

# ------------------------------------------------------------------------------------------------ S5 GSA
H.heading(doc, "S5. Global sensitivity analysis", 1)
G = R5["gsa"]
rows = [["Parameter", "Range", "Scale"]] + [[p["label"], "%g to %g" % (p["low"], p["high"]), p["scale"]] for p in G["parameters"]]
H.table(doc, rows, widths=[3.2, 1.3, 0.8], size=8)
H.para(doc, "%d Latin hypercube points; each point mixes four sub-worlds (straight or parallel-and-branch geometry, seen or unseen soils) of %d independent networks of %d corridors per cell. %s" % (G["n_points"], G["blocks_per_subworld"], G["corridors_per_cell_per_block"], G["note"]), size=8)
for p, d in G["sobol"].items():
    for resp, s in d.items():
        H.heading(doc, "%s, response %s (surrogate hold-out R² = %.2f; sum of first-order indices %.2f; Kendall τ of the total-order ranking against 60 bootstrap refits: mean %.2f, 5th percentile %.2f)" % (
            W5.POLICY_LABEL[p], "unsafe-release probability" if resp == "P_F" else "conditional risk", s["r2_holdout"], s["sum_S1"], s["kendall_tau_vs_base"][0], s["kendall_tau_vs_base"][1]), 3)
        rows = [["Parameter", "First order", "Total order", "95% interval (total)", "Ranked first (share of refits)", "Spearman rank correlation"]]
        for i, prm in enumerate(G["parameters"]):
            rows.append([prm["label"], "%.2f" % s["S1"][i], "%.2f" % s["ST"][i], "%.2f to %.2f" % (s["ST_ci"][0][i], s["ST_ci"][1][i]), "%.0f%%" % (100 * s["share_ranked_first"][i]), "%+.2f" % s["spearman"][i]])
        H.table(doc, rows, widths=[2.4, 0.8, 0.8, 1.2, 1.2, 1.1], size=7)

# ------------------------------------------------------------------------------------------------ S6 verification
H.heading(doc, "S6. Verification prioritisation", 1)
H.para(doc, "Share of the corridor cleared by trial pits (percent of all segments) for a pit budget of 2%, 5%, 10%, 20% and 40% of all segments, spent on the segments left unverified by P5.", size=9)
rows = [["Scenario", "Unverified by P5", "Order"] + ["%g%%" % (100 * s) for s in next(iter(SCN.values()))["verification"]["shares"]]]
for n, rec in SCN.items():
    v = rec["verification"]
    for o in ("random", "lowest_probability", "highest_voi"):
        rows.append([n.replace("_", " "), "%.1f%%" % (100 * v["unverified_share"]), o.replace("_", " ")] + ["%.1f" % (100 * x) for x in v[o]])
H.table(doc, rows, widths=[1.5, 0.9, 1.4] + [0.5] * 5, size=6.8)

# ------------------------------------------------------------------------------------------------ S7..S11 change-aware experiments
import numpy as np  # noqa: E402
import SubSurface_v6 as W6  # noqa: E402
R6 = K.R6
G6 = W6.CGRID
DOMS = (("utility", "Underground utilities"), ("scaffold", "Industrial scaffolding"))


def f6(x, d=2, s=100.0):
    if x is None or x[0] is None:
        return "n/a"
    return ("%." + str(d) + "f (±%." + str(d) + "f)") % (s * x[0], s * (x[1] or 0.0))


def f6p(x, d=2, s=100.0):
    return "n/a" if x is None or x[0] is None else ("%." + str(d) + "f") % (s * x[0])


def cur(rec, key, c):
    j = int(np.argmin(np.abs(G6 - c)))
    return f6(rec[key][j])


H.heading(doc, "S7. Change-aware experiments: calibration, dynamic versus static (E1, E2) and transfer (E6)", 1)
H.para(doc, "Percentages with 95%% t-interval half-widths over %d test sites of %d worlds each (elements: %d utility segments or %d scaffold members; %d epochs). Element-level metrics are over element-epochs; structure-level metrics (scaffold) are over scaffold-epochs." % (
    R6["meta"]["n_test_sites"], R6["meta"]["worlds_per_site"], W6.DOMAINS["utility"]["N"], W6.DOMAINS["scaffold"]["N"], R6["meta"]["epochs"]), size=9)
rows = [["Domain", "e (record active)", "authorized share (record)", "e (no record)", "authorized share (no record)", "e (pooled)", "authorized share (pooled)", "calibration sites x worlds"]]
for dom, lab in DOMS:
    c = R6["calibration"][dom]
    rows.append([lab] + ["%.5f" % c[k] for k in ("e_perm", "a_perm", "e_nop", "a_nop", "e_all", "a_all")] + ["%d x %d" % (c["n_sites"], c["R"])])
H.table(doc, rows, widths=[1.3, 0.8, 0.9, 0.8, 0.9, 0.7, 0.8, 0.8], size=6.8)
H.para(doc, "Event probabilities per element and epoch estimated on the calibration sites of the nominal world.", size=8)
for exp, ttl in (("dynamic_vs_static", "E1/E2: surveys only (no point sensors)"), ("transfer", "E6: point sensors on 10% of the elements")):
    for dom, lab in DOMS:
        H.heading(doc, "%s, %s" % (ttl, lab), 3)
        src = R6[exp][dom]["methods"] if exp == "dynamic_vs_static" else R6[exp][dom]
        rows = [["Method", "Coverage", "Conditional risk", "Unsafe probability", "False escalation", "Mean delay (epochs)", "Onsets missed", "Structure: coverage", "Structure: risk"]]
        for m, v in src.items():
            lab_m = W6.METHOD_LABEL.get(m, W6.BASELINE_LABEL.get(m, m))
            if "element" in v:
                e = v["element"]
                st = v.get("structure")
                rows.append([lab_m, f6(e["coverage"], 1), f6(e["cond_risk"], 3), f6(e["unsafe_prob"], 3), f6(e["false_escalation_rate"], 2), f6(v["delay"]["mean_delay"], 1, 1.0), f6(v["delay"]["share_missed"], 1),
                             f6(st["coverage"], 1) if st else "", f6(st["cond_risk"], 2) if st else ""])
            else:
                st = v["structure"]
                rows.append([lab_m, "", "", "", "", "", "", f6(st["coverage"], 1), f6(st["cond_risk"], 2)])
        H.table(doc, rows, widths=[2.0, 0.7, 0.8, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7], size=6.2)
        key = "s_curve" if dom == "scaffold" else "curve"
        rows = [["Method"] + ["%d%%" % round(100 * c) for c in (0.1, 0.2, 0.3, 0.5, 0.7, 0.9)]]
        for m, v in src.items():
            if key in v:
                rows.append([W6.METHOD_LABEL.get(m, W6.BASELINE_LABEL.get(m, m))] + [cur(v, key, c) for c in (0.1, 0.2, 0.3, 0.5, 0.7, 0.9)])
        H.para(doc, "Conditional risk (%) at matched decision coverage (" + ("structure" if dom == "scaffold" else "element") + " level).", size=8)
        H.table(doc, rows, widths=[2.2] + [0.8] * 6, size=6.6)
H.heading(doc, "Risk against the age of the last survey (E2, surveys only)", 3)
for dom, lab in DOMS:
    by = R6["dynamic_vs_static"][dom]["by_age"]
    d_ = 2 if dom == "utility" else 3
    rows = [[lab + ": method / epochs since the survey"] + [str(a) for a in R6["dynamic_vs_static"][dom]["ages"]]]
    for m in ("S0", "D0", "D2"):
        rows.append([W6.METHOD_LABEL[m] + ", observed risk (%)"] + [f6p(v, d_) for v in by[m]["cond_risk"]])
    rows.append(["D2, risk predicted by the estimator (%)"] + [f6p(v, d_) for v in by["D2"]["predicted"]])
    H.table(doc, rows, widths=[2.6] + [0.35] * 12, size=6.2)
H.heading(doc, "Regime map (utilities): unsafe-release probability of the static twin / of the dynamic estimator", 3)
rg = R6["regime"]
rms = sorted({float(k.split("|")[0]) for k in rg})
ivs = sorted({int(k.split("|")[1]) for k in rg})
rows = [["Event-rate multiplier / survey interval"] + ["%d epochs" % i for i in ivs]]
for rm in rms:
    rows.append(["x%g" % rm] + ["%.2f%% / %.2f%%" % (100 * rg["%s|%s" % (rm, iv)]["S0"]["unsafe_prob"][0], 100 * rg["%s|%s" % (rm, iv)]["D2"]["unsafe_prob"][0]) for iv in ivs])
H.table(doc, rows, widths=[1.8] + [1.2] * 4, size=7.5)

H.heading(doc, "S8. Work-record reconciliation (E3)", 1)
H.para(doc, "A point sensor on every element. Flagged = verify or escalate two epochs after the event; hazardous and not flagged = hazard present and decision a release; both as shares of the events or element-epochs of the case.", size=9)
cases = R6["permits"]["utility"]["cases"]
for dom, lab in DOMS:
    P_ = R6["permits"][dom]["methods"]
    H.heading(doc, lab, 3)
    rows = [["Method", "Case", "Flagged (%)", "Hazardous after (%)", "Hazardous and not flagged (%)"]]
    for m in ("D0", "D1", "D2"):
        for c in cases:
            rows.append([W6.METHOD_LABEL[m], c.replace("_", " "), f6(P_[m][c]["flagged"], 1), f6(P_[m][c]["hazardous_after"], 1), f6(P_[m][c]["hazard_missed"], 2)])
    H.table(doc, rows, widths=[2.0, 2.0, 0.9, 0.9, 1.0], size=6.5)
    rows = [["Method", "Attribution correct when decided (%)", "Left uncertain (%)", "Onsets missed (%)", "Mean delay (epochs)", "False escalation (%)", "Conditional risk (%)", "Coverage (%)"]]
    for m in ("D0", "D1", "D2"):
        a = P_[m]["attribution"]
        rows.append([W6.METHOD_LABEL[m], f6(a["accuracy_when_decided"], 1), f6(a["uncertain"], 1), f6(P_[m]["delay"]["share_missed"], 1), f6(P_[m]["delay"]["mean_delay"], 1, 1.0),
                     f6(P_[m]["overall"]["false_escalation_rate"], 2), f6(P_[m]["overall"]["cond_risk"], 3), f6(P_[m]["overall"]["coverage"], 1)])
    H.table(doc, rows, widths=[2.0, 0.9, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7], size=6.4)

H.heading(doc, "S9. Hybrid sensing configurations (E4)", 1)
H.para(doc, "pN: baseline survey only and point sensors on N% of the elements; sI: periodic survey every I epochs, no point sensors; hN/I: both. Cost in node equivalents. Element-level metrics of D2 and of the gated method; structure-level metrics for the scaffold.", size=9)
for dom, lab in DOMS:
    H.heading(doc, lab, 3)
    rows = [["Configuration", "Cost", "Method", "Coverage (%)", "Conditional risk (%)", "Onsets missed (%)", "Mean delay (epochs)", "Structure: coverage (%)", "Structure: risk (%)"]]
    for name, v in R6["hybrid"][dom].items():
        for m in ("D2", "G"):
            mm_ = v["methods"][m]
            st = mm_.get("structure")
            rows.append([name, "%.0f" % v["cost"], m, f6(mm_["element"]["coverage"], 1), f6(mm_["element"]["cond_risk"], 3), f6(mm_["delay"]["share_missed"], 1), f6(mm_["delay"]["mean_delay"], 1, 1.0),
                         f6(st["coverage"], 1) if st else "", f6(st["cond_risk"], 2) if st else ""])
    H.table(doc, rows, widths=[1.0, 0.5, 0.5, 0.8, 0.9, 0.8, 0.8, 0.8, 0.8], size=6.0)

H.heading(doc, "S10. Combined failures (E7) and ablation, with coverage", 1)
H.para(doc, "Conditional risk (%) and decision coverage (%) per scenario and method; element level for utilities, structure level for the scaffold (element-level values are in the results file).", size=9)
for dom, lab in DOMS:
    H.heading(doc, lab, 3)
    lvl_ = "structure" if dom == "scaffold" else "element"
    rows = [["Scenario", "Method", "Conditional risk", "Coverage", "Unsafe probability"]]
    for sc, d in R6["combined_failures"][dom].items():
        for m, v in d.items():
            rows.append([W6.SCEN_LABEL[sc], m, f6(v[lvl_]["cond_risk"], 2), f6(v[lvl_]["coverage"], 1), f6(v[lvl_]["unsafe_prob"], 3)])
    H.table(doc, rows, widths=[2.2, 0.8, 1.2, 1.0, 1.1], size=6.2)
    rows = [["Scenario", "Variant", "Conditional risk", "Coverage"]]
    for sc, d in R6["ablation"][dom].items():
        for vv, v in d.items():
            rows.append([W6.SCEN_LABEL[sc], vv.replace("_", " "), f6(v[lvl_]["cond_risk"], 2), f6(v[lvl_]["coverage"], 1)])
    H.table(doc, rows, widths=[2.0, 2.0, 1.2, 1.0], size=6.2)

H.heading(doc, "S11. Sensor placement (E5)", 1)
for dom, lab in DOMS:
    H.heading(doc, lab, 3)
    rows = [["Budget", "Strategy", "Unsafe probability (%)", "Conditional risk (%)", "Onsets missed (%)", "Mean delay (epochs)"]]
    for fr, d in R6["placement"][dom].items():
        for st_, v in d.items():
            rows.append(["%d%%" % round(100 * float(fr)), st_.replace("_", " "), f6(v["element"]["unsafe_prob"], 3), f6(v["element"]["cond_risk"], 3), f6(v["delay"]["share_missed"], 1), f6(v["delay"]["mean_delay"], 1, 1.0)])
    H.table(doc, rows, widths=[0.7, 1.4, 1.2, 1.1, 1.0, 1.0], size=6.5)

# ------------------------------------------------------------------------------------------------ S12.. lateral-tracking and cost experiments
H.heading(doc, "S12. Lateral-tracking experiments: scenario tables (six models in sixteen scenarios)", 1)
H.para(doc, "Percentages. Sensitivity is among decided segments; false clearance is the share of released (called absent) segments that are truly occupied; unverified and released are shares of all segments; intersections per km are released occupied segments per km of corridor (modeled intersections). "
            "ECE is the expected calibration error of the probability (mean over blocks, 95% interval over blocks).", size=9)
for name, sc in SC4.items():
    H.heading(doc, "%s  (%s; %d corridors; truth label: %s)" % (name.replace("_", " "), ", ".join("%s=%s" % (k, v) for k, v in sc["definition"].items()) or "defaults", sc["n_corridors"], sc["truth"]), 3)
    rows = [["Model", "Sensitivity", "False clearance", "False alarm", "Unverified", "Released", "Intersections/km", "ECE"]]
    for m, rec in sc["models"].items():
        d = rec["metrics"]
        ece = rec.get("ece")
        rows.append([LAB4[m], f(d["sensitivity"]), f(d["false_clearance"]), f(d["false_alarm"]), f(d["unverified"]), f(d["released"]), f(d["strikes_per_km"], 1, 1.0), ("%.3f" % ece[0]) if ece else "n/a"])
    H.table(doc, rows, widths=[1.7, 0.9, 0.9, 0.85, 0.8, 0.8, 0.9, 0.5], size=6.5)

H.heading(doc, "S13. Equal-coverage clearance (lateral-tracking experiments, both worlds)", 1)
for key, ttl in (("equal_coverage", "Matched model"), ("equal_coverage_half_shifts", "Half of utility losses are lateral shifts")):
    E = R4[key]
    H.heading(doc, ttl, 3)
    rows = [["Policy"] + ["%d%%" % round(100 * c) for c in E["coverage_grid"]] + ["max release", "cov. at <=1%", "<=2%", "<=5%"]]
    for p, pol in E["policies"].items():
        row = [pol["label"]]
        for q in pol["by_coverage"]:
            row.append("n/a" if q["strikes_per_km"] is None else "%.1f" % q["strikes_per_km"][0])
        row.append("%.0f%%" % (100 * pol["max_coverage"][0]))
        for r_ in ("0.01", "0.02", "0.05"):
            row.append("%.1f%%" % (100 * pol["equal_risk_coverage"][r_][0]))
        rows.append(row)
    H.table(doc, rows, widths=[1.9] + [0.38] * 8 + [0.5, 0.5, 0.4, 0.4], size=6.5)
H.para(doc, "Modelled intersections per km of corridor. Policies rank segments by probability (EM only and GPR only by detection).", size=8)

H.heading(doc, "S14. Capability zones and attenuation consistency", 1)
Z = R4["zones"]
rows = [["Soil"] + ["%s" % u.replace("_", " ") for u in next(iter(Z["deepest"].values())).keys()]]
for s, d in Z["deepest"].items():
    rows.append([s.replace("_", " ")] + ["%.1f / %.1f" % (v["zone_A_to_m"], v["zone_B_to_m"]) for v in d.values()])
H.table(doc, rows, widths=[1.0] + [0.75] * 7, size=7)
H.para(doc, "Entries are A / B: the deepest depth (m) with fused signal detection probability at least 0.9 (zone A) and at least 0.3 (zone A or B), on a 0.5 m grid up to 7 m.", size=8)
rows = [["Soil", "Two-way attenuation at 250 MHz (dB/m)", "Assumed relative permittivity", "Implied conductivity (mS/m)"]]
for s, v in R4["attenuation_consistency"].items():
    rows.append([s.replace("_", " "), "%.1f" % v["two_way_db_per_m_at_250MHz"], "%.0f" % v["assumed_eps_r"], "%.1f" % v["implied_conductivity_mS_per_m"]])
H.table(doc, rows, widths=[1.3, 1.9, 1.7, 1.6], size=8)

H.heading(doc, "S15. Value of information: change in total cost against no pits (US$ thousand per km)", 1)
for h, V_ in R4["voi"].items():
    H.heading(doc, "Holding cost US$%s per segment" % "{:,}".format(int(float(h))), 3)
    rows = [["Strategy"] + ["%g%%" % (100 * b) for b in V_["budgets_fraction_of_all_candidate_pit_cost"]]]
    for s, pts in V_["strategies"].items():
        rows.append([s.replace("_", " ")] + ["%.1f (+-%.1f)" % (p["change_vs_no_pits_usd_per_km"][0] / 1000, p["change_vs_no_pits_usd_per_km"][1] / 1000) for p in pts])
    H.table(doc, rows, widths=[1.5] + [0.7] * 7, size=7)

H.heading(doc, "S16. Pilot sample sizes (exact binomial, two-sided 95% interval)", 1)
P_ = R4["pilot_sample_sizes"]
rows = [["Target upper bound for a failure rate", "Observed failures", "Segments required"]]
for r_ in P_["false_clearance_or_event_rate"]:
    rows.append(["%.0f%%" % (100 * r_["target_upper_bound"]), str(r_["observed_events"]), str(r_["n_required"])])
H.table(doc, rows, widths=[2.4, 1.5, 1.5], size=8)
rows = [["Target lower bound for sensitivity", "Observed misses", "Occupied segments required"]]
for r_ in P_["sensitivity"]:
    rows.append(["%.0f%%" % (100 * r_["target_lower_bound"]), str(r_["observed_misses"]), str(r_["n_present_segments_required"])])
H.table(doc, rows, widths=[2.4, 1.5, 1.8], size=8)

H.heading(doc, "S17. Supplementary figures", 1)
_sf = os.path.join(HERE, "out", "supp_figs_ca.json")
if os.path.exists(_sf):
    figs = json.load(open(_sf))
    figs.sort(key=lambda d: int(re.search(r"Fig\. S(\d+)", d["caption"]).group(1)))
    for d in figs:
        H.figure(doc, d["path"], min(d["width"], 6.3), d["caption"])
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
import usspell
usspell.apply(doc, stop_at=None)
doc.save(os.path.join(HERE, "out", "Supplementary_Material_CA.docx"))
print("saved supplement")
