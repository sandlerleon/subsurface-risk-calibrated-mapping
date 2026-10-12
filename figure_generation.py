# -*- coding: utf-8 -*-
"""Regenerate every figure of the paper from results.json (written by SubSurface_MC.py --reproduce).

    python figure_generation.py --results out/results.json --out out/figures

Colour-blind-safe palette (Okabe-Ito); every figure is also legible in greyscale (markers and line styles differ).
"""
import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import SubSurface_MC as S

C = dict(blue="#0072B2", orange="#E69F00", green="#009E73", red="#D55E00", purple="#CC79A7", sky="#56B4E9", yellow="#F0E442", black="#222222", grey="#8c8c8c")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5, "legend.fontsize": 7,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.7, "figure.dpi": 150, "savefig.dpi": 300, "lines.linewidth": 1.4})
UL = S.UTIL_LABEL
SL = S.SOIL_LABEL
UCOL = {"pe_water": C["blue"], "ci_water": C["black"], "plastic_sewer": C["orange"], "concrete_sewer": C["red"], "power": C["green"], "telephone": C["purple"], "fibre": C["sky"]}
UMK = {"pe_water": "o", "ci_water": "s", "plastic_sewer": "^", "concrete_sewer": "v", "power": "D", "telephone": "P", "fibre": "X"}


def pct(x):
    return 100 * x


