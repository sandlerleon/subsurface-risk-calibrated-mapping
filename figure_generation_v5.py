# -*- coding: utf-8 -*-
"""Figures 22-30 (reliability analyses) from results_v5.json (written by SubSurface_v5.py --reproduce).

    python figure_generation_v5.py --results results_v5/results_v5.json --out results_v5/figures
"""
import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import SubSurface_v5 as W5

C = dict(blue="#0072B2", orange="#E69F00", green="#009E73", red="#D55E00", purple="#CC79A7", sky="#56B4E9", black="#222222", grey="#8c8c8c", yellow="#F0E442")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.2, "legend.fontsize": 6.8, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.7, "figure.dpi": 150, "savefig.dpi": 300, "lines.linewidth": 1.3})
FLOOR = 2e-4
SCLAB = {"baseline": "Baseline", "shifted_frequent": "Frequent shifts", "A_gpr_failed_flagged": "A: GPR failed, flagged", "B_gpr_failed_unflagged": "B: GPR failed, unflagged",
         "C_em_degraded_wrong_geometry": "C: EM degraded, wrong geometry", "D_common_cause": "D: common cause", "G3_parallel": "Parallel utility", "G4_parallel_branch": "Parallel + branch",
         "B_x_G4": "B with parallel + branch", "ood_soils_check": "Unseen soils", "mixed_health": "Mixed sensor health", "combined": "Combined"}
SCSHORT = {"baseline": "Baseline", "shifted_frequent": "Shifts", "A_gpr_failed_flagged": "A", "B_gpr_failed_unflagged": "B", "C_em_degraded_wrong_geometry": "C", "D_common_cause": "D",
           "G3_parallel": "Parallel", "G4_parallel_branch": "Par.+branch", "B_x_G4": "B + Par.+br.", "ood_soils_check": "Unseen soils", "mixed_health": "Mixed health", "combined": "Combined"}
CURVE_STYLE = {"fusion": ("Standard fusion", C["grey"], "-"), "1d_blind": ("1D filter + blind-cell rule", C["orange"], "-"), "nominal": ("Health-aware lateral filter", C["sky"], "-"),
               "quality": ("Quality-adjusted (P2)", C["blue"], "-"), "robust": ("Robust (P5)", C["red"], "-"), "robust_swath": ("Robust incl. full swath (P7)", C["purple"], "-"), "oracle": ("Oracle parameters and health", C["black"], "--")}
POL_STYLE = {"B1_fusion_fixed": ("B1 standard fusion, 0.5", C["grey"], "x", 36), "B2_1d_framework": ("B2 1D framework", C["orange"], "^", 26), "P1_fixed": ("P1 fixed threshold", C["sky"], "o", 26),
             "P2_quality": ("P2 quality-adjusted", C["blue"], "o", 26), "P3_exp_loss": ("P3 expected loss", C["green"], "s", 26), "P4_robust_theta": ("P4 robust (parameters)", C["yellow"], "D", 24),
             "P5_robust_theta_struct": ("P5 robust (parameters + structure)", C["red"], "*", 60), "P6_robust_exp_loss": ("P6 robust expected loss", C["purple"], "P", 30),
             "P7_robust_swath": ("P7 robust incl. swath", "#7A3B69", "v", 26), "B5_oracle": ("B5 oracle", C["black"], "+", 40),
             "RC_fusion": ("calibrated fusion + abstention", "#9a9a9a", "d", 22), "RC_robust": ("calibrated robust + abstention", "#e8a090", "h", 24)}


