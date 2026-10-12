# -*- coding: utf-8 -*-
"""
SubSurface_v4.py - extensions of SubSurface_MC.py (v1.0.0 results are unchanged and remain reproducible with that file).

EVERYTHING HERE IS A SIMULATION UNDER STATED ASSUMPTIONS. No field data are used.

Adds (each addresses a limitation named in the v1.0.0 manuscript):
  1  two-dimensional lateral tracking: a filter over a lateral grid (-5 m to +5 m, 0.5 m) with a survey-geometry observation model
  2  sensor-health-aware fusion with an imperfect health diagnostic, scenarios A-D, fail-safe three-state rule
  3  depth-resolved capability zones (A detectable, B marginal, C not established) and escalation
  4  out-of-distribution soils with an on-site reference-target check; cluster-bootstrap intervals; a five-model comparison over a scenario matrix
  5  excavation-clearance comparison at EQUAL released coverage and at equal risk, with an explicit cost model
  6  value-of-information allocation of trial pits against random and probability-ranked allocation
  7  five-year total cost of ownership with scenario and sensitivity analysis; pilot sample sizes (exact binomial)

Usage
  python SubSurface_v4.py --demo                      self-tests of the new code
  python SubSurface_v4.py --reproduce --out results_v4 --seed 42
  python SubSurface_v4.py --reproduce --quick
"""
import argparse
import copy
import json
import os
import sys
import time
import zlib

import numpy as np
from scipy import stats

import SubSurface_MC as S

VERSION = "1.1.0"
NU = S.NU
SOILS4 = S.SOILS + ["wet_clay", "saline_fill"]          # the last two are out-of-distribution soils
NS4 = len(SOILS4)
ASSUME_SOIL = {5: 3, 6: 4}                                # the filter uses the nearest in-distribution soil for an unseen soil
NY = 21                                                   # lateral grid: -5 m to +5 m in 0.5 m steps
Y0 = 10
YM = (np.arange(NY) - Y0) * 0.5
GONE = -1
FOOT = 2                                                  # footprint half-width in grid steps (1 m)

# ----------------------------------------------------------------------------------------------------------------
# Assumptions of the v4 experiments (added to the register of v1.0.0; every value is an assumption)
# ----------------------------------------------------------------------------------------------------------------
A4 = {
    "ood_soils": {"names": ["wet_clay", "saline_fill"], "atten_250_db_per_m": [30.0, 12.0], "sigma_seg_db": [7.0, 8.0],
                  "clutter_pfa": [0.05, 0.08], "em_atten_db_per_m": [5.0, 3.0]},
    "lateral_response": {"gpr_width_m": [0.6, 0.35], "em_width_m": [1.0, 0.5], "penalty_db_at_width": 10.0, "cap_db": 60.0},
    "geometry": {                                         # per 100 m unless stated
        "straight": {"loss": 0.2, "rebirth": 0.05, "shift": 0.0, "drift_per_seg": 0.0},
        "curved": {"loss": 0.2, "rebirth": 0.05, "shift": 0.0, "drift_per_seg": 0.10},
        "shifted": {"loss": 0.2, "rebirth": 0.05, "shift": 0.5, "drift_per_seg": 0.0},
        "shifted_frequent": {"loss": 0.2, "rebirth": 0.05, "shift": 1.5, "drift_per_seg": 0.0},
        "interrupted": {"loss": 0.6, "rebirth": 0.30, "shift": 0.0, "drift_per_seg": 0.0},
    },
    "shift_magnitude_steps": [2, 8],                      # 1 m to 4 m
    "filter_2d": {"loss_per_seg": 0.01, "rebirth_per_seg": 0.0025, "shift_per_seg": 0.005, "drift_per_seg": 0.02, "rebirth_sigma_steps": 4.0},
    "health": {"degraded_loss_db": 6.0,
               "diag": {"failed_flagged_failed": 0.90, "degraded_flagged_degraded": 0.50, "degraded_flagged_failed": 0.05,
                        "healthy_flagged_failed": 0.02, "healthy_flagged_degraded": 0.03}},
    "map": {"offset_steps": [3, 6], "misleading_anchor_true_reliability": 0.5},
    "zones": {"A": 0.9, "C": 0.3, "depth_rel_error": 0.10},
    "tau_absent": 0.1, "tau_present": 0.5,
    "reference_check": {"n_passes": 20, "alpha": 0.01},
    "costs_usd": {"strike_per_consequence_unit": 5000.0, "hold_per_segment": 1000.0, "pit_base": 400.0, "pit_per_m": 200.0,
                  "survey_per_km_low": 200.0, "survey_per_km_base": 500.0, "survey_per_km_high": 800.0},
    "tco": {"capital_low": 36800.0, "capital_base": 66900.0, "capital_high": 97000.0, "years": 5,
            "maintenance_frac_per_year": {"low": 0.05, "base": 0.08, "high": 0.12}, "gnss_subscription_per_year": {"low": 300.0, "base": 500.0, "high": 900.0},
            "data_consumables_per_year": {"low": 500.0, "base": 1000.0, "high": 2000.0}, "training_refresher_per_year": {"low": 250.0, "base": 250.0, "high": 500.0},
            "crew_per_field_day": {"low": 100.0, "base": 150.0, "high": 250.0}, "field_days_per_year": {"low": 40, "base": 60, "high": 100},
            "km_per_day": {"low": 1.0, "base": 2.4, "high": 3.0}, "downtime_frac": {"low": 0.05, "base": 0.10, "high": 0.20}},
}


def make_cfg4():
    c = copy.deepcopy(S.CFG)
    o = A4["ood_soils"]
    c["soil"]["atten_250_db_per_m"] += o["atten_250_db_per_m"]
    c["soil"]["sigma_seg_db"] += o["sigma_seg_db"]
    c["soil"]["clutter_pfa"] += o["clutter_pfa"]
    c["soil"]["em_atten_db_per_m"] += o["em_atten_db_per_m"]
    return c


def attenuation_from_conductivity(sigma_s_per_m, eps_r):
    """one-way low-loss attenuation (dB/m) of an electromagnetic wave: 1636 sigma / sqrt(eps_r) (standard low-loss approximation)"""
    return 1636.0 * np.asarray(sigma_s_per_m, float) / np.sqrt(np.asarray(eps_r, float))


# ----------------------------------------------------------------------------------------------------------------
# Lateral response of the instruments
# ----------------------------------------------------------------------------------------------------------------
def pen_db(delta_m, depth, kind):
    lr = A4["lateral_response"]
    a, b = lr["gpr_width_m"] if kind == "gpr" else lr["em_width_m"]
    w = a + b * np.asarray(depth, float)
    return np.minimum(lr["penalty_db_at_width"] * (np.asarray(delta_m, float) / w) ** 2, lr["cap_db"])


# ----------------------------------------------------------------------------------------------------------------
# World: corridors with a lateral position, sensor health and map quality
# ----------------------------------------------------------------------------------------------------------------
def make_world(rng, cfg, soils, n_per_cell, geom="straight", map_quality="accurate", gpr_state="healthy", em_state="healthy", K=100):
    cells = [(s, u) for s in soils for u in range(NU)]
    ncell_all = NS4 * NU
    N = len(cells) * n_per_cell
    soil = np.repeat([c[0] for c in cells], n_per_cell)
    util = np.repeat([c[1] for c in cells], n_per_cell)
    cell = soil * NU + util
    dr = np.array(cfg["util"]["depth_m"], float)
    depth = dr[util, 0] + (dr[util, 1] - dr[util, 0]) * rng.random(N)
    g = A4["geometry"][geom] if isinstance(geom, str) else geom
    seg = cfg["truth"]["segment_m"] / 100.0
    hg, rb, hs, pdr = g["loss"] * seg, g["rebirth"] * seg, g["shift"] * seg, g["drift_per_seg"]
    y = np.full(N, Y0)
    gone = np.zeros(N, bool)
    if map_quality == "offset":
        lo, hi = A4["map"]["offset_steps"]
        y = Y0 + rng.integers(lo, hi + 1, N) * rng.choice([-1, 1], N)
    elif map_quality == "misleading":
        gone = rng.random(N) < (1.0 - A4["map"]["misleading_anchor_true_reliability"])
    ypos = np.empty((N, K), np.int16)
    ypos[:, 0] = np.where(gone, GONE, y)
    goneh = np.zeros((N, K), bool)
    goneh[:, 0] = gone
    y_init = y.copy()
    mlo, mhi = g.get("mag", A4["shift_magnitude_steps"])
    for k in range(1, K):
        u = rng.random(N); v = rng.random(N); w = rng.random(N)
        on = ~gone
        leave = on & (u < hg)
        come = gone & (u < rb)
        shift = on & ~leave & (v < hs)
        drift = on & ~leave & ~shift & (w < pdr)
        mag = rng.integers(mlo, mhi + 1, N) * rng.choice([-1, 1], N)
        y = np.where(shift, np.clip(y + mag, 0, NY - 1), y)
        y = np.where(drift, np.clip(y + rng.choice([-1, 1], N), 0, NY - 1), y)
        gone = np.where(leave, True, np.where(come, False, gone))
        ypos[:, k] = np.where(gone, GONE, y)
        goneh[:, k] = gone
    extra = []
    extra_truth = np.zeros((N, K), bool)
    sp = g.get("spline")
    if sp:
        # structurally different truth: piecewise-linear paths with abrupt bends (not a Markov chain on the grid), optional parallel utility and branch
        def spline_path(y_start):
            yy = np.asarray(y_start, float).copy()
            path = np.empty((N, K))
            path[:, 0] = yy
            slope = rng.uniform(-sp["max_slope"], sp["max_slope"], N)
            cnt = rng.integers(sp["leg"][0], sp["leg"][1] + 1, N)
            for k in range(1, K):
                new = cnt <= 0
                slope = np.where(new, rng.uniform(-sp["max_slope"], sp["max_slope"], N), slope)
                cnt = np.where(new, rng.integers(sp["leg"][0], sp["leg"][1] + 1, N), cnt)
                yy = np.clip(yy + slope, 0, NY - 1)
                path[:, k] = yy
                cnt = cnt - 1
            return path
        base = spline_path(y_init)
        ypos = np.where(goneh, GONE, np.rint(base)).astype(np.int16)
        if sp.get("parallel"):
            ystart_d = np.clip(Y0 + rng.choice([-1, 1], N) * rng.integers(4, 11, N), 0, NY - 1)
            extra.append((np.rint(spline_path(ystart_d)).astype(np.int16), np.ones((N, K), bool)))
        if sp.get("branch"):
            kb = rng.integers(20, 61, N)
            sb = rng.choice([-1, 1], N) * rng.uniform(0.4, 0.9, N)
            kk = np.arange(K)[None, :]
            ystart_b = base[np.arange(N), kb]
            bpath = np.clip(ystart_b[:, None] + sb[:, None] * (kk - kb[:, None]), 0, NY - 1)
            present = kk >= kb[:, None]
            bi = np.rint(bpath).astype(np.int16)
            extra.append((bi, present))
            extra_truth = present & (np.abs(bi.astype(int) - Y0) <= FOOT)
    coupled = rng.random(N) < S.em_coupling_eff(cfg)[util]

    def health(state):
        if state == "mixed":
            return rng.choice([0, 1, 2], N, p=[0.7, 0.2, 0.1])
        return np.full(N, {"healthy": 0, "degraded": 1, "failed": 2}[state])
    hg_, he_ = health(gpr_state), health(em_state)
    d = A4["health"]["diag"]

    def flag(h):
        u = rng.random(N)
        f = np.zeros(N, int)
        f = np.where((h == 2) & (u < d["failed_flagged_failed"]), 2, f)
        f = np.where((h == 1) & (u < d["degraded_flagged_degraded"]), 1, f)
        f = np.where((h == 1) & (u >= d["degraded_flagged_degraded"]) & (u < d["degraded_flagged_degraded"] + d["degraded_flagged_failed"]), 2, f)
        f = np.where((h == 0) & (u < d["healthy_flagged_failed"]), 2, f)
        f = np.where((h == 0) & (u >= d["healthy_flagged_failed"]) & (u < d["healthy_flagged_failed"] + d["healthy_flagged_degraded"]), 1, f)
        return f
    return dict(N=N, K=K, n=n_per_cell, cell=cell, soil=soil, util=util, depth=depth, ypos=ypos, coupled=coupled,
                health_g=hg_, health_e=he_, flag_g=flag(hg_), flag_e=flag(he_), map_quality=map_quality, soils=list(soils), ncell_all=ncell_all,
                shadow=np.zeros(N), state=(ypos != GONE).astype(np.uint8), extra=extra, extra_truth=extra_truth)