def panel(ax, s):
    ax.text(-0.14, 1.05, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def save(fig, out, name):
    p = os.path.join(out, name)
    fig.savefig(p + ".png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p + ".png"


# ------------------------------------------------------------------------------------------------------------
def fig_framework(out):
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    ax.set_xlim(0, 100); ax.set_ylim(0, 50); ax.axis("off")

    def box(x, y, w, h, text, fc, ec=C["black"], fs=7.2, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9, lw=0.9, color=C["black"]))
    box(1, 34, 17, 12, "Anchors\nmanholes, chambers,\nrecords (network\nidentity, reliability)", "#e8f1f8")
    box(1, 18, 17, 12, "GPR 250 / 600 MHz\ndetect / no-detect\nper 5 m segment", "#e8f1f8")
    box(1, 2, 17, 12, "EM locator\npassive / active,\nclamp where possible", "#e8f1f8")
    box(24, 18, 19, 12, "Soil- and depth-aware\nlikelihoods\nPd, Pfa per soil,\nmaterial, depth", "#fdf1d6")
    box(48, 18, 20, 12, "Belief propagation\nalong the corridor\npredict (loss, re-birth)\nand update (odds)", "#dff1ea")
    box(73, 34, 26, 12, "present\nbelief p > 0.5", "#f6e1d6", bold=True)
    box(73, 18, 26, 12, "absent\np ≤ 0.5 in a cell with\nadequate detectability", "#f6e1d6", bold=True)
    box(73, 2, 26, 12, "unverified\nfused Pd at mid-depth < 0.3\n(sensor-blind cell)", "#f6e1d6", bold=True, fs=6.2)
    box(24, 2, 44, 10, "Verification priority: consequence- and cost-weighted\nresidual probability → trial pits / hand digging", "#ececec")
    arrow(18, 40, 48, 28); arrow(18, 24, 24, 24); arrow(18, 8, 27, 18)
    arrow(43, 24, 48, 24); arrow(68, 28, 73, 38); arrow(68, 24, 73, 24); arrow(68, 20, 73, 9)
    arrow(80, 18, 68, 9)
    ax.text(50, 49, "Risk-calibrated decision layer (this work)", ha="center", fontsize=8.5, fontweight="bold")
    return save(fig, out, "fig01_framework")


def fig_detectability(R, out):
    cfg = R["config"]
    ds = np.arange(0.25, 7.01, 0.05)
    fig, axs = plt.subplots(1, 5, figsize=(7.4, 2.2), sharey=True)
    for s, ax in enumerate(axs):
        for u, un in enumerate(S.UTILS):
            ax.plot(ds, S.pd_fused(cfg, s, u, ds), color=UCOL[un], ls="-" if un not in ("telephone", "fibre", "pe_water") else "--", lw=1.1, label=UL[un])
        ax.axhline(0.3, color=C["grey"], lw=0.6, ls=":")
        ax.axhline(0.9, color=C["grey"], lw=0.6, ls=":")
        ax.set_title(SL[S.SOILS[s]], fontsize=8)
        ax.set_xlim(0, 7); ax.set_ylim(0, 1.02)
        ax.set_xlabel("depth (m)")
    axs[0].set_ylabel("fused signal detection\nprobability (GPR dual + EM)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=7, frameon=False, bbox_to_anchor=(0.5, -0.30), handlelength=1.6, columnspacing=1.0)
    return save(fig, out, "fig02_detectability_depth")


def fig_heatmaps(R, out):
    pd = np.array([[R["pd_mid_depth"][s][u] for u in S.UTILS] for s in S.SOILS])
    rd = np.array([[R["reliable_depth_m"][s][u] for u in S.UTILS] for s in S.SOILS])
    blind = np.array([[R["sensor_blind"][s][u] for u in S.UTILS] for s in S.SOILS])
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.9), gridspec_kw=dict(wspace=0.08))
    for k, (ax, M, ttl, fmt, cmap, vmax) in enumerate(((axs[0], pd, "Fused detection probability, mid-depth", "%.2f", "viridis", 1.0),
                                                          (axs[1], rd, "Deepest depth with fused Pd ≥ 0.9 (m)", "%.1f", "viridis", 7.5))):
        im = ax.imshow(M, cmap=cmap, vmin=0, vmax=vmax, aspect="auto")
        ax.set_xticks(range(S.NU)); ax.set_xticklabels([UL[u].replace(" ", "\n", 1) for u in S.UTILS], fontsize=6.3)
        ax.set_yticks(range(S.NS)); ax.set_yticklabels([SL[s] for s in S.SOILS] if k == 0 else [], fontsize=7)
        for i in range(S.NS):
            for j in range(S.NU):
                col = "white" if M[i, j] < 0.55 * vmax else "black"
                ax.text(j, i, fmt % M[i, j], ha="center", va="center", fontsize=6.3, color=col)
                if blind[i, j]:
                    ax.add_patch(plt.Rectangle((j - 0.48, i - 0.48), 0.96, 0.96, fill=False, edgecolor=C["red"], lw=1.6))
        ax.set_title(ttl, fontsize=7.6)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    panel(axs[0], "a"); panel(axs[1], "b")
    return save(fig, out, "fig03_detectability_maps")


def fig_ablation(R, out):
    M = R["main"]["methods"]
    order = ["em_only", "gpr250", "gpr_dual", "rule_or", "seg_flat", "seg_prior", "prop_no_anchor", "anch_gpr", "anch_generic", "anch_full", "anch_depthmarg", "anch_oracle_depth"]
    lab = {"em_only": "EM only", "gpr250": "GPR 250 MHz", "gpr_dual": "GPR dual-band", "rule_or": "OR rule", "seg_flat": "Fusion, per segment",
           "seg_prior": "Fusion, per segment,\nbase-rate prior", "prop_no_anchor": "Propagation, no anchor", "anch_gpr": "Anchored, GPR only",
           "anch_generic": "Anchored, generic soil", "anch_full": "Anchored, GPR + EM (framework)", "anch_depthmarg": "Anchored, depth-averaged", "anch_oracle_depth": "Anchored, true depth known"}
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 3.8), sharey=True)
    y = np.arange(len(order))[::-1]
    for ax, key, ttl in zip(axs, ("acc", "miss", "fa"), ("Accuracy (%)", "Miss rate (%)", "False-alarm rate (%)")):
        for dy, view, col, mk in ((0.17, "visible", C["blue"], "o"), (-0.17, "all", C["orange"], "s")):
            v = np.array([M[m][view][key][0] for m in order]) * 100
            e = np.array([M[m][view][key][1] for m in order]) * 100
            ax.errorbar(v, y + dy, xerr=e, fmt=mk, color=col, ms=3.8, lw=0.8, capsize=1.5, label=("sensor-visible cells" if view == "visible" else "all cells (blind forced to binary)"))
        ax.set_title(ttl, fontsize=8)
        ax.grid(axis="x", lw=0.3, color="#dddddd")
    axs[0].set_yticks(y); axs[0].set_yticklabels([lab[m] for m in order], fontsize=7)
    axs[1].legend(loc="center right", fontsize=6.5, frameon=False)
    for a, s in zip(axs, "abc"):
        panel(a, s)
    return save(fig, out, "fig04_ablation")


