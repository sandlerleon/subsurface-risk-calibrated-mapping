# -*- coding: utf-8 -*-
"""Figures 31-39 (change-aware reliability analysis) from results_v6.json (written by SubSurface_v6.py --reproduce).

    python figure_generation_v6.py --results results_v6/results_v6.json --out results_v6/figures
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
import SubSurface_v6 as V6

C = dict(blue="#0072B2", orange="#E69F00", green="#009E73", red="#D55E00", purple="#CC79A7", sky="#56B4E9", black="#222222", grey="#8c8c8c", yellow="#F0E442")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.2, "legend.fontsize": 6.8, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.7, "figure.dpi": 150, "savefig.dpi": 300, "lines.linewidth": 1.3})
DL = {"utility": "Underground utilities", "scaffold": "Industrial scaffolding"}
MC = {"S0": C["grey"], "S0d": "#bdbdbd", "S1": C["orange"], "D0": C["sky"], "D1": C["purple"], "D2": C["blue"], "G": C["red"], "ORACLE": C["black"], "ANY": "#7a7a7a", "SSI": "#a05a2c", "SSI_NS": "#d9a066"}
ML = {"S0": "Static twin (surveys only)", "S0d": "Static twin, ad hoc decay", "S1": "Static-state fusion", "D0": "Dynamic, no work records", "D1": "Dynamic, permit suppression",
      "D2": "Dynamic, permit as context", "G": "Reliability-gated", "ORACLE": "Oracle", "ANY": "Point-sensor alarm", "SSI": "Weighted index, permits suppress", "SSI_NS": "Weighted index, no suppression"}
FLOOR = 1e-4


def panel(ax, s, dx=-0.16):
    ax.text(dx, 1.05, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def save(fig, out, name):
    p = os.path.join(out, name + ".png")
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def mv(x):
    return np.nan if x is None or x[0] is None else x[0]


def hv(x):
    return 0.0 if x is None or x[1] is None else x[1]


def curve(rec, key="curve"):
    c = rec[key]
    return V6.CGRID, np.array([np.nan if v[0] is None else v[0] for v in c]), np.array([0.0 if v[1] is None else v[1] for v in c])


# ----------------------------------------------------------------------------------------------------------------
def fig_framework(R, out):
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    ax.set_xlim(0, 100); ax.set_ylim(0, 58); ax.axis("off")

    def box(x, y, w, h, t, fc, fs=6.6, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=C["black"], lw=0.6))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=7, lw=0.8, color=C["black"]))
    box(1, 44, 27, 11, "Continuous observations\nutilities: point monitors\nscaffold: tilt, proximity", "#cfe4f3")
    box(36, 44, 27, 11, "Periodic observations\nutilities: GPR and EM survey\nscaffold: 3D vision sweep", "#d9efe4")
    box(71, 44, 28, 11, "Work records\nutilities: work orders\nscaffold: permits to work", "#fbe9c0")
    box(14, 27, 72, 12, "Dynamic infrastructure-state estimator\nhazard state per element, modification events, sensor health, observation age;\nsensors update only the elements they cover", "#eadbe6", 6.8, True)
    box(2, 12, 44, 11, "Permit and work-event reconciliation\nauthorized / unauthorized / unknown; kept separate\nfrom the probability of a hazardous state", "#f4d6c8", 6.6)
    box(54, 12, 44, 11, "Mismatch-aware reliability gate\nmodel alternatives, survey predictive likelihood,\nsupremum of the retained hazard probabilities", "#f4d6c8", 6.6)
    box(2, 0.5, 30, 8, "Decision supported\n(risk criterion met)", "#c7e9c0", 6.6)
    box(35, 0.5, 30, 8, "Verification needed\n(insufficient evidence)", "#fff2a8", 6.6)
    box(68, 0.5, 30, 8, "Escalate\n(potential hazardous state)", "#f6b5a0", 6.6)
    for x in (14.5, 49.5, 85):
        arrow(x, 44, 50 if x != 49.5 else 50, 39.3)
    arrow(30, 27, 24, 23.3); arrow(70, 27, 76, 23.3)
    arrow(24, 12, 17, 8.7); arrow(76, 12, 83, 8.7); arrow(50, 12, 50, 8.7)
    return save(fig, out, "fig31_framework")


def fig_staleness(R, out):
    fig, axs = plt.subplots(1, 3, figsize=(7.6, 2.9), gridspec_kw=dict(width_ratios=[1, 1, 1.05]))
    for ax, dom, s in zip(axs[:2], ("utility", "scaffold"), "ab"):
        by = R["dynamic_vs_static"][dom]["by_age"]
        ages = np.array(R["dynamic_vs_static"][dom]["ages"])
        for m in ("S0", "S0d", "D0", "D2"):
            y = np.array([mv(v) for v in by[m]["cond_risk"]]); h = np.array([hv(v) for v in by[m]["cond_risk"]])
            cvg = np.array([mv(v) for v in by[m]["coverage"]])
            y = np.where(cvg < 0.01, np.nan, y)
            y = np.maximum(y, FLOOR)
            ax.plot(ages, 100 * y, color=MC[m], marker="o", ms=2.5, label=ML[m])
            ax.fill_between(ages, 100 * np.maximum(y - h, FLOOR), 100 * (y + h), color=MC[m], alpha=0.15, lw=0)
        pr = np.array([mv(v) for v in by["D2"]["predicted"]])
        ax.plot(ages, 100 * np.maximum(pr, FLOOR), color=C["blue"], ls="--", lw=1.0, label="D2: risk predicted by the estimator")
        ax.set_yscale("log"); ax.set_xlabel("epochs since the last survey"); ax.set_title(DL[dom], fontsize=7.6)
        panel(ax, s)
    axs[0].set_ylabel("conditional risk among released (%)")
    ax = axs[2]
    rg = R["regime"]
    rms = sorted({float(k.split("|")[0]) for k in rg}); ivs = sorted({int(k.split("|")[1]) for k in rg})
    Z = np.zeros((len(rms), len(ivs)))
    for i, rm in enumerate(rms):
        for j, iv in enumerate(ivs):
            d = rg["%s|%s" % (rm, iv)]
            Z[i, j] = mv(d["S0"]["unsafe_prob"]) / max(mv(d["D2"]["unsafe_prob"]), 1e-6)
    im = ax.imshow(np.log10(Z), origin="lower", cmap="RdBu_r", vmin=-1.5, vmax=1.5, aspect="auto")
    ax.set_xticks(range(len(ivs))); ax.set_xticklabels(ivs); ax.set_yticks(range(len(rms))); ax.set_yticklabels(["%g" % r for r in rms])
    for i in range(len(rms)):
        for j in range(len(ivs)):
            ax.text(j, i, "%.1f" % Z[i, j], ha="center", va="center", fontsize=6.2, color="white" if abs(np.log10(Z[i, j])) > 0.9 else "black")
    ax.set_xlabel("survey interval (epochs)"); ax.set_ylabel("event-rate multiplier")
    ax.set_title("Utilities: unsafe release, static / dynamic", fontsize=7.4)
    panel(ax, "c", -0.22)
    h, l = axs[0].get_legend_handles_labels()
    fig.tight_layout(w_pad=1.0)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.3, bbox_to_anchor=(0.4, -0.13))
    return save(fig, out, "fig32_staleness")


def fig_permits(R, out):
    fig, axs = plt.subplots(2, 3, figsize=(7.6, 4.6))
    cases = ["no_change_no_permit", "change_valid_permit", "change_no_permit", "change_missing_or_wrong_record"]
    clab = ["no change,\nno permit", "change,\nvalid permit", "change,\nno permit", "change,\nrecord missing\nor wrong"]
    for r, dom in enumerate(("utility", "scaffold")):
        P = R["permits"][dom]["methods"]
        x = np.arange(len(cases)); w = 0.26
        for key, ax, ttl in (("flagged", axs[r, 0], "Flagged (verify or escalate)"), ("hazard_missed", axs[r, 1], "Hazardous and not flagged")):
            for i, m in enumerate(("D0", "D1", "D2")):
                v = np.array([mv(P[m][c][key]) for c in cases]); h = np.array([hv(P[m][c][key]) for c in cases])
                ax.bar(x + (i - 1) * w, 100 * v, w * 0.92, yerr=100 * h, color=MC[m], label=ML[m], error_kw=dict(lw=0.6, capsize=0))
            ax.set_xticks(x); ax.set_xticklabels(clab, fontsize=5.8); ax.set_title("%s: %s (%%)" % (DL[dom].split()[-1].capitalize(), ttl), fontsize=7)
        ax = axs[r, 2]
        for i, m in enumerate(("D0", "D1", "D2")):
            a = P[m]["attribution"]
            ax.bar([i - 0.2], [100 * mv(a["accuracy_when_decided"])], 0.38, color=MC[m], yerr=[100 * hv(a["accuracy_when_decided"])], error_kw=dict(lw=0.6, capsize=0))
            ax.bar([i + 0.2], [100 * mv(a["uncertain"])], 0.38, color=MC[m], alpha=0.35, yerr=[100 * hv(a["uncertain"])], error_kw=dict(lw=0.6, capsize=0))
        ax.set_xticks(range(3)); ax.set_xticklabels(["D0", "D1", "D2"]); ax.set_title("Attribution at reported changes (%)", fontsize=7)
        ax.text(0.02, 0.97, "dark: correct when decided\nlight: left uncertain", transform=ax.transAxes, fontsize=5.8, va="top")
    panel(axs[0, 0], "a"); panel(axs[0, 1], "b"); panel(axs[0, 2], "c"); panel(axs[1, 0], "d"); panel(axs[1, 1], "e"); panel(axs[1, 2], "f")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout(h_pad=0.9, w_pad=0.8)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.05))
    return save(fig, out, "fig33_permits")


def fig_hybrid(R, out):
    fig, axs = plt.subplots(2, 2, figsize=(7.6, 5.0))
    for c, dom in enumerate(("utility", "scaffold")):
        H = R["hybrid"][dom]
        for r, (key, ttl) in enumerate((("share_missed", "Hazard onsets not flagged (%)"), ("cond_risk", "Conditional risk among released (%)"))):
            ax = axs[r, c]
            for name, v in H.items():
                kind = name.split("_")[0]
                col = {"point": C["orange"], "survey": C["green"], "hybrid": C["blue"]}[kind]
                mk = {"point": "s", "survey": "^", "hybrid": "o"}[kind]
                m = v["methods"]["D2"]
                if key == "share_missed":
                    y = mv(m["delay"]["share_missed"]); e = hv(m["delay"]["share_missed"])
                else:
                    src = m["structure"] if (dom == "scaffold" and m.get("structure")) else m["element"]
                    y = mv(src["cond_risk"]); e = hv(src["cond_risk"])
                if not np.isfinite(y):
                    continue
                ax.errorbar([v["cost"]], [100 * y], yerr=[100 * e], color=col, marker=mk, ms=4.5, lw=0, elinewidth=0.6, capsize=0)
                ax.text(v["cost"], 100 * y, " " + name.replace("point_only_", "p").replace("survey_only_", "s").replace("hybrid_", "h").replace("_", "/"), fontsize=5.0, va="bottom")
            ax.set_xlabel("cost (sensor-node equivalents)"); ax.set_title("%s: %s" % (DL[dom].split()[-1].capitalize(), ttl), fontsize=7)
            if key == "cond_risk":
                ax.set_yscale("log")
    panel(axs[0, 0], "a"); panel(axs[0, 1], "b"); panel(axs[1, 0], "c"); panel(axs[1, 1], "d")
    for col, mk, lab in ((C["orange"], "s", "point sensors + baseline survey (pN)"), (C["green"], "^", "periodic survey only (sI, interval I)"), (C["blue"], "o", "hybrid (hN/I: N% sensors, interval I)")):
        axs[0, 0].plot([], [], color=col, marker=mk, lw=0, label=lab)
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout(h_pad=1.0)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.04))
    return save(fig, out, "fig34_hybrid")


def fig_placement(R, out):
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 2.8))
    strat = ["random", "uniform", "uncertainty", "risk_optimised"]
    slab = ["random", "uniform", "uncertainty-based", "risk-optimized"]
    scol = [C["grey"], C["sky"], C["orange"], C["red"]]
    for ax, dom, s in zip(axs, ("utility", "scaffold"), "ab"):
        P = R["placement"][dom]
        fr = sorted(P, key=float)
        x = np.arange(len(fr)); w = 0.2
        for i, (st, col, lab) in enumerate(zip(strat, scol, slab)):
            v = np.array([mv(P[f][st]["element"]["unsafe_prob"]) for f in fr]); h = np.array([hv(P[f][st]["element"]["unsafe_prob"]) for f in fr])
            ax.bar(x + (i - 1.5) * w, 100 * v, w * 0.92, yerr=100 * h, color=col, label=lab, error_kw=dict(lw=0.6, capsize=0))
        ax.set_xticks(x); ax.set_xticklabels(["%d%% of elements" % round(100 * float(f)) for f in fr]); ax.set_title(DL[dom], fontsize=7.6)
        ax.set_ylabel("unsafe-release probability (%)"); panel(ax, s)
    h, l = axs[0].get_legend_handles_labels()
    fig.tight_layout(w_pad=1.0)
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=6.4, bbox_to_anchor=(0.5, -0.1))
    return save(fig, out, "fig35_placement")


def fig_transfer(R, out):
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.2))
    ax = axs[0]
    T = R["transfer"]["utility"]
    for m in ("S0", "S1", "D0", "D2", "G", "ORACLE"):
        g, y, h = curve(T[m])
        ok = np.isfinite(y)
        ax.plot(g[ok], np.maximum(y[ok], FLOOR), color=MC[m], ls="--" if m == "ORACLE" else "-", label=ML[m], lw=1.6 if m == "D2" else 1.2)
        if m in ("S1", "D2"):
            ax.fill_between(g[ok], np.maximum(y[ok] - h[ok], FLOOR), np.maximum(y[ok] + h[ok], FLOOR), color=MC[m], alpha=0.15, lw=0)
    ax.set_yscale("log"); ax.set_ylim(FLOOR, 1.0); ax.set_xlabel("released coverage (element level)"); ax.set_ylabel("conditional risk"); ax.set_title(DL["utility"], fontsize=7.6); panel(ax, "a")
    ax = axs[1]
    T = R["transfer"]["scaffold"]
    for m in ("S0", "S1", "D0", "D2", "G", "ORACLE", "SSI", "SSI_NS"):
        if m not in T or "s_curve" not in T[m]:
            continue
        g, y, h = curve(T[m], "s_curve")
        ok = np.isfinite(y)
        ax.plot(g[ok], np.maximum(y[ok], FLOOR), color=MC[m], ls="--" if m in ("ORACLE", "SSI_NS") else "-", label=ML[m], lw=1.6 if m == "D2" else 1.2)
    a = T["ANY"]["structure"]
    ax.scatter([mv(a["coverage"])], [max(mv(a["cond_risk"]), FLOOR)], marker="x", color=MC["ANY"], s=26, label=ML["ANY"], zorder=5)
    ax.set_yscale("log"); ax.set_ylim(FLOOR, 1.0); ax.set_xlabel("continue-decision coverage (structure level)"); ax.set_title(DL["scaffold"], fontsize=7.6); panel(ax, "b")
    h1, l1 = axs[0].get_legend_handles_labels(); h2, l2 = axs[1].get_legend_handles_labels()
    seen = {}
    for h_, l_ in zip(h1 + h2, l1 + l2):
        seen.setdefault(l_, h_)
    fig.tight_layout(w_pad=1.0)
    fig.legend(list(seen.values()), list(seen.keys()), loc="lower center", ncol=4, frameon=False, fontsize=6.2, bbox_to_anchor=(0.5, -0.16))
    return save(fig, out, "fig36_transfer")


def fig_combined(R, out):
    fig, axs = plt.subplots(2, 2, figsize=(7.6, 5.0), sharex=True)
    scen = list(V6.SCENARIOS)
    methods = ["S1", "D0", "D2", "G", "ORACLE"]
    for c, dom in enumerate(("utility", "scaffold")):
        for r, key in enumerate(("cond_risk", "coverage")):
            ax = axs[r, c]
            x = np.arange(len(scen)); w = 0.16
            for i, m in enumerate(methods):
                v, h = [], []
                for sc in scen:
                    rec = R["combined_failures"][dom][sc][m]
                    src = rec["structure"] if (dom == "scaffold" and rec.get("structure")) else rec["element"]
                    v.append(mv(src[key])); h.append(hv(src[key]))
                v = np.array(v); h = np.array(h)
                val = np.maximum(v, FLOOR) if key == "cond_risk" else v
                ax.bar(x + (i - 2) * w, 100 * val, w * 0.92, yerr=100 * h, color=MC[m], label=ML[m], error_kw=dict(lw=0.5, capsize=0))
            if key == "cond_risk":
                ax.set_yscale("log")
            ax.set_title("%s: %s (%%)" % (DL[dom].split()[-1].capitalize(), "conditional risk" if key == "cond_risk" else "released coverage"), fontsize=7)
    for ax in axs[1]:
        ax.set_xticks(np.arange(len(scen))); ax.set_xticklabels([V6.SCEN_LABEL[s].replace(" (3x)", "").replace(" weaker than assumed", "\nweaker").replace("Unflagged sensor failures", "Unflagged\nsensor failures").replace("3x event rate with bursts", "3x events,\nbursts").replace("Erroneous permits", "Erroneous\npermits") for s in scen], fontsize=5.8)
    panel(axs[0, 0], "a"); panel(axs[0, 1], "b"); panel(axs[1, 0], "c"); panel(axs[1, 1], "d")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout(h_pad=0.8)
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=6.2, bbox_to_anchor=(0.5, -0.04))
    return save(fig, out, "fig37_combined_failures")


def fig_ablation(R, out):
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.3))
    var = ["full", "no_gate_selection", "no_gate", "no_permit_context", "no_dynamics", "no_point_sensors", "no_survey", "no_health_flags"]
    vl = ["full", "no gate\nselection", "no gate", "no permit\ncontext", "no\ndynamics", "no point\nsensors", "no\nsurvey", "no health\nflags"]
    for ax, dom, s in zip(axs, ("utility", "scaffold"), "ab"):
        x = np.arange(len(var)); w = 0.38
        for i, (sc, col) in enumerate((("nominal", C["blue"]), ("combined", C["red"]))):
            v, h, cv = [], [], []
            for vv in var:
                rec = R["ablation"][dom][sc][vv]
                src = rec["structure"] if (dom == "scaffold" and rec.get("structure")) else rec["element"]
                v.append(mv(src["cond_risk"])); h.append(hv(src["cond_risk"])); cv.append(mv(src["coverage"]))
            v = np.maximum(np.array(v), FLOOR)
            ax.bar(x + (i - 0.5) * w, 100 * v, w * 0.92, yerr=100 * np.array(h), color=col, label=V6.SCEN_LABEL[sc], error_kw=dict(lw=0.5, capsize=0))
        ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(vl, fontsize=5.6); ax.set_title(DL[dom], fontsize=7.6); ax.set_ylabel("conditional risk (%)"); panel(ax, s)
    axs[0].legend(frameon=False, fontsize=6.4)
    fig.tight_layout(w_pad=1.0)
    return save(fig, out, "fig38_ablation")


def _risk30(rec, key="s_curve", c=0.3):
    j = int(np.argmin(np.abs(V6.CGRID - c)))
    return mv(rec[key][j])


def fig_structure_defs(R, out):
    """E8: does the scaffold conclusion depend on the definition of an unsafe structure? 4 critical-member shares x 4 bay thresholds"""
    sd = R["structure_definitions"]
    cs_list, k_list = V6.STRUCT_CRIT, V6.STRUCT_K
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.6))

    def grid(scen, fn):
        g = np.full((len(cs_list), len(k_list)), np.nan)
        for i, cs in enumerate(cs_list):
            for j, kb in enumerate(k_list):
                g[i, j] = fn(sd[scen][V6.struct_key(cs, kb)])
        return g

    def draw(ax, g, title, fmt, cmap, vmin=None, vmax=None, label=None):
        im = ax.imshow(g, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax, origin="lower")
        ax.set_xticks(range(len(k_list))); ax.set_xticklabels(k_list)
        ax.set_yticks(range(len(cs_list))); ax.set_yticklabels(["%d%%" % round(100 * c) for c in cs_list])
        ax.set_xlabel("non-critical members of a bay that make it unsafe"); ax.set_ylabel("critical members")
        ax.set_title(title, fontsize=7.2)
        for i in range(g.shape[0]):
            for j in range(g.shape[1]):
                v = g[i, j]
                ax.text(j, i, "n/a" if not np.isfinite(v) else fmt(v), ha="center", va="center", fontsize=6.4, color="white" if (np.isfinite(v) and vmax is not None and v > 0.6 * vmax) else "black")
        ax.axhline(cs_list.index(0.20) - 0.5, color="none")
        bi, bj = cs_list.index(0.20), k_list.index(2)
        ax.add_patch(plt.Rectangle((bj - 0.5, bi - 0.5), 1, 1, fill=False, ec=C["red"], lw=1.6))
        return im

    def ratio(a, b):
        def f(rec):
            ra, rb = _risk30(rec["methods"][a]), _risk30(rec["methods"][b])
            return ra / rb if (np.isfinite(ra) and np.isfinite(rb) and rb > 0) else np.nan
        return f
    draw(axs[0, 0], grid("nominal", ratio("S1", "D2")), "Static-state fusion / dynamic (D2)\nrisk ratio at 30% coverage, nominal", lambda v: "%.1f" % v, "Blues", 1, 8)
    draw(axs[0, 1], grid("combined", ratio("S1", "D2")), "Static-state fusion / dynamic (D2)\nrisk ratio at 30% coverage, combined failures", lambda v: "%.1f" % v, "Blues", 1, 8)
    draw(axs[1, 0], grid("nominal", ratio("SSI", "D2")), "Weighted index / dynamic (D2)\nrisk ratio at 30% coverage, nominal", lambda v: "%.1f" % v, "Oranges", 1, 8)

    def gate_cov(rec):
        st = rec["methods"]["G"]["structure"]["coverage"]
        return mv(st)
    draw(axs[1, 1], grid("combined", gate_cov), "Reliability gate: share of structures\nreleased under combined failures", lambda v: "%.1f%%" % (100 * v), "Greens", 0, 0.3)
    for ax, s_ in zip(axs.ravel(), "abcd"):
        panel(ax, s_, dx=-0.22)
    fig.tight_layout(h_pad=1.2, w_pad=1.0)
    return save(fig, out, "fig39_structure_definitions")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results_v6/results_v6.json")
    ap.add_argument("--out", default="results_v6/figures")
    a = ap.parse_args()
    R = json.load(open(a.results, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    for f in (fig_framework, fig_staleness, fig_permits, fig_hybrid, fig_placement, fig_transfer, fig_combined, fig_ablation, fig_structure_defs):
        print(f(R, a.out))


if __name__ == "__main__":
    main()