def observe_world(rng, cfg, W, passes_m, dropout=0.0):
    """detections per pass: dict pass -> {'d250','d600','dem'} of (N,K) booleans; a dropped observation is recorded as a non-detection and masked.
    Extra sources (a parallel utility, a branch) produce signals in the same way and are OR-ed into the detections."""
    N, K = W["N"], W["K"]
    g, e = cfg["gpr"], cfg["em"]
    rho = g["band_correlation"]
    soil, util, depth = W["soil"], W["util"], W["depth"]
    sseg = np.asarray(cfg["soil"]["sigma_seg_db"])[soil][:, None]
    pfa = np.asarray(cfg["soil"]["clutter_pfa"])[soil][:, None]
    deg = A4["health"]["degraded_loss_db"]
    m250 = (S.gpr_margin(cfg, soil, util, depth, "250") + g["threshold_db"])[:, None]
    m600 = (S.gpr_margin(cfg, soil, util, depth, "600") + g["threshold_db"])[:, None]
    em_mean = (e["budget_db"] - e["spreading_coef"] * np.log10(1.0 + depth) - np.asarray(cfg["soil"]["em_atten_db_per_m"])[soil] * depth)[:, None]
    sources = [(W["ypos"], W["ypos"] == GONE)] + [(yp, ~pr) for yp, pr in W.get("extra", [])]
    out = {}
    for pi, p in enumerate(passes_m):
        zr1 = rng.standard_normal(N)[:, None]
        zr2 = rho * zr1 + np.sqrt(1 - rho ** 2) * rng.standard_normal(N)[:, None]
        s250 = np.zeros((N, K), bool); s600 = np.zeros((N, K), bool); sem = np.zeros((N, K), bool)
        for ypath, absent in sources:
            dl = np.abs((ypath.astype(float) - Y0) * 0.5 - p)
            penG = pen_db(dl, depth[:, None], "gpr") + deg * (W["health_g"][:, None] == 1)
            penE = pen_db(dl, depth[:, None], "em") + deg * (W["health_e"][:, None] == 1)
            e1 = rng.standard_normal((N, K))
            e2 = rho * e1 + np.sqrt(1 - rho ** 2) * rng.standard_normal((N, K))
            ee = rng.standard_normal((N, K))
            okg = (~absent) & (W["health_g"][:, None] != 2)
            s250 |= (m250 - penG + g["sigma_run_db"] * zr1 + sseg * e1 > g["threshold_db"]) & okg
            s600 |= (m600 - penG + g["sigma_run_db"] * zr2 + sseg * e2 > g["threshold_db"]) & okg
            sem |= (em_mean - penE + e["sigma_seg_db"] * ee > e["threshold_db"]) & (~absent) & W["coupled"][:, None] & (W["health_e"][:, None] != 2)
        d250 = s250 | (rng.random((N, K)) < pfa)
        d600 = s600 | (rng.random((N, K)) < pfa)
        dem = sem | (rng.random((N, K)) < e["pfa"])
        if dropout > 0:
            miss = rng.random((N, K)) < dropout
            d250, d600, dem = d250 & ~miss, d600 & ~miss, dem & ~miss
            out[pi] = dict(d250=d250, d600=d600, dem=dem, mask=~miss)
        else:
            out[pi] = dict(d250=d250, d600=d600, dem=dem, mask=np.ones((N, K), bool))
    return out


# ----------------------------------------------------------------------------------------------------------------
# Likelihood tables and the lateral filter
# ----------------------------------------------------------------------------------------------------------------
def assumed_soil(s):
    return ASSUME_SOIL.get(int(s), int(s))


def lateral_tables(cfg, passes_m):
    """total detection probability tables (what the field software would hold), indexed [sensor][health][cell, y, pass]; and clutter rates [sensor][cell]"""
    md = S.mid_depth(cfg)
    ncell = NS4 * NU
    P = len(passes_m)
    deg = A4["health"]["degraded_loss_db"]
    tab = {(s, h): np.zeros((ncell, NY, P)) for s in ("g250", "g600", "em", "emc") for h in (0, 1)}
    pf = {s: np.zeros(ncell) for s in ("g250", "g600", "em")}
    for soil in range(NS4):
        sa = assumed_soil(soil)
        for u in range(NU):
            c = soil * NU + u
            dl = np.abs(YM[:, None] - np.asarray(passes_m, float)[None, :])
            for h in (0, 1):
                penG = pen_db(dl, md[u], "gpr") + deg * h
                penE = pen_db(dl, md[u], "em") + deg * h
                for s, band in (("g250", "250"), ("g600", "600")):
                    p = S.pd_gpr(cfg, sa, u, md[u], band, penG)
                    pfa = cfg["soil"]["clutter_pfa"][sa]
                    tab[(s, h)][c] = p + (1 - p) * pfa
                p = S.pd_em(cfg, sa, u, md[u], penE)
                tab[("em", h)][c] = p + (1 - p) * cfg["em"]["pfa"]
                pc_ = S.pd_em_signal(cfg, sa, u, md[u], penE)                        # detection probability of a COUPLED utility
                tab[("emc", h)][c] = pc_ + (1 - pc_) * cfg["em"]["pfa"]
            pf["g250"][c] = pf["g600"][c] = cfg["soil"]["clutter_pfa"][sa]
            pf["em"][c] = cfg["em"]["pfa"]
    for k in tab:
        tab[k] = np.clip(tab[k], 1e-4, 1 - 1e-3)
    return tab, pf


def build_T(par):
    n = NY + 1
    T = np.zeros((n, n))
    hg, rb, hs, pdr = par["loss_per_seg"], par["rebirth_per_seg"], par["shift_per_seg"], par["drift_per_seg"]
    mlo, mhi = A4["shift_magnitude_steps"]
    for i in range(NY):
        T[i, NY] += hg
        tgt = [j for j in range(NY) if mlo <= abs(j - i) <= mhi]
        if tgt:
            for j in tgt:
                T[i, j] += hs / len(tgt)
        else:
            T[i, i] += hs
        for j in (i - 1, i + 1):
            if 0 <= j < NY:
                T[i, j] += pdr / 2.0
            else:
                T[i, i] += pdr / 2.0
        T[i, i] += 1.0 - T[i].sum()
    w = np.exp(-0.5 * ((np.arange(NY) - Y0) / par["rebirth_sigma_steps"]) ** 2)
    w /= w.sum()
    T[NY, :NY] = rb * w
    T[NY, NY] = 1.0 - rb
    return T


def prior_belief(N, mode, rel=1.0):
    b = np.zeros((N, NY + 1))
    if mode == "anchor":
        b[:, Y0] = rel
        b[:, NY] = 1.0 - rel
        b = np.maximum(b, 1e-6)
    else:                                                  # no anchor: half the mass on "absent", the rest spread around the reference alignment
        w = np.exp(-0.5 * ((np.arange(NY) - Y0) / 4.0) ** 2)
        b[:, :NY] = 0.5 * w / w.sum()
        b[:, NY] = 0.5
    return b / b.sum(1, keepdims=True)