def panel(ax, s, dx=-0.16):
    ax.text(dx, 1.05, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def save(fig, out, name):
    p = os.path.join(out, name + ".png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def fl(x):
    return np.array([np.nan if v is None else v for v in x], float)


# ----------------------------------------------------------------------------------------------------------------
def fig_tree(R, out):
    st = R["scenario_study"]["scenarios"]
    fig = plt.figure(figsize=(7.6, 4.4))
    ax = fig.add_axes([0.0, 0.0, 0.50, 1.0]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    def box(x, y, w, h, text, fc, fs=6.4, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012", fc=fc, ec=C["black"], lw=0.6, zorder=3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", zorder=4)
    box(0.12, 0.88, 0.76, 0.10, "Top event F: segment released (A = 1) and a modelled\nutility intersects its excavation envelope (U = 1)", "#f4d6c8", 6.8, True)
    heads = [("Detection failure", "#cfe4f3", ["weak signal at depth\n(capability zone B)", "miss inside the\ncapable zone"]),
             ("Model failure", "#d9efe4", ["unmodelled branch or\nparallel utility", "sensor parameters\ndiffer from assumed", "unseen soil"]),
             ("Decision failure", "#fbe9c0", ["threshold too permissive:\npredicted risk below\nobserved risk"]),
             ("Verification failure", "#eadbe6", ["sensor fault not\nflagged", "reference check\nmisses a shift"])]
    xs = [0.0, 0.26, 0.52, 0.76]
    for (h, col, leaves), x0 in zip(heads, xs):
        w = 0.23
        ax.plot([0.5, x0 + w / 2], [0.88, 0.76], color=C["black"], lw=0.6, zorder=1)
        box(x0, 0.66, w, 0.10, h.replace(" failure", chr(10) + "failure"), col, 6.2, True)
        for i, lf in enumerate(leaves):
            y = 0.50 - 0.17 * i
            ax.plot([x0 + w / 2, x0 + w / 2], [0.66, y + 0.12], color=C["grey"], lw=0.5, zorder=1)
            box(x0, y, w, 0.12, lf, "white", 5.2)
    ax.text(0.5, 0.03, "Conceptual decomposition, not a complete Boolean tree: the branches\nare correlated and share causes (soil, sensor, geometry).", ha="center", va="bottom", fontsize=6.3, color=C["black"], style="italic")
    panel(ax, "a", 0.0)
    ax2 = fig.add_axes([0.62, 0.17, 0.37, 0.78])
    cats = [("verification_missed_sensor_diagnostic", "Sensor fault not flagged", C["purple"]), ("verification_missed_reference_check_unseen_soil", "Unseen soil not flagged", "#b07aa1"),
            ("model_unmodelled_branch", "Unmodelled branch", C["green"]), ("detection_marginal_capability", "Marginal capability", C["sky"]), ("detection_miss_in_capable_zone", "Miss in capable zone", C["blue"])]
    names = [n for n in W5.SCEN_D if "P2_quality" in st[n]["attribution"] and st[n]["attribution_unsafe_mass"]["P2_quality"] > 5e-4]
    names = names[:9]
    y = np.arange(len(names))[::-1]
    left = np.zeros(len(names))
    for key, lab, col in cats:
        v = np.array([st[n]["attribution"]["P2_quality"][key] for n in names])
        ax2.barh(y, v, left=left, color=col, edgecolor="white", lw=0.4, label=lab)
        left += v
    ax2.set_yticks(y); ax2.set_yticklabels([SCSHORT[n] for n in names], fontsize=6.6)
    for yi, n in zip(y, names):
        ax2.text(1.02, yi, "%.1f%%" % (100 * st[n]["attribution_unsafe_mass"]["P2_quality"]), va="center", fontsize=6.2)
    ax2.text(1.02, len(names) - 0.2, "P(F)", fontsize=6.2, fontweight="bold")
    ax2.set_xlim(0, 1); ax2.set_xlabel("share of unsafe releases of policy P2 (%)"); ax2.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax2.set_xticklabels(["0", "25", "50", "75", "100"])
    ax2.legend(loc="upper center", bbox_to_anchor=(0.45, -0.22), ncol=2, frameon=False, fontsize=6.1)
    panel(ax2, "b", -0.42)
    return save(fig, out, "fig22_failure_tree")


def fig_rc(R, out, names=("baseline", "mixed_health", "G4_parallel_branch", "D_common_cause", "ood_soils_check", "B_gpr_failed_unflagged")):
    st = R["scenario_study"]["scenarios"]
    grid = W5.CGRID
    fig, axs = plt.subplots(2, 3, figsize=(7.6, 4.8), sharex=True)
    for ax, n, s in zip(axs.ravel(), names, "abcdef"):
        for key, (lab, col, ls) in CURVE_STYLE.items():
            m = fl(st[n]["curves"][key][0]); h = fl(st[n]["curves"][key][1])
            ok = np.isfinite(m)
            if not ok.any():
                continue
            mm = np.maximum(m, FLOOR)
            ax.plot(grid[ok], mm[ok], color=col, ls=ls, lw=1.2 if key != "robust" else 1.8, label=lab)
            if key in ("quality", "robust", "fusion"):
                lo = np.maximum(m - np.nan_to_num(h), FLOOR); hi = np.maximum(m + np.nan_to_num(h), FLOOR)
                ax.fill_between(grid[ok], lo[ok], hi[ok], color=col, alpha=0.18, lw=0)
        ax.set_yscale("log"); ax.set_ylim(FLOOR, 1.0); ax.set_xlim(0, 0.9)
        ax.set_title(SCLAB[n], fontsize=7.4)
        panel(ax, s, -0.2)
        if s in "def":
            ax.set_xlabel("released coverage P(A)")
        if s in "ad":
            ax.set_ylabel("conditional risk P(U | A)")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout(h_pad=0.8, w_pad=0.6)
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=6.4, bbox_to_anchor=(0.5, -0.07))
    return save(fig, out, "fig23_reliability_coverage")


def fig_policies(R, out, names=("baseline", "mixed_health", "G4_parallel_branch", "D_common_cause", "ood_soils_check", "B_gpr_failed_unflagged")):
    st = R["scenario_study"]["scenarios"]
    fig, axs = plt.subplots(2, 3, figsize=(7.6, 5.0), sharex=True)
    for ax, n, s in zip(axs.ravel(), names, "abcdef"):
        for p, (lab, col, mk, ms) in POL_STYLE.items():
            if p not in st[n]["policies"]:
                continue
            d = st[n]["policies"][p]
            x = d["coverage"][0]; y = max(d["cond_risk"][0], FLOOR)
            lo = max(d["cond_risk"][1], FLOOR) if d["cond_risk"][1] is not None else y; hi = max(d["cond_risk"][2], FLOOR) if d["cond_risk"][2] is not None else y
            ax.errorbar([x], [y], yerr=[[max(y - lo, 0)], [max(hi - y, 0)]], xerr=[[max(x - d["coverage"][1], 0)], [max(d["coverage"][2] - x, 0)]], color=col, lw=0.5, capsize=0, zorder=2)
            ax.scatter([x], [y], marker=mk, s=ms, color=col, zorder=3, label=lab, linewidth=0.4, **({} if mk in ("x", "+") else dict(edgecolor="white")))
        ax.set_yscale("log"); ax.set_ylim(FLOOR, 1.0); ax.set_xlim(0, 1.0)
        ax.set_title(SCLAB[n], fontsize=7.4)
        panel(ax, s, -0.2)
        if s in "def":
            ax.set_xlabel("released coverage P(A)")
        if s in "ad":
            ax.set_ylabel("conditional risk P(U | A)")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout(h_pad=0.8, w_pad=0.6)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.2, bbox_to_anchor=(0.5, -0.1))
    return save(fig, out, "fig24_policy_tradeoff")


def fig_faults(R, out):
    st = R["scenario_study"]["scenarios"]
    names = ["baseline", "A_gpr_failed_flagged", "B_gpr_failed_unflagged", "C_em_degraded_wrong_geometry", "D_common_cause", "G3_parallel", "G4_parallel_branch", "B_x_G4"]
    pols = [("P1_fixed", C["sky"], "P1 fixed"), ("P2_quality", C["blue"], "P2 quality-adjusted"), ("P5_robust_theta_struct", C["red"], "P5 robust"), ("B2_1d_framework", C["orange"], "B2 1D framework")]
    fig, axs = plt.subplots(2, 1, figsize=(7.6, 5.0), sharex=True)
    x = np.arange(len(names)); w = 0.2
    for ax, key, ttl in zip(axs, ("cond_risk", "coverage"), ("Conditional false-clearance risk P(U | A)", "Released coverage P(A)")):
        for i, (p, col, lab) in enumerate(pols):
            v = np.array([st[n]["policies"][p][key] for n in names], float)
            val = np.maximum(v[:, 0], FLOOR) if key == "cond_risk" else v[:, 0]
            lo = np.maximum(v[:, 1], FLOOR) if key == "cond_risk" else v[:, 1]; hi = np.maximum(v[:, 2], FLOOR) if key == "cond_risk" else v[:, 2]
            ax.bar(x + (i - 1.5) * w, val, w * 0.92, color=col, label=lab, yerr=[np.maximum(val - lo, 0), np.maximum(hi - val, 0)], error_kw=dict(lw=0.6, capsize=0))
        ax.set_ylabel(ttl, fontsize=7.4)
        if key == "cond_risk":
            ax.set_yscale("log"); ax.set_ylim(FLOOR, 1.0)
            # independent-combination prediction for the compound case B with parallel + branch
            rB = st["B_gpr_failed_unflagged"]["policies"]["P2_quality"]["cond_risk"][0]; rG = st["G4_parallel_branch"]["policies"]["P2_quality"]["cond_risk"][0]
            naive = 1 - (1 - rB) * (1 - rG)
            ax.scatter([x[-1] + 0.0], [naive], marker="D", s=28, color="white", edgecolor=C["black"], zorder=5, label="independent-combination prediction (P2)")
    axs[1].set_xticks(x); axs[1].set_xticklabels([SCSHORT[n] for n in names], fontsize=6.8)
    panel(axs[0], "a", -0.08); panel(axs[1], "b", -0.08)
    h, l = axs[0].get_legend_handles_labels()
    fig.tight_layout(h_pad=0.6)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.4, bbox_to_anchor=(0.5, -0.07))
    return save(fig, out, "fig25_fault_combinations")


