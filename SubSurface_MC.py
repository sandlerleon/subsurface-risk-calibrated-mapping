# -*- coding: utf-8 -*-
"""
SubSurface_MC.py - risk-calibrated fusion of ground-penetrating radar (GPR), electromagnetic (EM) locator and
anchor knowledge for underground utility mapping: a seeded Monte Carlo study.

EVERYTHING HERE IS A SIMULATION UNDER STATED ASSUMPTIONS. No field data are used and no result in this file is a
measurement. The parameters in CFG are an assumptions register to be calibrated against ground truth.

Usage
  python SubSurface_MC.py --demo                       closed-form versus Monte Carlo self-tests (fast)
  python SubSurface_MC.py --grid-size                  the 1,470-configuration closed-form reference grid
  python SubSurface_MC.py --reproduce --out out --n 500 --blocks 10 --seed 42
                                                       every table, figure and results.json of the paper
  python SubSurface_MC.py --reproduce --quick          small run (smoke test, ~1 minute)

Design: one corridor = one utility of one type buried at one depth in one soil, tracked along 100 segments of 5 m.
Truth is a Markov process (on the tracked alignment / lost / laterally shifted). Each segment is observed by two GPR
bands (250 and 600 MHz) and an EM locator through a thresholded signal-to-noise model with run-level (shared) and
segment-level noise. A Bayesian filter anchored at a known manhole carries a belief along the corridor; cells where the
expected fused detection probability at the class mid-depth is below 0.3 are reported as "unverified".
"""
import argparse
import copy
import hashlib
import json
import os
import platform
import sys
import time
import zlib

import numpy as np
import scipy
from scipy.special import ndtr, ndtri
from scipy.stats import multivariate_normal
from scipy.stats import t as student_t

VERSION = "1.0.0"
LIK_FLOOR = 1e-3   # model-error floor on the probability of a non-detection / detection in the filter

SOILS = ["dry_sand", "dry_loam", "moist_loam", "clay", "rubble_fill"]
UTILS = ["pe_water", "ci_water", "plastic_sewer", "concrete_sewer", "power", "telephone", "fibre"]
NS, NU = len(SOILS), len(UTILS)
UTIL_LABEL = {"pe_water": "PE/PVC water", "ci_water": "Cast-iron water", "plastic_sewer": "Plastic sewer",
              "concrete_sewer": "Concrete sewer", "power": "Power duct", "telephone": "Telephone duct", "fibre": "Dielectric fibre"}
SOIL_LABEL = {"dry_sand": "Dry sand", "dry_loam": "Dry loam", "moist_loam": "Moist loam", "clay": "Clay", "rubble_fill": "Rubble fill"}

# ----------------------------------------------------------------------------------------------------------------
# Assumptions register (all values are assumptions; see README and the manuscript, Table 1)
# ----------------------------------------------------------------------------------------------------------------
CFG = {
    "gpr": {
        "threshold_db": 8.0,                    # detection threshold on SNR
        "sigma_run_db": 3.0,                    # run-level noise, shared along a corridor
        "band_correlation": 0.7,                # correlation of run- and segment-level noise between the two bands
        "budget_db": {"250": 70.0, "600": 74.0},
        "freq_mhz": {"250": 250.0, "600": 600.0},
        "freq_exponent": 0.5,                   # attenuation scales as (f/250)^0.5
        "spreading_coef": 40.0,                 # spreading loss = coef * log10(max(2 d, 1)), d in m
    },
    "soil": {                                   # order: SOILS
        "atten_250_db_per_m": [1.5, 4.0, 8.0, 14.0, 6.0],
        "sigma_seg_db": [4.0, 4.5, 5.0, 6.0, 7.0],
        "clutter_pfa": [0.010, 0.015, 0.020, 0.030, 0.060],
        "em_atten_db_per_m": [0.5, 1.0, 2.0, 3.5, 1.5],
    },
    "util": {                                   # order: UTILS
        "reflectivity_db": [-12.0, 0.0, -8.0, -6.0, -4.0, -10.0, -14.0],
        "em_coupling": [0.08, 0.60, 0.05, 0.02, None, 0.35, 0.12],  # power duct: see power_*
        "depth_m": [[1.0, 2.0], [1.0, 2.0], [3.0, 7.0], [3.0, 7.0], [0.5, 2.0], [0.6, 1.0], [1.0, 2.0]],
        "share": [0.16, 0.04, 0.10, 0.10, 0.20, 0.20, 0.20],
        "consequence": [4.0, 6.0, 3.0, 3.0, 10.0, 2.0, 2.0],   # relative cost of a strike (assumed)
    },
    "power_energised_share": 0.5,
    "power_coupling_live": 0.85,
    "power_coupling_dead": 0.25,
    "em": {"budget_db": 55.0, "threshold_db": 8.0, "sigma_seg_db": 5.0, "pfa": 0.01, "spreading_coef": 40.0},
    "truth": {
        "hazard_per_100m": 0.2,                 # utility leaves the tracked alignment
        "rebirth_per_100m": 0.05,               # utility returns to the alignment
        "shift_fraction": 0.0,                  # share of losses that are lateral shifts (utility still physically near)
        "off_alignment_penalty_db": 6.0,
        "anchor_true_reliability": 1.0,         # probability the anchor really is on the alignment
        "segment_m": 5.0,
        "n_segments": 100,
    },
    "filter": {
        "hazard_per_100m": 0.2,                 # filter's assumed values (matched by default)
        "rebirth_per_100m": 0.05,
        "anchor_reliability": 1.0,              # start belief b(0)
        "present_threshold": 0.5,
        "unverified_pd_threshold": 0.3,
        "rescan_band": [0.15, 0.85],
    },
    "shadow_db": {"pe_water": 3.0, "ci_water": 10.0},
    "positioning": {"rtk_m": 0.05, "standalone_m": 3.0, "pick_base_m": 0.10, "pick_per_m": 0.05,
                    "velocity_rel": 0.10, "depth_pick_m": 0.05},
    "pit": {"base": 1.0, "per_m_depth": 0.5},
}
T975 = {n: float(student_t.ppf(0.975, n - 1)) for n in range(2, 41)}


def seg_rates(cfg):
    L = cfg["truth"]["segment_m"]
    return cfg["truth"]["hazard_per_100m"] * L / 100.0, cfg["truth"]["rebirth_per_100m"] * L / 100.0


def filt_rates(cfg):
    L = cfg["truth"]["segment_m"]
    return cfg["filter"]["hazard_per_100m"] * L / 100.0, cfg["filter"]["rebirth_per_100m"] * L / 100.0


def em_coupling_eff(cfg):
    c = [x for x in cfg["util"]["em_coupling"]]
    pw = UTILS.index("power")
    c[pw] = cfg["power_energised_share"] * cfg["power_coupling_live"] + (1 - cfg["power_energised_share"]) * cfg["power_coupling_dead"]
    return np.array(c, float)


def mid_depth(cfg):
    return np.array([0.5 * (a + b) for a, b in cfg["util"]["depth_m"]])


# ----------------------------------------------------------------------------------------------------------------
# Closed-form detection probabilities (signal only; clutter handled separately)
# ----------------------------------------------------------------------------------------------------------------
def gpr_margin(cfg, soil, util, depth, band, loss_db=0.0):
    """mean SNR minus threshold (dB) for one band"""
    g = cfg["gpr"]
    att = np.asarray(cfg["soil"]["atten_250_db_per_m"])[soil] * (g["freq_mhz"][band] / 250.0) ** g["freq_exponent"]
    refl = np.asarray(cfg["util"]["reflectivity_db"])[util]
    spread = g["spreading_coef"] * np.log10(np.maximum(2.0 * np.asarray(depth, float), 1.0))
    return g["budget_db"][band] + refl - att * depth - spread - loss_db - g["threshold_db"]


def gpr_sigma_total(cfg, soil):
    return np.sqrt(cfg["gpr"]["sigma_run_db"] ** 2 + np.asarray(cfg["soil"]["sigma_seg_db"])[soil] ** 2)


def pd_gpr(cfg, soil, util, depth, band, loss_db=0.0):
    return ndtr(gpr_margin(cfg, soil, util, depth, band, loss_db) / gpr_sigma_total(cfg, soil))


def bvn_cdf(x, y, rho):
    """P(X <= x, Y <= y) for standard bivariate normal with correlation rho (arrays allowed)"""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    pts = np.clip(np.column_stack([x.ravel(), y.ravel()]), -8.0, 8.0)
    mv = multivariate_normal(mean=[0.0, 0.0], cov=[[1.0, rho], [rho, 1.0]])
    return np.atleast_1d(mv.cdf(pts)).reshape(x.shape)


def pd_gpr_joint(cfg, soil, util, depth, loss_db=0.0):
    """joint signal-detection table for the two bands: returns (p11, p10, p01, p00) for scalars/arrays"""
    m1 = gpr_margin(cfg, soil, util, depth, "250", loss_db) / gpr_sigma_total(cfg, soil)
    m2 = gpr_margin(cfg, soil, util, depth, "600", loss_db) / gpr_sigma_total(cfg, soil)
    rho = cfg["gpr"]["band_correlation"]
    p1, p2 = ndtr(m1), ndtr(m2)
    p00 = bvn_cdf(-m1, -m2, rho)
    p11 = p1 + p2 - 1.0 + p00
    return p11, p1 - p11, p2 - p11, p00


def pd_gpr_any(cfg, soil, util, depth, loss_db=0.0):
    return 1.0 - pd_gpr_joint(cfg, soil, util, depth, loss_db)[3]