def run_lateral(cfg, W, obs, passes_m, passes_used, tabs, pfs, prior="anchor", prior_rel=1.0, health_aware=True, params=None, track_time=False, latent_coupling=True):
    """2D filter. passes_used: list of pass INDICES into passes_m / obs. Returns P_on (N,K), P_present_any (N,K), lateral mean (N,K).
    With latent_coupling the filter carries a persistent per-corridor 'EM-coupled' state, so repeated EM non-detections are not counted as independent
    evidence of absence (the coupling of a utility to the locator is a property of the corridor, not of a segment)."""
    params = params or A4["filter_2d"]
    N, K = W["N"], W["K"]
    T = build_T(params)
    b0 = prior_belief(N, prior, prior_rel)
    cpl = S.em_coupling_eff(cfg)[W["util"]]
    if latent_coupling:
        b = np.stack([b0 * (1.0 - cpl)[:, None], b0 * cpl[:, None]], axis=1)          # layer 0: not coupled, layer 1: coupled
    else:
        b = b0[:, None, :]
    pidx = list(passes_used)
    cell = W["cell"]
    ft = {"g250": W["flag_g"], "g600": W["flag_g"], "em": W["flag_e"]}
    key = {"g250": "d250", "g600": "d600", "em": "dem"}
    tt = {}
    names = {"g250": "g250", "g600": "g600", "em": "emc" if latent_coupling else "em"}
    for s in ("g250", "g600", "em"):
        t0, t1 = tabs[(names[s], 0)][cell], tabs[(names[s], 1)][cell]                 # (N, NY, NP)
        if health_aware:
            tt[s] = np.where(ft[s][:, None, None] == 1, t1, t0)
        else:
            tt[s] = t0
    pfc = {s: pfs[s][cell] for s in pfs}
    Pon = np.empty((N, K)); Pany = np.empty((N, K)); Lat = np.empty((N, K))
    foot = np.zeros(NY + 1, bool)
    foot[Y0 - FOOT:Y0 + FOOT + 1] = True
    t_start = time.time()
    for k in range(K):
        if k > 0:
            b = b @ T
        for pi in pidx:
            m = obs[pi]["mask"][:, k]
            for s in ("g250", "g600", "em"):
                det = obs[pi][key[s]][:, k]
                tab = tt[s][:, :, pi]
                lik = np.where(det[:, None], tab, 1.0 - tab)
                lg = np.where(det, pfc[s], 1.0 - pfc[s])
                if health_aware:
                    dead = ft[s] == 2
                    lik = np.where(dead[:, None], 1.0, lik)
                    lg = np.where(dead, 1.0, lg)
                lik = np.where(m[:, None], lik, 1.0)
                lg = np.where(m, lg, 1.0)
                if latent_coupling and s == "em":
                    b[:, 1, :NY] *= lik
                    b[:, 1, NY] *= lg
                    b[:, 0, :] *= lg[:, None]                                         # an uncoupled utility is seen only through clutter
                else:
                    b[:, :, :NY] *= lik[:, None, :]
                    b[:, :, NY] *= lg[:, None]
            b /= b.sum((1, 2), keepdims=True)
            b = np.maximum(b, 1e-12)
        bp = b.sum(1)
        Pon[:, k] = bp[:, foot].sum(1)
        Pany[:, k] = 1.0 - bp[:, NY]
        pos = bp[:, :NY]
        Lat[:, k] = (pos * YM[None, :]).sum(1) / np.maximum(pos.sum(1), 1e-12)
    secs = time.time() - t_start
    return (Pon, Pany, Lat, secs) if track_time else (Pon, Pany, Lat)


# ----------------------------------------------------------------------------------------------------------------
# Capability zones (closed form, depth-resolved)
# ----------------------------------------------------------------------------------------------------------------
def capability(cfg, W, flags=True, depth_error=True, rng=None):
    """fused closed-form signal detection probability at the ESTIMATED depth (true depth with a 10% velocity-calibration error), using the sensors
    that the health diagnostic has not declared failed (a sensor flagged degraded is evaluated with the degradation loss) and the filter's (assumed) soil parameters"""
    N = W["N"]
    sa = np.array([assumed_soil(s) for s in W["soil"]])
    d = W["depth"].copy()
    if depth_error:
        d = d * (1.0 + A4["zones"]["depth_rel_error"] * rng.standard_normal(N))
        d = np.maximum(d, 0.2)
    deg = A4["health"]["degraded_loss_db"]
    pg0, pg1, pe0, pe1 = (np.zeros(N) for _ in range(4))
    for s in np.unique(sa):
        for u in range(NU):
            m = (sa == s) & (W["util"] == u)
            if not m.any():
                continue
            pg0[m] = S.pd_gpr_any(cfg, s, u, d[m]); pg1[m] = S.pd_gpr_any(cfg, s, u, d[m], deg)
            pe0[m] = S.pd_em(cfg, s, u, d[m]); pe1[m] = S.pd_em(cfg, s, u, d[m], deg)
    if flags:
        pg = np.where(W["flag_g"] == 2, 0.0, np.where(W["flag_g"] == 1, pg1, pg0))
        pe = np.where(W["flag_e"] == 2, 0.0, np.where(W["flag_e"] == 1, pe1, pe0))
    else:
        pg, pe = pg0, pe0
    return 1.0 - (1.0 - pg) * (1.0 - pe)


def zone_of(pcap):
    z = A4["zones"]
    return np.where(pcap >= z["A"], 0, np.where(pcap >= z["C"], 1, 2))     # 0 = A, 1 = B, 2 = C


# ----------------------------------------------------------------------------------------------------------------
# Metrics with an unverified state, cluster bootstrap
# ----------------------------------------------------------------------------------------------------------------
SEG_PER_KM = 1000.0 / 5.0


def corridor_counts(call, truth):
    """call: int8 (N,K): 1 present, 0 absent, 2 unverified. returns (N,6) per-corridor fractions [tp, fn, fp, tn, unverified-on, unverified-off]"""
    parts = [(call == 1) & truth, (call == 0) & truth, (call == 1) & ~truth, (call == 0) & ~truth, (call == 2) & truth, (call == 2) & ~truth]
    return np.stack([p.mean(1) for p in parts], axis=1)


def metrics_from_counts(c):
    tp, fn, fp, tn, uo, uf = c
    dec = tp + fn + fp + tn
    return dict(sensitivity=tp / (tp + fn) if tp + fn > 0 else np.nan,
                false_clearance=fn / (fn + tn) if fn + tn > 0 else np.nan,
                false_alarm=fp / (fp + tn) if fp + tn > 0 else np.nan,
                unverified=uo + uf, released=fn + tn, accuracy_decided=(tp + tn) / dec if dec > 0 else np.nan,
                strikes_per_km=fn * SEG_PER_KM, prevalence=tp + fn + uo,
                unverified_present_share=uo / (tp + fn + uo) if tp + fn + uo > 0 else np.nan)


def cell_mean_counts(X, cell, weights):
    """X (N,6) per corridor; cell index per corridor; weights over cells -> weighted mean count vector"""
    tot = np.zeros(6)
    ws = 0.0
    for c in np.unique(cell):
        w = weights[c]
        if w <= 0:
            continue
        tot += w * X[cell == c].mean(0)
        ws += w
    return tot / ws


def bootstrap_metrics(X, cell, weights, B, rng):
    """cluster (corridor) bootstrap stratified by cell. returns {metric: [point, lo, hi]}"""
    cells = [c for c in np.unique(cell) if weights[c] > 0]
    point = metrics_from_counts(cell_mean_counts(X, cell, weights))
    acc = np.zeros((B, 6))
    ws = 0.0
    for c in cells:
        Xc = X[cell == c]
        idx = rng.integers(0, len(Xc), (B, len(Xc)))
        acc += weights[c] * Xc[idx].mean(1)
        ws += weights[c]
    acc /= ws
    keys = list(point.keys())
    draws = {k: np.empty(B) for k in keys}
    for b in range(B):
        m = metrics_from_counts(acc[b])
        for k in keys:
            draws[k][b] = m[k]
    out = {}
    for k in keys:
        v = draws[k][np.isfinite(draws[k])]
        out[k] = [float(point[k]), float(np.percentile(v, 2.5)) if len(v) else None, float(np.percentile(v, 97.5)) if len(v) else None]
    return out


def world_weights(cfg, soils):
    sh = np.array(cfg["util"]["share"], float)
    sh = sh / sh.sum()
    w = np.zeros(NS4 * NU)
    for s in soils:
        w[s * NU:(s + 1) * NU] = sh / len(soils)
    return w


def ranked_strike_rate(score, truth, wseg, coverage):
    """release the `coverage` share of segments with the lowest score (ties broken at random by the caller's jitter); returns strikes per km of corridor and strike rate among released"""
    s = score.ravel(); t = truth.ravel(); w = wseg.ravel()
    o = np.argsort(s, kind="stable")
    cw = np.cumsum(w[o])
    cw = cw / cw[-1]
    j = np.searchsorted(cw, coverage)
    rel = o[:j + 1]
    wr = w[rel].sum()
    strikes = (w[rel] * t[rel]).sum() / w.sum()
    return strikes * SEG_PER_KM, (w[rel] * t[rel]).sum() / max(wr, 1e-12)


# ----------------------------------------------------------------------------------------------------------------
# On-site reference-target check (out-of-distribution guard)
# ----------------------------------------------------------------------------------------------------------------
def reference_check(rng, cfg, W):
    """the crew passes a reference target of the corridor's utility class n times at class mid-depth; the observed detection rate is compared
    with the rate predicted by the filter's (assumed) soil tables with a two-sided exact binomial test. returns a boolean flag per corridor"""
    n = A4["reference_check"]["n_passes"]
    alpha = A4["reference_check"]["alpha"]
    md = S.mid_depth(cfg)
    N = W["N"]
    p_true = np.zeros(N)
    p_hat = np.zeros(N)
    for s in np.unique(W["soil"]):
        for u in range(NU):
            m = (W["soil"] == s) & (W["util"] == u)
            if not m.any():
                continue
            for soil_idx, dest in ((s, "t"), (assumed_soil(s), "h")):
                pg = float(S.pd_gpr_any(cfg, soil_idx, u, md[u]))
                pe = float(S.pd_em(cfg, soil_idx, u, md[u]))
                pf = cfg["soil"]["clutter_pfa"][soil_idx]
                p = 1.0 - (1.0 - pg) * (1.0 - pe)
                p = p + (1 - p) * pf
                if dest == "t":
                    p_true[m] = p
                else:
                    p_hat[m] = p
    k = rng.binomial(n, p_true)
    flag = np.zeros(N, bool)
    cache = {}
    for i in range(N):
        key = (round(p_hat[i], 6), int(k[i]))
        if key not in cache:
            cache[key] = stats.binomtest(int(k[i]), n, min(max(p_hat[i], 1e-9), 1 - 1e-9)).pvalue < alpha
        flag[i] = cache[key]
    return flag