def fig_trace(R, out):
    e = R["example"]
    if not e:
        return None
    k = np.arange(len(e["truth"])) * 5.0
    fig, axs = plt.subplots(3, 1, figsize=(7.4, 3.9), sharex=True, gridspec_kw=dict(height_ratios=[0.8, 0.8, 2.0], hspace=0.12))
    ax = axs[0]
    ax.fill_between(k, 0, 1, where=np.array(e["truth"]), step="mid", color=C["green"], alpha=0.55, lw=0)
    ax.set_yticks([]); ax.set_ylabel("truth", rotation=0, ha="right", va="center", fontsize=7.5)
    ax.text(k[1], 0.5, "utility on tracked alignment", fontsize=6.5, va="center")
    ax = axs[1]
    for i, (key, lab, col) in enumerate((("d250", "GPR 250", C["blue"]), ("d600", "GPR 600", C["sky"]), ("dem", "EM", C["red"]))):
        idx = np.where(e[key])[0]
        ax.plot(k[idx], np.full(len(idx), i), "|", color=col, ms=8, mew=1.2)
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["GPR 250", "GPR 600", "EM"], fontsize=6.8); ax.set_ylim(-0.7, 2.7)
    ax.set_ylabel("detections", rotation=0, ha="right", va="center", fontsize=7.5, labelpad=34)
    ax = axs[2]
    ax.plot(k, e["p_persegment"], color=C["orange"], lw=1.0, ls="--", label="per-segment fusion")
    ax.plot(k, e["p_anchored"], color=C["blue"], lw=1.6, label="anchored belief")
    ax.axhline(0.5, color=C["grey"], lw=0.6, ls=":")
    ax.set_ylim(-0.03, 1.03); ax.set_ylabel("probability utility\nis on the alignment"); ax.set_xlabel("distance along corridor (m)")
    ax.legend(loc="center right", fontsize=7, frameon=False)
    fig.suptitle("%s, %s at %.1f m depth" % (SL[e["soil"]], UL[e["util"]].lower(), e["depth"]), fontsize=8, x=0.5, y=0.97)
    return save(fig, out, "fig05_belief_trace")