def pd_em_signal(cfg, soil, util, depth, loss_db=0.0):
    """P(SNR > threshold | utility is coupled to the locator)"""
    e = cfg["em"]
    att = np.asarray(cfg["soil"]["em_atten_db_per_m"])[soil]
    margin = e["budget_db"] - e["spreading_coef"] * np.log10(1.0 + np.asarray(depth, float)) - att * depth - loss_db - e["threshold_db"]
    return ndtr(margin / e["sigma_seg_db"])


def pd_em(cfg, soil, util, depth, loss_db=0.0):
    """signal detection probability including the coupling probability of the utility"""
    return em_coupling_eff(cfg)[util] * pd_em_signal(cfg, soil, util, depth, loss_db)


def pd_fused(cfg, soil, util, depth, loss_db=0.0, gpr="dual", em=True, shadow_db=0.0):
    """closed-form probability that at least one sensor produces a true signal detection (GPR and EM independent)"""
    loss = loss_db + shadow_db
    if gpr == "dual":
        miss = 1.0 - pd_gpr_any(cfg, soil, util, depth, loss)
    elif gpr in ("250", "600"):
        miss = 1.0 - pd_gpr(cfg, soil, util, depth, gpr, loss)
    else:
        miss = 1.0
    if em:
        miss = miss * (1.0 - pd_em(cfg, soil, util, depth, loss))
    return 1.0 - miss


def blind_table(cfg):
    """(NS, NU) boolean: sensor-blind cell (fused signal Pd at class mid-depth below threshold), and the Pd table"""
    md = mid_depth(cfg)
    pd = np.array([[pd_fused(cfg, s, u, md[u]) for u in range(NU)] for s in range(NS)])
    return pd < cfg["filter"]["unverified_pd_threshold"], pd


def cell_weights(cfg):
    sh = np.array(cfg["util"]["share"], float)
    return np.tile(sh / sh.sum() / NS, (NS, 1))   # (NS, NU), sums to 1


# ----------------------------------------------------------------------------------------------------------------
# Random numbers
# ----------------------------------------------------------------------------------------------------------------
def rng_for(seed, tag, block=0):
    return np.random.default_rng(np.random.SeedSequence([int(seed), zlib.crc32(tag.encode()), int(block)]))


# ----------------------------------------------------------------------------------------------------------------
# Simulation of corridors
# ----------------------------------------------------------------------------------------------------------------
def make_block(rng, cfg, n_per_cell, shadow=None, fixed_depth=None):
    """cell-major corridors: corridor i belongs to cell i // n_per_cell, cell = soil*NU + util"""
    K = cfg["truth"]["n_segments"]
    ncell = NS * NU
    N = ncell * n_per_cell
    cell = np.repeat(np.arange(ncell), n_per_cell)
    soil, util = cell // NU, cell % NU
    dr = np.array(cfg["util"]["depth_m"], float)
    depth = dr[util, 0] + (dr[util, 1] - dr[util, 0]) * rng.random(N) if fixed_depth is None else np.full(N, float(fixed_depth))
    h, r = seg_rates(cfg)
    phi = cfg["truth"]["shift_fraction"]
    state = np.empty((N, K), np.uint8)
    s = (rng.random(N) < cfg["truth"]["anchor_true_reliability"]).astype(np.uint8)
    state[:, 0] = s
    for k in range(1, K):
        u = rng.random(N); v = rng.random(N)
        on = s == 1
        lose = on & (u < h)
        shift = lose & (v < phi)
        regain = (~on) & (u < r)
        s = np.where(lose, np.where(shift, 2, 0), np.where(regain, 1, s)).astype(np.uint8)
        state[:, k] = s
    cc = em_coupling_eff(cfg)[util]
    coupled = rng.random(N) < cc
    B = dict(N=N, K=K, n=n_per_cell, cell=cell, soil=soil, util=util, depth=depth, state=state, coupled=coupled,
             shadow=np.zeros(N) if shadow is None else np.asarray(shadow, float))
    return B


def observe(rng, B, cfg, prev=None, rho_pass=1.0, rho_ge=0.0, fail=None):
    """detections of the two GPR bands and the EM locator.
    prev: dict from an earlier call (run-level noise reused with correlation rho_pass for a repeat pass)
    rho_ge: correlation between the standardised segment noise of GPR-250 and EM (correlated-failure stress test)
    fail: dict with per-corridor boolean arrays 'gpr' / 'em' (sensor dead: only clutter is returned)"""
    N, K = B["N"], B["K"]
    g, e = cfg["gpr"], cfg["em"]
    rho = g["band_correlation"]
    soil, util, depth = B["soil"], B["util"], B["depth"]
    zr1 = rng.standard_normal(N); zr2 = rho * zr1 + np.sqrt(1 - rho ** 2) * rng.standard_normal(N)
    if prev is not None and rho_pass < 1.0:
        a = np.sqrt(1 - rho_pass ** 2)
        zr1 = rho_pass * prev["zr1"] + a * zr1
        zr2 = rho_pass * prev["zr2"] + a * zr2
    elif prev is not None:
        zr1, zr2 = prev["zr1"], prev["zr2"]
    e1 = rng.standard_normal((N, K)); e2 = rho * e1 + np.sqrt(1 - rho ** 2) * rng.standard_normal((N, K))
    ee = rng.standard_normal((N, K))
    if rho_ge > 0:
        ee = rho_ge * e1 + np.sqrt(1 - rho_ge ** 2) * ee
    sseg = np.asarray(cfg["soil"]["sigma_seg_db"])[soil][:, None]
    pen = cfg["truth"]["off_alignment_penalty_db"]
    st = B["state"]
    loss = B["shadow"][:, None] + pen * (st == 2)
    out = {}
    sig = {}
    for band, zr, ez in (("250", zr1, e1), ("600", zr2, e2)):
        mean_snr = gpr_margin(cfg, soil, util, depth, band) + g["threshold_db"]
        snr = mean_snr[:, None] - loss + g["sigma_run_db"] * zr[:, None] + sseg * ez
        sig[band] = (snr > g["threshold_db"]) & (st > 0)
    em_mean = e["budget_db"] - e["spreading_coef"] * np.log10(1.0 + depth) - np.asarray(cfg["soil"]["em_atten_db_per_m"])[soil] * depth
    snr_em = em_mean[:, None] - loss + e["sigma_seg_db"] * ee
    sig["em"] = (snr_em > e["threshold_db"]) & (st > 0) & B["coupled"][:, None]
    if fail is not None:
        for key, bands in (("gpr", ("250", "600")), ("em", ("em",))):
            if key in fail and fail[key] is not None:
                for b in bands:
                    sig[b] = sig[b] & ~fail[key][:, None]
    pfa_g = np.asarray(cfg["soil"]["clutter_pfa"])[soil][:, None]
    out["d250"] = sig["250"] | (rng.random((N, K)) < pfa_g)
    out["d600"] = sig["600"] | (rng.random((N, K)) < pfa_g)
    out["dem"] = sig["em"] | (rng.random((N, K)) < e["pfa"])
    out["zr1"], out["zr2"] = zr1, zr2
    out["sig"] = sig
    return out


# ----------------------------------------------------------------------------------------------------------------
# Likelihood tables used by the filter (what the "field software" would use)
# ----------------------------------------------------------------------------------------------------------------
def lr_tables(cfg, B, mode="matched", depth_mode="class", shadow_known=False):
    """per-corridor log-likelihood ratios for detection (ld) and non-detection (ln) of the three sensors and the joint
    GPR table; 'matched' uses the true soil, 'generic' averages the soils; depth 'class' uses the class mid-depth,
    'true' the corridor depth."""
    soil, util = B["soil"], B["util"]
    N = B["N"]
    md = mid_depth(cfg)
    depth = md[util] if depth_mode == "class" else B["depth"]
    loss = B["shadow"] if shadow_known else np.zeros(N)
    pfa_s = np.asarray(cfg["soil"]["clutter_pfa"])

    def tot(p, pfa):
        # total detection probability (signal or clutter), floored so that a non-detection never has zero likelihood
        return np.minimum(p + (1 - p) * pfa, 1.0 - LIK_FLOOR)

    dr = np.array(cfg["util"]["depth_m"], float)

    def table(sidx):
        if depth_mode == "marginal":      # average over the class depth range (unknown depth, uniform prior)
            ng = 9
            acc3 = [0.0, 0.0, 0.0]
            for gi in range(ng):
                d = dr[util, 0] + (dr[util, 1] - dr[util, 0]) * (gi + 0.5) / ng
                acc3[0] = acc3[0] + pd_gpr(cfg, sidx, util, d, "250", loss) / ng
                acc3[1] = acc3[1] + pd_gpr(cfg, sidx, util, d, "600", loss) / ng
                acc3[2] = acc3[2] + pd_em(cfg, sidx, util, d, loss) / ng
            return tuple(acc3)
        d = depth
        pg1 = pd_gpr(cfg, sidx, util, d, "250", loss)
        pg2 = pd_gpr(cfg, sidx, util, d, "600", loss)
        pe = pd_em(cfg, sidx, util, d, loss)
        return pg1, pg2, pe

    if mode == "generic":
        acc = [np.zeros(N), np.zeros(N), np.zeros(N)]
        for s in range(NS):
            t = table(np.full(N, s))
            for i in range(3):
                acc[i] += t[i] / NS
        pg1, pg2, pe = acc
        pfg = np.full(N, pfa_s.mean())
    else:
        pg1, pg2, pe = table(soil)
        pfg = pfa_s[soil]
    pfe = np.full(N, cfg["em"]["pfa"])
    L = {}
    for name, p, pf in (("g250", pg1, pfg), ("g600", pg2, pfg), ("em", pe, pfe)):
        pt = tot(p, pf)
        L[name] = (np.log(pt / pf), np.log((1 - pt) / (1 - pf)))
    # joint GPR table on (d250, d600) in {00,01,10,11} (order index = 2*d250 + d600)
    if depth_mode == "class" and mode == "matched":
        j = np.zeros((N, 4))
        for s in range(NS):
            for u in range(NU):
                m = (soil == s) & (util == u)
                if not m.any():
                    continue
                p11, p10, p01, p00 = [float(np.ravel(x)[0]) for x in pd_gpr_joint(cfg, s, u, md[u], 0.0)]
                pf = pfa_s[s]
                sig = {(1, 1): p11, (1, 0): p10, (0, 1): p01, (0, 0): p00}
                tab = np.zeros(4); tab0 = np.zeros(4)
                for o1 in (0, 1):
                    for o2 in (0, 1):
                        pr = 0.0
                        for (s1, s2), ps in sig.items():
                            a = float(o1) if s1 else (pf if o1 else 1 - pf)   # observed = signal OR clutter
                            b = float(o2) if s2 else (pf if o2 else 1 - pf)
                            pr += ps * a * b
                        tab[2 * o1 + o2] = pr
                        tab0[2 * o1 + o2] = (pf if o1 else 1 - pf) * (pf if o2 else 1 - pf)
                tab = np.maximum(tab, LIK_FLOOR * 0.1)
                j[m] = np.log(tab / tab0)
        L["gj"] = j
    return L