# ----------------------------------------------------------------------------------------------------------------
# The models on one simulated world
# ----------------------------------------------------------------------------------------------------------------
PASSES_ALL = [-4.0, -3.0, -2.0, 0.0, 2.0, 3.0, 4.0, 0.0, 0.0]       # lateral positions (m); the last two repeat the centre line (effort-matched baseline)
CENTRE, REP = 3, [7, 8]
P1, P3 = [CENTRE], [1, CENTRE, 5]
MODELS = ["em_only", "gpr_only", "fusion", "continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass"]
MODEL_LABEL = {"em_only": "EM only", "gpr_only": "GPR only (dual band)", "fusion": "Per-segment GPR + EM fusion", "continuity_1d": "Continuity-aware 1D filter (v1.0 framework), one pass",
               "continuity_1d_3rep": "Continuity-aware 1D filter, three repeat passes on the centre line (equal effort)",
               "proposed_1pass": "Proposed: lateral tracking + sensor health + depth zones, one pass",
               "proposed_3pass": "Proposed, three parallel passes (-3, 0, +3 m)"}
ZONE_B_TAU_ABSENT = 0.02          # in the marginal zone an absent call needs a much lower probability


def filter_1d_multi(obs_list, L, cfg, b0, masks):
    """the v1.0 continuity filter with several observation sets per segment (repeat passes), same prediction step"""
    N, K = obs_list[0]["d250"].shape
    h, r = S.filt_rates(cfg)
    b = np.full(N, b0)
    P = np.empty((N, K))
    for k in range(K):
        if k > 0:
            b = b * (1 - h) + (1 - b) * r
        lo = S.logit(b)
        for ob, mk in zip(obs_list, masks):
            step = S.llr_step(L, ob, k, ("g250", "g600", "em"))
            lo = lo + np.where(mk[:, k], step, 0.0)
        b = S.sigmoid(lo)
        P[:, k] = b
    return P


def run_models(cfg, W, obs, rng, prior_mode, prior_rel, guard=False, which=MODELS, tabs=None, pfs=None, truth_mode="footprint"):
    N, K = W["N"], W["K"]
    if truth_mode == "swath":
        truth = W["ypos"] != GONE
    else:
        truth = ((np.abs(W["ypos"].astype(int) - Y0) <= FOOT) & (W["ypos"] != GONE)) | W["extra_truth"]

    def d1(i):
        return dict(d250=obs[i]["d250"], d600=obs[i]["d600"], dem=obs[i]["dem"])
    centre = obs[CENTRE]
    mask = centre["mask"]
    ob1 = d1(CENTRE)
    sa = np.array([assumed_soil(s) for s in W["soil"]])
    B1 = dict(N=N, K=K, n=W["n"], cell=W["cell"], soil=sa, util=W["util"], depth=W["depth"], shadow=np.zeros(N))
    L = S.lr_tables(cfg, B1, "matched", "class")
    blind, _ = S.blind_table(cfg)
    bl = blind[sa, W["util"]]
    b0 = 0.5 if prior_mode == "none" else 1.0
    out = {}
    times = {}
    if "em_only" in which:
        out["em_only"] = dict(call=np.where(ob1["dem"], 1, 0).astype(np.int8), P=None)
    if "gpr_only" in which:
        t0 = time.time(); P = S.persegment(ob1, L, ("g250", "g600"), 0.5); times["gpr_only"] = time.time() - t0
        out["gpr_only"] = dict(call=np.where(P > 0.5, 1, 0).astype(np.int8), P=P)
    if "fusion" in which:
        t0 = time.time(); P = S.persegment(ob1, L, ("g250", "g600", "em"), 0.5); times["fusion"] = time.time() - t0
        out["fusion"] = dict(call=np.where(P > 0.5, 1, 0).astype(np.int8), P=P)
    if "continuity_1d" in which:
        t0 = time.time()
        P = S.run_filter(ob1, L, cfg, b0=b0, mask=mask)
        times["continuity_1d"] = time.time() - t0
        call = np.where(bl[:, None], 2, np.where(P > 0.5, 1, 0)).astype(np.int8)
        out["continuity_1d"] = dict(call=call, P=P, P_binary_call=np.where(P > 0.5, 1, 0).astype(np.int8))
    if "continuity_1d_3rep" in which:
        t0 = time.time()
        idx = [CENTRE] + REP
        P = filter_1d_multi([d1(i) for i in idx], L, cfg, b0, [obs[i]["mask"] for i in idx])
        times["continuity_1d_3rep"] = time.time() - t0
        call = np.where(bl[:, None], 2, np.where(P > 0.5, 1, 0)).astype(np.int8)
        out["continuity_1d_3rep"] = dict(call=call, P=P)
    if tabs is None:
        tabs, pfs = lateral_tables(cfg, PASSES_ALL)
    pcap = capability(cfg, W, flags=True, depth_error=True, rng=rng)
    zone = zone_of(pcap)
    gflag = reference_check(rng, cfg, W) if guard else np.zeros(N, bool)
    ta, tp_ = A4["tau_absent"], A4["tau_present"]
    for name, used in (("proposed_1pass", P1), ("proposed_3pass", P3)):
        if name not in which:
            continue
        Pon, Pany, Lat, secs = run_lateral(cfg, W, obs, PASSES_ALL, used, tabs, pfs, prior=prior_mode, prior_rel=prior_rel, health_aware=True, track_time=True)
        times[name] = secs
        Pdec = Pany if truth_mode == "swath" else Pon
        tau_a = np.where(zone[:, None] == 1, ZONE_B_TAU_ABSENT, ta)
        call = np.where(Pdec >= tp_, 1, np.where(Pdec <= tau_a, 0, 2)).astype(np.int8)
        unv_zone = (zone == 2) | gflag
        call = np.where(unv_zone[:, None], 2, call).astype(np.int8)
        out[name] = dict(call=call, P=Pdec, Pany=Pany, Lat=Lat, zone=zone, gflag=gflag, call_balanced=np.where(Pdec > 0.5, 1, 0).astype(np.int8),
                         P_binary_call=np.where(Pdec > 0.5, 1, 0).astype(np.int8))
    out["_truth"] = truth
    out["_times"] = times
    return out


SCENARIOS = [
    ("baseline", dict()),
    ("curved", dict(geom="curved")),
    ("shifted", dict(geom="shifted")),
    ("shifted_frequent", dict(geom="shifted_frequent")),
    ("interrupted", dict(geom="interrupted")),
    ("B_gpr_failed_flagged", dict(gpr_state="failed", flag="all")),
    ("C_gpr_failed_unflagged", dict(gpr_state="failed", flag="none")),
    ("D_both_degraded", dict(gpr_state="degraded", em_state="degraded")),
    ("mixed_health_realistic_diagnostic", dict(gpr_state="mixed", em_state="mixed")),
    ("map_offset", dict(map_quality="offset", truth_mode="swath")),
    ("map_incomplete", dict(map_quality="incomplete")),
    ("map_misleading", dict(map_quality="misleading")),
    ("sparse_coverage", dict(dropout=0.5)),
    ("ood_soils", dict(soils=[5, 6], guard=True)),
    ("ood_soils_no_guard", dict(soils=[5, 6], guard=False)),
    ("combined_stress", dict(geom="shifted", gpr_state="mixed", em_state="mixed", map_quality="offset", dropout=0.3, truth_mode="swath")),
]


def apply_flag_override(W, mode):
    if mode == "all":
        W["flag_g"] = np.where(W["health_g"] == 2, 2, W["flag_g"])
        W["flag_e"] = np.where(W["health_e"] == 2, 2, W["flag_e"])
    elif mode == "none":
        W["flag_g"] = np.zeros(W["N"], int)
        W["flag_e"] = np.zeros(W["N"], int)


