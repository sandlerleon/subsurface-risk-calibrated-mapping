# -*- coding: utf-8 -*-
"""Figures 8 (replacing the v1.0 panel) and 13-19 from results_v4.json (written by SubSurface_v4.py --reproduce).

    python figure_generation_v4.py --results results_v4/results_v4.json --out results_v4/figures
"""
import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import SubSurface_MC as S
import SubSurface_v4 as V

C = dict(blue="#0072B2", orange="#E69F00", green="#009E73", red="#D55E00", purple="#CC79A7", sky="#56B4E9", black="#222222", grey="#8c8c8c")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5, "legend.fontsize": 6.8, "xtick.labelsize": 7.2, "ytick.labelsize": 7.2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.7, "figure.dpi": 150, "savefig.dpi": 300, "lines.linewidth": 1.4})
MCOL = {"fusion": C["grey"], "continuity_1d": C["orange"], "continuity_1d_3rep": C["red"], "proposed_1pass": C["sky"], "proposed_3pass": C["blue"], "em_only": C["black"], "gpr_only": C["purple"]}
MMK = {"fusion": "^", "continuity_1d": "s", "continuity_1d_3rep": "D", "proposed_1pass": "v", "proposed_3pass": "o", "em_only": "x", "gpr_only": "P"}
MLAB = {"fusion": "per-segment fusion", "continuity_1d": "v1.0 continuity filter, one pass", "continuity_1d_3rep": "v1.0 filter, three repeat passes", "proposed_1pass": "proposed, one pass",
        "proposed_3pass": "proposed, three parallel passes", "em_only": "EM only", "gpr_only": "GPR only"}


def panel(ax, s):
    ax.text(-0.14, 1.05, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def save(fig, out, name):
    p = os.path.join(out, name + ".png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def pe(v):
    """[point, lo, hi] -> (point, lower error, upper error) in percent"""
    return 100 * v[0], 100 * (v[0] - v[1]), 100 * (v[2] - v[0])


def fig_lateral(R, out):
    sw = R["shift_sweep"]["rate_per_100m"]
    rates = sorted(sw, key=float)
    x = np.arange(len(rates))
    fig, axs = plt.subplots(1, 4, figsize=(7.6, 2.6))
    models = ["continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass"]
    for ax, key, ttl in zip(axs[:2], ("false_alarm", "false_clearance"), ("False-alarm rate (%)", "False clearance (%)")):
        for i, m in enumerate(models):
            v = [pe(sw[r][m]["metrics"][key]) for r in rates]
            ax.errorbar(x + (i - 1.5) * 0.06, [a[0] for a in v], yerr=[[a[1] for a in v], [a[2] for a in v]], color=MCOL[m], marker=MMK[m], ms=3.5, capsize=1.2, lw=1.0, label=MLAB[m])
        ax.set_xticks(x); ax.set_xticklabels(rates); ax.set_xlabel("lateral shifts per 100 m"); ax.set_title(ttl, fontsize=7.8)
    ax = axs[2]
    for i, m in enumerate(models):
        ax.plot(x, [sw[r][m]["ece"][0] for r in rates], color=MCOL[m], marker=MMK[m], ms=3.5, lw=1.0)
    ax.set_xticks(x); ax.set_xticklabels(rates); ax.set_xlabel("lateral shifts per 100 m"); ax.set_title("Calibration error (ECE)", fontsize=7.8)
    ax = axs[3]
    for m in ("proposed_1pass", "proposed_3pass"):
        ax.plot(x, [100 * sw[r][m]["lateral_error_m"]["share_within_0p5m"] for r in rates], color=MCOL[m], marker=MMK[m], ms=3.5, lw=1.0)
    ax.set_xticks(x); ax.set_xticklabels(rates); ax.set_xlabel("lateral shifts per 100 m"); ax.set_title("Lateral error ≤ 0.5 m (%)", fontsize=7.8)
    h, l = axs[0].get_legend_handles_labels()
    for a, s in zip(axs, "abcd"):
        panel(a, s)
    fig.tight_layout(w_pad=0.9)
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.1))
    return save(fig, out, "fig13_lateral_robustness")