def logit(p):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def llr_step(L, obs, k, use, temper=1.0, joint=False):
    tot = 0.0
    if joint and ("g250" in use or "g600" in use):
        idx = 2 * obs["d250"][:, k].astype(int) + obs["d600"][:, k].astype(int)
        tot = tot + L["gj"][np.arange(len(idx)), idx] * temper
        names = [u for u in use if u == "em"]
    else:
        names = list(use)
    key = {"g250": "d250", "g600": "d600", "em": "dem"}
    for nme in names:
        d = obs[key[nme]][:, k]
        tot = tot + np.where(d, L[nme][0], L[nme][1]) * temper
    return tot


def run_filter(obs, L, cfg, use=("g250", "g600", "em"), b0=None, joint=False, temper=1.0, hazard=None, rebirth=None,
               mask=None, obs2=None, avail2=None, L2=None, shift_aware=False):
    """Bayesian filter along the corridor: predict (survival h, re-birth r) then odds update with detect/no-detect likelihood
    ratios.  mask (N,K) False = no observation at that segment.  obs2/avail2: optional repeat pass for uncertain segments."""
    N, K = obs["d250"].shape
    h, r = filt_rates(cfg)
    if hazard is not None:
        h = hazard * cfg["truth"]["segment_m"] / 100.0
    if rebirth is not None:
        r = rebirth * cfg["truth"]["segment_m"] / 100.0
    b = np.full(N, cfg["filter"]["anchor_reliability"] if b0 is None else b0)
    P = np.empty((N, K))
    nres = np.zeros(N)
    lo, hi = cfg["filter"]["rescan_band"]
    for k in range(K):
        if k > 0:
            b = b * (1 - h) + (1 - b) * r
        lo_ = logit(b) + llr_step(L, obs, k, use, temper, joint)
        if mask is not None:
            lo_ = np.where(mask[:, k], lo_, logit(b))
        b = sigmoid(lo_)
        if obs2 is not None:
            trig = (b > lo) & (b < hi) & avail2[:, k]
            if trig.any():
                lo2 = logit(b) + llr_step(L2 if L2 is not None else L, obs2, k, use, temper, False)
                b = np.where(trig, sigmoid(lo2), b)
                nres += trig
        P[:, k] = b
    return (P, nres) if obs2 is not None else P


def persegment(obs, L, use, prior, temper=1.0, joint=False):
    N, K = obs["d250"].shape
    P = np.empty((N, K))
    lp = logit(prior) if np.ndim(prior) == 0 else logit(prior)
    for k in range(K):
        P[:, k] = sigmoid(lp + llr_step(L, obs, k, use, temper, joint))
    return P


# ----------------------------------------------------------------------------------------------------------------
# Metrics
# ----------------------------------------------------------------------------------------------------------------
def cell_fracs(call, truth, ncell):
    """(ncell, 4) fractions [tp, fn, fp, tn] of each cell's segments (cell-major layout)"""
    N, K = call.shape
    n = N // ncell
    c = call.reshape(ncell, n * K); t = truth.reshape(ncell, n * K)
    return np.stack([(c & t).mean(1), (~c & t).mean(1), (c & ~t).mean(1), (~c & ~t).mean(1)], axis=1)


def mix(F, w):
    """weighted mixture of cell fractions F (ncell, 4) with weights w (ncell); returns metric dict"""
    w = np.asarray(w, float)
    if w.sum() <= 0:
        return dict(acc=np.nan, miss=np.nan, fa=np.nan, prev=np.nan, bacc=np.nan, tp=np.nan, fn=np.nan, fp=np.nan, tn=np.nan)
    w = w / w.sum()
    tp, fn, fp, tn = (w[:, None] * F).sum(0)
    miss = fn / (tp + fn) if tp + fn > 0 else np.nan
    fa = fp / (fp + tn) if fp + tn > 0 else np.nan
    return dict(acc=tp + tn, miss=miss, fa=fa, prev=tp + fn, bacc=0.5 * ((1 - miss) + (1 - fa)), tp=tp, fn=fn, fp=fp, tn=tn)


def ci_stats(vals):
    v = np.asarray(vals, float)
    n = len(v)
    m = float(np.nanmean(v))
    if n < 2:
        return m, float("nan")
    sd = float(np.nanstd(v, ddof=1))
    return m, T975.get(n, 1.96) * sd / np.sqrt(n)


def summarise(blocks, keys=None):
    """list of metric dicts -> {key: [mean, halfwidth]}"""
    keys = keys or list(blocks[0].keys())
    return {k: list(ci_stats([b[k] for b in blocks])) for k in keys}


def views(cfg):
    blind, pdtab = blind_table(cfg)
    w = cell_weights(cfg).ravel()
    bl = blind.ravel()
    return dict(all=w, visible=w * ~bl, blind=w * bl), bl, pdtab


def calib_stats(P, Y, wc, nb=10, bl=None):
    """weighted reliability statistics. P, Y (N,K); wc (N,) corridor weights summing to 1. returns bin arrays, ECE, Brier"""
    N, K = P.shape
    w = np.repeat(wc / K, K)
    p = P.ravel(); y = Y.ravel().astype(float)
    b = np.minimum((p * nb).astype(int), nb - 1)
    cnt = np.bincount(b, weights=w, minlength=nb)
    sp = np.bincount(b, weights=w * p, minlength=nb)
    sy = np.bincount(b, weights=w * y, minlength=nb)
    with np.errstate(invalid="ignore", divide="ignore"):
        mp, my = sp / cnt, sy / cnt
    ece = float(np.nansum(cnt * np.abs(mp - my)) / cnt.sum())
    brier = float(np.sum(w * (p - y) ** 2) / w.sum())
    return dict(count=cnt, mean_p=mp, mean_y=my, ece=ece, brier=brier)


def corr_weights(B, wcell):
    return np.repeat(np.asarray(wcell, float) / B["n"], B["n"])


# ----------------------------------------------------------------------------------------------------------------
# Position-error model (closed form)
# ----------------------------------------------------------------------------------------------------------------
def position_probs(cfg, depth, gnss_m, tol_h=1.0, tol_d=0.5):
    p = cfg["positioning"]
    pick = p["pick_base_m"] + p["pick_per_m"] * np.asarray(depth, float)
    s2 = gnss_m ** 2 + pick ** 2
    ph = 1.0 - np.exp(-tol_h ** 2 / (2 * s2))
    sd = np.sqrt((p["velocity_rel"] * np.asarray(depth, float)) ** 2 + p["depth_pick_m"] ** 2)
    pdp = 2 * ndtr(tol_d / sd) - 1.0
    return ph, pdp