def run_scenario(cfg, name, sc, seed, nblocks, n, boots, log, tabs_cache, cfg_true=None):
    soils = sc.get("soils", [0, 1, 2, 3, 4])
    geom = sc.get("geom", "straight")
    mq = sc.get("map_quality", "accurate")
    tmode = sc.get("truth_mode", "footprint")
    prior_mode = "none" if mq == "incomplete" else "anchor"
    prior_rel = 1.0
    if "tabs" not in tabs_cache:
        tabs_cache["tabs"] = lateral_tables(cfg, PASSES_ALL)
    tabs, pfs = tabs_cache["tabs"]
    wts = world_weights(cfg, soils)
    pooled = {m: [] for m in MODELS}
    cells = []
    cal = {m: [] for m in ("fusion", "continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass")}
    lat = {m: [] for m in ("proposed_1pass", "proposed_3pass")}
    zones, gflags = [], []
    times = {m: [] for m in MODELS}
    cov = {m: {0.3: [], 0.5: [], "30_binary": [], "50_binary": []} for m in MODELS}
    bal = {m: [] for m in ("proposed_1pass", "proposed_3pass")}
    for b in range(nblocks):
        rng = S.rng_for(seed, "v4-" + name, b)
        W = make_world(rng, cfg_true or cfg, soils, n, geom=geom, map_quality=mq, gpr_state=sc.get("gpr_state", "healthy"), em_state=sc.get("em_state", "healthy"))
        apply_flag_override(W, sc.get("flag"))
        obs = observe_world(rng, cfg_true or cfg, W, PASSES_ALL, dropout=sc.get("dropout", 0.0))
        res = run_models(cfg, W, obs, rng, prior_mode, prior_rel, guard=sc.get("guard", False), tabs=tabs, pfs=pfs, truth_mode=tmode)
        truth = res["_truth"]
        cells.append(W["cell"])
        wcorr = wts[W["cell"]]
        wcorr = wcorr / wcorr.sum()
        wseg = np.repeat(wcorr / W["K"], W["K"]).reshape(W["N"], W["K"])
        for m in MODELS:
            pooled[m].append(corridor_counts(res[m]["call"], truth))
            times[m].append(res["_times"].get(m, 0.0))
            P = res[m]["P"]
            if m in cal and P is not None:
                cal[m].append(S.calib_stats(P, truth, wcorr))
            if P is not None:
                sc_ = np.where(res[m]["call"] == 2, 2.0, P)
                sc_b = P
            else:
                sc_ = res[m]["call"].astype(float)
                sc_b = sc_
            jit = 1e-9 * rng.random(sc_.shape)
            cap = float((wseg * (res[m]["call"] != 2)).sum() / wseg.sum())          # share of the corridor the model is willing to release at all
            for c in (0.3, 0.5):
                cov[m][c].append(ranked_strike_rate(sc_ + jit, truth, wseg, c)[0] if cap >= c else np.nan)
                cov[m]["%d_binary" % int(100 * c)].append(ranked_strike_rate(sc_b + jit, truth, wseg, c)[0])
        for m in ("proposed_1pass", "proposed_3pass"):
            r = res[m]
            present = (W["ypos"] != GONE) & (r["Pany"] > 0.5)
            err = np.abs(r["Lat"] - (W["ypos"].astype(float) - Y0) * 0.5)[present]
            lat[m].append(err)
            bal[m].append(corridor_counts(r["call_balanced"], truth))
        zones.append(res["proposed_1pass"]["zone"])
        gflags.append(res["proposed_1pass"]["gflag"])
        log("   %s block %d/%d" % (name, b + 1, nblocks))
    cellv = np.concatenate(cells)
    rngb = S.rng_for(seed, "v4-boot-" + name, 0)
    out = {"n_corridors": int(len(cellv)), "weights_note": "cell weights: assumed network share, soils in the scenario weighted equally", "truth": tmode, "models": {}}
    for m in MODELS:
        X = np.concatenate(pooled[m])
        d = bootstrap_metrics(X, cellv, wts, boots, rngb)
        rec = {"metrics": d, "compute_seconds_per_block": float(np.mean(times[m])),
               "strikes_per_km_at_30pct_released": ci_list(cov[m][0.3]), "strikes_per_km_at_50pct_released": ci_list(cov[m][0.5]),
               "strikes_per_km_at_30pct_released_ignoring_unverified": ci_list(cov[m]["30_binary"]), "strikes_per_km_at_50pct_released_ignoring_unverified": ci_list(cov[m]["50_binary"])}
        if m in cal and cal[m]:
            rec["ece"] = ci_list([c["ece"] for c in cal[m]]); rec["brier"] = ci_list([c["brier"] for c in cal[m]])
        if m in lat:
            e = np.concatenate(lat[m])
            rec["lateral_error_m"] = dict(median=float(np.median(e)) if len(e) else None, share_within_0p5m=float((e <= 0.5).mean()) if len(e) else None, n=int(len(e)))
            Xb = np.concatenate(bal[m])
            rec["balanced_rule_metrics"] = {k: v for k, v in bootstrap_metrics(Xb, cellv, wts, max(50, boots // 4), rngb).items() if k in ("sensitivity", "false_clearance", "false_alarm", "strikes_per_km")}
        out["models"][m] = rec
    zz = np.concatenate(zones)
    out["zone_share"] = {"A": float((zz == 0).mean()), "B": float((zz == 1).mean()), "C": float((zz == 2).mean())}
    gf = np.concatenate(gflags)
    out["reference_check_flag_share"] = float(gf.mean()) if sc.get("guard") else None
    return out


def ci_list(v):
    m, h = S.ci_stats(v)
    return [float(m), float(h)]


# ----------------------------------------------------------------------------------------------------------------
# Excavation clearance at EQUAL released coverage, equal risk and total cost (v1.0.0 world)
# ----------------------------------------------------------------------------------------------------------------
POLICIES = ["em_only", "gpr_dual", "seg_flat", "anch_binary", "anch_three_state", "random"]
POLICY_LABEL = {"em_only": "EM locator only", "gpr_dual": "GPR dual-band, per segment", "seg_flat": "GPR + EM fusion, per segment", "anch_binary": "Anchored filter, binary map",
                "anch_three_state": "Anchored filter, three-state (unverified never released)", "random": "Random release (reference)"}
COVS = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]


def _v1_block(cfg1, seed, tag, b, n, which=("em_only", "gpr_dual", "seg_flat", "anch_full")):
    rng = S.rng_for(seed, tag, b)
    B = S.make_block(rng, cfg1, n)
    obs = S.observe(rng, B, cfg1)
    res = S.all_methods(cfg1, B, obs, which=which)
    return rng, B, obs, res


def exp_equal_coverage(cfg1, seed, nblocks, n, log, tag="v4-cover"):
    blind, _ = S.blind_table(cfg1)
    wmix = S.cell_weights(cfg1).ravel()
    cons = np.array(cfg1["util"]["consequence"], float)
    cst = A4["costs_usd"]
    grid = np.arange(0.01, 0.951, 0.01)
    rec = {p: dict(strike=[], rate=[], cons=[]) for p in POLICIES}
    eqr = {p: {str(r): [] for r in (0.01, 0.02, 0.05)} for p in POLICIES}
    costcurve = {p: [] for p in POLICIES}
    maxcov = {p: [] for p in POLICIES}
    for b in range(nblocks):
        rng, B, obs, res = _v1_block(cfg1, seed, tag, b, n)
        truth = B["state"] == 1
        wc = S.corr_weights(B, wmix)
        wseg = np.repeat(wc / B["K"], B["K"]).reshape(B["N"], B["K"])
        bl = blind[B["soil"], B["util"]]
        consseg = cons[B["util"]][:, None] * np.ones((1, B["K"]))
        P_anch = res["anch_full"][0]
        jit = 1e-9 * rng.random(truth.shape)
        scores = {"em_only": res["em_only"][1].astype(float) + jit, "gpr_dual": res["gpr_dual"][0] + jit, "seg_flat": res["seg_flat"][0] + jit,
                  "anch_binary": P_anch + jit, "anch_three_state": np.where(bl[:, None], 2.0, P_anch) + jit, "random": rng.random(truth.shape)}
        for p in POLICIES:
            s = scores[p].ravel(); t = truth.ravel(); w = wseg.ravel(); cs = consseg.ravel()
            o = np.argsort(s, kind="stable")
            cw = np.cumsum(w[o]); tot = cw[-1]; cw = cw / tot
            cum_t = np.cumsum((w * t)[o]) / tot                      # strikes per segment-weight of the whole corridor
            cum_c = np.cumsum((w * t * cs)[o]) / tot
            rate = cum_t / np.maximum(cw, 1e-12)
            maxcov[p].append(float(cw[-1] if p != "anch_three_state" else cw[np.searchsorted(s[o], 1.5) - 1]))
            for c in COVS:
                j = min(np.searchsorted(cw, c), len(cw) - 1)
                if p == "anch_three_state" and s[o][j] > 1.5:
                    rec[p]["strike"].append((c, np.nan, np.nan, np.nan, b)); continue
                rec[p]["strike"].append((c, cum_t[j] * SEG_PER_KM, rate[j], cum_c[j] * SEG_PER_KM, b))
            for r in (0.01, 0.02, 0.05):
                ok = np.where(rate <= r)[0]
                lim = len(cw) if p != "anch_three_state" else np.searchsorted(s[o], 1.5)
                ok = ok[ok < lim]
                eqr[p][str(r)].append(float(cw[ok[-1]]) if len(ok) else 0.0)
            # total cost per km of corridor as a function of released coverage c
            cl = []
            for c in grid:
                j = min(np.searchsorted(cw, c), len(cw) - 1)
                if p == "anch_three_state" and s[o][j] > 1.5:
                    cl.append((c, np.nan, np.nan)); continue
                strike_cost = cum_c[j] * SEG_PER_KM * cst["strike_per_consequence_unit"]
                hold_cost = (1.0 - cw[j]) * SEG_PER_KM * cst["hold_per_segment"]
                cl.append((c, strike_cost, hold_cost))
            costcurve[p].append(cl)
        log("   equal-coverage block %d/%d" % (b + 1, nblocks))
    out = {"coverage_grid": COVS, "policies": {}}
    for p in POLICIES:
        arr = np.array(rec[p]["strike"], float)
        pol = {"label": POLICY_LABEL[p], "by_coverage": []}
        for c in COVS:
            sel = arr[np.isclose(arr[:, 0], c)]
            if np.isnan(sel[:, 1]).all():
                pol["by_coverage"].append(dict(coverage=c, strikes_per_km=None, strike_rate=None, consequence_strikes_per_km=None)); continue
            pol["by_coverage"].append(dict(coverage=c, strikes_per_km=ci_list(sel[:, 1]), strike_rate=ci_list(sel[:, 2]), consequence_strikes_per_km=ci_list(sel[:, 3])))
        pol["equal_risk_coverage"] = {r: ci_list(v) for r, v in eqr[p].items()}
        pol["max_coverage"] = ci_list(maxcov[p])
        cc = np.array(costcurve[p], float)                              # (blocks, grid, 3)
        pol["cost_per_km"] = {}
        for mult_name, mult in (("strike_cost_x0.25", 0.25), ("strike_cost_x1", 1.0), ("strike_cost_x4", 4.0)):
            tot = cc[:, :, 1] * mult + cc[:, :, 2]
            tm = np.nanmean(tot, axis=0)
            if np.isnan(tm).all():
                pol["cost_per_km"][mult_name] = None; continue
            j = int(np.nanargmin(tm))
            pol["cost_per_km"][mult_name] = dict(min_cost_usd_per_km_excl_survey=float(tm[j]), coverage_at_min=float(grid[j]),
                                                 curve=[[float(grid[i]), (None if np.isnan(tm[i]) else float(tm[i]))] for i in range(0, len(grid), 5)])
        out["policies"][p] = pol
    out["note"] = "strikes per km of corridor surveyed; consequence-weighted strikes use the relative consequence weights x US$2,000; hold cost applies to every segment not released for mechanical excavation; survey cost per km is common to all policies and is excluded"
    return out


# ----------------------------------------------------------------------------------------------------------------
# Value-of-information allocation of trial pits (v1.0.0 world)
# ----------------------------------------------------------------------------------------------------------------
def exp_voi(cfg1, seed, nblocks, n, log, hold=None):
    wmix = S.cell_weights(cfg1).ravel()
    cons = np.array(cfg1["util"]["consequence"], float)
    c = A4["costs_usd"]
    budgets = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40]
    strategies = ["random", "probability", "value_of_information"]
    rec = {s: {bf: [] for bf in budgets} for s in strategies}
    blind, _ = S.blind_table(cfg1)
    for b in range(nblocks):
        rng, B, obs, res = _v1_block(cfg1, seed, "v4-voi", b, n, which=("anch_full",))
        P = res["anch_full"][0]
        truth = B["state"] == 1
        wc = S.corr_weights(B, wmix)
        K = B["K"]
        wseg = np.repeat(wc / K, K)
        Cs = (c["strike_per_consequence_unit"] * cons[B["util"]])[:, None] * np.ones((1, K))
        Ch = float(hold if hold is not None else c["hold_per_segment"])
        Cp = (c["pit_base"] + c["pit_per_m"] * B["depth"])[:, None] * np.ones((1, K))
        voi = np.minimum(P * Cs, Ch) - P * Ch - Cp
        bl = blind[B["soil"], B["util"]][:, None] * np.ones((1, K), bool)
        cand = (P <= 0.5) | bl
        pf, tf, wf, csf, chf, cpf, vf, cand_f = (x.ravel() for x in (P, truth, wseg, Cs, np.full(P.shape, Ch), Cp, voi, cand))
        pit_all = (wf * cpf)[cand_f].sum()
        idx = np.where(cand_f)[0]
        rj = rng.random(len(idx))
        orders = {"random": idx[np.argsort(rj)], "probability": idx[np.argsort(-pf[idx], kind="stable")],
                  "value_of_information": idx[np.argsort(-vf[idx], kind="stable")]}
        tot_w = wf.sum()
        for s in strategies:
            o = orders[s]
            if s == "value_of_information":
                o = o[vf[o] > 0]
            cum = np.cumsum((wf * cpf)[o])
            for bf in budgets:
                j = np.searchsorted(cum, bf * pit_all)
                sel = o[:j]
                ver = np.zeros(len(pf), bool); ver[sel] = True
                release_unv = (pf * csf < chf)
                released = np.where(ver, ~tf, release_unv)
                strike = (wf * released * tf * csf).sum() / tot_w                 # US$ per segment
                nstrike = (wf * released * tf).sum() / tot_w
                hold = (wf * (~released) * chf).sum() / tot_w
                pits = (wf * ver * cpf).sum() / tot_w
                rec[s][bf].append((SEG_PER_KM * (strike + hold + pits), SEG_PER_KM * nstrike, (wf * released).sum() / tot_w, SEG_PER_KM * pits))
        log("   VOI block %d/%d" % (b + 1, nblocks))
    out = {"hold_cost_per_segment_usd": float(hold if hold is not None else c["hold_per_segment"]), "budgets_fraction_of_all_candidate_pit_cost": budgets, "strategies": {}}
    for s in strategies:
        out["strategies"][s] = [dict(budget=bf, total_cost_usd_per_km=ci_list([x[0] for x in rec[s][bf]]),
                                     change_vs_no_pits_usd_per_km=ci_list([x[0] - y[0] for x, y in zip(rec[s][bf], rec[s][0.0])]), strikes_per_km=ci_list([x[1] for x in rec[s][bf]]),
                                     released_share=ci_list([x[2] for x in rec[s][bf]]), pit_cost_usd_per_km=ci_list([x[3] for x in rec[s][bf]])) for bf in budgets]
    out["note"] = "total cost = pits + holding cost of segments not released + consequence-weighted strike cost of released occupied segments (US$ per km of corridor; scenario assumptions, not observed costs)"
    return out


# ----------------------------------------------------------------------------------------------------------------
# Capability zones: closed-form table and the depth-resolved unverified rule (v1.0.0 world)
# ----------------------------------------------------------------------------------------------------------------
def zone_table(cfg):
    ds = np.arange(0.5, 7.01, 0.5)
    z = A4["zones"]
    tab = {}
    share = {"A": 0, "B": 0, "C": 0}
    tot = 0
    deepest = {}
    for s in range(NS4):
        tab[SOILS4[s]] = {}
        deepest[SOILS4[s]] = {}
        for u in range(NU):
            p = S.pd_fused(cfg, s, u, ds)
            letters = ["A" if x >= z["A"] else ("B" if x >= z["C"] else "C") for x in p]
            tab[SOILS4[s]][S.UTILS[u]] = "".join(letters)
            da = [d for d, x in zip(ds, p) if x >= z["A"]]
            db = [d for d, x in zip(ds, p) if x >= z["C"]]
            deepest[SOILS4[s]][S.UTILS[u]] = dict(zone_A_to_m=float(max(da)) if da else 0.0, zone_B_to_m=float(max(db)) if db else 0.0)
            if s < 5:
                for l in letters:
                    share[l] += 1; tot += 1
    return dict(depths_m=[float(x) for x in ds], zones=tab, deepest=deepest, share_in_distribution_grid={k: v / tot for k, v in share.items()},
                thresholds=dict(A_at_least=z["A"], C_below=z["C"]))


def exp_depth_resolved(cfg1, seed, nblocks, n, log):
    """compare the cell-level (mid-depth) unverified rule with the depth-resolved rule on the same anchored filter"""
    blind, _ = S.blind_table(cfg1)
    wmix = S.cell_weights(cfg1).ravel()
    recs = {"cell_level": [], "depth_resolved": [], "depth_resolved_tau": []}
    perutil = {k: {u: [] for u in S.UTILS} for k in ("cell_level", "depth_resolved", "depth_resolved_tau")}
    for b in range(nblocks):
        rng, B, obs, res = _v1_block(cfg1, seed, "v4-depth", b, n, which=("anch_full",))
        P = res["anch_full"][0]
        truth = B["state"] == 1
        Wd = dict(N=B["N"], soil=B["soil"], util=B["util"], depth=B["depth"], flag_g=np.zeros(B["N"], int), flag_e=np.zeros(B["N"], int))
        pcap = capability(cfg1, Wd, flags=False, depth_error=True, rng=rng)
        zone = zone_of(pcap)
        bl = blind[B["soil"], B["util"]]
        calls = {}
        base = np.where(P > 0.5, 1, 0)
        calls["cell_level"] = np.where(bl[:, None], 2, base).astype(np.int8)
        calls["depth_resolved"] = np.where((zone == 2)[:, None], 2, base).astype(np.int8)
        tau_a = np.where((zone == 1)[:, None], ZONE_B_TAU_ABSENT, A4["tau_absent"])
        calls["depth_resolved_tau"] = np.where((zone == 2)[:, None], 2, np.where(P >= A4["tau_present"], 1, np.where(P <= tau_a, 0, 2))).astype(np.int8)
        for k, cl in calls.items():
            X = corridor_counts(cl, truth)
            recs[k].append(metrics_from_counts(cell_mean_counts(X, B["cell"], wmix)))
            if k in perutil:
                for ui, u in enumerate(S.UTILS):
                    m = B["util"] == ui
                    Xu = X[m]; cu = B["cell"][m]
                    perutil[k][u].append(metrics_from_counts(cell_mean_counts(Xu, cu, np.where(np.arange(len(wmix)) % S.NU == ui, 1.0, 0.0)))["false_clearance"])
        log("   depth-resolved block %d/%d" % (b + 1, nblocks))
    return {"rules": {k: {m: ci_list([r[m] for r in v]) for m in ("sensitivity", "false_clearance", "false_alarm", "unverified", "released", "strikes_per_km")} for k, v in recs.items()},
            "false_clearance_by_utility": {k: {u: ci_list(v) for u, v in d.items()} for k, d in perutil.items()}}


# ----------------------------------------------------------------------------------------------------------------
# Five-year total cost of ownership and pilot sample sizes
# ----------------------------------------------------------------------------------------------------------------
def tco(km_per_year, level_map):
    t = A4["tco"]

    def g(key):
        return t[key][level_map[key]]
    cap = {"low": t["capital_low"], "base": t["capital_base"], "high": t["capital_high"]}[level_map["capital"]]
    yearly = (g("maintenance_frac_per_year") * cap + g("gnss_subscription_per_year") + g("data_consumables_per_year") + g("training_refresher_per_year")
              + g("crew_per_field_day") * g("field_days_per_year"))
    total = cap + t["years"] * yearly
    km_surveyed_year = min(km_per_year, g("km_per_day") * g("field_days_per_year") * (1.0 - g("downtime_frac")))
    return dict(capital=cap, annual_operating=yearly, tco_5yr=total, km_surveyed_per_year=km_surveyed_year, cost_per_surveyed_km=total / (t["years"] * km_surveyed_year))


def exp_tco(decided_share, released_share_three_state):
    t = A4["tco"]
    levels = ("low", "base", "high")
    out = {"assumptions": t, "scenarios": {}, "sensitivity": []}
    # scenario naming follows the reviewer's table: low = favourable cost, high = unfavourable (names refer to cost)
    fav = {"capital": "low", "maintenance_frac_per_year": "low", "gnss_subscription_per_year": "low", "data_consumables_per_year": "low", "training_refresher_per_year": "low",
           "crew_per_field_day": "low", "field_days_per_year": "high", "km_per_day": "high", "downtime_frac": "low"}
    unf = {"capital": "high", "maintenance_frac_per_year": "high", "gnss_subscription_per_year": "high", "data_consumables_per_year": "high", "training_refresher_per_year": "high",
           "crew_per_field_day": "high", "field_days_per_year": "low", "km_per_day": "low", "downtime_frac": "high"}
    base = {k: "base" for k in fav}
    for name, lm in (("favourable", fav), ("base", base), ("unfavourable", unf)):
        r = tco(1e9, lm)
        r["cost_per_km_with_decision_resolved"] = r["cost_per_surveyed_km"] / max(decided_share, 1e-9)
        r["cost_per_km_released_for_mechanical_excavation"] = r["cost_per_surveyed_km"] / max(released_share_three_state, 1e-9)
        out["scenarios"][name] = r
    b = tco(1e9, base)["cost_per_surveyed_km"]
    for k in fav:
        lo = dict(base); lo[k] = fav[k]
        hi = dict(base); hi[k] = unf[k]
        out["sensitivity"].append(dict(parameter=k, favourable=tco(1e9, lo)["cost_per_surveyed_km"], unfavourable=tco(1e9, hi)["cost_per_surveyed_km"], base=b))
    out["sensitivity"].sort(key=lambda r: -(abs(r["unfavourable"] - r["base"]) + abs(r["favourable"] - r["base"])))
    out["utilisation"] = {}
    for km in (24, 50, 100):
        for name, lm in (("favourable", fav), ("base", base), ("unfavourable", unf)):
            r = tco(float(km), lm)
            out["utilisation"].setdefault(str(km), {})[name] = dict(cost_per_surveyed_km=r["cost_per_surveyed_km"], km_surveyed_per_year=r["km_surveyed_per_year"], tco_5yr=r["tco_5yr"])
    out["note"] = "every operating-cost input is an assumption (not a vendor quote); capital low/high are the published list-price ranges of the white paper and base is their midpoint; utilisation caps the surveyed kilometres per unit-year"
    return out


def pilot_sample_sizes():
    """exact (Clopper-Pearson) sample sizes: smallest n such that, with x observed events, the two-sided 95% upper bound is at most the target"""
    rows = []
    for target in (0.01, 0.02, 0.05):
        for x in (0, 1, 2, 5):
            n = max(x + 1, 1)
            while stats.beta.ppf(0.975, x + 1, n - x) > target:
                n += 1
                if n > 100000:
                    break
            rows.append(dict(target_upper_bound=target, observed_events=x, n_required=n))
    sens = []
    for target in (0.90, 0.95):
        for miss in (0, 1, 2, 5):
            n = max(miss + 1, 1)
            while stats.beta.ppf(0.025, n - miss, miss + 1) < target:
                n += 1
                if n > 100000:
                    break
            sens.append(dict(target_lower_bound=target, observed_misses=miss, n_present_segments_required=n))
    return dict(false_clearance_or_event_rate=rows, sensitivity=sens, method="two-sided 95% Clopper-Pearson interval")


# ----------------------------------------------------------------------------------------------------------------
# Self-tests of the new code
# ----------------------------------------------------------------------------------------------------------------
def selftests_v4(seed=42, verbose=True):
    res = []

    def rec(name, ok, detail):
        res.append(dict(name=name, passed=bool(ok), detail=detail))
        if verbose:
            print("  [%s] %s: %s" % ("PASS" if ok else "FAIL", name, detail))
    cfg = make_cfg4()
    T = build_T(A4["filter_2d"])
    rec("transition matrix rows sum to one and are non-negative", bool(np.allclose(T.sum(1), 1.0) and (T >= 0).all()), "max deviation %.1e" % np.abs(T.sum(1) - 1).max())
    passes = [-3.0, 0.0, 3.0]
    rng = S.rng_for(seed, "v4-selftest", 0)
    W = make_world(rng, cfg, [0, 1], 20, geom="shifted")
    obs = observe_world(rng, cfg, W, passes)
    tabs, pfs = lateral_tables(cfg, passes)
    Pon, Pany, Lat = run_lateral(cfg, W, obs, passes, [1], tabs, pfs)
    rec("lateral filter probabilities are finite and within [0,1]", bool(np.isfinite(Pon).all() and Pon.min() >= 0 and Pon.max() <= 1 + 1e-9), "range %.2e to %.6f" % (Pon.min(), Pon.max()))
    # sensor flagged failed is ignored exactly
    W2 = dict(W); W2["flag_g"] = np.full(W["N"], 2); W2["flag_e"] = np.zeros(W["N"], int)
    a = run_lateral(cfg, W2, obs, passes, [1], tabs, pfs)[0]
    obs_noG = {i: dict(d250=np.zeros_like(o["d250"]), d600=np.zeros_like(o["d600"]), dem=o["dem"], mask=o["mask"]) for i, o in obs.items()}
    W3 = dict(W); W3["flag_g"] = np.full(W["N"], 2); W3["flag_e"] = np.zeros(W["N"], int)
    b = run_lateral(cfg, W3, obs_noG, passes, [1], tabs, pfs)[0]
    rec("a GPR flagged failed contributes nothing to the belief", bool(np.allclose(a, b, atol=1e-12)), "max abs diff %.1e" % np.abs(a - b).max())
    # truth located by a clean strong detector
    Wc = make_world(S.rng_for(seed, "v4-selftest", 1), cfg, [0], 20, geom="straight")
    Wc["ypos"][:, :] = Y0 + 4
    obs_c = {i: dict(d250=np.ones_like(Wc["ypos"], bool) if i == 1 else np.zeros_like(Wc["ypos"], bool), d600=np.zeros_like(Wc["ypos"], bool), dem=np.zeros_like(Wc["ypos"], bool), mask=np.ones_like(Wc["ypos"], bool)) for i in range(3)}
    _, _, lat_c = run_lateral(cfg, Wc, obs_c, passes, [1], tabs, pfs)
    rec("a persistent centre-pass detection keeps the posterior near the pass (|y| small)", bool(np.nanmedian(np.abs(lat_c[:, -1])) < 2.0), "median |y| %.2f m" % np.nanmedian(np.abs(lat_c[:, -1])))
    z = zone_of(np.array([0.95, 0.5, 0.1]))
    rec("zone thresholds", bool((z == np.array([0, 1, 2])).all()), str(z))
    ds = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    pc = np.array([float(S.pd_fused(cfg, 2, 3, d)) for d in ds])
    rec("capability falls monotonically with depth", bool((np.diff(pc) <= 1e-12).all()), str(np.round(pc, 3)))
    # bootstrap behaves
    rng = np.random.default_rng(1)
    X = np.column_stack([rng.random(400) * 0.1, rng.random(400) * 0.02, rng.random(400) * 0.02, rng.random(400) * 0.5, np.zeros(400), np.zeros(400)])
    cell = np.repeat([0, 1], 200)
    w = np.array([0.5, 0.5])
    m = bootstrap_metrics(X, cell, w, 300, rng)["false_clearance"]
    rec("bootstrap interval contains the point estimate", bool(m[1] <= m[0] <= m[2]), "%.4f [%.4f, %.4f]" % tuple(m))
    # equal-coverage ranking: requested coverage reached
    sc_ = rng.random((50, 20)); tr = rng.random((50, 20)) < 0.3; ws = np.full((50, 20), 1.0)
    sk, rate = ranked_strike_rate(sc_, tr, ws, 0.999999)
    rec("releasing everything gives the prevalence as strike rate", abs(rate - tr.mean()) < 0.01, "rate %.3f, prevalence %.3f" % (rate, tr.mean()))
    # VOI sign: with zero pit cost VOI is non-negative
    p = np.linspace(0, 1, 11); Cs, Ch = 6000.0, 150.0
    v = np.minimum(p * Cs, Ch) - p * Ch
    rec("value of information is non-negative before the pit cost", bool((v >= -1e-9).all()), "min %.2f" % v.min())
    # pilot sample sizes: rule of three-like
    ps = pilot_sample_sizes()
    n0 = [r for r in ps["false_clearance_or_event_rate"] if r["target_upper_bound"] == 0.01 and r["observed_events"] == 0][0]["n_required"]
    rec("exact n for zero events and a 1% upper bound is about 370", 360 <= n0 <= 380, "n = %d" % n0)
    # guard false-flag rate in-distribution
    W4 = make_world(S.rng_for(seed, "v4-selftest", 2), cfg, [0, 1, 2, 3, 4], 40)
    fl = reference_check(S.rng_for(seed, "v4-selftest", 3), cfg, W4)
    rec("reference-target check flags few in-distribution corridors", float(fl.mean()) < 0.06, "flag share %.3f (alpha %.2f)" % (fl.mean(), A4["reference_check"]["alpha"]))
    # spline world: paths stay on the grid, the branch adds truth, extra sources exist
    Wsp = make_world(S.rng_for(seed, "v4-selftest", 4), cfg, [0], 10, geom=dict(MISMATCH[4][1]))
    okp = bool(len(Wsp["extra"]) == 2 and Wsp["extra_truth"].any() and all(((p >= 0) & (p < NY)).all() for p, _ in Wsp["extra"]) and ((Wsp["ypos"] == GONE) | ((Wsp["ypos"] >= 0) & (Wsp["ypos"] < NY))).all())
    rec("spline world with parallel utility and branch is well formed", okp, "extra sources %d, branch truth share %.3f" % (len(Wsp["extra"]), float(Wsp["extra_truth"].mean())))
    # determinism
    r1 = make_world(S.rng_for(seed, "v4-det", 0), cfg, [0], 5)["ypos"]
    r2 = make_world(S.rng_for(seed, "v4-det", 0), cfg, [0], 5)["ypos"]
    rec("same seed gives identical lateral truth", bool(np.array_equal(r1, r2)), "arrays equal")
    sig = attenuation_from_conductivity(0.01, 9.0)
    rec("conductivity-to-attenuation low-loss formula", abs(float(sig) - 1636 * 0.01 / 3.0) < 1e-9, "0.01 S/m, eps_r 9 -> %.2f dB/m one-way" % sig)
    return res


# ----------------------------------------------------------------------------------------------------------------
# Lateral-shift sweep: frequency and magnitude of displacements
# ----------------------------------------------------------------------------------------------------------------
def exp_shift_sweep(cfg, seed, nblocks, n, boots, log):
    cache = {}
    out = {"rate_per_100m": {}, "magnitude": {}}
    base = dict(A4["geometry"]["straight"])
    for rate in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0):
        g = dict(base); g["shift"] = rate
        r = run_scenario(cfg, "sweep-rate-%s" % rate, dict(geom=g), seed, nblocks, n, boots, log, cache)
        out["rate_per_100m"][str(rate)] = {m: dict(metrics={k: r["models"][m]["metrics"][k] for k in ("sensitivity", "false_clearance", "false_alarm", "unverified")},
                                                   ece=r["models"][m].get("ece"), lateral_error_m=r["models"][m].get("lateral_error_m")) for m in ("continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass")}
    for name, mag in (("small_1_to_2_m", [2, 4]), ("large_3_to_4_m", [6, 8])):
        g = dict(base); g["shift"] = 1.0; g["mag"] = mag
        r = run_scenario(cfg, "sweep-mag-%s" % name, dict(geom=g), seed, nblocks, n, boots, log, cache)
        out["magnitude"][name] = {m: dict(metrics={k: r["models"][m]["metrics"][k] for k in ("sensitivity", "false_clearance", "false_alarm", "unverified")},
                                          ece=r["models"][m].get("ece"), lateral_error_m=r["models"][m].get("lateral_error_m")) for m in ("continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass")}
    return out