def fig_health(R, out):
    names = ["baseline", "B_gpr_failed_flagged", "C_gpr_failed_unflagged", "D_both_degraded", "mixed_health_realistic_diagnostic"]
    lab = ["A\nhealthy", "B\nfailed,\nflagged", "C\nfailed,\nunflagged", "D\ndegraded", "mixed,\nrealistic\ndiagnostic"]
    models = ["fusion", "continuity_1d", "proposed_1pass", "proposed_3pass"]
    fig, axs = plt.subplots(1, 3, figsize=(7.6, 2.9))
    x = np.arange(len(names))
    for ax, key, ttl in zip(axs, ("false_clearance", "unverified", "sensitivity"), ("False clearance among released (%)", "Share of corridor unverified (%)", "Sensitivity among decided segments (%)")):
        for i, m in enumerate(models):
            v = [pe(R["scenarios"][n]["models"][m]["metrics"][key]) for n in names]
            ax.errorbar(x + (i - 1.5) * 0.12, [a[0] for a in v], yerr=[[a[1] for a in v], [a[2] for a in v]], color=MCOL[m], marker=MMK[m], ms=3.5, capsize=1.2, lw=0, elinewidth=0.9, label=MLAB[m])
        ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=6.3); ax.set_title(ttl, fontsize=7.8)
    h, l = axs[0].get_legend_handles_labels()
    for a, s in zip(axs, "abc"):
        panel(a, s)
    fig.tight_layout(w_pad=0.9)
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.06))
    return save(fig, out, "fig14_sensor_health")


def fig_zones(R, out):
    z = R["zones"]
    ds = z["depths_m"]
    soils = V.SOILS4
    utils = S.UTILS
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    col = {"A": C["green"], "B": "#F0E442", "C": C["red"]}
    cw, ch = len(ds) + 2, 1.0
    for i, s in enumerate(soils):
        for j, u in enumerate(utils):
            letters = z["zones"][s][u]
            for k, l in enumerate(letters):
                ax.add_patch(Rectangle((j * cw + k, -i * 1.4), 1, 1.0, color=col[l], lw=0))
    ax.set_xlim(-0.5, len(utils) * cw)
    ax.set_ylim(-len(soils) * 1.4 + 0.2, 1.3)
    ax.set_yticks([-i * 1.4 + 0.5 for i in range(len(soils))]); ax.set_yticklabels([S.SOIL_LABEL.get(s, s.replace("_", " ").capitalize()) + (" (unseen)" if i >= 5 else "") for i, s in enumerate(soils)], fontsize=7)
    ax.set_xticks([j * cw + len(ds) / 2 for j in range(len(utils))]); ax.set_xticklabels([S.UTIL_LABEL[u].replace(" ", "\n", 1) for u in utils], fontsize=6.3)
    ax.xaxis.tick_top()
    for sp in ("left", "bottom", "top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    ax.text(0, -len(soils) * 1.4 + 0.3, "each strip: depth 0.5 m (left) to 7 m (right) in 0.5 m steps", fontsize=6.3, color=C["black"])
    for l, c_ in (("A  detectable (≥ 0.9)", col["A"]), ("B  marginal (0.3 to 0.9)", col["B"]), ("C  not established (< 0.3)", col["C"])):
        pass
    handles = [Rectangle((0, 0), 1, 1, color=col[k]) for k in "ABC"]
    ax.legend(handles, ["Zone A: detectable (fused P ≥ 0.9)", "Zone B: marginal", "Zone C: capability not established (< 0.3)"], loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False, fontsize=6.5)
    return save(fig, out, "fig15_capability_zones")


def fig_equal_coverage(R, out):
    fig, axs = plt.subplots(2, 2, figsize=(7.6, 5.4))
    pols = ["em_only", "gpr_dual", "seg_flat", "anch_binary", "anch_three_state", "random"]
    lab = {"em_only": "EM only", "gpr_dual": "GPR dual", "seg_flat": "GPR + EM, per segment", "anch_binary": "anchored, binary", "anch_three_state": "anchored, three-state", "random": "random"}
    col = {"em_only": C["black"], "gpr_dual": C["purple"], "seg_flat": C["grey"], "anch_binary": C["orange"], "anch_three_state": C["blue"], "random": C["red"]}
    mk = {"em_only": "x", "gpr_dual": "P", "seg_flat": "^", "anch_binary": "s", "anch_three_state": "o", "random": "d"}
    for ax, key, ttl in ((axs[0, 0], "equal_coverage", "Matched model"), (axs[0, 1], "equal_coverage_half_shifts", "Half of losses are lateral shifts")):
        E = R[key]
        for p in pols:
            pts = [(c["coverage"], c["strikes_per_km"]) for c in E["policies"][p]["by_coverage"] if c["strikes_per_km"] is not None]
            xs = [100 * a for a, _ in pts]
            ys = [max(b[0], 0.05) for _, b in pts]
            lo = [max(b[0] - b[1], 0.04) for _, b in pts]
            hi = [b[0] + b[1] for _, b in pts]
            ax.plot(xs, ys, color=col[p], marker=mk[p], ms=3.5, lw=1.0, label=lab[p])
        ax.set_yscale("log"); ax.set_ylim(0.04, 200); ax.set_xlabel("corridor released for mechanical excavation (%)"); ax.set_ylabel("utility strikes per km"); ax.set_title(ttl, fontsize=8)
    axs[0, 0].legend(fontsize=5.8, frameon=False, loc="lower right")
    ax = axs[1, 0]
    risks = ["0.01", "0.02", "0.05"]
    w = 0.16
    for i, p in enumerate(["gpr_dual", "seg_flat", "anch_binary", "anch_three_state"]):
        v = [100 * R["equal_coverage"]["policies"][p]["equal_risk_coverage"][r][0] for r in risks]
        e = [100 * R["equal_coverage"]["policies"][p]["equal_risk_coverage"][r][1] for r in risks]
        ax.bar(np.arange(3) + (i - 1.5) * w, v, w, yerr=e, color=col[p], label=lab[p], capsize=1.5)
    ax.set_xticks(range(3)); ax.set_xticklabels(["≤ 1%", "≤ 2%", "≤ 5%"]); ax.set_xlabel("maximum strike rate among released segments"); ax.set_ylabel("corridor that can be released (%)")
    ax.set_title("Equal-risk operating points (matched model)", fontsize=8)
    ax = axs[1, 1]
    for p in ["gpr_dual", "seg_flat", "anch_binary", "anch_three_state", "random"]:
        cc = R["equal_coverage"]["policies"][p]["cost_per_km"]["strike_cost_x1"]
        if not cc:
            continue
        pts = [(a, b) for a, b in cc["curve"] if b is not None]
        ax.plot([100 * a for a, _ in pts], [b / 1000 for _, b in pts], color=col[p], marker=mk[p], ms=3, lw=1.0, label=lab[p])
    ax.set_xlabel("corridor released for mechanical excavation (%)"); ax.set_ylabel("strike + holding cost (US$ thousand per km)"); ax.set_title("Cost against coverage (scenario assumptions)", fontsize=8)
    ax.set_yscale("log")
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: "{:,.0f}".format(v)))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, p: ""))
    for a, s in zip(axs.ravel(), "abcd"):
        panel(a, s)
    fig.tight_layout(h_pad=1.5, w_pad=1.2)
    return save(fig, out, "fig08_equal_coverage")