# ----------------------------------------------------------------------------------------------------------------
# Self-tests
# ----------------------------------------------------------------------------------------------------------------
def selftests(cfg, seed=42, verbose=True):
    res = []

    def rec(name, ok, detail):
        res.append(dict(name=name, passed=bool(ok), detail=detail))
        if verbose:
            print("  [%s] %s: %s" % ("PASS" if ok else "FAIL", name, detail))

    rng = rng_for(seed, "selftest")
    # 1-3: closed-form detection versus Monte Carlo (signal only, no clutter, one cell)
    cases = [(2, 3, 3.5), (1, 3, 3.0), (0, 0, 1.5), (3, 1, 1.5), (4, 4, 1.0)]
    for s, u, d in cases:
        n = 400000
        rho = cfg["gpr"]["band_correlation"]
        zr1 = rng.standard_normal(n); zr2 = rho * zr1 + np.sqrt(1 - rho ** 2) * rng.standard_normal(n)
        e1 = rng.standard_normal(n); e2 = rho * e1 + np.sqrt(1 - rho ** 2) * rng.standard_normal(n)
        sg = cfg["soil"]["sigma_seg_db"][s]; sr = cfg["gpr"]["sigma_run_db"]
        m1 = gpr_margin(cfg, s, u, d, "250"); m2 = gpr_margin(cfg, s, u, d, "600")
        s1 = m1 + sr * zr1 + sg * e1 > 0
        s2 = m2 + sr * zr2 + sg * e2 > 0
        a1 = float(pd_gpr(cfg, s, u, d, "250")); mc1 = s1.mean(); se1 = np.sqrt(mc1 * (1 - mc1) / n) + 1e-12
        rec("GPR-250 Pd %s/%s at %.1f m" % (SOILS[s], UTILS[u], d), abs(a1 - mc1) < 4 * se1 + 1e-4, "closed form %.4f, Monte Carlo %.4f (SE %.4f)" % (a1, mc1, se1))
        anyc = float(pd_gpr_any(cfg, s, u, d)); mca = (s1 | s2).mean(); sea = np.sqrt(mca * (1 - mca) / n) + 1e-12
        rec("dual-band bivariate Pd %s/%s at %.1f m" % (SOILS[s], UTILS[u], d), abs(anyc - mca) < 4 * sea + 1e-4, "closed form %.4f, Monte Carlo %.4f (SE %.4f)" % (anyc, mca, sea))
        cp = em_coupling_eff(cfg)[u]
        em_mean = cfg["em"]["budget_db"] - cfg["em"]["spreading_coef"] * np.log10(1 + d) - cfg["soil"]["em_atten_db_per_m"][s] * d
        se_ = (em_mean + cfg["em"]["sigma_seg_db"] * rng.standard_normal(n) > cfg["em"]["threshold_db"]) & (rng.random(n) < cp)
        ae = float(pd_em(cfg, s, u, d)); mce = se_.mean(); see = np.sqrt(mce * (1 - mce) / n) + 1e-12
        rec("EM Pd with coupling %s/%s at %.1f m" % (SOILS[s], UTILS[u], d), abs(ae - mce) < 4 * see + 1e-4, "closed form %.4f, Monte Carlo %.4f (SE %.4f)" % (ae, mce, see))
    # 4: engine marginal detection in simulate/observe equals closed form (signal), through the actual code path
    c2 = copy.deepcopy(cfg)
    B = make_block(rng, c2, 300)
    o = observe(rng, B, c2)
    cell = 2 * NU + 3
    m = B["cell"] == cell
    d_ = B["depth"][m]
    ana = float(np.mean(pd_gpr(c2, 2, 3, d_, "250")))
    mc = float((o["sig"]["250"][m] & (B["state"][m] > 0)).sum() / (B["state"][m] > 0).sum())
    rec("engine versus closed form (moist loam, concrete sewer, depth-averaged)", abs(ana - mc) < 0.02, "closed form %.4f, engine %.4f" % (ana, mc))
    # 5: Markov chain persistence and mean presence
    c3 = copy.deepcopy(cfg)
    h, r = seg_rates(c3)
    B = make_block(rng_for(seed, "selftest-markov"), c3, 2000)
    st = (B["state"] == 1)
    pres_mc = st[:, :60].mean()
    pi = r / (h + r); k = np.arange(60)
    pres_an = float(np.mean(pi + (1 - pi) * (1 - h - r) ** k))
    se = np.sqrt(pres_an * (1 - pres_an) / (st.shape[0] * 4))
    rec("mean presence over 60 segments (hazard and re-birth)", abs(pres_mc - pres_an) < 4 * se + 0.005, "analytic %.4f, Monte Carlo %.4f" % (pres_an, pres_mc))
    c3["truth"]["rebirth_per_100m"] = 0.0
    B = make_block(rng_for(seed, "selftest-surv"), c3, 2000)
    surv_mc = (B["state"][:, 59] == 1).mean(); surv_an = (1 - h) ** 59
    rec("persistence P(on at segment 59 | on at 0), no re-birth", abs(surv_mc - surv_an) < 4 * np.sqrt(surv_an * (1 - surv_an) / B["N"]) + 0.003, "analytic %.4f, Monte Carlo %.4f" % (surv_an, surv_mc))
    # 6: filter equals the cumulative likelihood-ratio posterior when h = r = 0
    c4 = copy.deepcopy(cfg)
    B = make_block(rng_for(seed, "selftest-filter"), c4, 20)
    ob = observe(rng_for(seed, "selftest-filter-obs"), B, c4)
    L = lr_tables(c4, B)
    ob6 = {k: v[:, :6] for k, v in ob.items() if k in ("d250", "d600", "dem")}
    Pf = run_filter(ob6, L, c4, hazard=0.0, rebirth=0.0, b0=0.5)
    lo = np.zeros(B["N"]); worst = np.zeros(B["N"])
    for kk in range(6):
        lo = lo + llr_step(L, ob6, kk, ("g250", "g600", "em"))
        worst = np.maximum(worst, np.abs(lo))
    ok_ = worst < 15.0     # beyond |logit| ~ 20 the filter deliberately saturates (belief clipped to [1e-9, 1-1e-9])
    dif = float(np.max(np.abs(Pf[ok_, -1] - sigmoid(lo[ok_]))))
    rec("filter with h=r=0 and flat start equals cumulative likelihood ratio (6 segments, unsaturated corridors)", dif < 1e-9, "%d corridors, max abs diff %.2e" % (int(ok_.sum()), dif))
    # 7: belief bounds and monotone response
    Pa = run_filter(ob, L, c4)
    rec("belief stays in [0,1] and is finite", bool(np.isfinite(Pa).all() and Pa.min() >= 0 and Pa.max() <= 1), "range %.2e to %.6f" % (Pa.min(), Pa.max()))
    # 8: position-error closed form versus sampling
    rng2 = rng_for(seed, "selftest-pos")
    for d, g in ((5.0, cfg["positioning"]["rtk_m"]), (7.0, cfg["positioning"]["rtk_m"]), (3.5, cfg["positioning"]["standalone_m"])):
        ph, pdp = position_probs(cfg, d, g)
        p = cfg["positioning"]; pick = p["pick_base_m"] + p["pick_per_m"] * d
        sh = np.sqrt(g ** 2 + pick ** 2); n = 400000
        x = sh * rng2.standard_normal(n); y = sh * rng2.standard_normal(n)
        phm = float((np.hypot(x, y) <= 1.0).mean())
        sd = np.sqrt((p["velocity_rel"] * d) ** 2 + p["depth_pick_m"] ** 2)
        pdm = float((np.abs(sd * rng2.standard_normal(n)) <= 0.5).mean())
        rec("position error closed form at %.1f m, GNSS %.2f m" % (d, g), abs(ph - phm) < 0.004 and abs(pdp - pdm) < 0.004, "horizontal %.4f vs %.4f, depth %.4f vs %.4f" % (ph, phm, pdp, pdm))
    # 9: metric bookkeeping: fractions sum to one; weights sum to one
    call = ob["dem"]; truth = B["state"] == 1
    F = cell_fracs(call, truth, NS * NU)
    rec("confusion fractions sum to one in every cell", bool(np.allclose(F.sum(1), 1.0)), "max deviation %.1e" % float(np.max(np.abs(F.sum(1) - 1))))
    rec("cell weights sum to one", abs(cell_weights(cfg).sum() - 1) < 1e-12, "sum %.12f" % cell_weights(cfg).sum())
    # 10: determinism
    ra = observe(rng_for(seed, "det"), make_block(rng_for(seed, "det-b"), cfg, 5), cfg)["dem"]
    rb = observe(rng_for(seed, "det"), make_block(rng_for(seed, "det-b"), cfg, 5), cfg)["dem"]
    rec("same seed gives identical simulation", bool(np.array_equal(ra, rb)), "arrays equal")
    # 11: grid size
    rec("reference grid has 1,470 configurations", grid_size() == 1470, "%d" % grid_size())
    return res


# ----------------------------------------------------------------------------------------------------------------
# Closed-form reference grid
# ----------------------------------------------------------------------------------------------------------------
GRID_DEPTHS = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
GRID_GPR = ["250", "600", "dual"]


def grid_size():
    return NS * NU * len(GRID_DEPTHS) * len(GRID_GPR) * 2


def grid(cfg):
    rows = []
    for s in range(NS):
        for u in range(NU):
            for d in GRID_DEPTHS:
                for gp in GRID_GPR:
                    for em in (False, True):
                        rows.append((s, u, d, gp, em, float(pd_fused(cfg, s, u, d, gpr=gp, em=em))))
    pds = np.array([r[-1] for r in rows])
    return dict(n=len(rows), share_ge_0p9=float((pds >= 0.9).mean()), share_le_0p5=float((pds <= 0.5).mean()),
                share_le_0p3=float((pds <= 0.3).mean()), rows=rows)


def reliable_depth(cfg, level=0.9, step=0.25, dmax=10.0):
    """deepest depth (m) at which the fused closed-form signal Pd (dual GPR + EM) is at least `level`; 0 if never"""
    ds = np.arange(0.25, dmax + 1e-9, step)
    out = np.zeros((NS, NU))
    for s in range(NS):
        for u in range(NU):
            pd = pd_fused(cfg, s, u, ds)
            ok = np.where(pd >= level)[0]
            # contiguous from the shallow end
            if len(ok) and ok[0] == 0:
                brk = np.where(np.diff(ok) > 1)[0]
                last = ok[brk[0]] if len(brk) else ok[-1]
                out[s, u] = ds[last]
    return out


# ----------------------------------------------------------------------------------------------------------------
# Experiments
# ----------------------------------------------------------------------------------------------------------------
METHODS_MAIN = ["em_only", "gpr250", "gpr600", "gpr_dual", "rule_or", "rule_and", "seg_flat", "seg_prior",
                "prop_no_anchor", "anch_gpr", "anch_full", "anch_generic", "anch_joint", "anch_oracle_depth", "anch_depthmarg", "anch_tempered"]