# ----------------------------------------------------------------------------------------------------------------
# Structural mismatch: truth generated by a different process than the one the filter assumes
# ----------------------------------------------------------------------------------------------------------------
MISMATCH = [
    ("L0 matched: straight", dict(A4["geometry"]["straight"])),
    ("L1 curved (drift)", dict(A4["geometry"]["curved"])),
    ("L2 spline with abrupt bends", dict(loss=0.2, rebirth=0.05, shift=0.0, drift_per_seg=0.0, spline=dict(max_slope=0.5, leg=[8, 25]))),
    ("L3 bends + parallel utility", dict(loss=0.2, rebirth=0.05, shift=0.0, drift_per_seg=0.0, spline=dict(max_slope=0.5, leg=[8, 25], parallel=True))),
    ("L4 bends + parallel + branch", dict(loss=0.2, rebirth=0.05, shift=0.0, drift_per_seg=0.0, spline=dict(max_slope=0.5, leg=[8, 25], parallel=True, branch=True))),
]


def exp_mismatch(cfg, seed, nblocks, n, boots, log):
    cache = {}
    out = {"levels": []}
    for name, g in MISMATCH:
        r = run_scenario(cfg, "mismatch-" + name, dict(geom=g), seed, nblocks, n, boots, log, cache)
        out["levels"].append({"name": name, "models": {m: dict(metrics={k: r["models"][m]["metrics"][k] for k in ("sensitivity", "false_clearance", "false_alarm", "unverified", "released")},
                                                              ece=r["models"][m].get("ece")) for m in ("fusion", "continuity_1d", "continuity_1d_3rep", "proposed_1pass", "proposed_3pass")}})
    return out