def fig_stress(R, out):
    s = R["stress"]
    fig, axs = plt.subplots(2, 3, figsize=(7.4, 4.5))
    ax = axs[0, 0]
    hz = sorted(s["hazard"], key=float)
    x = [float(h) for h in hz]
    for m, col, mk, lb in (("em_only", C["grey"], "^", "EM only"), ("seg_flat", C["orange"], "s", "per-segment fusion"), ("anch_full", C["blue"], "o", "anchored")):
        ax.errorbar(x, [pct(s["hazard"][h][m]["all"]["acc"][0]) for h in hz], yerr=[pct(s["hazard"][h][m]["all"]["acc"][1]) for h in hz], color=col, marker=mk, ms=3.5, capsize=1.5, label=lb)
    ax.set_xscale("log"); ax.set_xlabel("loss hazard (per 100 m)"); ax.set_ylabel("accuracy, all cells (%)"); ax.legend(fontsize=6.3, frameon=False)
    ax = axs[0, 1]
    ax2 = ax.twinx(); ax2.spines["right"].set_visible(True)
    for h_, mk in zip(hz, "o"):
        pass
    ax.plot(x, [pct(R["class_balance"][h]["acc"][0]) for h in hz], "o-", color=C["blue"], ms=3.5, label="accuracy")
    ax.plot(x, [pct(R["class_balance"][h]["bacc"][0]) for h in hz], "s-", color=C["green"], ms=3.5, label="balanced accuracy")
    ax.plot(x, [pct(R["class_balance"][h]["always_absent_acc"][0]) for h in hz], "^--", color=C["grey"], ms=3.5, label='"always absent"')
    ax2.plot(x, [pct(R["class_balance"][h]["prev"][0]) for h in hz], "d:", color=C["red"], ms=3.5, label="share truly present")
    ax.set_xscale("log"); ax.set_xlabel("loss hazard (per 100 m)"); ax.set_ylabel("%"); ax2.set_ylabel("share truly present (%)", color=C["red"])
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=6, frameon=False, loc="center left")
    ax = axs[0, 2]
    sh = sorted(s["shift"], key=float); x = [float(h) * 100 for h in sh]
    for m, col, mk, lb in (("em_only", C["grey"], "^", "EM only"), ("seg_flat", C["orange"], "s", "per-segment fusion"), ("anch_full", C["blue"], "o", "anchored")):
        ax.errorbar(x, [pct(s["shift"][h][m]["all"]["acc"][0]) for h in sh], yerr=[pct(s["shift"][h][m]["all"]["acc"][1]) for h in sh], color=col, marker=mk, ms=3.5, capsize=1.5, label=lb)
    ax.set_xlabel("losses that are lateral shifts (%)"); ax.set_ylabel("accuracy, all cells (%)")
    ax = axs[1, 0]
    rel = sorted(s["anchor"], key=float, reverse=True); x = [float(r) for r in rel]
    for k, col, mk, lb in (("per_segment", C["orange"], "s", "per-segment fusion"), ("overconfident", C["red"], "^", "anchored, anchor assumed certain"), ("calibrated", C["blue"], "o", "anchored, anchor reliability known")):
        ax.errorbar(x, [pct(s["anchor"][r][k]["all"]["acc"][0]) for r in rel], yerr=[pct(s["anchor"][r][k]["all"]["acc"][1]) for r in rel], color=col, marker=mk, ms=3.5, capsize=1.5, label=lb)
    ax.invert_xaxis(); ax.set_xlabel("probability the anchor is on the alignment"); ax.set_ylabel("accuracy, all cells (%)"); ax.legend(fontsize=5.8, frameon=False, loc="lower left")
    ax = axs[1, 1]
    q = sorted(s["sensor_failure"], key=float); x = [float(v) * 100 for v in q]
    for k, col, mk, lb in (("gpr", C["blue"], "o", "GPR fails"), ("em", C["red"], "s", "EM fails")):
        ax.errorbar(x, [pct(s["sensor_failure"][v][k]["all"]["acc"][0]) for v in q], yerr=[pct(s["sensor_failure"][v][k]["all"]["acc"][1]) for v in q], color=col, marker=mk, ms=3.5, capsize=1.5, label=lb)
    ax.set_xlabel("runs in which a sensor is dead (%)"); ax.set_ylabel("accuracy, all cells (%)"); ax.legend(fontsize=6.3, frameon=False)
    ax = axs[1, 2]
    fh = sorted(s["hazard_misspecified"], key=float); x = [float(v) for v in fh]
    ax.errorbar(x, [pct(s["hazard_misspecified"][v]["anch_full"]["all"]["acc"][0]) for v in fh], yerr=[pct(s["hazard_misspecified"][v]["anch_full"]["all"]["acc"][1]) for v in fh], color=C["blue"], marker="o", ms=3.5, capsize=1.5, label="all cells")
    ax.errorbar(x, [pct(s["hazard_misspecified"][v]["anch_full"]["visible"]["acc"][0]) for v in fh], yerr=[pct(s["hazard_misspecified"][v]["anch_full"]["visible"]["acc"][1]) for v in fh], color=C["green"], marker="s", ms=3.5, capsize=1.5, label="sensor-visible cells")
    ax.axvline(0.2, color=C["grey"], lw=0.6, ls=":"); ax.set_xscale("log")
    ax.set_xlabel("hazard assumed by the filter (truth 0.2 per 100 m)"); ax.set_ylabel("accuracy (%)"); ax.legend(fontsize=6.3, frameon=False)
    for a, t in zip(axs.ravel(), "abcdef"):
        panel(a, t)
    fig.tight_layout(h_pad=1.4, w_pad=1.1)
    return save(fig, out, "fig07_stress_tests")


