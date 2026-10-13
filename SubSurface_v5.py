# -*- coding: utf-8 -*-
"""
SubSurface_v5.py - reliability analyses for Reliability Engineering & System Safety (extends SubSurface_v4.py and SubSurface_MC.py, which are unchanged).

EVERYTHING HERE IS A SIMULATION UNDER STATED ASSUMPTIONS. No field data are used. The numbers are conditional on the simulated environment.

Reliability definitions (all per 5 m segment, cell-weighted over soil x utility class; denominators are explicit)
  F        safety failure event: the segment is RELEASED (A = 1) and a modelled utility intersects its excavation envelope (U = 1)
  P(F)     = P(A=1, U=1)   unsafe-release probability (joint)          = fn / all segments            (v4: strikes_per_km / 200)
  P(U|A)   conditional false-clearance risk                           = fn / (fn + tn)               (v4: false_clearance)
  P(A)     release coverage                                           = fn + tn                      (v4: released)
  R_dec    = 1 - P(U|A)   conditional decision reliability in the SIMULATED environment (not the probability that an excavation is accident-free)

Adds
  1  six release policies (fixed threshold, sensor-quality-adjusted, expected-loss, robust over a parameter set, robust over parameters and structure,
     robust expected-loss) and baselines (standard fusion, risk-controlled calibrated abstention, health-aware filter, oracle parameters)
  2  fault scenarios with sensor-health combinations and model mismatch (including a common-cause case) and an attribution of unsafe releases to the branches of the failure tree
  3  reliability-coverage curves (conditional risk against released coverage) with intervals over independent simulated networks
  4  aleatory / epistemic decomposition of unsafe-release risk over an explicit parameter envelope and five structural models
  5  ablation at equal released coverage; value-of-information verification prioritisation
  6  global sensitivity analysis (Latin hypercube, surrogate, Sobol indices, bootstrap rank stability)

Usage
  python SubSurface_v5.py --demo
  python SubSurface_v5.py --reproduce --out results_v5 --seed 42 [--quick] [--workers 8]
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse
import copy
import json
import multiprocessing as mp
import sys
import time

import numpy as np
from scipy import stats

import SubSurface_MC as S
import SubSurface_v4 as V

VERSION = "1.3.0"
NU = S.NU
SEG_PER_KM = V.SEG_PER_KM
A4 = V.A4
CGRID = np.round(np.arange(0.01, 0.9001, 0.01), 2)               # released-coverage grid of the reliability-coverage curves
ALPHA_TARGET = 0.02                                               # conditional-risk target of the risk-controlled (calibrated) abstention baseline
TAU_A, TAU_B, TAU_P = 0.10, 0.02, 0.50                            # absent threshold (zone A), marginal-zone absent threshold, present threshold
UNSTABLE = dict(loss_per_seg=0.05, rebirth_per_seg=0.02, shift_per_seg=0.03, drift_per_seg=0.10, rebirth_sigma_steps=4.0)
MEMORYLESS = dict(loss_per_seg=0.5, rebirth_per_seg=0.5, shift_per_seg=0.3, drift_per_seg=0.2, rebirth_sigma_steps=4.0)

# the filter-side uncertainty set U (explicit): parameter variants (theta) and structural alternatives (M); every member is an assumption
THETA = [("nominal", {}), ("atten_x2", dict(att=2.0)), ("sensors_minus3dB", dict(db=-3.0)), ("em_coupling_x0.5", dict(coupling=0.5)), ("atten_x2_and_minus3dB", dict(att=2.0, db=-3.0))]
STRUCT = [("unstable_geometry", dict(params=UNSTABLE)), ("no_anchor", dict(prior="none"))]

POLICIES = ["B1_fusion_fixed", "B2_1d_framework", "P1_fixed", "P2_quality", "P3_exp_loss", "P4_robust_theta", "P5_robust_theta_struct", "P6_robust_exp_loss", "P7_robust_swath", "B5_oracle",
            "RC_fusion", "RC_1d_raw", "RC_1d_blind", "RC_nominal", "RC_quality", "RC_robust"]
POLICY_LABEL = {
    "B1_fusion_fixed": "Standard Bayesian fusion, fixed 0.5 threshold, no abstention", "B2_1d_framework": "Continuity-aware 1D filter with blind-cell rule (v1.0 framework)",
    "P1_fixed": "Health-aware lateral filter, fixed threshold", "P2_quality": "Sensor-quality-adjusted thresholds",
    "P3_exp_loss": "Expected-loss policy (nominal probability)", "P4_robust_theta": "Robust over parameter set",
    "P5_robust_theta_struct": "Robust over parameter set and structural alternatives", "P6_robust_exp_loss": "Robust expected-loss policy",
    "P7_robust_swath": "Robust, with the full-swath alternative (most conservative)",
    "B5_oracle": "Oracle parameters and health (unattainable reference)",
    "RC_fusion": "Calibrated fusion + abstention (risk-controlled)", "RC_1d_raw": "Calibrated 1D filter + abstention (risk-controlled)",
    "RC_1d_blind": "1D filter with blind-cell rule + abstention (risk-controlled)", "RC_nominal": "Health-aware lateral filter + abstention (risk-controlled)",
    "RC_quality": "Quality-adjusted score + abstention (risk-controlled)", "RC_robust": "Robust score + abstention (risk-controlled)"}
FAMILIES = ["fusion", "1d_raw", "1d_blind", "nominal", "quality", "robust"]
FAM2POL = {"fusion": "RC_fusion", "1d_raw": "RC_1d_raw", "1d_blind": "RC_1d_blind", "nominal": "RC_nominal", "quality": "RC_quality", "robust": "RC_robust"}
CURVE_SCORES = ["fusion", "1d_raw", "1d_blind", "nominal", "quality", "robust_theta", "robust", "robust_swath", "oracle"]
ABLATION = ["full", "no_sensor_health", "no_spatial_continuity", "no_structural_uncertainty", "no_parameter_uncertainty", "no_capability_thresholds", "no_robustness"]

# ----------------------------------------------------------------------------------------------------------------
# Scenarios: sensor health x geometry model x parameter mismatch of the TRUE world (the filter always assumes the nominal configuration)
# ----------------------------------------------------------------------------------------------------------------
G = dict(V.MISMATCH)
G_STRAIGHT, G_L3, G_L4 = G["L0 matched: straight"], G["L3 bends + parallel utility"], G["L4 bends + parallel + branch"]
G_SHIFT = dict(A4["geometry"]["shifted_frequent"])
SCEN = [
    ("baseline", dict(geom=G_STRAIGHT, label="Baseline: sensors healthy, geometry as assumed")),
    ("shifted_frequent", dict(geom=G_SHIFT, label="Frequent lateral shifts (1.5 per 100 m)")),
    ("A_gpr_failed_flagged", dict(geom=G_STRAIGHT, gpr_state="failed", flag="all", label="Failure A: GPR failed and flagged; EM healthy")),
    ("B_gpr_failed_unflagged", dict(geom=G_STRAIGHT, gpr_state="failed", flag="none", label="Failure B: GPR failed, not flagged; EM healthy")),
    ("C_em_degraded_wrong_geometry", dict(geom=G_L3, em_state="degraded", label="Failure C: GPR healthy, EM degraded, geometry incorrect (parallel utility)")),
    ("D_common_cause", dict(geom=G_L4, gpr_state="degraded", em_state="degraded", th=dict(att=2.0), label="Common cause: both sensors degraded, soil twice as lossy as assumed, parallel utility and branch")),
    ("G3_parallel", dict(geom=G_L3, label="Geometry incorrect: bends and a parallel utility")),
    ("G4_parallel_branch", dict(geom=G_L4, label="Geometry incorrect: bends, parallel utility and branch")),
    ("B_x_G4", dict(geom=G_L4, gpr_state="failed", flag="none", label="Unflagged GPR failure together with incorrect geometry (bends, parallel, branch)")),
    ("ood_soils_check", dict(geom=G_STRAIGHT, soils=[5, 6], label="Unseen soils, on-site reference check active")),
    ("mixed_health", dict(geom=G_STRAIGHT, gpr_state="mixed", em_state="mixed", label="Mixed sensor health, imperfect diagnostic")),
    ("combined", dict(geom=G_SHIFT, gpr_state="mixed", em_state="mixed", dropout=0.3, label="Shifts, mixed health and 30% dropped observations")),
]
SCEN_D = dict(SCEN)

# ----------------------------------------------------------------------------------------------------------------
# Configurations: variants of the sensor model (filter-side uncertainty set and true-world mismatch)
# ----------------------------------------------------------------------------------------------------------------


def cfg_variant(cfg, att=1.0, db=0.0, coupling=1.0):
    c = copy.deepcopy(cfg)
    c["soil"]["atten_250_db_per_m"] = [x * att for x in cfg["soil"]["atten_250_db_per_m"]]
    c["soil"]["em_atten_db_per_m"] = [x * att for x in cfg["soil"]["em_atten_db_per_m"]]
    c["gpr"]["budget_db"] = {k: v + db for k, v in cfg["gpr"]["budget_db"].items()}
    c["em"]["budget_db"] = cfg["em"]["budget_db"] + db
    c["util"]["em_coupling"] = [None if x is None else min(1.0, x * coupling) for x in cfg["util"]["em_coupling"]]
    c["power_coupling_live"] = min(1.0, cfg["power_coupling_live"] * coupling)
    c["power_coupling_dead"] = min(1.0, cfg["power_coupling_dead"] * coupling)
    return c


_TAB_CACHE = {}


def tables_for(cfg, key, oracle_soil=False):
    k = (key, oracle_soil)
    if k not in _TAB_CACHE:
        if oracle_soil:
            old = dict(V.ASSUME_SOIL)
            V.ASSUME_SOIL.clear()
            try:
                _TAB_CACHE[k] = V.lateral_tables(cfg, V.PASSES_ALL)
            finally:
                V.ASSUME_SOIL.update(old)
        else:
            _TAB_CACHE[k] = V.lateral_tables(cfg, V.PASSES_ALL)
    return _TAB_CACHE[k]


# ----------------------------------------------------------------------------------------------------------------
# Metrics (eight per-corridor columns: tp fn fp tn unverified-on unverified-off cost pits)
# ----------------------------------------------------------------------------------------------------------------
def metrics8(c):
    tp, fn, fp, tn, uo, uf, cost, pit = c
    return dict(P_F=fn, cond_risk=fn / (fn + tn) if fn + tn > 0 else np.nan, coverage=fn + tn, unverified=uo + uf,
                sensitivity=tp / (tp + fn) if tp + fn > 0 else np.nan, false_alarm=fp / (fp + tn) if fp + tn > 0 else np.nan,
                cost_per_km=cost * SEG_PER_KM, pits_per_km=pit * SEG_PER_KM, unsafe_per_km=fn * SEG_PER_KM)


def cell_mean8(X, cell, weights):
    tot = np.zeros(X.shape[1]); ws = 0.0
    for c in np.unique(cell):
        w = weights[c]
        if w <= 0:
            continue
        tot += w * X[cell == c].mean(0); ws += w
    return tot / ws


def boot8(X, cell, weights, B, rng):
    """cluster bootstrap over corridors, stratified by cell. returns {metric: [point, lo, hi]}"""
    cells = [c for c in np.unique(cell) if weights[c] > 0]
    point = metrics8(cell_mean8(X, cell, weights))
    acc = np.zeros((B, X.shape[1])); ws = 0.0
    for c in cells:
        Xc = X[cell == c]
        idx = rng.integers(0, len(Xc), (B, len(Xc)))
        acc += weights[c] * Xc[idx].mean(1); ws += weights[c]
    acc /= ws
    draws = {k: np.empty(B) for k in point}
    for b in range(B):
        m = metrics8(acc[b])
        for k in point:
            draws[k][b] = m[k]
    out = {}
    for k in point:
        v = draws[k][np.isfinite(draws[k])]
        out[k] = [float(point[k]), float(np.percentile(v, 2.5)) if len(v) else None, float(np.percentile(v, 97.5)) if len(v) else None]
    return out


# ----------------------------------------------------------------------------------------------------------------
# Decision rules
# ----------------------------------------------------------------------------------------------------------------
def tri_call(P, zone=None, gflag=None, tau_a=TAU_A, tau_b=TAU_B, tau_p=TAU_P):
    """present (1) if P >= tau_p; absent (0) if P <= tau_a (tau_b in the marginal zone); otherwise unverified (2); zone C and a failed reference check force unverified"""
    ta = tau_a if zone is None else np.where(zone[:, None] == 1, tau_b, tau_a)
    call = np.where(P >= tau_p, 1, np.where(P <= ta, 0, 2)).astype(np.int8)
    if zone is not None:
        call = np.where(((zone == 2) | gflag)[:, None], 2, call).astype(np.int8)
    return call


def quality_score(P, zone, gflag):
    """P divided by the zone-specific absent threshold: release iff score <= 1 reproduces the quality-adjusted rule; sweeping the level traces its reliability-coverage curve"""
    tz = np.where(zone == 1, TAU_B, TAU_A)[:, None]
    return np.where(((zone == 2) | gflag)[:, None], np.inf, P / tz)


def cost_params(cfg):
    c = A4["costs_usd"]
    return c["strike_per_consequence_unit"] * np.array(cfg["util"]["consequence"], float), c["hold_per_segment"], c["pit_base"] + c["pit_per_m"] * S.mid_depth(cfg)


def expected_loss_call(P, util, cp):
    """action minimising expected loss: release p*Cs, verify Cp + p*Ch (a pit finds the utility, then hold), restrict Ch. returns 0 release, 2 verify, 1 restrict"""
    Cs_u, Ch, Cp_u = cp
    Cs, Cp = Cs_u[util][:, None], Cp_u[util][:, None]
    rel, ver, res = P * Cs, Cp + P * Ch, np.full_like(P, Ch)
    return np.where(rel <= np.minimum(ver, res), 0, np.where(ver < res, 2, 1)).astype(np.int8)


def seg_cost(call, truth, util, cp):
    Cs_u, Ch, Cp_u = cp
    Cs, Cp = Cs_u[util][:, None], Cp_u[util][:, None]
    return np.where(call == 0, np.where(truth, Cs, 0.0), np.where(call == 1, Ch, Cp + np.where(truth, Ch, 0.0))).mean(1)


def counts8(call, truth, util, cp):
    cc = V.corridor_counts(call, truth)
    return np.column_stack([cc, seg_cost(call, truth, util, cp), (call == 2).mean(1)])


# ----------------------------------------------------------------------------------------------------------------
# Reliability-coverage curve and risk-controlled threshold
# ----------------------------------------------------------------------------------------------------------------
def rc_curve(score, truth, wseg, grid, rng):
    """release the segments with the lowest score; conditional risk P(U|A) at each released coverage (NaN where the score cannot release that much)"""
    s = score.ravel(); t = truth.ravel().astype(float); w = wseg.ravel()
    jit = rng.random(len(s))
    o = np.lexsort((jit, s))
    fin = np.isfinite(s[o])
    o = o[fin]
    cw = np.cumsum(w[o]) / w.sum()
    cr = np.cumsum(w[o] * t[o]) / np.cumsum(w[o])
    out = np.full(len(grid), np.nan)
    j = np.searchsorted(cw, grid)
    ok = j < len(o)
    out[ok] = cr[j[ok]]
    return out


def level_for_risk(score, truth, wseg, alpha):
    """largest score level whose released set has conditional risk <= alpha (pooled calibration segments)"""
    s = score.ravel(); t = truth.ravel().astype(float); w = wseg.ravel()
    o = np.argsort(s, kind="stable")
    o = o[np.isfinite(s[o])]
    cr = np.cumsum(w[o] * t[o]) / np.cumsum(w[o])
    cw = np.cumsum(w[o])
    ok = np.where((cr <= alpha) & (cw / w.sum() > 0.005))[0]
    if len(ok) == 0:
        return -np.inf
    return float(s[o[ok[-1]]])


def level_for_calibrated(score, truth, wseg, alpha):
    """calibrated abstention: the score is isotonic-calibrated against the outcome on calibration networks (weighted), and a segment is released iff its calibrated
    probability of a utility is at most alpha (a per-segment criterion, not a pooled one); returns the largest score level that satisfies it"""
    from sklearn.isotonic import IsotonicRegression
    s = score.ravel(); t = truth.ravel().astype(float); w = wseg.ravel()
    fin = np.isfinite(s)
    s, t, w = s[fin], t[fin], w[fin]
    iso = IsotonicRegression(increasing=True, out_of_bounds="clip").fit(s, t, sample_weight=w / w.sum())
    grid = np.unique(s)
    f = iso.predict(grid)
    ok = np.where(f <= alpha)[0]
    return float(grid[ok[-1]]) if len(ok) else -np.inf


# ----------------------------------------------------------------------------------------------------------------
# Reference check against the TRUE world (the v4 check compares the assumed soil with the true soil only)
# ----------------------------------------------------------------------------------------------------------------
def reference_check_true(rng, cfg_f, cfg_t, W):
    n, alpha = A4["reference_check"]["n_passes"], A4["reference_check"]["alpha"]
    md = S.mid_depth(cfg_f)
    N = W["N"]
    p_true = np.zeros(N); p_hat = np.zeros(N)
    for s in np.unique(W["soil"]):
        for u in range(NU):
            m = (W["soil"] == s) & (W["util"] == u)
            if not m.any():
                continue
            for cfg_, soil_idx, dest in ((cfg_t, s, "t"), (cfg_f, V.assumed_soil(s), "h")):
                pg = float(S.pd_gpr_any(cfg_, soil_idx, u, md[u])); pe = float(S.pd_em(cfg_, soil_idx, u, md[u]))
                pf = cfg_["soil"]["clutter_pfa"][soil_idx]
                p = 1.0 - (1.0 - pg) * (1.0 - pe)
                p = p + (1 - p) * pf
                if dest == "t":
                    p_true[m] = p
                else:
                    p_hat[m] = p
    k = rng.binomial(n, p_true)
    flag = np.zeros(N, bool); cache = {}
    for i in range(N):
        key = (round(p_hat[i], 6), int(k[i]))
        if key not in cache:
            cache[key] = stats.binomtest(int(k[i]), n, min(max(p_hat[i], 1e-9), 1 - 1e-9)).pvalue < alpha
        flag[i] = cache[key]
    return flag


def draw_health(rng, N, p_failed, p_degraded, diag_failed):
    """health states for one sensor and the (imperfect) flags; diag_failed = probability that a failed sensor is flagged failed"""
    u = rng.random(N)
    h = np.where(u < p_failed, 2, np.where(u < p_failed + p_degraded, 1, 0))
    d = A4["health"]["diag"]
    v = rng.random(N)
    f = np.zeros(N, int)
    f = np.where((h == 2) & (v < diag_failed), 2, f)
    f = np.where((h == 1) & (v < d["degraded_flagged_degraded"]), 1, f)
    f = np.where((h == 1) & (v >= d["degraded_flagged_degraded"]) & (v < d["degraded_flagged_degraded"] + d["degraded_flagged_failed"]), 2, f)
    f = np.where((h == 0) & (v < d["healthy_flagged_failed"]), 2, f)
    f = np.where((h == 0) & (v >= d["healthy_flagged_failed"]) & (v < d["healthy_flagged_failed"] + d["healthy_flagged_degraded"]), 1, f)
    return h, f


# ----------------------------------------------------------------------------------------------------------------
# One simulated network (block): world, observations, filters, every policy and every score
# ----------------------------------------------------------------------------------------------------------------
def _members(cfg_f, W, obs, tabs_cache_key, prior_mode, health_aware=True, params_override=None, P_1d=None):
    """P_on and P_any of every member of the filter-side uncertainty set, run on the same observations. kind 'theta': sensor-parameter variants;
    kind 'struct': structural alternatives (a less stable geometry model, no anchor, the on-alignment 1D model)"""
    out = []
    for name, sp in THETA:
        cfgj = cfg_variant(cfg_f, **sp)
        tabs, pfs = tables_for(cfgj, ("f", name))
        Pon, Pany, _ = V.run_lateral(cfgj, W, obs, V.PASSES_ALL, V.P3, tabs, pfs, prior=prior_mode, prior_rel=1.0, health_aware=health_aware, params=params_override)
        out.append(dict(name=name, kind="theta", Pon=Pon, Pany=Pany))
    tabs, pfs = tables_for(cfg_f, ("f", "nominal"))
    for name, sp in STRUCT:
        prior = sp.get("prior", prior_mode)
        par = sp.get("params", params_override)
        Pon, Pany, _ = V.run_lateral(cfg_f, W, obs, V.PASSES_ALL, V.P3, tabs, pfs, prior=prior, prior_rel=1.0, health_aware=health_aware, params=par)
        out.append(dict(name=name, kind="struct", Pon=Pon, Pany=Pany))
    if P_1d is not None:
        out.append(dict(name="on_alignment_1d", kind="struct", Pon=P_1d, Pany=P_1d))
    return out


def _sup(members, theta=True, struct=True, swath=False):
    """pointwise supremum over the selected members of the probability that a utility lies in the excavation envelope; with swath=True also over the
    probability that a utility lies ANYWHERE in the +-5 m swath (the most conservative structural alternative)"""
    P = None
    for m in members:
        if m["kind"] == "theta" and not theta and m["name"] != "nominal":
            continue
        if m["kind"] == "struct" and not struct:
            continue
        for c in ([m["Pon"], m["Pany"]] if swath else [m["Pon"]]):
            P = c if P is None else np.maximum(P, c)
    return P


def simulate_block(spec):
    """returns small summaries only; spec is a plain dict (picklable)"""
    seed, tag, b = spec["seed"], spec["tag"], spec["block"]
    cfg_f = V.make_cfg4()
    th = spec.get("th") or {}
    cfg_t = cfg_variant(cfg_f, **th) if th else cfg_f
    if "perturb" in spec:
        cfg_t, _ = V.perturbed_cfg(cfg_f, S.rng_for(seed, "v5-perturb", spec["perturb"]))
    soils = spec.get("soils", [0, 1, 2, 3, 4])
    n = spec["n"]
    rng = S.rng_for(seed, tag, b)
    W = V.make_world(rng, cfg_t, soils, n, geom=spec["geom"], map_quality="accurate", gpr_state=spec.get("gpr_state", "healthy"), em_state=spec.get("em_state", "healthy"))
    if "health" in spec:                                       # (p_failed, p_degraded, diag_failed) for the global sensitivity design
        pf_, pd_, dg_ = spec["health"]
        W["health_g"], W["flag_g"] = draw_health(rng, W["N"], pf_, pd_, dg_)
        W["health_e"], W["flag_e"] = draw_health(rng, W["N"], pf_, pd_, dg_)
    V.apply_flag_override(W, spec.get("flag"))
    obs = V.observe_world(rng, cfg_t, W, V.PASSES_ALL, dropout=spec.get("dropout", 0.0))
    N, K = W["N"], W["K"]
    truth = ((np.abs(W["ypos"].astype(int) - V.Y0) <= V.FOOT) & (W["ypos"] != V.GONE)) | W["extra_truth"]
    wts = V.world_weights(cfg_f, soils)
    wc = wts[W["cell"]]; wc = wc / wc.sum()
    wseg = np.repeat(wc / K, K).reshape(N, K)
    cp = cost_params(cfg_f)
    util = W["util"]
    full = spec.get("full", False)
    # filters ---------------------------------------------------------------------------------------------------------------
    base = V.run_models(cfg_f, W, obs, rng, "anchor", 1.0, guard=False, which=("fusion", "continuity_1d"), tabs=tables_for(cfg_f, ("f", "nominal")) [0], pfs=tables_for(cfg_f, ("f", "nominal"))[1])
    P_fus, P_1d, call_1d = base["fusion"]["P"], base["continuity_1d"]["P"], base["continuity_1d"]["call"]
    members = _members(cfg_f, W, obs, None, "anchor", P_1d=P_1d)
    P_nom = members[0]["Pon"]
    P_rth = _sup(members, theta=True, struct=False)
    P_rob = _sup(members, theta=True, struct=True)
    P_rsw = _sup(members, theta=True, struct=True, swath=True)
    pcap = V.capability(cfg_f, W, flags=True, depth_error=True, rng=S.rng_for(seed, tag + "-cap", b))
    zone = V.zone_of(pcap)
    gflag = reference_check_true(S.rng_for(seed, tag + "-ref", b), cfg_f, cfg_t, W) if spec.get("guard", True) else np.zeros(N, bool)
    # oracle: true parameters, true soil and true health states as flags -------------------------------------------------------
    if full or spec.get("oracle", False):
        Wo = dict(W)
        Wo["flag_g"], Wo["flag_e"] = W["health_g"].copy(), W["health_e"].copy()
        key = ("t", json.dumps(th, sort_keys=True), spec.get("perturb", -1), tag if "perturb" in spec else "")
        tabs_o, pfs_o = tables_for(cfg_t, key, oracle_soil=True)
        P_orc = V.run_lateral(cfg_t, Wo, obs, V.PASSES_ALL, V.P3, tabs_o, pfs_o, prior="anchor", prior_rel=1.0, health_aware=True)[0]
    else:
        P_orc = None
    # calls -----------------------------------------------------------------------------------------------------------------
    calls = {}
    calls["B1_fusion_fixed"] = np.where(P_fus > 0.5, 1, 0).astype(np.int8)
    calls["B2_1d_framework"] = call_1d
    calls["P1_fixed"] = tri_call(P_nom)
    calls["P2_quality"] = tri_call(P_nom, zone, gflag)
    calls["P3_exp_loss"] = expected_loss_call(P_nom, util, cp)
    calls["P4_robust_theta"] = tri_call(P_rth, zone, gflag)
    calls["P5_robust_theta_struct"] = tri_call(P_rob, zone, gflag)
    calls["P6_robust_exp_loss"] = expected_loss_call(P_rob, util, cp)
    calls["P7_robust_swath"] = tri_call(P_rsw, zone, gflag)
    if P_orc is not None:
        calls["B5_oracle"] = tri_call(P_orc)
    levels = spec.get("levels")
    fam_score = {"fusion": P_fus, "1d_raw": P_1d, "1d_blind": np.where(call_1d == 2, np.inf, P_1d), "nominal": P_nom,
                 "quality": quality_score(P_nom, zone, gflag), "robust": quality_score(P_rob, zone, gflag)}
    if levels:
        for f in FAMILIES:
            calls[FAM2POL[f]] = np.where(fam_score[f] <= levels[f], 0, 2).astype(np.int8)
    out = {"N": N, "cell": W["cell"].astype(np.int16)}
    out["X"] = {p: counts8(c, truth, util, cp).astype(np.float32) for p, c in calls.items()}
    # per-network cell-weighted vectors (for the variance decomposition) and the decision-level calibration gap -----------------------
    out["blockvec"] = {p: cell_mean8(out["X"][p].astype(float), W["cell"], wts) for p in calls}
    gap = {}
    for p, Pdec in (("P1_fixed", P_nom), ("P2_quality", P_nom), ("P5_robust_theta_struct", P_rob), ("P7_robust_swath", P_rsw)):
        rel = calls[p] == 0
        if rel.any():
            gap[p] = dict(predicted=float((wseg * Pdec * rel).sum() / (wseg * rel).sum()), observed=float((wseg * truth * rel).sum() / (wseg * rel).sum()))
    out["decision_gap"] = gap
    out["zone_share"] = [float((wc * (zone == z)).sum()) for z in range(3)]
    out["guard_flag_share"] = float((wc * gflag).sum())
    out["rob_gap"] = dict(mean_sup_minus_nominal=float((wseg * (P_rob - P_nom)).sum()))
    if spec.get("score_dump"):
        out["score_dump"] = {f: fam_score[f][:, ::4].astype(np.float32) for f in FAMILIES}
        out["score_dump"]["truth"] = truth[:, ::4]
        out["score_dump"]["w"] = wseg[:, ::4].astype(np.float32)
    if full:
        # reliability-coverage curves ------------------------------------------------------------------------------------
        rr = S.rng_for(seed, tag + "-rc", b)
        sc = {"fusion": P_fus, "1d_raw": P_1d, "1d_blind": fam_score["1d_blind"], "nominal": P_nom, "quality": fam_score["quality"],
              "robust_theta": quality_score(P_rth, zone, gflag), "robust": fam_score["robust"], "robust_swath": quality_score(P_rsw, zone, gflag), "oracle": P_orc}
        out["curves"] = {k: rc_curve(v, truth, wseg, CGRID, rr) for k, v in sc.items()}
        # ablation variants, equal released coverage -----------------------------------------------------------------------
        mem_nh = _members(cfg_f, W, obs, None, "anchor", health_aware=False, P_1d=P_1d)
        pcap_nf = V.capability(cfg_f, W, flags=False, depth_error=True, rng=S.rng_for(seed, tag + "-cap", b))
        zone_nf = V.zone_of(pcap_nf)
        mem_nc = _members(cfg_f, W, obs, None, "anchor", params_override=MEMORYLESS, P_1d=P_1d)
        P_noh = _sup(mem_nh, True, True)
        P_noc = _sup(mem_nc, True, True)
        P_nop = _sup([m for m in members if m["name"] == "nominal" or m["kind"] == "struct"], True, True)
        abl = {"full": fam_score["robust"],
               "no_sensor_health": quality_score(P_noh, zone_nf, gflag),
               "no_spatial_continuity": quality_score(P_noc, zone, gflag),
               "no_structural_uncertainty": quality_score(P_rth, zone, gflag),
               "no_parameter_uncertainty": quality_score(P_nop, zone, gflag),
               "no_capability_thresholds": P_rob,
               "no_robustness": fam_score["quality"]}
        out["ablation_curves"] = {k: rc_curve(v, truth, wseg, CGRID, rr) for k, v in abl.items()}
        # value-of-information verification prioritisation (policy 5: unverified segments) ------------------------------------
        out["verification"] = verification_curves(calls["P5_robust_theta_struct"], P_rob, truth, wseg, util, cp, rr)
        # attribution of unsafe releases to the branches of the failure tree ---------------------------------------------------
        out["attribution"] = {p: attribution(calls[p], truth, W, zone, gflag, wseg, pcap) for p in ("P1_fixed", "P2_quality", "P5_robust_theta_struct")}
    return out


def verification_curves(call, P, truth, wseg, util, cp, rng, shares=(0.02, 0.05, 0.10, 0.20, 0.40)):
    """segments left unverified by policy 5 are verified with a trial pit until the budget (share of ALL segments) is spent, in three orders: random,
    most-likely-clear first (lowest probability) and highest value of information; a verified segment is cleared if no utility is found (coverage gained) and held otherwise"""
    Cs_u, Ch, Cp_u = cp
    unv = call == 2
    idx = np.flatnonzero(unv.ravel())
    p = P.ravel()[idx]; t = truth.ravel()[idx]; w = wseg.ravel()[idx]
    Cs = Cs_u[util][:, None] * np.ones_like(P)
    voi = np.minimum(p * Cs.ravel()[idx], Ch) - (p * Ch + Cp_u[util][:, None].repeat(P.shape[1], 1).ravel()[idx])
    orders = {"random": rng.permutation(len(idx)), "lowest_probability": np.argsort(p, kind="stable"), "highest_voi": np.argsort(-voi, kind="stable")}
    out = {}
    cw_total = w.sum()
    for name, o in orders.items():
        cw = np.cumsum(w[o])
        cleared = np.cumsum(w[o] * (~t[o]))
        res = []
        for s in shares:
            j = np.searchsorted(cw, s)
            j = min(j, len(o) - 1)
            res.append(float(cleared[j]) if len(o) else 0.0)
        out[name] = res
    out["shares"] = list(shares)
    out["unverified_share"] = float(cw_total)
    return out


def attribution(call, truth, W, zone, gflag, wseg, pcap):
    """unsafe releases (released AND modelled intersection) assigned to ONE mechanism by a fixed priority order; the categories map to the branches of the failure tree"""
    F = (call == 0) & truth
    if not F.any():
        return {"unsafe_mass": 0.0}
    miss_diag = ((W["health_g"] == 2) & (W["flag_g"] != 2)) | ((W["health_e"] == 2) & (W["flag_e"] != 2)) | ((W["health_g"] == 1) & (W["flag_g"] == 0)) | ((W["health_e"] == 1) & (W["flag_e"] == 0))
    unseen = (W["soil"] >= 5) & ~gflag
    c1 = np.broadcast_to(miss_diag[:, None], F.shape)
    c2 = ~c1 & np.broadcast_to(unseen[:, None], F.shape)
    c3 = ~c1 & ~c2 & W["extra_truth"]
    c4 = ~c1 & ~c2 & ~c3 & np.broadcast_to((pcap < 0.9)[:, None], F.shape)
    c5 = F & ~c1 & ~c2 & ~c3 & ~c4
    tot = (wseg * F).sum()
    cats = {"verification_missed_sensor_diagnostic": c1, "verification_missed_reference_check_unseen_soil": c2, "model_unmodelled_branch": c3,
            "detection_marginal_capability": c4, "detection_miss_in_capable_zone": c5}
    r = {k: float((wseg * (F & m)).sum() / tot) for k, m in cats.items()}
    r["unsafe_mass"] = float(tot)
    return r


# ----------------------------------------------------------------------------------------------------------------
# Pool driver
# ----------------------------------------------------------------------------------------------------------------
def run_jobs(specs, workers, log, label):
    t0 = time.time()
    res = {}
    keyed = [(i, s) for i, s in enumerate(specs)]
    if workers > 1:
        with mp.get_context("spawn").Pool(workers) as pool:
            for k, (i, r) in enumerate(pool.imap_unordered(_job, keyed, chunksize=1)):
                res[i] = r
                if (k + 1) % max(1, len(specs) // 10) == 0:
                    log("   %s %d/%d (%.0f s)" % (label, k + 1, len(specs), time.time() - t0))
    else:
        for i, s in keyed:
            res[i] = simulate_block(s)
    return [res[i] for i in range(len(specs))]


def _job(arg):
    i, s = arg
    return i, simulate_block(s)


def agg_scenario(blocks, soils, cfg_f, boots, rng, policies=None):
    """pool the corridors of all blocks of one scenario: bootstrap metrics per policy"""
    wts = V.world_weights(cfg_f, soils)
    cell = np.concatenate([b["cell"] for b in blocks]).astype(int)
    pol = policies or [p for p in POLICIES if p in blocks[0]["X"]]
    out = {}
    for p in pol:
        if p not in blocks[0]["X"]:
            continue
        X = np.concatenate([b["X"][p] for b in blocks]).astype(float)
        out[p] = boot8(X, cell, wts, boots, rng)
    return out


def curve_stats(blocks, key):
    """mean and 95% t-interval over independent simulated networks"""
    A = np.array([b[key] for b in blocks], float)
    return A


def mean_ci(A):
    n = (~np.isnan(A)).sum(0)
    m = np.nanmean(A, 0)
    sd = np.nanstd(A, 0, ddof=1)
    t = np.array([S.T975.get(int(k), 1.96) if k >= 2 else np.nan for k in n])
    h = t * sd / np.sqrt(np.maximum(n, 1))
    return m, h, n


def dominance(curvesA, curvesB, min_blocks=6):
    """paired differences r_A(c) - r_B(c) over blocks; A better where the 95% interval lies below zero"""
    D = np.array(curvesA, float) - np.array(curvesB, float)
    m, h, n = mean_ci(D)
    ok = n >= min_blocks
    better = ok & (m + h < 0)
    worse = ok & (m - h > 0)
    return dict(grid=CGRID.tolist(), mean_diff=[None if np.isnan(x) else float(x) for x in m], half=[None if np.isnan(x) else float(x) for x in h],
                n_points=int(ok.sum()), share_A_better=float(better.sum() / max(ok.sum(), 1)), share_B_better=float(worse.sum() / max(ok.sum(), 1)),
                share_indistinguishable=float((ok & ~better & ~worse).sum() / max(ok.sum(), 1)), A_dominates_everywhere=bool(ok.any() and not worse.any()),
                coverage_range=[float(CGRID[ok].min()), float(CGRID[ok].max())] if ok.any() else None)


# ----------------------------------------------------------------------------------------------------------------
# Experiments
# ----------------------------------------------------------------------------------------------------------------
def exp_calibration(seed, nblocks, n, workers, log):
    """calibrated-abstention levels: for every score family the largest level whose isotonic-calibrated probability of a utility is <= alpha, fitted on separate calibration networks (baseline conditions)"""
    sp = dict(SCEN_D["baseline"])
    specs = [dict(seed=seed, tag="v5-cal", block=b, n=n, geom=sp["geom"], score_dump=True, full=False) for b in range(nblocks)]
    res = run_jobs(specs, workers, log, "calibration")
    levels = {}
    for f in FAMILIES:
        s = np.concatenate([r["score_dump"][f].ravel() for r in res])
        t = np.concatenate([r["score_dump"]["truth"].ravel() for r in res])
        w = np.concatenate([r["score_dump"]["w"].ravel() for r in res])
        levels[f] = level_for_calibrated(s, t, w, ALPHA_TARGET)
    return levels


ATTR_CATS = ["verification_missed_sensor_diagnostic", "verification_missed_reference_check_unseen_soil", "model_unmodelled_branch", "detection_marginal_capability", "detection_miss_in_capable_zone"]


def ci1(v):
    """mean and 95% t half-width of a vector of per-network values"""
    m, h, _ = mean_ci(np.asarray(v, float)[:, None])
    return [float(m[0]), None if np.isnan(h[0]) else float(h[0])]


def fl(x):
    return [None if np.isnan(v) else float(v) for v in x]


def exp_scenarios(seed, levels, nblocks, n, boots, workers, log):
    cfg_f = V.make_cfg4()
    specs, owner = [], []
    for name, sc in SCEN:
        for b in range(nblocks):
            sp = dict(seed=seed, tag="v5-" + name, block=b, n=n, geom=sc["geom"], soils=sc.get("soils", [0, 1, 2, 3, 4]), gpr_state=sc.get("gpr_state", "healthy"),
                      em_state=sc.get("em_state", "healthy"), flag=sc.get("flag"), dropout=sc.get("dropout", 0.0), th=sc.get("th"), full=True, levels=levels)
            specs.append(sp); owner.append(name)
    res = run_jobs(specs, workers, log, "scenarios")
    byname = {name: [r for r, o in zip(res, owner) if o == name] for name, _ in SCEN}
    out = {"levels": levels, "alpha_target": ALPHA_TARGET, "scenarios": {}, "n_blocks": nblocks, "corridors_per_cell_per_block": n}
    rngb = S.rng_for(seed, "v5-boot", 0)
    for name, sc in SCEN:
        blocks = byname[name]
        soils = sc.get("soils", [0, 1, 2, 3, 4])
        rec = {"label": sc["label"], "policies": agg_scenario(blocks, soils, cfg_f, boots, rngb)}
        curves = {k: np.array([b["curves"][k] for b in blocks]) for k in CURVE_SCORES}
        rec["curves"] = {k: [fl(mean_ci(A)[0]), fl(mean_ci(A)[1])] for k, A in curves.items()}
        rec["curves_raw"] = {k: A.tolist() for k, A in curves.items()}
        rec["ablation"] = {k: np.array([b["ablation_curves"][k] for b in blocks]).tolist() for k in ABLATION}
        vs = {o: np.mean([b["verification"][o] for b in blocks], 0).tolist() for o in ("random", "lowest_probability", "highest_voi")}
        vs["shares"] = blocks[0]["verification"]["shares"]
        vs["unverified_share"] = float(np.mean([b["verification"]["unverified_share"] for b in blocks]))
        rec["verification"] = vs
        att, mass = {}, {}
        for p in blocks[0]["attribution"]:
            ms = np.array([b["attribution"][p].get("unsafe_mass", 0.0) for b in blocks])
            mass[p] = float(ms.mean())
            if ms.sum() > 0:
                att[p] = {k: float(sum(b["attribution"][p].get(k, 0.0) * m for b, m in zip(blocks, ms)) / ms.sum()) for k in ATTR_CATS}
        rec["attribution"], rec["attribution_unsafe_mass"] = att, mass
        rec["decision_gap"] = {p: dict(predicted=float(np.mean([b["decision_gap"][p]["predicted"] for b in blocks if p in b["decision_gap"]])),
                                       observed=float(np.mean([b["decision_gap"][p]["observed"] for b in blocks if p in b["decision_gap"]])))
                               for p in ("P1_fixed", "P2_quality", "P5_robust_theta_struct") if any(p in b["decision_gap"] for b in blocks)}
        rec["zone_share"] = [float(np.mean([b["zone_share"][z] for b in blocks])) for z in range(3)]
        rec["guard_flag_share"] = float(np.mean([b["guard_flag_share"] for b in blocks]))
        rec["robust_minus_nominal_probability"] = float(np.mean([b["rob_gap"]["mean_sup_minus_nominal"] for b in blocks]))
        out["scenarios"][name] = rec
    pairs = [("robust", "quality"), ("quality", "fusion"), ("robust", "fusion"), ("nominal", "fusion"), ("quality", "1d_blind"), ("robust", "1d_blind"), ("robust", "robust_theta"), ("robust_theta", "quality"), ("oracle", "robust")]
    out["dominance"] = {name: {"%s_vs_%s" % pr: dominance([b["curves"][pr[0]] for b in byname[name]], [b["curves"][pr[1]] for b in byname[name]]) for pr in pairs} for name, _ in SCEN}
    abl = {}
    for name, _ in SCEN:
        blocks = byname[name]
        ent = {}
        cov5 = float(np.mean([metrics8(b["blockvec"]["P5_robust_theta_struct"])["coverage"] for b in blocks]))
        jstar = int(np.argmin(np.abs(CGRID - cov5)))
        ent["_operating_point"] = dict(coverage_of_full_policy=cov5, grid_value=float(CGRID[jstar]))
        for k in ABLATION:
            A = np.array([b["ablation_curves"][k] for b in blocks])
            F0 = np.array([b["ablation_curves"]["full"] for b in blocks])
            ent[k] = {}
            for c in (0.10, 0.20, 0.30, 0.40, "op"):
                j = jstar if c == "op" else int(np.argmin(np.abs(CGRID - c)))
                ok = bool(np.isfinite(A[:, j]).all())
                ent[k][str(c)] = dict(reachable=ok, risk=ci1(A[:, j]) if ok else [None, None], diff_vs_full=ci1(A[:, j] - F0[:, j]) if ok and np.isfinite(F0[:, j]).all() else [None, None])
        abl[name] = ent
    out["ablation_equal_coverage"] = abl
    return out


def exp_decomposition(seed, nblocks_r, ndraw, n, workers, log):
    """aleatory and epistemic contributions to unsafe-release risk. Epistemic uncertainty: sensor parameters theta (log-uniform attenuation x0.25-4, thresholds +-3 dB,
    budgets +-3 dB, spreading coefficient 30-50, EM coupling x0.5-1.5) drawn from the v4 envelope, and five structural models M of the geometry (scenarios, NOT weighted).
    Aleatory uncertainty: between-network variation within a (theta, M) cell. Law of total variance within each structural model."""
    cfg_f = V.make_cfg4()
    specs, owner = [], []
    for mname, g in V.MISMATCH:
        for d in range(ndraw):
            for r in range(nblocks_r):
                specs.append(dict(seed=seed, tag="v5-dec-%s-%d" % (mname, d), block=r, n=n, geom=g, perturb=d, full=False))
                owner.append((mname, d, r))
    res = run_jobs(specs, workers, log, "decomposition")
    pols = ["B1_fusion_fixed", "B2_1d_framework", "P1_fixed", "P2_quality", "P3_exp_loss", "P4_robust_theta", "P5_robust_theta_struct", "P6_robust_exp_loss"]
    out = {"n_theta_draws": ndraw, "blocks_per_cell": nblocks_r, "corridors_per_cell_per_block": n,
           "network_size_corridors": int(res[0]["N"]), "structural_models": [m for m, _ in V.MISMATCH], "by_policy": {}}
    for p in pols:
        ent = {}
        for mname, _ in V.MISMATCH:
            Y = np.full((ndraw, nblocks_r), np.nan); C = np.full((ndraw, nblocks_r), np.nan); Cv = np.full((ndraw, nblocks_r), np.nan)
            for (m_, d, r), rr in zip(owner, res):
                if m_ != mname:
                    continue
                v = metrics8(rr["blockvec"][p]); Y[d, r] = v["P_F"]; C[d, r] = v["cond_risk"]; Cv[d, r] = v["coverage"]
            ent[mname] = decompose(Y, C, Cv)
        out["by_policy"][p] = ent
    # scenario envelope across structural models (no weights): max over M of the theta-mean
    return out


def decompose(Y, C, Cv):
    """Y (draws, replicate networks): unsafe-release probability per network. total = aleatory + epistemic (theta) by the law of total variance"""
    D, R = Y.shape
    cellmean = np.nanmean(Y, 1)
    within = np.nanvar(Y, 1, ddof=1)
    alea = float(np.nanmean(within))
    epi_raw = float(np.nanvar(cellmean, ddof=1))
    epi = max(epi_raw - alea / R, 0.0)
    tot = alea + epi
    # bootstrap over theta draws
    rng = np.random.default_rng(7)
    sh = []
    for _ in range(300):
        i = rng.integers(0, D, D)
        a = float(np.nanmean(within[i])); e = max(float(np.nanvar(cellmean[i], ddof=1)) - a / R, 0.0)
        sh.append(e / (a + e) if a + e > 0 else np.nan)
    sh = np.array(sh)
    pc = cellmean
    cr = np.nanmean(C, 1)
    cov = np.nanmean(Cv, 1)
    return dict(mean_P_F=float(np.nanmean(Y)), sd_within_network=float(np.sqrt(alea)), sd_between_theta=float(np.sqrt(epi)), aleatory_variance=alea, epistemic_variance=epi,
                epistemic_share=float(epi / tot) if tot > 0 else None, epistemic_share_ci=[float(np.nanpercentile(sh, 2.5)), float(np.nanpercentile(sh, 97.5))],
                P_F_theta_quantiles=[float(np.nanpercentile(pc, q)) for q in (5, 25, 50, 75, 95)], P_F_theta_max=float(np.nanmax(pc)),
                cond_risk_theta_quantiles=[float(np.nanpercentile(cr, q)) for q in (5, 25, 50, 75, 95)], cond_risk_theta_max=float(np.nanmax(cr)),
                coverage_mean=float(np.nanmean(cov)), theta_cell_P_F=[float(x) for x in pc], theta_cell_cond_risk=[None if np.isnan(x) else float(x) for x in cr])


# ---- global sensitivity -------------------------------------------------------------------------------------------------
GSA_PARAMS = [
    ("soil_attenuation_multiplier", "Soil attenuation multiplier (log-uniform)", 0.25, 4.0, "log"),
    ("sensor_sensitivity_db", "Sensor sensitivity offset (dB)", -4.0, 4.0, "lin"),
    ("diagnostic_sensitivity", "Probability a failed sensor is flagged", 0.0, 1.0, "lin"),
    ("sensor_failure_prevalence", "Sensor failure prevalence", 0.0, 0.30, "lin"),
    ("lateral_shift_per_100m", "Lateral displacements per 100 m", 0.0, 3.0, "lin"),
    ("branch_parallel_share", "Share of corridors with parallel utility and branch", 0.0, 1.0, "lin"),
    ("unseen_soil_share", "Share of corridors in unseen soils", 0.0, 0.5, "lin"),
    ("utility_loss_hazard_per_100m", "Utility leaves alignment per 100 m", 0.05, 1.0, "log"),
]


def lhs_design(npts, seed):
    from scipy.stats import qmc
    u = qmc.LatinHypercube(d=len(GSA_PARAMS), seed=int(seed)).random(npts)
    X = np.empty_like(u)
    for j, (_, _, lo, hi, kind) in enumerate(GSA_PARAMS):
        X[:, j] = np.exp(np.log(lo) + u[:, j] * (np.log(hi) - np.log(lo))) if kind == "log" else lo + u[:, j] * (hi - lo)
    return X


def gsa_specs(seed, X, nblocks_r, n):
    specs, owner = [], []
    for i, x in enumerate(X):
        att, db, diag, pfail, shift, fb, fo, haz = x
        for br in (0, 1):
            for oo in (0, 1):
                w = (fb if br else 1 - fb) * (fo if oo else 1 - fo)
                geom = dict(G_L4) if br else dict(loss=haz, rebirth=0.05, shift=shift, drift_per_seg=0.0)
                if br:
                    geom["loss"] = haz
                for r in range(nblocks_r):
                    specs.append(dict(seed=seed, tag="v5-gsa-%d-%d-%d" % (i, br, oo), block=r, n=n, geom=geom, soils=[5, 6] if oo else [0, 1, 2, 3, 4], th=dict(att=float(att), db=float(db)),
                                      health=(float(pfail), 0.2, float(diag)), full=False))
                    owner.append((i, br, oo, w))
    return specs, owner


def exp_gsa(seed, npts, nblocks_r, n, workers, log, nboot=60):
    cfg_f = V.make_cfg4()
    X = lhs_design(npts, seed)
    specs, owner = gsa_specs(seed, X, nblocks_r, n)
    res = run_jobs(specs, workers, log, "gsa")
    pols = ["P1_fixed", "P2_quality", "P5_robust_theta_struct", "B2_1d_framework"]
    vec = {(p, i): np.zeros(8) for p in pols for i in range(npts)}
    covv = {(p, i): np.zeros(8) for p in pols for i in range(npts)}
    for (i, br, oo, w), rr in zip(owner, res):
        for p in pols:
            vec[(p, i)] += w * rr["blockvec"][p] / nblocks_r
    Y = {}
    for p in pols:
        PF = np.array([metrics8(vec[(p, i)])["P_F"] for i in range(npts)])
        CR = np.array([metrics8(vec[(p, i)])["cond_risk"] for i in range(npts)])
        CV = np.array([metrics8(vec[(p, i)])["coverage"] for i in range(npts)])
        Y[p] = dict(P_F=PF, cond_risk=CR, coverage=CV)
    out = {"n_points": npts, "blocks_per_subworld": nblocks_r, "corridors_per_cell_per_block": n, "parameters": [dict(name=a, label=b, low=c, high=d, scale=k) for a, b, c, d, k in GSA_PARAMS],
           "design": X.tolist(), "responses": {p: {k: v.tolist() for k, v in y.items()} for p, y in Y.items()},
           "note": "each design point mixes four simulated sub-worlds (straight/branch x seen/unseen soils) with weights from the design; health states: degraded 20%, failed = prevalence"}
    out["sobol"] = {}
    for p in pols:
        out["sobol"][p] = {}
        for resp in ("P_F", "cond_risk"):
            out["sobol"][p][resp] = sobol_surrogate(X, Y[p][resp], seed, nboot=nboot)
    return out


def sobol_surrogate(X, y, seed, nboot=60, ns=4096):
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    ok = np.isfinite(y)
    X, y = X[ok], y[ok]
    lo = np.array([g[2] for g in GSA_PARAMS]); hi = np.array([g[3] for g in GSA_PARAMS]); log = np.array([g[4] == "log" for g in GSA_PARAMS])

    def unit(Z):
        out = (Z - lo) / (hi - lo)
        for j in np.flatnonzero(log):
            out[:, j] = (np.log(Z[:, j]) - np.log(lo[j])) / (np.log(hi[j]) - np.log(lo[j]))
        return out

    def fit(Xt, yt, rs):
        return GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.07, subsample=0.8, random_state=rs).fit(Xt, yt)

    def indices(model, rng):
        d = X.shape[1]
        A = rng.random((ns, d)); B = rng.random((ns, d))
        ya, yb = model.predict(A), model.predict(B)
        var = np.var(np.concatenate([ya, yb]))
        S1 = np.empty(d); ST = np.empty(d)
        for j in range(d):
            ABj = A.copy(); ABj[:, j] = B[:, j]
            yab = model.predict(ABj)
            S1[j] = np.mean(yb * (yab - ya)) / var            # Saltelli (2010)
            ST[j] = 0.5 * np.mean((ya - yab) ** 2) / var     # Jansen (1999)
        return S1, ST
    Xu = unit(X)
    Xtr, Xte, ytr, yte = train_test_split(Xu, y, test_size=0.2, random_state=int(seed))
    m0 = fit(Xtr, ytr, int(seed))
    r2 = float(m0.score(Xte, yte))
    model = fit(Xu, y, int(seed))
    rng = np.random.default_rng(int(seed))
    S1, ST = indices(model, rng)
    bs1, bst = [], []
    brng = np.random.default_rng(int(seed) + 1)
    for b in range(nboot):
        i = brng.integers(0, len(y), len(y))
        mb = fit(Xu[i], y[i], b)
        s1, st = indices(mb, np.random.default_rng(b + 100))
        bs1.append(s1); bst.append(st)
    bs1, bst = np.array(bs1), np.array(bst)
    rank_base = np.argsort(-ST)
    first = [float(np.mean(np.argmax(bst, 1) == j)) for j in range(len(ST))]
    from scipy.stats import kendalltau
    taus = [kendalltau(ST, bst[b])[0] for b in range(nboot)]
    # Spearman rank correlation as a model-free check
    from scipy.stats import spearmanr
    sp = [float(spearmanr(X[:, j], y)[0]) for j in range(X.shape[1])]
    return dict(S1=S1.tolist(), ST=ST.tolist(), S1_ci=[np.percentile(bs1, 2.5, 0).tolist(), np.percentile(bs1, 97.5, 0).tolist()],
                ST_ci=[np.percentile(bst, 2.5, 0).tolist(), np.percentile(bst, 97.5, 0).tolist()], r2_holdout=r2, share_ranked_first=first,
                kendall_tau_vs_base=[float(np.nanmean(taus)), float(np.nanpercentile(taus, 5))], spearman=sp, sum_S1=float(np.sum(S1)))


# ----------------------------------------------------------------------------------------------------------------
# Self-tests
# ----------------------------------------------------------------------------------------------------------------
def selftests_v5(seed=42, verbose=True):
    res = []

    def rec(name, ok, detail):
        res.append(dict(name=name, passed=bool(ok), detail=detail))
        if verbose:
            print("  [%s] %s: %s" % ("PASS" if ok else "FAIL", name, detail))
    rng = np.random.default_rng(3)
    # metric identities against the v4 definitions
    c6 = np.array([0.05, 0.02, 0.01, 0.40, 0.03, 0.04]); c6 = c6 / c6.sum()
    m4 = V.metrics_from_counts(c6)
    m8 = metrics8(np.concatenate([c6, [100.0, 0.07]]))
    ok = abs(m8["P_F"] - m4["strikes_per_km"] / SEG_PER_KM) < 1e-12 and abs(m8["cond_risk"] - m4["false_clearance"]) < 1e-12 and abs(m8["coverage"] - m4["released"]) < 1e-12
    rec("P(F), P(U|A), P(A) equal the v4 strikes/200, false_clearance and released", ok, "P_F %.4f, P(U|A) %.4f, P(A) %.4f" % (m8["P_F"], m8["cond_risk"], m8["coverage"]))
    rec("joint probability is the conditional risk times coverage", abs(m8["P_F"] - m8["cond_risk"] * m8["coverage"]) < 1e-12, "identity P(A,U) = P(U|A) P(A)")
    # tri_call reproduces the v4 rule
    P = rng.random((60, 30)) ** 3; zone = rng.integers(0, 3, 60); gf = rng.random(60) < 0.1
    ta = np.where(zone[:, None] == 1, V.ZONE_B_TAU_ABSENT, V.A4["tau_absent"])
    c4 = np.where(P >= V.A4["tau_present"], 1, np.where(P <= ta, 0, 2)).astype(np.int8)
    c4 = np.where(((zone == 2) | gf)[:, None], 2, c4).astype(np.int8)
    rec("quality-adjusted rule equals the v4 proposed rule on the same inputs", bool(np.array_equal(tri_call(P, zone, gf), c4)), "%d decisions" % P.size)
    sc = quality_score(P, zone, gf)
    rel = np.isfinite(sc) & (sc <= 1.0) & (P < TAU_P)
    rec("score <= 1 releases exactly the segments the rule releases", bool(np.array_equal(rel, tri_call(P, zone, gf) == 0)), "release share %.3f" % rel.mean())
    # expected-loss thresholds
    cfg = V.make_cfg4(); cp = cost_params(cfg)
    pw = S.UTILS.index("power")
    pp = np.array([[0.005, 0.01, 0.015, 0.05, 0.3, 0.9]])
    call = expected_loss_call(pp, np.array([pw]), cp)[0]
    rec("expected-loss action moves from release to verify to restrict as the probability rises", call.tolist() == [0, 0, 2, 2, 2, 1], "actions %s" % call.tolist())
    tcrit = cp[2][pw] / (cp[0][pw] - cp[1])
    pr = expected_loss_call(np.array([[0.99 * tcrit, 1.01 * tcrit]]), np.array([pw]), cp)[0]
    rec("power-duct release threshold equals pit cost over (strike cost - hold cost)", pr.tolist() == [0, 2], "threshold %.4f, actions %s" % (tcrit, pr.tolist()))
    # reliability-coverage curve
    s = rng.random((40, 50)); t = rng.random((40, 50)) < 0.3; w = np.full((40, 50), 1.0 / 2000)
    cur = rc_curve(s, t, w, CGRID, rng)
    rec("a random score gives a flat curve at the prevalence", abs(np.nanmean(cur) - t.mean()) < 0.03, "mean %.3f, prevalence %.3f" % (np.nanmean(cur), t.mean()))
    perfect = rc_curve(t.astype(float), t, w, CGRID, rng)
    rec("a perfect score gives zero risk until the clean segments run out", bool(np.nanmax(perfect[CGRID < 0.6]) < 1e-9), "max %.2e" % np.nanmax(perfect[CGRID < 0.6]))
    sc2 = t.astype(float) + 0.01 * s
    lev = level_for_risk(sc2, t, w, 0.02)
    relset = sc2 <= lev
    rec("risk-controlled level releases a set with conditional risk at or below the target", bool(t[relset].mean() <= 0.02 + 1e-9 and relset.mean() > 0.6), "released %.3f, risk %.4f" % (relset.mean(), t[relset].mean()))
    sc3 = np.where(t, 0.5, 0.0) + 0.4 * s
    lev3 = level_for_calibrated(sc3, t, w, 0.02)
    rel3 = sc3 <= lev3
    rec("calibrated abstention releases only scores whose calibrated risk is at most alpha", bool(t[rel3].mean() <= 0.02 + 1e-9 and rel3.mean() > 0.5), "released %.3f, risk %.4f" % (rel3.mean(), t[rel3].mean()))
    # variance decomposition on a nested design with known components
    D, R = 400, 5
    Ytest = 0.05 + 0.02 * rng.standard_normal((D, 1)) + 0.01 * rng.standard_normal((D, R))
    d = decompose(Ytest, Ytest, Ytest)
    rec("variance decomposition recovers the known components (aleatory 1e-4, epistemic 4e-4)", abs(d["aleatory_variance"] - 1e-4) < 2.5e-5 and abs(d["epistemic_variance"] - 4e-4) < 8e-5, "aleatory %.2e, epistemic %.2e" % (d["aleatory_variance"], d["epistemic_variance"]))
    # Latin hypercube stratification
    Xd = lhs_design(64, 1)
    strat = all(len(np.unique(np.floor(((np.log(Xd[:, j]) - np.log(g[2])) / (np.log(g[3]) - np.log(g[2])) if g[4] == "log" else (Xd[:, j] - g[2]) / (g[3] - g[2])) * 64).astype(int).clip(0, 63))) == 64 for j, g in enumerate(GSA_PARAMS))
    rec("Latin hypercube design has one point in every stratum of every parameter", bool(strat), "64 points, %d parameters" % len(GSA_PARAMS))
    # Sobol on the Ishigami function (analytic S1 = 0.314, 0.442, 0; ST = 0.558, 0.442, 0.244)
    xi = rng.random((1500, 3)); z = -np.pi + 2 * np.pi * xi
    yi = np.sin(z[:, 0]) + 7 * np.sin(z[:, 1]) ** 2 + 0.1 * z[:, 2] ** 4 * np.sin(z[:, 0])
    from sklearn.ensemble import GradientBoostingRegressor
    mdl = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, random_state=1).fit(xi, yi)
    A = rng.random((8192, 3)); B = rng.random((8192, 3)); ya, yb = mdl.predict(A), mdl.predict(B); var = np.var(np.concatenate([ya, yb]))
    S1 = []
    for j in range(3):
        ABj = A.copy(); ABj[:, j] = B[:, j]
        S1.append(np.mean(yb * (mdl.predict(ABj) - ya)) / var)
    rec("surrogate Sobol estimator recovers the Ishigami first-order indices (0.314, 0.442, 0)", abs(S1[0] - 0.314) < 0.07 and abs(S1[1] - 0.442) < 0.07 and abs(S1[2]) < 0.07, "estimated %s" % np.round(S1, 3).tolist())
    # block determinism and robust >= nominal
    spec = dict(seed=seed, tag="v5-selftest", block=0, n=6, geom=G_STRAIGHT, soils=[0, 3], full=False)
    a = simulate_block(spec); b = simulate_block(spec)
    rec("a simulated network is reproducible from its seed", bool(all(np.array_equal(a["X"][p], b["X"][p]) for p in a["X"])), "%d policies compared" % len(a["X"]))
    cfg_f = V.make_cfg4()
    rg = np.random.default_rng(1)
    Wt = V.make_world(rg, cfg_f, [0, 3], 6, geom=G_L3)
    ob = V.observe_world(rg, cfg_f, Wt, V.PASSES_ALL)
    mem = _members(cfg_f, Wt, ob, None, "anchor")
    Pn, Pr = mem[0]["Pon"], _sup(mem, True, True)
    rec("the supremum over the uncertainty set is never below the nominal probability", bool((Pr >= Pn - 1e-12).all()), "mean gap %.4f" % float((Pr - Pn).mean()))
    # reference check against the true world: few false alarms when the world equals the filter's model
    Wc = V.make_world(S.rng_for(seed, "v5-st", 1), cfg_f, [0, 1, 2, 3, 4], 30)
    fl = reference_check_true(S.rng_for(seed, "v5-st", 2), cfg_f, cfg_f, Wc)
    rec("reference check flags few corridors when the true parameters equal the assumed ones", float(fl.mean()) < 0.06, "flag share %.3f" % fl.mean())
    fl2 = reference_check_true(S.rng_for(seed, "v5-st", 2), cfg_f, cfg_variant(cfg_f, att=3.0), Wc)
    rec("reference check flags more corridors when the true soil is three times as lossy", float(fl2.mean()) > float(fl.mean()) + 0.05, "flag share %.3f" % fl2.mean())
    return res


# ----------------------------------------------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------------------------------------------
def reproduce(args):
    t0 = time.time()
    os.makedirs(args.out, exist_ok=True)

    def log(s):
        print(s, flush=True)
    seed = args.seed
    q = args.quick
    workers = args.workers
    R = {"meta": dict(software="SubSurface_v5.py", version=VERSION, command=" ".join(["python"] + sys.argv), seed=seed, python=sys.version.split()[0], numpy=np.__version__,
                      depends_on="SubSurface_MC.py v1.0.0 and SubSurface_v4.py (unchanged)", quick=bool(q), workers=workers),
         "definitions": dict(F="released (A=1) and a modelled utility intersects the excavation envelope (U=1)", P_F="P(A=1,U=1) = fn / all segments", cond_risk="P(U=1|A=1) = fn / (fn + tn)",
                             coverage="P(A=1) = fn + tn", R_decision="1 - P(U|A): conditional decision reliability in the simulated environment"),
         "uncertainty_set": dict(theta=[[n, s] for n, s in THETA], structure=[[n, {k: v for k, v in s.items()}] for n, s in STRUCT] + [["on_alignment_1d", {}]],
                                 note="filter-side set used by the robust policies P4-P6; P7 adds the swath alternative: the probability that a utility lies anywhere in the +-5 m swath"),
         "costs_usd": A4["costs_usd"], "thresholds": dict(tau_absent=TAU_A, tau_marginal=TAU_B, tau_present=TAU_P, alpha_target=ALPHA_TARGET), "policy_label": POLICY_LABEL}
    log("1/5 self-tests")
    R["selftests"] = selftests_v5(seed)
    nb, n, boots = (4, 12, 60) if q else (10, 40, 300)
    parts = set(args.parts.split(","))
    if "scenarios" in parts:
        log("2/5 calibration networks (calibrated-abstention levels)")
        levels = exp_calibration(seed, 3 if q else 8, 12 if q else 40, workers, log)
        log("3/5 scenarios, policies, curves, ablation, verification, attribution")
        R["scenario_study"] = exp_scenarios(seed, levels, nb, n, boots, workers, log)
    if "decomposition" in parts:
        log("4/5 aleatory / epistemic decomposition")
        R["decomposition"] = exp_decomposition(seed, 2 if q else 3, 8 if q else 40, 10 if q else 14, workers, log)
    if "gsa" in parts:
        log("5/5 global sensitivity analysis")
        R["gsa"] = exp_gsa(seed, 48 if q else 320, 1 if q else 2, 6 if q else 10, workers, log, nboot=8 if q else 60)
    R["meta"]["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(args.out, "results_v5.json"), "w", encoding="utf-8") as fh:
        json.dump(S.jsonable(R), fh, indent=1)
    log("results_v5.json written (%.1f s)" % (time.time() - t0))
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--reproduce", action="store_true")
    ap.add_argument("--out", default="results_v5")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--parts", default="scenarios,decomposition,gsa")
    ap.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 0)))
    a = ap.parse_args()
    if a.demo:
        r = selftests_v5(a.seed)
        print("%d of %d self-tests passed" % (sum(x["passed"] for x in r), len(r)))
        sys.exit(0 if all(x["passed"] for x in r) else 1)
    if a.reproduce:
        reproduce(a)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