# ----------------------------------------------------------------------------------------------------------------
# Parameter-uncertainty envelope: the true sensor parameters differ from the ones the filter assumes
# ----------------------------------------------------------------------------------------------------------------
def perturbed_cfg(cfg, rng):
    c = copy.deepcopy(cfg)
    mult = np.exp(rng.uniform(np.log(0.25), np.log(4.0), 5))
    for i in range(5):
        c["soil"]["atten_250_db_per_m"][i] = cfg["soil"]["atten_250_db_per_m"][i] * mult[i]
        c["soil"]["em_atten_db_per_m"][i] = cfg["soil"]["em_atten_db_per_m"][i] * mult[i]
    c["gpr"]["threshold_db"] = cfg["gpr"]["threshold_db"] + rng.uniform(-3, 3)
    sh = rng.uniform(-3, 3)
    c["gpr"]["budget_db"] = {k: v + sh for k, v in cfg["gpr"]["budget_db"].items()}
    c["gpr"]["spreading_coef"] = rng.uniform(30.0, 50.0)
    f = rng.uniform(0.5, 1.5)
    c["util"]["em_coupling"] = [None if x is None else min(1.0, x * f) for x in cfg["util"]["em_coupling"]]
    return c, mult


def exp_param_envelope(cfg, seed, ndraw, log):
    cache = {}
    rows = []
    for d in range(ndraw):
        rng = S.rng_for(seed, "v4-envelope", d)
        ct, mult = perturbed_cfg(cfg, rng)
        r = run_scenario(cfg, "envelope-%d" % d, dict(), seed, 2, 40, 20, lambda s: None, cache, cfg_true=ct)
        blind_true, _ = S.blind_table(ct)
        wsh = S.cell_weights(cfg)
        rows.append(dict(draw=d, atten_multipliers=[float(x) for x in mult], true_blind_share=float(wsh[blind_true].sum()),
                         **{m: dict(false_clearance=r["models"][m]["metrics"]["false_clearance"][0], unverified=r["models"][m]["metrics"]["unverified"][0], sensitivity=r["models"][m]["metrics"]["sensitivity"][0])
                            for m in ("fusion", "continuity_1d", "proposed_3pass")}))
        if (d + 1) % 10 == 0:
            log("   envelope draw %d/%d" % (d + 1, ndraw))
    def q(key, m, k):
        v = np.array([r[m][k] for r in rows if r[m][k] is not None and np.isfinite(r[m][k])])
        return [float(np.percentile(v, p)) for p in (5, 50, 95)]
    out = {"n_draws": ndraw, "draws": rows,
           "true_blind_share": [float(np.percentile([r["true_blind_share"] for r in rows], p)) for p in (5, 50, 95)],
           "summary": {m: {k: q(None, m, k) for k in ("false_clearance", "unverified", "sensitivity")} for m in ("fusion", "continuity_1d", "proposed_3pass")},
           "share_proposed_better_than_continuity": float(np.mean([r["proposed_3pass"]["false_clearance"] < r["continuity_1d"]["false_clearance"] for r in rows])),
           "share_proposed_better_than_fusion": float(np.mean([r["proposed_3pass"]["false_clearance"] < r["fusion"]["false_clearance"] for r in rows])),
           "note": "per draw: attenuation of each seen soil multiplied by a log-uniform factor 0.25 to 4, detection threshold +-3 dB, system budget +-3 dB, spreading coefficient 30 to 50, EM coupling x0.5 to 1.5; the filter keeps the nominal parameters"}
    return out