def fig_calibration(R, out):
    cal = R["main"]["calibration"]
    rc = R["main"]["recalibration"]
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.7))
    ax = axs[0]
    ax.plot([0, 1], [0, 1], color=C["grey"], lw=0.8, ls=":")
    for m, col, mk, lb in (("anch_full", C["blue"], "o", "anchored"), ("seg_flat", C["orange"], "s", "per-segment"), ("anch_generic", C["red"], "^", "anchored, generic soil")):
        b = cal[m]["bins"]
        ax.plot(b["mean_p"], b["mean_y"], marker=mk, color=col, ms=3.5, lw=1.0, label="%s (ECE %.3f)" % (lb, cal[m]["ece"][0]))
    ax.set_xlabel("reported probability"); ax.set_ylabel("observed frequency on alignment"); ax.legend(fontsize=6, frameon=False, loc="upper left"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax = axs[1]
    cnt = np.array(cal["anch_full"]["bins"]["count"]); ctr = (np.arange(10) + 0.5) / 10
    ax.bar(ctr, cnt / cnt.sum() * 100, width=0.085, color=C["blue"], alpha=0.85)
    ax.set_xlabel("reported probability"); ax.set_ylabel("share of segments (%)")
    ax = axs[2]
    ax.plot([0, 1], [0, 1], color=C["grey"], lw=0.8, ls=":")
    b = cal["anch_full"]["bins"]
    ax.plot(b["mean_p"], b["mean_y"], marker="o", color=C["blue"], ms=3.5, label="raw (ECE %.3f)" % rc["before"]["ece"][0])
    ax.plot(rc["after"]["bins"]["mean_p"], rc["after"]["bins"]["mean_y"], marker="s", color=C["green"], ms=3.5, label="isotonic, held-out (ECE %.3f)" % rc["after"]["ece"][0])
    ax.set_xlabel("reported probability"); ax.set_ylabel("observed frequency"); ax.legend(fontsize=6, frameon=False, loc="upper left"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    for a, t in zip(axs, "abc"):
        panel(a, t)
    fig.tight_layout(w_pad=1.2)
    return save(fig, out, "fig06_calibration")


def fig_decision(R, out):
    pol = R["decision"]["policies"]
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.1))
    ax = axs[0]
    items = [("EM locator only", C["grey"], "^"), ("GPR dual-band, per segment", C["orange"], "s"), ("fusion, per segment", C["purple"], "D"),
             ("anchored fusion, binary map (absent = clear)", C["red"], "v")]
    for name, col, mk in items:
        p = pol[name]
        ax.errorbar(p["cleared"][0] * 100, p["strikes_per_km"][0], yerr=p["strikes_per_km"][1], xerr=p["cleared"][1] * 100, color=col, marker=mk, ms=5, capsize=2, ls="none", label=name.replace("anchored fusion, binary map (absent = clear)", "anchored fusion, binary"))
    thr = [0.2, 0.1, 0.05, 0.02]
    xs = [pol["anchored fusion, three-state, clear if p<%.2f" % t]["cleared"][0] * 100 for t in thr]
    ys = [pol["anchored fusion, three-state, clear if p<%.2f" % t]["strikes_per_km"][0] for t in thr]
    ax.plot(xs, ys, "o-", color=C["blue"], ms=4.5, label="anchored three-state (clear if p < τ)")
    for t, x, y, off in zip(thr, xs, ys, ((6, 2), None, None, (6, -8))):
        if off:
            ax.annotate("τ=%.2f" % t, (x, y), textcoords="offset points", xytext=off, fontsize=6)
    ax.set_xlabel("corridor released for mechanical excavation (%)"); ax.set_ylabel("utility strikes per km of corridor"); ax.legend(fontsize=6, frameon=False, loc="upper left")
    ax.set_yscale("log")
    ax = axs[1]
    for name, col, mk, lb in (("probability", C["blue"], "o", "rank by residual probability"), ("consequence/cost", C["green"], "s", "rank by probability × consequence / cost"), ("random", C["grey"], "^", "random")):
        pts = R["decision"]["pits"][name]
        ax.errorbar([p["budget_fraction"] * 100 for p in pts], [p["residual_consequence"][0] * 100 for p in pts], yerr=[p["residual_consequence"][1] * 100 for p in pts], color=col, marker=mk, ms=3.8, capsize=1.5, label=lb)
    ax.set_xlabel("trial-pit budget (% of cost of pitting every candidate segment)"); ax.set_ylabel("consequence-weighted missed\nutility remaining (%)"); ax.legend(fontsize=6.2, frameon=False)
    panel(axs[0], "a"); panel(axs[1], "b")
    fig.tight_layout(w_pad=1.3)
    return save(fig, out, "fig08_decision")


