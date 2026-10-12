# -*- coding: utf-8 -*-
"""Supplementary Material for the TUST manuscript (version 1.1): full scenario tables, zone depths, equal-coverage and value-of-information tables, pilot sample sizes.
python build_supplement.py -> out/Supplementary_Material_TUST.docx"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import docx_helpers as H  # noqa: E402
from common import R4, TITLE, SW, PP  # noqa: E402

H.AUTO_MATH = False
doc = H.new_document(size=10, line=1.15)
SC = R4["scenarios"]
LAB = {"em_only": "EM only", "gpr_only": "GPR only (dual band)", "fusion": "Per-segment GPR + EM fusion", "continuity_1d": "v1.0 continuity filter, one pass", "continuity_1d_3rep": "v1.0 filter, three repeat passes",
       "proposed_1pass": "Proposed, one pass", "proposed_3pass": "Proposed, three parallel passes"}


def f(v, d=1, scale=100.0):
    if v is None or v[0] is None:
        return "n/a"
    if v[1] is None or v[2] is None:
        return ("%." + str(d) + "f") % (scale * v[0])
    return ("%." + str(d) + "f (%." + str(d) + "f to %." + str(d) + "f)") % (scale * v[0], scale * v[1], scale * v[2])


H.para(doc, "**Supplementary Material**", size=14, space_after=2)
H.para(doc, TITLE, size=10.5, space_after=2)
H.para(doc, "Software https://doi.org/%s; preprint https://doi.org/%s. All values are simulation results under stated assumptions; intervals are 95%% cluster-bootstrap percentile intervals over corridors (stratified by soil-by-utility cell) unless stated." % (SW, PP), size=9, space_after=8)

H.heading(doc, "S1. Scenario tables", 1)
H.para(doc, "Percentages. Sensitivity is among decided segments; false clearance is the share of released (called absent) segments that are truly occupied; unverified and released are shares of all segments; strikes per km are released occupied segments per km of corridor. "
            "ECE is the expected calibration error of the probability (mean over blocks, 95% interval over blocks). Compute is seconds per block of 3,500 corridors (100 segments each).", size=9)
for name, sc in SC.items():
    H.heading(doc, "%s  (%s; %d corridors; truth label: %s)" % (name.replace("_", " "), ", ".join("%s=%s" % (k, v) for k, v in sc["definition"].items()) or "defaults", sc["n_corridors"], sc["truth"]), 3)
    rows = [["Model", "Sensitivity", "False clearance", "False alarm", "Unverified", "Released", "Strikes/km", "ECE", "Compute (s)"]]
    for m, rec in sc["models"].items():
        d = rec["metrics"]
        ece = rec.get("ece")
        rows.append([LAB[m], f(d["sensitivity"]), f(d["false_clearance"]), f(d["false_alarm"]), f(d["unverified"]), f(d["released"]), f(d["strikes_per_km"], 1, 1.0), ("%.3f" % ece[0]) if ece else "n/a", "%.2f" % rec["compute_seconds_per_block"]])
    H.table(doc, rows, widths=[1.7, 0.9, 0.9, 0.85, 0.8, 0.8, 0.8, 0.5, 0.5], size=6.5)
    ex = "Zone shares (A/B/C): %.2f / %.2f / %.2f." % (sc["zone_share"]["A"], sc["zone_share"]["B"], sc["zone_share"]["C"])
    if sc.get("reference_check_flag_share") is not None:
        ex += " Reference check flagged %.1f%% of corridors." % (100 * sc["reference_check_flag_share"])
    H.para(doc, ex, size=8)

H.heading(doc, "S2. Equal-coverage clearance (all policies, both worlds)", 1)
for key, ttl in (("equal_coverage", "Matched model"), ("equal_coverage_half_shifts", "Half of utility losses are lateral shifts")):
    E = R4[key]
    H.heading(doc, ttl, 3)
    rows = [["Policy"] + ["%d%%" % round(100 * c) for c in E["coverage_grid"]] + ["max release", "cov. at <=1%", "<=2%", "<=5%"]]
    for p, pol in E["policies"].items():
        row = [pol["label"]]
        for q in pol["by_coverage"]:
            row.append("n/a" if q["strikes_per_km"] is None else "%.1f" % q["strikes_per_km"][0])
        row.append("%.0f%%" % (100 * pol["max_coverage"][0]))
        for r in ("0.01", "0.02", "0.05"):
            row.append("%.1f%%" % (100 * pol["equal_risk_coverage"][r][0]))
        rows.append(row)
    H.table(doc, rows, widths=[1.9] + [0.38] * 8 + [0.5, 0.5, 0.4, 0.4], size=6.5)
H.para(doc, "Strikes per km of corridor. Policies rank segments by probability (EM only and GPR only by detection); the three-state rule never releases unverified segments, so its maximum release is limited.", size=8)

H.heading(doc, "S3. Capability zones: deepest depth (m) of zone A and zone B", 1)
Z = R4["zones"]
rows = [["Soil"] + ["%s" % u.replace("_", " ") for u in next(iter(Z["deepest"].values())).keys()]]
for s, d in Z["deepest"].items():
    rows.append([s.replace("_", " ")] + ["%.1f / %.1f" % (v["zone_A_to_m"], v["zone_B_to_m"]) for v in d.values()])
H.table(doc, rows, widths=[1.0] + [0.75] * 7, size=7)
H.para(doc, "Entries are A / B: the deepest depth with fused signal detection probability at least 0.9 (zone A) and at least 0.3 (zone A or B), on a 0.5 m grid up to 7 m. Wet clay and saline fill are the unseen soils.", size=8)
rows = [["Soil", "Two-way attenuation at 250 MHz (dB/m)", "Assumed relative permittivity", "Implied conductivity (mS/m)"]]
for s, v in R4["attenuation_consistency"].items():
    rows.append([s.replace("_", " "), "%.1f" % v["two_way_db_per_m_at_250MHz"], "%.0f" % v["assumed_eps_r"], "%.1f" % v["implied_conductivity_mS_per_m"]])
H.table(doc, rows, widths=[1.3, 1.9, 1.7, 1.6], size=8)
H.para(doc, "Implied conductivity from the one-way low-loss relation alpha = 1636 sigma / sqrt(eps_r) dB/m. The permittivities are assumptions; the comparison with site measurements is part of any field calibration.", size=8)

H.heading(doc, "S4. Value of information: change in total cost against no pits (US$ thousand per km)", 1)
for h, V_ in R4["voi"].items():
    H.heading(doc, "Holding cost US$%s per segment" % "{:,}".format(int(float(h))), 3)
    rows = [["Strategy"] + ["%g%%" % (100 * b) for b in V_["budgets_fraction_of_all_candidate_pit_cost"]]]
    for s, pts in V_["strategies"].items():
        rows.append([s.replace("_", " ")] + ["%.1f (+-%.1f)" % (p["change_vs_no_pits_usd_per_km"][0] / 1000, p["change_vs_no_pits_usd_per_km"][1] / 1000) for p in pts])
    H.table(doc, rows, widths=[1.5] + [0.7] * 7, size=7)

H.heading(doc, "S5. Pilot sample sizes (exact binomial, two-sided 95% interval)", 1)
P_ = R4["pilot_sample_sizes"]
rows = [["Target upper bound for a failure rate", "Observed failures", "Segments required"]]
for r in P_["false_clearance_or_event_rate"]:
    rows.append(["%.0f%%" % (100 * r["target_upper_bound"]), str(r["observed_events"]), str(r["n_required"])])
H.table(doc, rows, widths=[2.4, 1.5, 1.5], size=8)
rows = [["Target lower bound for sensitivity", "Observed misses", "Occupied segments required"]]
for r in P_["sensitivity"]:
    rows.append(["%.0f%%" % (100 * r["target_lower_bound"]), str(r["observed_misses"]), str(r["n_present_segments_required"])])
H.table(doc, rows, widths=[2.4, 1.5, 1.8], size=8)
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
doc.save(os.path.join(HERE, "out", "Supplementary_Material_TUST.docx"))
print("saved supplement")