# ----------------------------------------------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------------------------------------------
def reproduce(args):
    t0 = time.time()
    os.makedirs(args.out, exist_ok=True)

    def log(s):
        print(s, flush=True)
    seed = args.seed
    cfg4 = make_cfg4()
    cfg1 = copy.deepcopy(S.CFG)
    nb, n1 = args.blocks, args.n
    nsb, nsn, boots = (3, 40, 60) if args.quick else (5, 100, 300)
    R = {"meta": dict(software="SubSurface_v4.py", version=VERSION, command=" ".join(["python"] + sys.argv), seed=seed, python=sys.version.split()[0], numpy=np.__version__,
                      depends_on="SubSurface_MC.py v1.0.0 (unchanged)", scenario_blocks=nsb, scenario_corridors_per_cell_per_block=nsn, bootstrap_draws=boots,
                      v1_blocks=nb, v1_corridors_per_cell_per_block=n1), "assumptions_v4": A4}
    log("1/8 self-tests (v4)")
    R["selftests"] = selftests_v4(seed)
    log("2/8 scenario matrix (five models; cluster bootstrap)")
    cache = {}
    R["scenarios"] = {}
    for name, sc in SCENARIOS + [("baseline_with_reference_check", dict(guard=True))]:
        R["scenarios"][name] = run_scenario(cfg4, name, sc, seed, nsb, nsn, boots, log, cache)
        R["scenarios"][name]["definition"] = {k: (v if not isinstance(v, np.ndarray) else v.tolist()) for k, v in sc.items()}
    log("2b/8 lateral-shift sweep")
    R["shift_sweep"] = exp_shift_sweep(cfg4, seed, max(3, nsb - 2), max(60, nsn // 2), max(60, boots // 2), log)
    log("2c/8 structural mismatch of the geometry")
    R["geometry_mismatch"] = exp_mismatch(cfg4, seed, max(3, nsb - 2), max(100, nsn), max(100, boots // 2), log)
    log("2d/8 parameter-uncertainty envelope")
    R["parameter_envelope"] = exp_param_envelope(cfg4, seed, 12 if args.quick else 40, log)
    log("3/8 equal-coverage clearance comparison")
    R["equal_coverage"] = exp_equal_coverage(cfg1, seed, nb, n1 // 2 if not args.quick else 30, log)
    cfg1s = copy.deepcopy(cfg1); cfg1s["truth"]["shift_fraction"] = 0.5
    R["equal_coverage_half_shifts"] = exp_equal_coverage(cfg1s, seed, nb, n1 // 2 if not args.quick else 30, log, tag="v4-cover-shift")
    log("4/8 value-of-information pit allocation")
    R["voi"] = {str(h): exp_voi(cfg1, seed, nb, n1 // 2 if not args.quick else 30, log, hold=h) for h in (1000.0, 3000.0, 10000.0)}
    log("5/8 capability zones and depth-resolved rule")
    R["zones"] = zone_table(cfg4)
    R["depth_resolved"] = exp_depth_resolved(cfg1, seed, nb, n1 // 2 if not args.quick else 30, log)
    log("6/8 total cost of ownership")
    base = R["scenarios"]["baseline"]["models"]["proposed_3pass"]["metrics"]
    R["tco"] = exp_tco(1.0 - base["unverified"][0], base["released"][0])
    log("7/8 pilot sample sizes and attenuation-conductivity consistency")
    R["pilot_sample_sizes"] = pilot_sample_sizes()
    soils_eps = {"dry_sand": 4.0, "dry_loam": 8.0, "moist_loam": 15.0, "clay": 25.0, "rubble_fill": 8.0, "wet_clay": 25.0, "saline_fill": 12.0}
    R["attenuation_consistency"] = {s: dict(two_way_db_per_m_at_250MHz=float(cfg4["soil"]["atten_250_db_per_m"][i]), assumed_eps_r=soils_eps[s],
                                            implied_conductivity_mS_per_m=float(1000.0 * cfg4["soil"]["atten_250_db_per_m"][i] / 2.0 * np.sqrt(soils_eps[s]) / 1636.0))
                                    for i, s in enumerate(SOILS4)}
    # external plausibility of the assumed attenuation (published ranges as tabulated by the US EPA Environmental Geophysics pages; no primary citation is given there, the frequency is not stated)
    R["external_plausibility"] = dict(
        source="US EPA Environmental Geophysics, ground-penetrating radar page, Table 1 (https://archive.epa.gov/esd/archive-geophysics/web/html/ground-penetrating_radar.html)",
        published={"dry_sand": dict(conductivity_mS_per_m=[0.01, 0.01], attenuation_db_per_m=[0.01, 0.01]), "wet_sand": dict(conductivity_mS_per_m=[0.1, 1], attenuation_db_per_m=[0.03, 0.3]),
                   "clays": dict(conductivity_mS_per_m=[2, 1000], attenuation_db_per_m=[1, 300]), "shales": dict(conductivity_mS_per_m=[1, 100], attenuation_db_per_m=[1, 100])},
        worked_example=dict(conductivity_mS_per_m=100, eps_r=20, published_attenuation_db_per_m=38.0, low_loss_formula_db_per_m=float(attenuation_from_conductivity(0.1, 20.0))),
        assumed_one_way_db_per_m_at_250MHz={SOILS4[i]: cfg4["soil"]["atten_250_db_per_m"][i] / 2.0 for i in range(NS4)},
        note="the assumed attenuation lumps absorption, scattering and clutter and is not a measured detection curve; no published detection-versus-depth dataset was reproduced")
    R["meta"]["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(args.out, "results_v4.json"), "w", encoding="utf-8") as fh:
        json.dump(S.jsonable(R), fh, indent=1)
    log("results_v4.json written (%.1f s)" % (time.time() - t0))
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--reproduce", action="store_true")
    ap.add_argument("--out", default="results_v4")
    ap.add_argument("--n", type=int, default=400, help="corridors per cell per block for the v1.0.0-world experiments")
    ap.add_argument("--blocks", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.quick:
        a.blocks, a.n = 3, 60
    if a.demo:
        r = selftests_v4(a.seed)
        print("%d of %d self-tests passed" % (sum(x["passed"] for x in r), len(r)))
        sys.exit(0 if all(x["passed"] for x in r) else 1)
    if a.reproduce:
        reproduce(a)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