def fig_decomp(R, out):
    D = R["decomposition"]["by_policy"]
    pols = [("P2_quality", C["blue"], "P2"), ("P5_robust_theta_struct", C["red"], "P5"), ("B2_1d_framework", C["orange"], "B2")]
    ms = R["decomposition"]["structural_models"]
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.4), gridspec_kw=dict(width_ratios=[1, 1.25]))
    ax = axs[0]
    y0 = np.arange(len(ms))[::-1]
    h = 0.24
    for i, (p, col, lab) in enumerate(pols):
        ep = np.array([D[p][m]["epistemic_share"] if D[p][m]["epistemic_share"] is not None else np.nan for m in ms], float)
        ci = np.array([D[p][m]["epistemic_share_ci"] for m in ms], float)
        yy = y0 + (1 - i) * h
        ax.barh(yy, 100 * ep, h * 0.9, color=col, label=lab + ": epistemic (parameters)")
        ax.barh(yy, 100 * (1 - ep), h * 0.9, left=100 * ep, color=col, alpha=0.28, label=lab + ": aleatory (network)")
        ax.errorbar(100 * ep, yy, xerr=[100 * np.maximum(ep - ci[:, 0], 0), 100 * np.maximum(ci[:, 1] - ep, 0)], fmt="none", ecolor=C["black"], lw=0.6, capsize=0)
    ax.set_yticks(y0); ax.set_yticklabels([m.split(" ", 1)[0] for m in ms]); ax.set_xlim(0, 100)
    ax.set_xlabel("share of variance of the unsafe-release probability (%)")
    ax.set_title("Variance decomposition per structural model", fontsize=7.4)
    panel(ax, "a", -0.14)
    ax2 = axs[1]
    pos = np.arange(len(ms))
    for i, (p, col, lab) in enumerate(pols):
        data = [100 * np.array(D[p][m]["theta_cell_P_F"]) for m in ms]
        bp = ax2.boxplot(data, positions=pos + (i - 1) * 0.26, widths=0.22, patch_artist=True, showfliers=False, medianprops=dict(color="white", lw=1.0), whiskerprops=dict(lw=0.6, color=col), capprops=dict(lw=0.6, color=col))
        for b in bp["boxes"]:
            b.set_facecolor(col); b.set_edgecolor(col)
        ax2.scatter(pos + (i - 1) * 0.26, [100 * D[p][m]["P_F_theta_max"] for m in ms], marker="v", s=14, color=col, zorder=5)
        ax2.plot([], [], color=col, lw=4, label=lab)
    ax2.set_xticks(pos); ax2.set_xticklabels([m.split(" ", 1)[0] for m in ms]); ax2.set_ylabel("P(F) over parameter draws (%)")
    ax2.set_yscale("symlog", linthresh=0.05); ax2.set_ylim(0, 20)
    ax2.set_title("Distribution over the parameter envelope; triangle = maximum", fontsize=7.4)
    ax2.set_xlabel("structural model of the geometry (scenario, not weighted)")
    h1, l1 = ax2.get_legend_handles_labels()
    ax2.legend(h1, l1, loc="upper left", frameon=False, fontsize=6.6)
    panel(ax2, "b", -0.14)
    fig.tight_layout(w_pad=1.2)
    return save(fig, out, "fig26_aleatory_epistemic")