def fig_scenarios(R, out):
    names = ["baseline", "curved", "shifted", "shifted_frequent", "interrupted", "map_offset", "map_incomplete", "map_misleading", "sparse_coverage", "mixed_health_realistic_diagnostic", "ood_soils", "combined_stress"]
    lab = {"baseline": "baseline", "curved": "curved", "shifted": "shifted", "shifted_frequent": "shifted, frequent", "interrupted": "interrupted", "map_offset": "map offset", "map_incomplete": "no anchor",
           "map_misleading": "misleading anchor", "sparse_coverage": "sparse coverage", "mixed_health_realistic_diagnostic": "mixed sensor health", "ood_soils": "unseen soils (with check)", "combined_stress": "combined stress"}
    models = ["fusion", "continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass"]
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 4.6), sharey=True)
    y = np.arange(len(names))[::-1]
    for ax, key, ttl in zip(axs, ("false_clearance", "unverified"), ("False clearance among released (%)", "Share of corridor unverified (%)")):
        for i, m in enumerate(models):
            v = [pe(R["scenarios"][n]["models"][m]["metrics"][key]) for n in names]
            ax.errorbar([a[0] for a in v], y + (i - 2) * 0.13, xerr=[[a[1] for a in v], [a[2] for a in v]], color=MCOL[m], marker=MMK[m], ms=3.5, lw=0, elinewidth=0.8, capsize=1.0, label=MLAB[m])
        ax.set_title(ttl, fontsize=8); ax.grid(axis="x", lw=0.3, color="#dddddd")
    axs[0].set_xscale("symlog", linthresh=1.0); axs[0].set_xlim(-0.2, 100)
    axs[0].set_yticks(y); axs[0].set_yticklabels([lab[n] for n in names], fontsize=7)
    h, l = axs[0].get_legend_handles_labels()
    panel(axs[0], "a"); panel(axs[1], "b")
    fig.tight_layout(w_pad=0.8)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.06))
    return save(fig, out, "fig16_model_comparison")


def fig_ood(R, out):
    names = ["baseline", "baseline_with_reference_check", "ood_soils_no_guard", "ood_soils"]
    lab = ["seen soils", "seen soils,\n+ check", "unseen soils", "unseen soils,\n+ check"]
    models = ["continuity_1d", "proposed_3pass"]
    fig, axs = plt.subplots(1, 3, figsize=(7.6, 2.8))
    x = np.arange(len(names))
    for ax, key, ttl in zip(axs[:2], ("false_clearance", "unverified"), ("False clearance among released (%)", "Share of corridor unverified (%)")):
        for i, m in enumerate(models):
            v = [pe(R["scenarios"][n]["models"][m]["metrics"][key]) for n in names]
            ax.errorbar(x + (i - 0.5) * 0.14, [a[0] for a in v], yerr=[[a[1] for a in v], [a[2] for a in v]], color=MCOL[m], marker=MMK[m], ms=4, capsize=1.5, lw=0, elinewidth=0.9, label=MLAB[m])
        ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=5.8); ax.set_title(ttl, fontsize=7.8)
    h, l = axs[0].get_legend_handles_labels()
    ax = axs[2]
    for i, m in enumerate(models):
        ax.bar(x + (i - 0.5) * 0.3, [R["scenarios"][n]["models"][m]["ece"][0] for n in names], 0.3, color=MCOL[m])
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=5.8); ax.set_title("Expected calibration error", fontsize=7.8)
    for a, s in zip(axs, "abc"):
        panel(a, s)
    fig.tight_layout(w_pad=0.9)
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.08))
    return save(fig, out, "fig17_out_of_distribution")