METHOD_LABEL = {
    "em_only": "EM locator only (proxy for current practice)", "gpr250": "GPR 250 MHz only", "gpr600": "GPR 600 MHz only",
    "gpr_dual": "GPR dual-band, per segment", "rule_or": "OR rule (any sensor detects)", "rule_and": "AND rule (GPR and EM detect)",
    "seg_flat": "GPR + EM fusion, per segment, flat prior", "seg_prior": "GPR + EM fusion, per segment, base-rate prior",
    "prop_no_anchor": "Propagation, no anchor (flat start)", "anch_gpr": "Anchored propagation, GPR dual only",
    "anch_full": "Anchored propagation, GPR + EM (proposed)", "anch_generic": "Anchored, generic soil likelihoods (no soil calibration)",
    "anch_joint": "Anchored, exact joint GPR-band likelihood", "anch_oracle_depth": "Anchored, true depth known", "anch_depthmarg": "Anchored, likelihood averaged over the depth range",
    "anch_tempered": "Anchored, evidence tempered by 0.5"}


def prevalence_prior(cfg):
    h, r = seg_rates(cfg)
    K = cfg["truth"]["n_segments"]
    a = cfg["truth"]["anchor_true_reliability"]
    pi = r / (h + r)
    return float(np.mean(pi + (a - pi) * (1 - h - r) ** np.arange(K)))


def all_methods(cfg, B, obs, which=METHODS_MAIN):
    """returns {method: (probability or None, call)}"""
    thr = cfg["filter"]["present_threshold"]
    Lm = lr_tables(cfg, B, "matched", "class")
    out = {}
    prior = prevalence_prior(cfg)
    if "em_only" in which: out["em_only"] = (None, obs["dem"])
    if "gpr250" in which: out["gpr250"] = (None, obs["d250"])
    if "gpr600" in which: out["gpr600"] = (None, obs["d600"])
    if "gpr_dual" in which:
        P = persegment(obs, Lm, ("g250", "g600"), 0.5); out["gpr_dual"] = (P, P > thr)
    if "rule_or" in which: out["rule_or"] = (None, obs["d250"] | obs["d600"] | obs["dem"])
    if "rule_and" in which: out["rule_and"] = (None, (obs["d250"] | obs["d600"]) & obs["dem"])
    if "seg_flat" in which:
        P = persegment(obs, Lm, ("g250", "g600", "em"), 0.5); out["seg_flat"] = (P, P > thr)
    if "seg_prior" in which:
        P = persegment(obs, Lm, ("g250", "g600", "em"), prior); out["seg_prior"] = (P, P > thr)
    if "prop_no_anchor" in which:
        P = run_filter(obs, Lm, cfg, b0=0.5); out["prop_no_anchor"] = (P, P > thr)
    if "anch_gpr" in which:
        P = run_filter(obs, Lm, cfg, use=("g250", "g600")); out["anch_gpr"] = (P, P > thr)
    if "anch_full" in which:
        P = run_filter(obs, Lm, cfg); out["anch_full"] = (P, P > thr)
    if "anch_generic" in which:
        Lg = lr_tables(cfg, B, "generic", "class"); P = run_filter(obs, Lg, cfg); out["anch_generic"] = (P, P > thr)
    if "anch_joint" in which:
        P = run_filter(obs, Lm, cfg, joint=True); out["anch_joint"] = (P, P > thr)
    if "anch_oracle_depth" in which:
        Lo = lr_tables(cfg, B, "matched", "true"); P = run_filter(obs, Lo, cfg); out["anch_oracle_depth"] = (P, P > thr)
    if "anch_depthmarg" in which:
        Ld = lr_tables(cfg, B, "matched", "marginal"); P = run_filter(obs, Ld, cfg); out["anch_depthmarg"] = (P, P > thr)
    if "anch_tempered" in which:
        P = run_filter(obs, Lm, cfg, temper=0.5); out["anch_tempered"] = (P, P > thr)
    return out