ABL_LAB = {"no_sensor_health": "no sensor-health information", "no_spatial_continuity": "no spatial continuity", "no_structural_uncertainty": "no structural uncertainty",
           "no_parameter_uncertainty": "no parameter uncertainty", "no_capability_thresholds": "no capability thresholds", "no_robustness": "no robustness (P2 ranking)"}
ABL_COL = [C["purple"], C["green"], C["orange"], C["yellow"], C["sky"], C["grey"]]


def fig_ablation(R, out, names=("baseline", "mixed_health", "combined", "G4_parallel_branch", "D_common_cause", "ood_soils_check", "B_gpr_failed_unflagged")):
    A = R["scenario_study"]["ablation_equal_coverage"]
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    keys = list(ABL_LAB)
    x = np.arange(len(names)); w = 0.13
    for i, (k, col) in enumerate(zip(keys, ABL_COL)):
        v = []
        for n in names:
            e = A[n][k]["op"]
            v.append([np.nan if e["diff_vs_full"][0] is None else 100 * e["diff_vs_full"][0], 0 if e["diff_vs_full"][1] is None else 100 * e["diff_vs_full"][1]])
        v = np.array(v)
        ax.bar(x + (i - 2.5) * w, v[:, 0], w * 0.92, color=col, yerr=v[:, 1], error_kw=dict(lw=0.6, capsize=0), label=ABL_LAB[k])
    ax.axhline(0, color=C["black"], lw=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(["%s\n(c = %.0f%%)" % (SCLAB[n].replace(": ", ":\n", 1) if len(SCLAB[n]) > 18 else SCLAB[n], 100 * A[n]["_operating_point"]["coverage_of_full_policy"]) for n in names], fontsize=6.3)
    ax.set_ylabel("change in P(U | A) when the component is removed\n(percentage points, equal released coverage)", fontsize=7.2)
    ax.set_yscale("symlog", linthresh=0.5)
    ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=6.3)
    fig.tight_layout()
    return save(fig, out, "fig27_ablation")