def fig_sections(R, out):
    sec = R["sections"]
    cols = ["Concrete sewer, A", "Sewer, B (PE/PVC above)", "Sewer, B (cast iron above)", "PE/PVC water", "Fibre, A", "Fibre, C (PE/PVC above)"]
    M = np.array([[sec["table"][s][c] for c in cols] for s in S.SOILS])
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels([c.replace(", ", "\n").replace(" (", "\n(") for c in cols], fontsize=6.4)
    ax.set_yticks(range(S.NS)); ax.set_yticklabels([SL[s] for s in S.SOILS], fontsize=7)
    for i in range(S.NS):
        for j in range(len(cols)):
            ax.text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=6.6, color="white" if M[i, j] < 0.55 else "black")
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label("fused detection probability", fontsize=7); cb.ax.tick_params(labelsize=6.5)
    return save(fig, out, "fig10_cross_sections")


def fig_position(R, out):
    cfg = R["config"]
    ds = np.linspace(0.25, 7.0, 100)
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.5))
    ax = axs[0]
    for g, col, lb in ((cfg["positioning"]["rtk_m"], C["blue"], "RTK-class GNSS (0.05 m)"), (cfg["positioning"]["standalone_m"], C["red"], "standalone GNSS (3 m)")):
        ph, _ = S.position_probs(cfg, ds, g)
        ax.plot(ds, ph, color=col, label=lb)
    ax.set_xlabel("depth (m)"); ax.set_ylabel("P(horizontal error ≤ 1 m)"); ax.set_ylim(0, 1.02); ax.legend(fontsize=6.5, frameon=False, loc="center right")
    ax = axs[1]
    _, pdp = S.position_probs(cfg, ds, 0.05)
    ax.plot(ds, pdp, color=C["green"])
    ax.set_xlabel("depth (m)"); ax.set_ylabel("P(depth error ≤ 0.5 m)"); ax.set_ylim(0, 1.02)
    panel(axs[0], "a"); panel(axs[1], "b")
    fig.tight_layout(w_pad=1.5)
    return save(fig, out, "fig09_position_depth")