def exp_main(cfg, seed, nblocks, n, log):
    """E1/E2/E4: baselines, ablations, three-state output, per-cell results, calibration"""
    vw, bl, pdtab = views(cfg)
    ncell = NS * NU
    store = {m: [] for m in METHODS_MAIN}
    cellstore = {m: [] for m in ("anch_full", "em_only", "seg_flat", "gpr_dual")}
    cal = {m: [] for m in ("anch_full", "seg_flat", "anch_generic", "anch_tempered", "anch_joint", "gpr_dual", "seg_prior", "anch_depthmarg", "anch_oracle_depth")}
    wmix = cell_weights(cfg).ravel()
    keep_P = []   # for recalibration
    three = []
    for b in range(nblocks):
        t0 = time.time()
        rng = rng_for(seed, "main", b)
        B = make_block(rng, cfg, n)
        obs = observe(rng, B, cfg)
        truth = B["state"] == 1
        res = all_methods(cfg, B, obs)
        wc = corr_weights(B, wmix)
        for m, (P, call) in res.items():
            F = cell_fracs(call, truth, ncell)
            store[m].append({v: mix(F, w) for v, w in vw.items()})
            if m in cellstore:
                cellstore[m].append(F)
            if P is not None and m in cal:
                cal[m].append(calib_stats(P, truth, wc))
        # three-state confusion for the proposed method (fractions of all segments)
        call = res["anch_full"][1]
        F = cell_fracs(call, truth, ncell)
        w = wmix / wmix.sum()
        unv = bl.astype(float)
        present_dec = [(w * (1 - unv) * F[:, 0]).sum(), (w * (1 - unv) * F[:, 1]).sum(), (w * (1 - unv) * F[:, 2]).sum(), (w * (1 - unv) * F[:, 3]).sum()]
        tu = (w * unv * (F[:, 0] + F[:, 1])).sum(); au = (w * unv * (F[:, 2] + F[:, 3])).sum()
        three.append(dict(truth_present_called_present=present_dec[0], truth_present_called_absent=present_dec[1],
                          truth_present_unverified=tu, truth_absent_called_present=present_dec[2],
                          truth_absent_called_absent=present_dec[3], truth_absent_unverified=au))
        if b < 5:
            keep_P.append((res["anch_full"][0].astype(np.float32), truth, wc, B["cell"].copy()))
        log("   main block %d/%d  %.1fs" % (b + 1, nblocks, time.time() - t0))
    out = {"methods": {}, "view_weights": {v: float(w.sum()) for v, w in vw.items()}}
    for m in METHODS_MAIN:
        out["methods"][m] = {v: summarise([blk[v] for blk in store[m]], ["acc", "miss", "fa", "prev", "bacc"]) for v in vw}
    # per-cell for headline methods (mean across blocks)
    out["cells"] = {}
    for m, lst in cellstore.items():
        Fm = np.mean(lst, axis=0)
        cells = {}
        for s in range(NS):
            for u in range(NU):
                tp, fn, fp, tn = Fm[s * NU + u]
                cells["%s|%s" % (SOILS[s], UTILS[u])] = dict(miss=float(fn / (tp + fn)) if tp + fn > 0 else None,
                                                               fa=float(fp / (fp + tn)) if fp + tn > 0 else None,
                                                               acc=float(tp + tn), prevalence=float(tp + fn),
                                                               blind=bool(bl[s * NU + u]))
        out["cells"][m] = cells
        # per utility (mixture over soils, equal soil weights) and per soil
        pu, ps = {}, {}
        for u in range(NU):
            sel = [s * NU + u for s in range(NS)]
            pu[UTILS[u]] = {k: v for k, v in mix(Fm[sel], np.ones(NS)).items() if k in ("acc", "miss", "fa")}
            sel_vis = [s * NU + u for s in range(NS) if not bl[s * NU + u]]
            pu[UTILS[u]]["miss_visible"] = mix(Fm[sel_vis], np.ones(len(sel_vis)))["miss"] if sel_vis else None
        for s in range(NS):
            sel = [s * NU + u for u in range(NU)]
            ww = np.array(cfg["util"]["share"])
            ps[SOILS[s]] = {k: v for k, v in mix(Fm[sel], ww).items() if k in ("acc", "miss", "fa")}
        out["cells"][m + "_by_utility"] = pu
        out["cells"][m + "_by_soil"] = ps
    out["three_state"] = summarise(three)
    out["sensor_blind_cells"] = [dict(soil=SOILS[i // NU], util=UTILS[i % NU], pd_mid=float(pdtab.ravel()[i])) for i in range(ncell) if bl[i]]
    out["sensor_blind_share"] = float(wmix[bl].sum())
    out["calibration"] = {}
    for m, lst in cal.items():
        out["calibration"][m] = dict(ece=list(ci_stats([c["ece"] for c in lst])), brier=list(ci_stats([c["brier"] for c in lst])),
                                     bins=dict(count=np.nanmean([c["count"] for c in lst], 0).tolist(),
                                               mean_p=np.nanmean([c["mean_p"] for c in lst], 0).tolist(),
                                               mean_y=np.nanmean([c["mean_y"] for c in lst], 0).tolist()))
    # low-probability occupancy (fraction of segments reported below 0.1 and their occupancy)
    lows = []
    for P, tr, wc, _ in keep_P:
        ww = np.repeat(wc / P.shape[1], P.shape[1]); p = P.ravel(); y = tr.ravel()
        m_ = p < 0.1
        lows.append(dict(share=float(ww[m_].sum() / ww.sum()), occupied=float((ww[m_] * y[m_]).sum() / max(ww[m_].sum(), 1e-12))))
        m2 = p > 0.9
        lows[-1].update(high_share=float(ww[m2].sum() / ww.sum()), high_correct=float((ww[m2] * y[m2]).sum() / max(ww[m2].sum(), 1e-12)))
    out["probability_bands"] = summarise(lows)
    # recalibration: fit isotonic map on blocks 0-1, test on blocks 2-4
    out["recalibration"] = recalibration(keep_P)
    return out, keep_P


def recalibration(keep_P, nq=400):
    from scipy.optimize import isotonic_regression
    if len(keep_P) < 3:
        return None
    nfit = max(1, len(keep_P) * 2 // 5)
    fit, test = keep_P[:nfit], keep_P[nfit:]
    p = np.concatenate([f[0].ravel() for f in fit]).astype(np.float64)
    y = np.concatenate([f[1].ravel() for f in fit]).astype(np.float64)
    w = np.concatenate([np.repeat(f[2] / f[0].shape[1], f[0].shape[1]) for f in fit])
    o = np.argsort(p)
    p, y, w = p[o], y[o], w[o]
    edges = np.quantile(p, np.linspace(0, 1, nq + 1))
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, nq - 1)
    wb = np.bincount(idx, weights=w, minlength=nq)
    yb = np.bincount(idx, weights=w * y, minlength=nq) / np.maximum(wb, 1e-18)
    pb = np.bincount(idx, weights=w * p, minlength=nq) / np.maximum(wb, 1e-18)
    keep = wb > 0
    iso = isotonic_regression(yb[keep], weights=wb[keep], increasing=True).x
    px = pb[keep]
    before, after = [], []
    for P, tr, wc, _ in test:
        before.append(calib_stats(P.astype(np.float64), tr, wc))
        Q = np.interp(P.astype(np.float64), px, iso)
        after.append(calib_stats(Q, tr, wc))
    return dict(fit_blocks=nfit, test_blocks=len(test),
                before=dict(ece=list(ci_stats([c["ece"] for c in before])), brier=list(ci_stats([c["brier"] for c in before]))),
                after=dict(ece=list(ci_stats([c["ece"] for c in after])), brier=list(ci_stats([c["brier"] for c in after])),
                           bins=dict(mean_p=np.nanmean([c["mean_p"] for c in after], 0).tolist(), mean_y=np.nanmean([c["mean_y"] for c in after], 0).tolist())))


def main_metrics_only(cfg, seed, nblocks, n, tag, methods=("seg_flat", "anch_full"), filt_over=None, obs_kw=None, vis_cfg=None, calib=False):
    """helper for stress tests: simulate with `cfg` (truth/sensor), run methods; returns {method: view->summary} """
    vw, bl, pdtab = views(vis_cfg or cfg)
    ncell = NS * NU
    store = {m: [] for m in methods}
    cstore = {m: [] for m in methods}
    wmix = cell_weights(cfg).ravel()
    for b in range(nblocks):
        rng = rng_for(seed, tag, b)
        B = make_block(rng, cfg, n)
        kw = obs_kw(rng, B) if callable(obs_kw) else (obs_kw or {})
        obs = observe(rng, B, cfg, **kw)
        truth = B["state"] == 1
        fcfg = filt_over(cfg) if callable(filt_over) else cfg
        res = all_methods(fcfg, B, obs, which=methods)
        for m, (P, call) in res.items():
            store[m].append({v: mix(cell_fracs(call, truth, ncell), w) for v, w in vw.items()})
            if calib and P is not None:
                cstore[m].append(calib_stats(P, truth, corr_weights(B, wmix)))
    out = {m: {v: summarise([blk[v] for blk in store[m]], ["acc", "miss", "fa", "prev", "bacc"]) for v in vw} for m in methods}
    if calib:
        for m in methods:
            if cstore[m]:
                out[m]["calibration"] = dict(ece=list(ci_stats([c["ece"] for c in cstore[m]])), brier=list(ci_stats([c["brier"] for c in cstore[m]])))
    return out


def exp_stress(cfg, seed, nblocks, n, log):
    out = {}
    # (a) loss hazard, matched filter
    out["hazard"] = {}
    for hz in (0.05, 0.2, 0.5, 1.0):
        c = copy.deepcopy(cfg); c["truth"]["hazard_per_100m"] = hz; c["filter"]["hazard_per_100m"] = hz
        out["hazard"][str(hz)] = main_metrics_only(c, seed, nblocks, n, "stress-hazard-%s" % hz, ("em_only", "seg_flat", "anch_full"))
        log("   hazard %s done" % hz)
    # (b) hazard mis-specified: truth 0.2, filter assumes other values
    out["hazard_misspecified"] = {}
    for fh in (0.05, 0.2, 0.5, 1.0, 2.0):
        c = copy.deepcopy(cfg); c["filter"]["hazard_per_100m"] = fh
        out["hazard_misspecified"][str(fh)] = main_metrics_only(c, seed, nblocks, n, "stress-hazmis", ("anch_full",))
    # (c) lateral shifts
    out["shift"] = {}
    for sh in (0.0, 0.25, 0.5, 1.0):
        c = copy.deepcopy(cfg); c["truth"]["shift_fraction"] = sh
        out["shift"][str(sh)] = main_metrics_only(c, seed, nblocks, n, "stress-shift-%s" % sh, ("em_only", "seg_flat", "anch_full"))
        log("   shift %s done" % sh)
    # (d) anchor reliability: overconfident (filter assumes 1) vs calibrated (filter assumes truth)
    out["anchor"] = {}
    for rel in (1.0, 0.9, 0.7, 0.5):
        c = copy.deepcopy(cfg); c["truth"]["anchor_true_reliability"] = rel
        over = main_metrics_only(c, seed, nblocks, n, "stress-anchor-%s" % rel, ("seg_flat", "anch_full"))
        c2 = copy.deepcopy(c); c2["filter"]["anchor_reliability"] = rel
        cal = main_metrics_only(c, seed, nblocks, n, "stress-anchor-%s" % rel, ("anch_full",), filt_over=lambda cc: c2)
        out["anchor"][str(rel)] = dict(per_segment=over["seg_flat"], overconfident=over["anch_full"], calibrated=cal["anch_full"])
        log("   anchor %s done" % rel)
    # (e) sensor failure (a dead modality returns clutter only), unaware filter
    out["sensor_failure"] = {}
    for q in (0.0, 0.1, 0.25, 0.5):
        res = {}
        for which in ("gpr", "em"):
            c = cfg

            def okw(rng, B, which=which, q=q):
                return dict(fail={which: rng.random(B["N"]) < q})
            res[which] = main_metrics_only(c, seed, nblocks, n, "stress-fail-%s-%s" % (which, q), ("anch_full",), obs_kw=okw)["anch_full"]
        out["sensor_failure"][str(q)] = res
        log("   failure %s done" % q)
    # (f) correlated evidence between GPR and EM
    out["correlation"] = {}
    for rg in (0.0, 0.3, 0.6, 0.9):
        res = {}
        for name, kw in (("independent", dict(methods=("anch_full",))), ("tempered", dict(methods=("anch_tempered",))), ("joint_gpr", dict(methods=("anch_joint",)))):
            r_ = main_metrics_only(cfg, seed, nblocks, n, "stress-corr-%s" % rg, kw["methods"], obs_kw=dict(rho_ge=rg), calib=True)
            res[name] = list(r_.values())[0]
        out["correlation"][str(rg)] = res
        log("   correlation %s done" % rg)
    # (g) segment dropout (GNSS or acquisition gaps): no observation, prediction only
    out["dropout"] = {}
    for dp in (0.0, 0.1, 0.3, 0.5):
        vw, bl, _ = views(cfg); ncell = NS * NU
        store = []
        for b in range(max(2, nblocks // 2)):
            rng = rng_for(seed, "stress-drop-%s" % dp, b)
            B = make_block(rng, cfg, n); obs = observe(rng, B, cfg)
            mask = rng.random((B["N"], B["K"])) >= dp
            Lm = lr_tables(cfg, B)
            P = run_filter(obs, Lm, cfg, mask=mask)
            truth = B["state"] == 1
            store.append({v: mix(cell_fracs(P > 0.5, truth, ncell), w) for v, w in vw.items()})
        out["dropout"][str(dp)] = {v: summarise([s[v] for s in store], ["acc", "miss", "fa"]) for v in vw}
    return out


def exp_class_balance(cfg, seed, nblocks, n, log):
    """why does accuracy rise with the loss hazard: prevalence, balanced accuracy and the naive 'always absent' baseline"""
    out = {}
    for hz in (0.05, 0.2, 0.5, 1.0):
        c = copy.deepcopy(cfg); c["truth"]["hazard_per_100m"] = hz; c["filter"]["hazard_per_100m"] = hz
        vw, bl, _ = views(c); ncell = NS * NU
        recs = []
        for b in range(nblocks):
            rng = rng_for(seed, "stress-hazard-%s" % hz, b)
            B = make_block(rng, c, n); obs = observe(rng, B, c)
            truth = B["state"] == 1
            Lm = lr_tables(c, B)
            P = run_filter(obs, Lm, c)
            F = cell_fracs(P > 0.5, truth, ncell)
            m = mix(F, vw["all"])
            Fa = cell_fracs(np.zeros_like(truth), truth, ncell)
            ma = mix(Fa, vw["all"])
            recs.append(dict(acc=m["acc"], bacc=m["bacc"], prev=m["prev"], miss=m["miss"], fa=m["fa"], always_absent_acc=ma["acc"]))
        out[str(hz)] = summarise(recs)
    return out


def exp_sensitivity(cfg, seed, nblocks, n, log):
    """one-at-a-time parameter sensitivity of the proposed method (all-cell accuracy, visible-cell miss, unverified share)"""
    def run(c, tag):
        r = main_metrics_only(c, seed, nblocks, n, tag, ("anch_full",), vis_cfg=c)["anch_full"]
        bl = views(c)[1]
        return dict(acc=r["all"]["acc"][0], miss_visible=r["visible"]["miss"][0], fa_visible=r["visible"]["fa"][0],
                    unverified_share=float(cell_weights(c).ravel()[bl].sum()))
    out = {"base": run(cfg, "sens")}
    plan = []

    def add(name, fn_lo, fn_hi, lo_label, hi_label):
        plan.append((name, fn_lo, fn_hi, lo_label, hi_label))

    def mod(path, f):
        def g(c):
            c = copy.deepcopy(c); d = c
            for k in path[:-1]:
                d = d[k]
            d[path[-1]] = f(d[path[-1]])
            return c
        return g
    add("detection threshold +/-2 dB", mod(("gpr", "threshold_db"), lambda v: v - 2), mod(("gpr", "threshold_db"), lambda v: v + 2), "6 dB", "10 dB")
    add("soil attenuation x0.75 / x1.25", mod(("soil", "atten_250_db_per_m"), lambda v: [x * 0.75 for x in v]), mod(("soil", "atten_250_db_per_m"), lambda v: [x * 1.25 for x in v]), "x0.75", "x1.25")
    add("segment noise -1 / +1 dB", mod(("soil", "sigma_seg_db"), lambda v: [x - 1 for x in v]), mod(("soil", "sigma_seg_db"), lambda v: [x + 1 for x in v]), "-1 dB", "+1 dB")
    add("run-level noise 1.5 / 4.5 dB", mod(("gpr", "sigma_run_db"), lambda v: 1.5), mod(("gpr", "sigma_run_db"), lambda v: 4.5), "1.5 dB", "4.5 dB")
    add("system budget -3 / +3 dB", mod(("gpr", "budget_db"), lambda v: {k: x + 3 for k, x in v.items()}), mod(("gpr", "budget_db"), lambda v: {k: x - 3 for k, x in v.items()}), "+3 dB", "-3 dB")
    add("clutter false-alarm x0.5 / x2", mod(("soil", "clutter_pfa"), lambda v: [x * 0.5 for x in v]), mod(("soil", "clutter_pfa"), lambda v: [x * 2 for x in v]), "x0.5", "x2")
    add("EM coupling x0.5 / x1.5", mod(("util", "em_coupling"), lambda v: [None if x is None else x * 0.5 for x in v]), mod(("util", "em_coupling"), lambda v: [None if x is None else min(1.0, x * 1.5) for x in v]), "x0.5", "x1.5")
    add("loss hazard 0.1 / 0.4 per 100 m", lambda c: _hz(c, 0.1), lambda c: _hz(c, 0.4), "0.1", "0.4")
    add("band correlation 0.5 / 0.9", mod(("gpr", "band_correlation"), lambda v: 0.5), mod(("gpr", "band_correlation"), lambda v: 0.9), "0.5", "0.9")
    add("spreading coefficient 35 / 45", mod(("gpr", "spreading_coef"), lambda v: 35.0), mod(("gpr", "spreading_coef"), lambda v: 45.0), "35", "45")
    out["items"] = []
    for i, (name, flo, fhi, ll, hl) in enumerate(plan):
        lo = run(flo(cfg), "sens"); hi = run(fhi(cfg), "sens")      # common random numbers: every variant shares the base streams
        out["items"].append(dict(name=name, low_label=ll, high_label=hl, low=lo, high=hi))
        log("   sensitivity %s done" % name)
    return out


def _hz(c, hz):
    c = copy.deepcopy(c); c["truth"]["hazard_per_100m"] = hz; c["filter"]["hazard_per_100m"] = hz
    return c


def exp_decision(cfg, seed, nblocks, n, keep_main=None, log=print):
    """E5: clearance policies and trial-pit allocation"""
    vw, bl, pdtab = views(cfg)
    ncell = NS * NU
    wmix = cell_weights(cfg).ravel()
    cons = np.array(cfg["util"]["consequence"], float)
    seg_per_km = 1000.0 / cfg["truth"]["segment_m"]
    thr_list = [0.5, 0.2, 0.1, 0.05, 0.02]
    pol = {}
    pit_records = []
    for b in range(nblocks):
        rng = rng_for(seed, "decision", b)
        B = make_block(rng, cfg, n)
        obs = observe(rng, B, cfg)
        truth = B["state"] == 1
        res = all_methods(cfg, B, obs, which=("em_only", "gpr_dual", "seg_flat", "anch_full"))
        wc = corr_weights(B, wmix)
        blind_c = bl[B["cell"]]
        util = B["util"]
        csg = cons[util][:, None] * np.ones((1, B["K"]))

        def policy(name, cleared):
            """cleared (N,K) bool: segments released for mechanical excavation"""
            wseg = np.repeat(wc / B["K"], B["K"]).reshape(B["N"], B["K"])
            cl = float((wseg * cleared).sum())
            strike = float((wseg * cleared * truth).sum())
            cstrike = float((wseg * cleared * truth * csg).sum())
            pol.setdefault(name, []).append(dict(cleared=cl, strike_rate=strike / cl if cl > 0 else np.nan,
                                                 strikes_per_km=(strike) * seg_per_km, consequence_per_km=cstrike * seg_per_km,
                                                 unverified=float((wseg * np.broadcast_to(blind_c[:, None], truth.shape)).sum())))
        policy("no map: dig everywhere", np.ones_like(truth))
        policy("EM locator only", ~res["em_only"][1])
        policy("GPR dual-band, per segment", ~res["gpr_dual"][1])
        policy("fusion, per segment", ~res["seg_flat"][1])
        P = res["anch_full"][0]
        policy("anchored fusion, binary map (absent = clear)", P <= 0.5)
        for t in thr_list[1:]:
            policy("anchored fusion, three-state, clear if p<%.2f" % t, (P < t) & ~blind_c[:, None])
        # pit allocation: among segments not called present (absent or unverified), ranked by score; budget in pit cost units
        K = B["K"]
        cand = (P <= 0.5) | blind_c[:, None]
        cost = (cfg["pit"]["base"] + cfg["pit"]["per_m_depth"] * B["depth"])[:, None] * np.ones((1, K))
        w = np.repeat(wc / K, K)
        cand_f = cand.ravel(); truth_f = truth.ravel(); pf = P.ravel(); cs = csg.ravel(); co = cost.ravel(); idx_c = np.where(cand_f)[0]
        total_cost_all = float((w * co).sum())
        tot_missed = float((w[idx_c] * truth_f[idx_c]).sum())
        tot_missed_c = float((w[idx_c] * truth_f[idx_c] * cs[idx_c]).sum())
        rec = {}
        for name, score in (("probability", pf[idx_c]), ("consequence/cost", pf[idx_c] * cs[idx_c] / co[idx_c]),
                            ("random", rng.random(len(idx_c)))):
            order = idx_c[np.argsort(-score)]
            cumcost = np.cumsum(w[order] * co[order])
            cfound = np.cumsum(w[order] * truth_f[order])
            cfound_c = np.cumsum(w[order] * truth_f[order] * cs[order])
            curves = []
            for frac in (0.0, 0.01, 0.02, 0.05, 0.1, 0.2):
                j = np.searchsorted(cumcost, frac * total_cost_all)
                f1 = cfound[j - 1] if j > 0 else 0.0
                f2 = cfound_c[j - 1] if j > 0 else 0.0
                curves.append((frac, 1 - f1 / tot_missed if tot_missed > 0 else 0.0, 1 - f2 / tot_missed_c if tot_missed_c > 0 else 0.0))
            rec[name] = curves
        pit_records.append(rec)
        log("   decision block %d/%d" % (b + 1, nblocks))
    out = {"policies": {k: summarise(v, ["cleared", "strike_rate", "strikes_per_km", "consequence_per_km", "unverified"]) for k, v in pol.items()}}
    pits = {}
    for name in pit_records[0]:
        pits[name] = []
        for j in range(len(pit_records[0][name])):
            frac = pit_records[0][name][j][0]
            r1 = ci_stats([r[name][j][1] for r in pit_records]); r2 = ci_stats([r[name][j][2] for r in pit_records])
            pits[name].append(dict(budget_fraction=frac, residual_missed=list(r1), residual_consequence=list(r2)))
    out["pits"] = pits
    return out


def exp_rescan(cfg, seed, nblocks, n, log):
    """E6: does a repeat pass help (connectivity scenario)? hard soils only"""
    ncell = NS * NU
    hard = [s for s in (1, 2, 3, 4)]   # dry loam, moist loam, clay, rubble fill (the four harder soils)
    w = cell_weights(cfg).ravel()
    sel = np.zeros(ncell, bool)
    for s in hard:
        sel[s * NU:(s + 1) * NU] = True
    wsel = w * sel
    bl_ = views(cfg)[1]
    wvis = wsel * ~bl_
    scen = {"no rescan": None, "offline (25% later)": (0.25, 1.0), "on the spot (95%)": (0.95, 1.0),
            "on the spot, repeat partly decorrelated (rho=0.5)": (0.95, 0.5), "on the spot, repeat decorrelated (rho=0)": (0.95, 0.0)}
    store = {k: [] for k in scen}; storev = {k: [] for k in scen}; frac = {k: [] for k in scen}
    for b in range(nblocks):
        rng = rng_for(seed, "rescan", b)
        B = make_block(rng, cfg, n)
        obs = observe(rng, B, cfg)
        truth = B["state"] == 1
        Lm = lr_tables(cfg, B)
        # fixed random streams for availability
        avail_u = rng.random((B["N"], B["K"]))
        rngp = rng_for(seed, "rescan-pass2", b)
        obs_by_rho = {}
        for k, v in scen.items():
            if v is None:
                P = run_filter(obs, Lm, cfg); nres = np.zeros(B["N"])
            else:
                pa, rho = v
                if rho not in obs_by_rho:
                    obs_by_rho[rho] = observe(rng_for(seed, "rescan-pass2-%s" % rho, b), B, cfg, prev=obs, rho_pass=rho)
                P, nres = run_filter(obs, Lm, cfg, obs2=obs_by_rho[rho], avail2=avail_u < pa)
            F = cell_fracs(P > 0.5, truth, ncell)
            store[k].append(mix(F, wsel)); storev[k].append(mix(F, wvis))
            frac[k].append(dict(rescan_fraction=float((nres * w[B["cell"]] / B["n"] * sel[B["cell"]]).sum() / wsel.sum() / B["K"])))
    out = {}
    for k in scen:
        d = summarise(store[k], ["acc", "miss", "fa"])
        d["visible"] = summarise(storev[k], ["acc", "miss", "fa"])
        d["rescan_fraction"] = list(ci_stats([f["rescan_fraction"] for f in frac[k]]))
        out[k] = d
    return out


def exp_sections(cfg, seed, log):
    """official cross-sections A, B, C: fused closed-form Pd with shadowing, plus Monte Carlo confirmation of selected cells"""
    sh = cfg["shadow_db"]
    items = [("Concrete sewer, A", "concrete_sewer", 3.5, 0.0), ("Sewer, B (PE/PVC above)", "concrete_sewer", 3.5, sh["pe_water"]),
             ("Sewer, B (cast iron above)", "concrete_sewer", 3.5, sh["ci_water"]), ("PE/PVC water", "pe_water", 1.8, 0.0),
             ("Fibre, A", "fibre", 1.8, 0.0), ("Fibre, C (PE/PVC above)", "fibre", 1.8, sh["pe_water"]),
             ("Power duct", "power", 0.8, 0.0), ("Telephone duct", "telephone", 0.8, 0.0)]
    tab = {}
    for s in range(NS):
        tab[SOILS[s]] = {}
        for name, un, d, shd in items:
            u = UTILS.index(un)
            tab[SOILS[s]][name] = float(pd_fused(cfg, s, u, d, shadow_db=shd))
    # MC confirmation for 6 cells
    chk = []
    rng = rng_for(seed, "sections")
    for (s, name) in ((2, "Sewer, B (PE/PVC above)"), (1, "Sewer, B (cast iron above)"), (4, "Fibre, C (PE/PVC above)")):
        it = [x for x in items if x[0] == name][0]
        u = UTILS.index(it[1])
        B = make_block(rng, cfg, 1, fixed_depth=it[2]); N = 60000
        c2 = copy.deepcopy(cfg)
        # build a custom block of N corridors in one cell
        Bc = dict(N=N, K=1, n=N, cell=np.full(N, s * NU + u), soil=np.full(N, s), util=np.full(N, u), depth=np.full(N, it[2]),
                  state=np.ones((N, 1), np.uint8), coupled=rng.random(N) < em_coupling_eff(cfg)[u], shadow=np.full(N, it[3]))
        o = observe(rng, Bc, c2)
        anyd = (o["sig"]["250"] | o["sig"]["600"] | o["sig"]["em"]).mean()
        chk.append(dict(soil=SOILS[s], item=name, closed_form=float(pd_fused(cfg, s, u, it[2], shadow_db=it[3])), monte_carlo=float(anyd)))
    return dict(table=tab, columns=[i[0] for i in items], mc_check=chk)


def exp_position(cfg):
    ds = [1.0, 2.0, 3.5, 5.0, 7.0]
    out = {}
    for lab, g in (("rtk", cfg["positioning"]["rtk_m"]), ("standalone", cfg["positioning"]["standalone_m"])):
        ph, pdp = position_probs(cfg, np.array(ds), g)
        out[lab] = dict(depths=ds, horizontal_within_1m=[float(x) for x in ph], depth_within_0p5m=[float(x) for x in pdp])
    return out


# ----------------------------------------------------------------------------------------------------------------
# Example corridor for the belief-trace figure
# ----------------------------------------------------------------------------------------------------------------
def example_corridor(cfg, seed, soil="clay", util="fibre", depth=1.8, tries=400):
    s, u = SOILS.index(soil), UTILS.index(util)
    for t in range(tries):
        rng = rng_for(seed, "example", t)
        B = make_block(rng, cfg, 1, fixed_depth=depth)
        sel = (B["soil"] == s) & (B["util"] == u)
        i = int(np.where(sel)[0][0])
        st = B["state"][i]
        if 25 < (st == 1).sum() < 75 and st[0] == 1 and st[-1] == 0 and (np.diff(st.astype(int)) != 0).sum() <= 3:
            obs = observe(rng, B, cfg)
            L = lr_tables(cfg, B)
            P = run_filter(obs, L, cfg)
            Pf = persegment(obs, L, ("g250", "g600", "em"), 0.5)
            return dict(truth=(st == 1).tolist(), p_anchored=P[i].tolist(), p_persegment=Pf[i].tolist(),
                        d250=obs["d250"][i].tolist(), d600=obs["d600"][i].tolist(), dem=obs["dem"][i].tolist(), soil=soil, util=util, depth=depth)
    return None


# ----------------------------------------------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------------------------------------------
def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, (np.floating,)):
        v = float(o)
        return None if np.isnan(v) else v
    if isinstance(o, float):
        return None if np.isnan(o) else o
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def reproduce(args):
    t0 = time.time()
    cfg = copy.deepcopy(CFG)
    os.makedirs(args.out, exist_ok=True)

    def log(s):
        print(s, flush=True)

    n, nb, seed = args.n, args.blocks, args.seed
    nsens = max(3, nb // 2)
    nsn = max(100, n // 2)
    R = {"meta": dict(software="SubSurface_MC.py", version=VERSION, command=" ".join(["python"] + sys.argv),
                      seed=seed, corridors_per_cell_per_block=n, blocks=nb, segments_per_corridor=cfg["truth"]["n_segments"],
                      corridors_per_block=n * NS * NU, python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                      platform=platform.platform()),
         "config": cfg}
    log("1/10 self-tests")
    R["selftests"] = selftests(cfg, seed)
    if not all(t["passed"] for t in R["selftests"]):
        log("SELF-TEST FAILURE")
    log("2/10 closed-form grid, reliable depth, positioning, cross-sections")
    g = grid(cfg)
    R["grid"] = {k: v for k, v in g.items() if k != "rows"}
    blind, pdtab = blind_table(cfg)
    R["pd_mid_depth"] = {SOILS[s]: {UTILS[u]: float(pdtab[s, u]) for u in range(NU)} for s in range(NS)}
    R["sensor_blind"] = {SOILS[s]: {UTILS[u]: bool(blind[s, u]) for u in range(NU)} for s in range(NS)}
    rd = reliable_depth(cfg)
    R["reliable_depth_m"] = {SOILS[s]: {UTILS[u]: float(rd[s, u]) for u in range(NU)} for s in range(NS)}
    R["positioning"] = exp_position(cfg)
    R["sections"] = exp_sections(cfg, seed, log)
    log("3/10 main experiment (baselines, ablations, three-state, calibration)")
    R["main"], keepP = exp_main(cfg, seed, nb, n, log)
    log("4/10 stress tests")
    R["stress"] = exp_stress(cfg, seed, nsens, nsn, log)
    log("5/10 class balance")
    R["class_balance"] = exp_class_balance(cfg, seed, nsens, nsn, log)
    log("6/10 decision-consequence experiment")
    R["decision"] = exp_decision(cfg, seed, nb, n, log=log)
    log("7/10 rescan / connectivity")
    R["rescan"] = exp_rescan(cfg, seed, nsens, nsn, log)
    log("8/10 parameter sensitivity")
    R["sensitivity"] = exp_sensitivity(cfg, seed, max(3, nb // 3), max(100, n // 3), log)
    log("9/10 example corridor")
    R["example"] = example_corridor(cfg, seed)
    R["grid_rows"] = [[SOILS[r[0]], UTILS[r[1]], r[2], r[3], r[4], r[5]] for r in g["rows"]]
    R["meta"]["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(args.out, "config.json"), "w", encoding="utf-8") as fh:
        json.dump(jsonable(cfg), fh, indent=1)
    with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(jsonable(R), fh, indent=1)
    log("results.json written (%.1f s)" % (time.time() - t0))
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true", help="run the closed-form versus Monte Carlo self-tests")
    ap.add_argument("--grid-size", action="store_true", help="print the closed-form reference grid summary")
    ap.add_argument("--reproduce", action="store_true", help="regenerate results.json (and figures with figure_generation.py)")
    ap.add_argument("--out", default="out")
    ap.add_argument("--n", type=int, default=500, help="corridors per soil x utility cell per block")
    ap.add_argument("--blocks", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--quick", action="store_true", help="small run for a smoke test")
    a = ap.parse_args()
    if a.quick:
        a.n, a.blocks = 60, 4
    if a.demo:
        res = selftests(CFG, a.seed)
        npass = sum(r["passed"] for r in res)
        print("%d of %d self-tests passed" % (npass, len(res)))
        sys.exit(0 if npass == len(res) else 1)
    if a.grid_size:
        g = grid(CFG)
        print("grid configurations: %d" % g["n"])
        print("closed-form fused detection probability >= 0.9: %.1f%%; <= 0.5: %.1f%%; <= 0.3: %.1f%%" % (100 * g["share_ge_0p9"], 100 * g["share_le_0p5"], 100 * g["share_le_0p3"]))
        return
    if a.reproduce:
        reproduce(a)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