GSA_SHORT = ["Soil attenuation", "Sensor sensitivity", "Diagnostic sensitivity", "Sensor failure prevalence", "Lateral shifts", "Parallel / branch share", "Unseen-soil share", "Utility loss hazard"]


def fig_gsa(R, out):
    G = R["gsa"]["sobol"]
    pols = [("P2_quality", "P2 quality-adjusted", C["blue"]), ("P5_robust_theta_struct", "P5 robust", C["red"]), ("B2_1d_framework", "B2 1D framework", C["orange"])]
    fig, axs = plt.subplots(2, 3, figsize=(7.6, 4.6), sharey=True)
    for r, (resp, rl) in enumerate((("P_F", "unsafe-release probability P(F)"), ("cond_risk", "conditional risk P(U | A)"))):
        for c, (p, pl, col) in enumerate(pols):
            ax = axs[r, c]
            s = G[p][resp]
            ST = np.array(s["ST"]); S1 = np.array(s["S1"]); ci = np.array(s["ST_ci"])
            order = np.argsort(ST)
            yy = np.arange(len(ST))
            ax.barh(yy, ST[order], color=col, alpha=0.75, label="total-order")
            ax.errorbar(ST[order], yy, xerr=[np.maximum(ST[order] - ci[0][order], 0), np.maximum(ci[1][order] - ST[order], 0)], fmt="none", ecolor=C["black"], lw=0.6, capsize=0)
            ax.scatter(S1[order], yy, marker="o", s=10, color="white", edgecolor=C["black"], lw=0.6, zorder=4, label="first-order")
            ax.set_yticks(yy); ax.set_yticklabels([GSA_SHORT[i] for i in order], fontsize=6.4)
            ax.set_title("%s\n%s (surrogate R² = %.2f)" % (pl, rl, s["r2_holdout"]), fontsize=6.6)
            if r == 1:
                ax.set_xlabel("Sobol index")
            ax.set_xlim(0, 1.0)
    axs[0, 0].legend(loc="lower right", frameon=False, fontsize=6.2)
    for ax, s in zip(axs[:, 0], "ad"):
        panel(ax, s, -0.9)
    fig.tight_layout(h_pad=0.9, w_pad=0.4)
    return save(fig, out, "fig28_global_sensitivity")