def fig_sensitivity(R, out):
    items = R["sensitivity"]["items"]; base = R["sensitivity"]["base"]
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    y = np.arange(len(items))[::-1]
    for ax, key, ttl, sc in ((axs[0], "acc", "Accuracy, all cells (%)", 100), (axs[1], "miss_visible", "Miss rate, sensor-visible cells (%)", 100)):
        b = base[key] * sc
        for yi, it in zip(y, items):
            lo, hi = it["low"][key] * sc, it["high"][key] * sc
            ax.plot([lo, hi], [yi, yi], color=C["grey"], lw=2.2, solid_capstyle="butt")
            ax.plot(lo, yi, "o", color=C["blue"], ms=3.8); ax.plot(hi, yi, "s", color=C["orange"], ms=3.8)
        ax.axvline(b, color=C["black"], lw=0.7, ls=":")
        ax.set_title(ttl, fontsize=8)
    axs[0].set_yticks(y); axs[0].set_yticklabels([it["name"] for it in items], fontsize=6.6)
    axs[1].plot([], [], "o", color=C["blue"], label="first value"); axs[1].plot([], [], "s", color=C["orange"], label="second value")
    axs[1].legend(fontsize=6.3, frameon=False, loc="lower right")
    panel(axs[0], "a"); panel(axs[1], "b")
    fig.tight_layout(w_pad=0.8)
    return save(fig, out, "fig11_sensitivity")


def fig_rescan_corr(R, out):
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.7))
    ax = axs[0]
    sc = R["rescan"]
    names = list(sc.keys())
    short = ["none", "offline\n25%", "on the spot\n95%", "spot, ρ=0.5", "spot, ρ=0"]
    x = np.arange(len(names))
    ax.errorbar(x - 0.1, [pct(sc[n]["visible"]["miss"][0]) for n in names], yerr=[pct(sc[n]["visible"]["miss"][1]) for n in names], fmt="o", color=C["blue"], capsize=2, ms=4, label="miss rate (visible)")
    ax.errorbar(x + 0.1, [pct(sc[n]["visible"]["fa"][0]) for n in names], yerr=[pct(sc[n]["visible"]["fa"][1]) for n in names], fmt="s", color=C["orange"], capsize=2, ms=4, label="false-alarm rate (visible)")
    ax.set_xticks(x); ax.set_xticklabels(short, fontsize=6.4); ax.set_ylabel("%"); ax.legend(fontsize=6.3, frameon=False)
    ax.set_title("Repeat pass on uncertain segments, four harder soils", fontsize=7.6)
    ax = axs[1]
    cr = R["stress"]["correlation"]; rg = sorted(cr, key=float); x = [float(r) for r in rg]
    for k, col, mk, lb in (("independent", C["blue"], "o", "independent evidence"), ("tempered", C["orange"], "s", "evidence tempered ×0.5"), ("joint_gpr", C["green"], "^", "exact joint GPR bands")):
        ax.plot(x, [cr[r][k]["calibration"]["ece"][0] for r in rg], marker=mk, color=col, ms=3.8, label=lb)
    ax.set_xlabel("correlation between GPR and EM noise"); ax.set_ylabel("expected calibration error"); ax.legend(fontsize=6.3, frameon=False)
    ax.set_title("Correlated evidence", fontsize=7.6)
    panel(axs[0], "a"); panel(axs[1], "b")
    fig.tight_layout(w_pad=1.3)
    return save(fig, out, "fig12_rescan_correlation")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join("out", "results.json"))
    ap.add_argument("--out", default=os.path.join("out", "figures"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    R = json.load(open(a.results, encoding="utf-8"))
    made = [fig_framework(a.out), fig_detectability(R, a.out), fig_heatmaps(R, a.out), fig_ablation(R, a.out), fig_trace(R, a.out),
            fig_stress(R, a.out), fig_calibration(R, a.out), fig_decision(R, a.out), fig_sections(R, a.out), fig_position(R, a.out),
            fig_sensitivity(R, a.out), fig_rescan_corr(R, a.out)]
    for m in made:
        print(m)


if __name__ == "__main__":
    main()