def fig_voi(R, out):
    fig, axs = plt.subplots(1, 3, figsize=(7.6, 2.7), sharey=False)
    col = {"random": C["grey"], "probability": C["orange"], "value_of_information": C["blue"]}
    lab = {"random": "random", "probability": "highest probability first", "value_of_information": "highest value of information first"}
    for ax, h in zip(axs, ("1000.0", "3000.0", "10000.0")):
        V_ = R["voi"][h]
        for s in ("random", "probability", "value_of_information"):
            pts = V_["strategies"][s]
            ax.errorbar([100 * p["budget"] for p in pts], [p["change_vs_no_pits_usd_per_km"][0] / 1000 for p in pts], yerr=[p["change_vs_no_pits_usd_per_km"][1] / 1000 for p in pts],
                        color=col[s], marker="o", ms=3, capsize=1.2, lw=1.0, label=lab[s])
        ax.axhline(0, color=C["black"], lw=0.6, ls=":")
        ax.set_title("holding cost US$%s per segment" % "{:,}".format(int(float(h))), fontsize=7.8)
        ax.set_xlabel("pit budget (% of all-candidate pit cost)")
    axs[0].set_ylabel("change in total cost vs no pits\n(US$ thousand per km)")
    axs[0].legend(fontsize=5.8, frameon=False)
    for a, s in zip(axs, "abc"):
        panel(a, s)
    fig.tight_layout(w_pad=1.0)
    return save(fig, out, "fig18_value_of_information")


def fig_tco(R, out):
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 2.9))
    ax = axs[0]
    sens = R["tco"]["sensitivity"]
    y = np.arange(len(sens))[::-1]
    names = {"km_per_day": "survey throughput (km/day)", "field_days_per_year": "field days per year", "capital": "equipment capital", "crew_per_field_day": "crew cost per field day",
             "downtime_frac": "equipment downtime", "maintenance_frac_per_year": "maintenance (% of capital)", "data_consumables_per_year": "data and consumables", "gnss_subscription_per_year": "GNSS subscription",
             "training_refresher_per_year": "refresher training"}
    for yi, r in zip(y, sens):
        ax.plot([r["favourable"], r["unfavourable"]], [yi, yi], color=C["grey"], lw=2.2, solid_capstyle="butt")
        ax.plot(r["favourable"], yi, "o", color=C["blue"], ms=3.8); ax.plot(r["unfavourable"], yi, "s", color=C["orange"], ms=3.8)
    ax.axvline(sens[0]["base"], color=C["black"], lw=0.7, ls=":")
    ax.set_yticks(y); ax.set_yticklabels([names.get(r["parameter"], r["parameter"]) for r in sens], fontsize=6.5)
    ax.set_xlabel("five-year cost per surveyed km (US$)")
    ax = axs[1]
    u = R["tco"]["utilisation"]
    kms = ["24", "50", "100"]
    x = np.arange(3)
    for i, sc in enumerate(("favourable", "base", "unfavourable")):
        ax.bar(x + (i - 1) * 0.26, [u[k][sc]["cost_per_surveyed_km"] for k in kms], 0.26, color=[C["blue"], C["grey"], C["orange"]][i], label=sc)
    ax.set_xticks(x); ax.set_xticklabels(["24", "50", "100"]); ax.set_xlabel("kilometres surveyed per unit-year"); ax.set_ylabel("US$ per surveyed km"); ax.legend(fontsize=6.3, frameon=False)
    ax.set_yscale("log")
    panel(axs[0], "a"); panel(axs[1], "b")
    fig.tight_layout(w_pad=1.2)
    return save(fig, out, "fig19_cost_of_ownership")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join("results_v4", "results_v4.json"))
    ap.add_argument("--out", default=os.path.join("results_v4", "figures"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    R = json.load(open(a.results, encoding="utf-8"))
    for f in (fig_lateral, fig_health, fig_zones, fig_equal_coverage, fig_scenarios, fig_ood, fig_voi, fig_tco):
        print(f(R, a.out))


if __name__ == "__main__":
    main()