def fig_verification(R, out, names=("baseline", "mixed_health", "ood_soils_check")):
    st = R["scenario_study"]["scenarios"]
    fig, axs = plt.subplots(1, 3, figsize=(7.6, 2.5), sharey=False)
    cols = {"random": C["grey"], "lowest_probability": C["blue"], "highest_voi": C["red"]}
    labs = {"random": "random order", "lowest_probability": "lowest probability first", "highest_voi": "highest value of information"}
    for ax, n, s in zip(axs, names, "abc"):
        v = st[n]["verification"]
        sh = 100 * np.array(v["shares"])
        for k in cols:
            ax.plot(sh, 100 * np.array(v[k]), color=cols[k], marker="o", ms=3, label=labs[k])
        ax.set_xlabel("trial pits (share of all segments, %)"); ax.set_title("%s (unverified %.0f%%)" % (SCLAB[n], 100 * v["unverified_share"]), fontsize=7)
        panel(ax, s, -0.2)
    axs[0].set_ylabel("segments cleared by pits (%)")
    h, l = axs[0].get_legend_handles_labels()
    fig.tight_layout(w_pad=0.8)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.4, bbox_to_anchor=(0.5, -0.12))
    return save(fig, out, "fig29_verification_prioritisation")


def fig_gap(R, out):
    st = R["scenario_study"]["scenarios"]
    pols = [("P1_fixed", C["sky"], "P1"), ("P2_quality", C["blue"], "P2"), ("P5_robust_theta_struct", C["red"], "P5"), ("P7_robust_swath", "#7A3B69", "P7")]
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    lim = [FLOOR, 1.0]
    ax.plot(lim, lim, color=C["black"], lw=0.7, ls=":")
    for p, col, lab in pols:
        xs, ys = [], []
        for n in st:
            g = st[n]["decision_gap"].get(p)
            if g:
                xs.append(max(g["predicted"], FLOOR)); ys.append(max(g["observed"], FLOOR))
        ax.scatter(xs, ys, s=18, color=col, label=lab, edgecolor="white", lw=0.4)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("risk predicted by the filter among released segments"); ax.set_ylabel("observed risk among released segments")
    ax.legend(frameon=False, loc="upper left")
    return save(fig, out, "fig30_decision_calibration")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results_v5/results_v5.json")
    ap.add_argument("--out", default="results_v5/figures")
    a = ap.parse_args()
    R = json.load(open(a.results, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    fns = []
    if "scenario_study" in R:
        fns += [fig_tree, fig_rc, fig_policies, fig_faults, fig_ablation, fig_verification, fig_gap]
    if "decomposition" in R:
        fns.append(fig_decomp)
    if "gsa" in R:
        fns.append(fig_gsa)
    for f in fns:
        print(f(R, a.out))


if __name__ == "__main__":
    main()
