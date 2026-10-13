# -*- coding: utf-8 -*-
"""
SubSurface_v6.py - change-aware, reliability-gated monitoring of infrastructure whose state changes over time (extends SubSurface_MC.py and SubSurface_v4.py, unchanged).

EVERYTHING HERE IS A SIMULATION UNDER STATED ASSUMPTIONS. No field data are used. The scaffold structural criterion is a synthetic benchmark, not an engineering model.

Two domains share one framework (elements with a latent hazard state, observed asynchronously):
  utility   200 segments of a corridor; hazard = a utility lies in the excavation envelope; periodic GPR/EM survey (capability from the sensor model of SubSurface_MC.py),
            continuous point monitors, work orders
  scaffold  240 members of a temporary scaffold; hazard = a member is missing or disconnected; periodic vision sweep (with occlusion), continuous point sensors, work permits
Per element and epoch: authorized and unauthorized modification events; a hazard state that an event may create or remove; event reports from point sensors (which can fail, flagged or not);
state readings from a periodic survey; permit records (which can be missing, misattributed or spurious).

Estimators (hazard posterior per element): static twin (S0: surveys only, the state assumed constant between and across them); static-state fusion (S1); dynamic hidden-Markov estimator without work records (D0);
with permit suppression, the rule 'a change matching a permit is logged and not escalated' (D1); with the permit as contextual evidence (D2); and the reliability-gated estimator (G):
D2 run over a set of model alternatives, alternatives rejected by the survey predictive likelihood are dropped, and the supremum of the retained hazard probabilities is used.

Usage
  python SubSurface_v6.py --demo
  python SubSurface_v6.py --reproduce --out results_v6 --seed 42 [--quick]
"""
import argparse
import copy
import json
import os
import sys
import time
import zlib

import numpy as np

import SubSurface_MC as S

VERSION = "2.0.0"
TAU_A, TAU_P = 0.05, 0.50                  # release if P(hazard) <= TAU_A; escalate if >= TAU_P; otherwise verify
TAU_S = 0.05                               # structure-level continue threshold (scaffold)
CGRID = np.round(np.arange(0.02, 0.9801, 0.02), 2)
T_EPOCHS = 48
DELTA = 12                                 # periodic survey interval (epochs)
PERMIT_WINDOW = (-1, 1)                    # a recorded authorized change at epoch t has a permit active from t-1 to t+1

DOMAINS = {
    "utility": dict(label="Underground utilities", N=200, lam_A=0.004, lam_U=0.0015, theta_A=0.5, theta_U=0.8, rho_fix=0.3, pi0=0.35, fv=0.02,
                    d_e=0.90, f_e=0.001, fail=0.004, diag=0.80, rho_rec=0.70, eta=0.10, sigma=0.002, occl=0.0, crit_share=0.0, bay=1, epoch="month",
                    node_cost=1.0, survey_cost=40.0),
    "scaffold": dict(label="Industrial scaffolding", N=240, lam_A=0.00015, lam_U=0.00003, theta_A=0.4, theta_U=0.95, rho_fix=0.5, pi0=0.0004, fv=0.002,
                     d_e=0.95, f_e=0.0005, fail=0.003, diag=0.80, rho_rec=0.80, eta=0.05, sigma=0.003, occl=0.25, crit_share=0.20, bay=12, epoch="day",
                     node_cost=1.0, survey_cost=10.0),
}
SCENARIOS = {                              # true-world departures from the assumptions the estimators are calibrated on
    "nominal": dict(),
    "silent_sensor_failures": dict(diag=0.0, fail_mult=3.0),
    "erroneous_permits": dict(eta=0.5, rho_rec=0.5, sigma_mult=4.0),
    "event_rate_and_bursts": dict(rate_mult=3.0, burst=0.5),
    "weak_survey": dict(dv_mult=0.6),
    "combined": dict(diag=0.0, fail_mult=3.0, eta=0.5, rho_rec=0.5, sigma_mult=4.0, rate_mult=3.0, burst=0.5, dv_mult=0.6),
}
SCEN_LABEL = {"nominal": "Nominal", "silent_sensor_failures": "Unflagged sensor failures (3x)", "erroneous_permits": "Erroneous permits", "event_rate_and_bursts": "3x event rate with bursts",
              "weak_survey": "Survey weaker than assumed", "combined": "Combined"}


def rng_for(seed, tag, k=0):
    return np.random.default_rng(np.random.SeedSequence([int(seed), zlib.crc32(tag.encode()), int(k)]))


# ----------------------------------------------------------------------------------------------------------------
# Sites
# ----------------------------------------------------------------------------------------------------------------
def make_site(rng, dom):
    D = DOMAINS[dom]
    N = D["N"]
    site = dict(dom=dom, N=N)
    if dom == "utility":
        cfg = S.CFG
        w = S.cell_weights(cfg).ravel()
        cell = rng.choice(w.size, N, p=w / w.sum())
        soil, util = cell // S.NU, cell % S.NU
        dr = np.array(cfg["util"]["depth_m"], float)
        depth = dr[util, 0] + (dr[util, 1] - dr[util, 0]) * rng.random(N)
        dv = np.zeros(N)
        for s_ in np.unique(soil):
            for u_ in np.unique(util[soil == s_]):
                m = (soil == s_) & (util == u_)
                dv[m] = np.asarray(S.pd_fused(cfg, s_, u_, depth[m]), float)
        site["dv"] = np.clip(dv, 0.0, 0.99)
        site["imp"] = np.array(cfg["util"]["consequence"], float)[util] / 10.0
        site["crit"] = np.zeros(N, bool)
        site["bay"] = np.arange(N)
        site["occluded"] = np.zeros(N, bool)
    else:
        bay = np.arange(N) // D["bay"]
        nb = bay.max() + 1
        occ_bay = rng.random(nb) < D["occl"]
        crit = rng.random(N) < D["crit_share"]
        site["dv"] = np.where(occ_bay[bay], 0.0, 0.85)
        site["imp"] = np.where(crit, 1.0, 0.3)
        site["crit"] = crit
        site["bay"] = bay
        site["occluded"] = occ_bay[bay]
    site["scale"] = rng.gamma(2.0, 0.5, N)             # heterogeneity of the modification rate (mean 1)
    return site


# ----------------------------------------------------------------------------------------------------------------
# World
# ----------------------------------------------------------------------------------------------------------------
def simulate_world(rng, site, R, scen=None, sensors=None, survey_interval=DELTA, T=T_EPOCHS, params_override=None):
    """arrays have shape (T+1, R, N) unless stated. sensors: boolean mask (N,) of elements with a continuous point sensor"""
    dom = site["dom"]
    D = dict(DOMAINS[dom])
    sc = dict(SCENARIOS["nominal"] if scen is None else scen)
    if params_override:
        D.update(params_override)
    N = site["N"]
    rm = sc.get("rate_mult", 1.0)
    lamA = D["lam_A"] * rm * site["scale"][None, :]
    lamU = D["lam_U"] * rm * site["scale"][None, :]
    EA = np.zeros((T + 1, R, N), bool)
    EU = np.zeros((T + 1, R, N), bool)
    uA = rng.random((T + 1, R, N)); uU = rng.random((T + 1, R, N))
    EA[1:] = uA[1:] < lamA[None]
    EU[1:] = uU[1:] < lamU[None]
    kap = sc.get("burst", 0.0)
    if kap > 0:                                         # bursts: an event may take the next element with it (mismatch: the estimators assume independence)
        spread = rng.random((T + 1, R, N)) < kap
        EAn = np.zeros_like(EA); EUn = np.zeros_like(EU)
        EAn[:, :, 1:] = EA[:, :, :-1] & spread[:, :, 1:]
        EUn[:, :, 1:] = EU[:, :, :-1] & spread[:, :, 1:]
        EA |= EAn; EU |= EUn
    E = EA | EU
    h = np.zeros((T + 1, R, N), bool)
    h[0] = rng.random((R, N)) < D["pi0"]
    ua = rng.random((T + 1, R, N)); ur = rng.random((T + 1, R, N))
    for t in range(1, T + 1):
        prev = h[t - 1]
        make = (EA[t] & (ua[t] < D["theta_A"])) | (EU[t] & (ua[t] < D["theta_U"]))
        fix = ur[t] < D["rho_fix"]
        h[t] = np.where(E[t], np.where(prev, ~fix, make), prev)
    # permits
    rho = sc.get("rho_rec", D["rho_rec"]); eta = sc.get("eta", D["eta"]); sig = D["sigma"] * sc.get("sigma_mult", 1.0)
    W = np.zeros((T + 1, R, N), bool)
    rec = EA & (rng.random((T + 1, R, N)) < rho)
    wrong = rng.random((T + 1, R, N)) < eta
    tt, rr, ii = np.nonzero(rec)
    tgt = np.where(wrong[tt, rr, ii], rng.integers(0, N, tt.size), ii)
    for dt in range(PERMIT_WINDOW[0], PERMIT_WINDOW[1] + 1):
        t2 = np.clip(tt + dt, 0, T)
        W[t2, rr, tgt] = True
    sp = rng.random((T + 1, R, N)) < sig
    for dt in range(0, 3):
        W[dt:] |= sp[:T + 1 - dt]
    # continuous point sensors (event reports)
    d_e, f_e = D["d_e"], D["f_e"]
    sens = np.zeros(N, bool) if sensors is None else np.asarray(sensors, bool)
    fail_t = rng.geometric(np.clip(D["fail"] * sc.get("fail_mult", 1.0), 1e-9, 1.0), (R, N))      # epoch of failure (>= 1)
    diag = sc.get("diag", D["diag"])
    flagged = rng.random((R, N)) < diag
    tgrid = np.arange(T + 1)[:, None, None]
    failed = tgrid >= fail_t[None]
    flag_failed = failed & flagged[None] & (tgrid >= fail_t[None] + 1)
    Ye = np.where(E, rng.random((T + 1, R, N)) < d_e, rng.random((T + 1, R, N)) < f_e) & sens[None, None, :] & ~failed
    # periodic survey (state reading of the hazard)
    surv_t = np.zeros(T + 1, bool)
    if survey_interval:
        surv_t[::survey_interval] = True
    dv_true = np.clip(site["dv"] * sc.get("dv_mult", 1.0), 0, 0.999)
    Yv = np.where(h, rng.random((T + 1, R, N)) < dv_true[None, None, :], rng.random((T + 1, R, N)) < D["fv"])
    cover = (site["dv"] > 0) & ~site["occluded"]
    return dict(E=E, EA=EA, EU=EU, h=h, W=W, Ye=Ye, Yv=Yv, surv_t=surv_t, cover=cover, sens=sens, flag_failed=flag_failed, failed=failed, T=T, R=R, N=N, D=D, scen=sc)


# ----------------------------------------------------------------------------------------------------------------
# Estimators
# ----------------------------------------------------------------------------------------------------------------
def calibrate(seed, dom, n_sites=8, R=40, scen=None):
    """event and permit statistics of the NOMINAL world, estimated on separate calibration sites (labels known)"""
    cnt = dict(ev_perm=0, n_perm=0, auth_perm=0, ev_nop=0, n_nop=0, auth_nop=0)
    for s_ in range(n_sites):
        rng = rng_for(seed, "cal-" + dom, s_)
        site = make_site(rng, dom)
        w = simulate_world(rng, site, R, scen, None)
        E, EA, W = w["E"][1:], w["EA"][1:], w["W"][1:]
        cnt["n_perm"] += W.sum(); cnt["ev_perm"] += (E & W).sum(); cnt["auth_perm"] += (EA & W).sum()
        cnt["n_nop"] += (~W).sum(); cnt["ev_nop"] += (E & ~W).sum(); cnt["auth_nop"] += (EA & ~W).sum()
    e_perm = cnt["ev_perm"] / max(cnt["n_perm"], 1); e_nop = cnt["ev_nop"] / max(cnt["n_nop"], 1)
    a_perm = cnt["auth_perm"] / max(cnt["ev_perm"], 1); a_nop = cnt["auth_nop"] / max(cnt["ev_nop"], 1)
    n_all = cnt["n_perm"] + cnt["n_nop"]
    e_all = (cnt["ev_perm"] + cnt["ev_nop"]) / n_all
    a_all = (cnt["auth_perm"] + cnt["auth_nop"]) / max(cnt["ev_perm"] + cnt["ev_nop"], 1)
    D = DOMAINS[dom]
    return dict(e_perm=float(e_perm), a_perm=float(a_perm), e_nop=float(e_nop), a_nop=float(a_nop), e_all=float(e_all), a_all=float(a_all), theta_A=D["theta_A"], theta_U=D["theta_U"],
                rho_fix=D["rho_fix"], pi0=D["pi0"], d_e=D["d_e"], f_e=D["f_e"], fv=D["fv"], n_sites=n_sites, R=R)


def _bayes(p, l1, l0):
    num = p * l1
    return num / np.clip(num + (1 - p) * l0, 1e-300, None)


def run_estimator(world, site, par, mode, use_sensors=True, use_survey=True, health_aware=True, rate_mult=1.0, permits_uninformative=False, sensors_uninformative=False, dv_mult=1.0, kappa=0.0):
    """hazard posterior P (T+1, R, N), cumulative survey predictive log-likelihood (T+1, R), authorization posterior at events (T+1, R, N)
    modes: S0 (static twin: surveys only, state assumed constant), S1 (static-state fusion), D0 (dynamic, no work records), D1 (dynamic, permit suppression), D2 (dynamic, permit as context)"""
    T, R, N = world["T"], world["R"], world["N"]
    P = np.zeros((T + 1, R, N)); ll = np.zeros((T + 1, R)); PA = np.full((T + 1, R, N), np.nan)
    dv = np.clip(site["dv"] * dv_mult, 0, 0.999)
    fv, d_e, f_e = par["fv"], par["d_e"], par["f_e"]
    cov = world["cover"]
    sens = world["sens"] & use_sensors & (not sensors_uninformative)
    pi0 = par["pi0"]

    def survey_lik(y):
        l1 = np.where(y, dv, 1 - dv)[...]
        l0 = np.where(y, fv, 1 - fv)
        return np.where(cov, l1, 1.0), np.where(cov, l0, 1.0)
    # t = 0
    p = np.full((R, N), pi0)
    if use_survey and world["surv_t"][0]:
        l1, l0 = survey_lik(world["Yv"][0])
        ll[0] += np.log(np.clip(p * l1 + (1 - p) * l0, 1e-300, None)).sum(1)
        p = _bayes(p, l1, l0)
    P[0] = p
    last_survey_p = p.copy()
    last_survey_t = np.zeros(1)
    for t in range(1, T + 1):
        y_e = world["Ye"][t]
        w_t = world["W"][t] if mode in ("D1", "D2") and not permits_uninformative else np.zeros((R, N), bool)
        healthy = ~(world["flag_failed"][t] & health_aware)
        sens_t = sens[None, :] & healthy
        if mode == "S0":
            if use_survey and world["surv_t"][t]:
                l1, l0 = survey_lik(world["Yv"][t])
                last_survey_p = _bayes(last_survey_p, l1, l0)
                last_survey_t = np.full(1, t)
            age = t - last_survey_t[0]
            P[t] = pi0 + (last_survey_p - pi0) * np.exp(-kappa * age) if kappa > 0 else last_survey_p
            continue
        if mode == "S1":
            p = P[t - 1]
            rep = y_e & sens_t
            p = np.where(rep, _bayes(p, np.full_like(p, d_e), np.full_like(p, f_e)), p)
            if use_survey and world["surv_t"][t]:
                l1, l0 = survey_lik(world["Yv"][t])
                p = _bayes(p, l1, l0)
            P[t] = p
            continue
        # dynamic estimators
        p_prev = P[t - 1]
        if mode == "D2":
            e = np.where(w_t, par["e_perm"], par["e_nop"]); a = np.where(w_t, par["a_perm"], par["a_nop"])
        else:
            e = np.full((R, N), par["e_all"]); a = np.full((R, N), par["a_all"])
        e = np.clip(e * rate_mult, 0, 0.95)
        thA, thU, rf = par["theta_A"], par["theta_U"], par["rho_fix"]
        pa, pu, p0e = e * a, e * (1 - a), 1 - e
        h1_0 = p_prev * p0e                                           # no event
        h0_0 = (1 - p_prev) * p0e
        h1_A = pa * ((1 - p_prev) * thA + p_prev * (1 - rf)); h0_A = pa * ((1 - p_prev) * (1 - thA) + p_prev * rf)
        h1_U = pu * ((1 - p_prev) * thU + p_prev * (1 - rf)); h0_U = pu * ((1 - p_prev) * (1 - thU) + p_prev * rf)
        lE1 = np.where(sens_t, np.where(y_e, d_e, 1 - d_e), 1.0)       # likelihood of the report under an event
        lE0 = np.where(sens_t, np.where(y_e, f_e, 1 - f_e), 1.0)       # under no event
        n1 = h1_0 * lE0 + (h1_A + h1_U) * lE1
        n0 = h0_0 * lE0 + (h0_A + h0_U) * lE1
        tot = np.clip(n1 + n0, 1e-300, None)
        p_new = n1 / tot
        wA = (pa * lE1)
        wU = (pu * lE1)
        PA[t] = wA / np.clip(wA + wU, 1e-300, None)                   # authorization posterior given an event
        if mode == "D1":                                              # permit suppression: a reported change that matches an active permit is logged and not escalated
            sup = world["W"][t] & y_e & sens_t
            p_new = np.where(sup, p_prev, p_new)
        if use_survey and world["surv_t"][t]:
            l1, l0 = survey_lik(world["Yv"][t])
            ll[t] += np.log(np.clip(p_new * l1 + (1 - p_new) * l0, 1e-300, None)).sum(1)
            pn = _bayes(p_new, l1, l0)
            if mode == "D1":
                sup2 = world["W"][t] & world["Yv"][t] & cov[None, :]
                pn = np.where(sup2, p_new, pn)
            p_new = pn
        ll[t] += ll[t - 1]
        P[t] = np.clip(p_new, 0, 1)
    return P, ll, PA


GATE_MEMBERS = [("nominal", {}), ("event_rate_x3", dict(rate_mult=3.0)), ("permits_uninformative", dict(permits_uninformative=True)), ("point_sensors_uninformative", dict(sensors_uninformative=True)),
                ("survey_weaker", dict(dv_mult=0.6)), ("worst_combined", dict(rate_mult=3.0, sensors_uninformative=True, dv_mult=0.6, permits_uninformative=True))]
GATE_DELTA = 5.0


def run_gate(world, site, par, select=True, **kw):
    """reliability-gated estimator: D2 over the model alternatives; alternatives whose survey predictive log-likelihood falls more than GATE_DELTA behind the best are dropped;
    returns the supremum of the retained hazard probabilities, the nominal one, and the number of retained alternatives"""
    outs = [run_estimator(world, site, par, "D2", **{**kw, **m}) for _, m in GATE_MEMBERS]
    ll = np.stack([o[1] for o in outs])                                   # (M, T+1, R)
    keep = ll >= (ll.max(0, keepdims=True) - GATE_DELTA) if select else np.ones_like(ll, bool)
    Ps = np.stack([o[0] for o in outs])                                   # (M, T+1, R, N)
    Pg = np.where(keep[..., None], Ps, 0.0).max(0)
    Pg = np.maximum(Pg, 0.0)
    return Pg, outs[0][0], keep.sum(0).mean()


# ----------------------------------------------------------------------------------------------------------------
# Decisions and metrics
# ----------------------------------------------------------------------------------------------------------------
def decide(P, ta=TAU_A, tp=TAU_P):
    return np.where(P <= ta, 0, np.where(P >= tp, 2, 1)).astype(np.int8)       # 0 release, 1 verify, 2 escalate


def element_metrics(P, world, ta=TAU_A, tp=TAU_P, mask=None, t0=0):
    h = world["h"][t0:]
    d = decide(P[t0:], ta, tp)
    if mask is not None:
        h, d = h[:, :, mask], d[:, :, mask]
    rel = d == 0
    n = rel.size
    r = dict(n=float(n), release=float(rel.sum()), unsafe=float((rel & h).sum()), escalate=float((d == 2).sum()), false_escalate=float(((d == 2) & ~h).sum()), verify=float((d == 1).sum()),
             hazard=float(h.sum()), safe=float((~h).sum()))
    r["coverage"] = r["release"] / n
    r["cond_risk"] = r["unsafe"] / r["release"] if r["release"] > 0 else np.nan
    r["unsafe_prob"] = r["unsafe"] / n
    r["false_escalation_rate"] = r["false_escalate"] / r["safe"] if r["safe"] > 0 else np.nan
    r["verify_share"] = r["verify"] / n
    return r


def detection_delay(P, world, ta=TAU_A, mask=None):
    """for each hazard onset (h goes 0 -> 1): epochs until the decision is no longer 'release'; missed if it never happens before the hazard ends or the horizon"""
    h = world["h"]
    d = decide(P, ta)
    T = h.shape[0] - 1
    onset = np.full(h.shape[1:], -1)
    delays, missed = [], 0
    if mask is not None:
        h, d = h[:, :, mask], d[:, :, mask]
        onset = np.full(h.shape[1:], -1)
    for t in range(1, T + 1):
        new = h[t] & ~h[t - 1]
        onset = np.where(new, t, onset)
        awaiting = onset >= 0
        flagged = awaiting & (d[t] != 0)
        if flagged.any():
            delays.append((t - onset[flagged]).astype(float))
        onset = np.where(flagged, -1, onset)
        ended = awaiting & ~flagged & ~h[t]
        missed += int(ended.sum())
        onset = np.where(ended, -1, onset)
    missed += int((onset >= 0).sum())
    dl = np.concatenate(delays) if delays else np.array([])
    return dict(n_flagged=int(dl.size), n_missed=int(missed), mean_delay=float(dl.mean()) if dl.size else np.nan, share_missed=float(missed / max(dl.size + missed, 1)))


def rc_points(P, h, nb=240):
    """coverage and conditional risk of releasing every element whose hazard probability is at most a threshold (log-spaced thresholds)"""
    edges = np.concatenate([[0.0], np.logspace(-7, 0, nb)])
    cnt, _ = np.histogram(P.ravel(), bins=edges)
    haz, _ = np.histogram(P[h].ravel(), bins=edges)
    c, k = np.cumsum(cnt), np.cumsum(haz)
    cov = c / P.size
    risk = np.where(c > 0, k / np.maximum(c, 1), np.nan)
    return cov, risk


def rc_curve(P, h, grid=CGRID):
    cov, risk = rc_points(P, h)
    out = np.full(grid.size, np.nan)
    ok = np.isfinite(risk)
    cv, rk = cov[ok], risk[ok]
    j = np.searchsorted(cv, grid)
    good = j < cv.size
    out[good] = rk[j[good]]
    return out


# ---- scaffold structure level --------------------------------------------------------------------------------------
def structure_unsafe_prob(P, site):
    """P(structure unsafe) from independent element hazard probabilities: unsafe if any critical member is hazardous or at least two non-critical members of a bay are hazardous"""
    crit, bay = site["crit"], site["bay"]
    Pc = np.clip(P, 0.0, 1 - 1e-9)
    safe_c = np.prod(1 - Pc[..., crit], axis=-1)
    nb = bay.max() + 1
    safe_n = np.ones(P.shape[:-1])
    for b in range(nb):
        m = (bay == b) & ~crit
        if not m.any():
            continue
        q = Pc[..., m]
        p0 = np.prod(1 - q, axis=-1)
        p1 = p0 * np.sum(q / (1 - q), axis=-1)
        safe_n *= np.clip(p0 + p1, 0, 1)
    return 1.0 - safe_c * safe_n


def structure_unsafe_truth(h, site):
    crit, bay = site["crit"], site["bay"]
    bad = h[..., crit].any(-1)
    nb = bay.max() + 1
    for b in range(nb):
        m = (bay == b) & ~crit
        if m.any():
            bad |= h[..., m].sum(-1) >= 2
    return bad


def structure_metrics(Pu, truth, ts=TAU_S, tp=TAU_P):
    cont = Pu <= ts
    esc = Pu >= tp
    n = cont.size
    return dict(n=float(n), coverage=float(cont.mean()), cond_risk=float((cont & truth).sum() / max(cont.sum(), 1)) if cont.any() else np.nan, unsafe_prob=float((cont & truth).sum() / n),
                escalate=float(esc.mean()), false_escalation_rate=float((esc & ~truth).sum() / max((~truth).sum(), 1)), unsafe_share=float(truth.mean()))


# ----------------------------------------------------------------------------------------------------------------
# Baselines of the scaffold domain
# ----------------------------------------------------------------------------------------------------------------
def baseline_any_alarm(world, site):
    """escalate the structure once any healthy point sensor has reported a change (no probabilities, no survey, no work records); continue otherwise"""
    T = world["T"]
    y = (world["Ye"] & ~world["flag_failed"]).any(-1)
    flag = np.zeros(world["R"], bool)
    out = np.zeros((T + 1, world["R"]), bool)
    for t in range(T + 1):
        flag |= y[t]
        out[t] = flag
    return ~out


def baseline_ssi(world, site, par, w_ev=40.0, w_sv=40.0, amber=30.0, red=60.0, suppress=True):
    """a weighted index of the kind used in operational displays (0-100): importance-weighted event reports and survey detections, permit-matched changes suppressed; green below 'amber'"""
    T = world["T"]
    imp = site["imp"] / site["imp"].sum() * 10.0
    score = np.zeros((T + 1, world["R"]))
    ev = np.zeros(world["R"]); sv = np.zeros(world["R"])
    for t in range(T + 1):
        rep = world["Ye"][t] & ~world["flag_failed"][t]
        if suppress:
            rep = rep & ~world["W"][t]
        ev = ev + (rep * imp[None, :]).sum(-1)
        if world["surv_t"][t]:
            sd = world["Yv"][t] & world["cover"][None, :]
            if suppress:
                sd = sd & ~world["W"][t]
            sv = (sd * imp[None, :]).sum(-1)
        score[t] = np.clip(w_ev * ev + w_sv * sv, 0, 100)
    return score < amber                                                # continue iff green


# ----------------------------------------------------------------------------------------------------------------
# Sensor allocation
# ----------------------------------------------------------------------------------------------------------------
def allocate(strategy, site, budget, rng, risk_score=None):
    N = site["N"]
    m = np.zeros(N, bool)
    if budget <= 0:
        return m
    if strategy == "random":
        m[rng.choice(N, budget, replace=False)] = True
    elif strategy == "uniform":
        m[np.round(np.linspace(0, N - 1, budget)).astype(int)] = True
    elif strategy == "uncertainty":                                    # least observable by the periodic survey, most uncertain prior hazard
        score = (1 - site["dv"] * (~site["occluded"])) * site["scale"]
        m[np.argsort(-score, kind="stable")[:budget]] = True
    elif strategy == "risk_optimised":
        m[np.argsort(-risk_score, kind="stable")[:budget]] = True
    return m


def pilot_risk_score(seed, site, dom, par, R=40, T=T_EPOCHS, k=0):
    """training worlds (independent of the test worlds): mean importance-weighted unsafe-release mass per element without point sensors"""
    rng = rng_for(seed, "train-%s" % dom, k)
    w = simulate_world(rng, site, R, None, None)
    P = run_estimator(w, site, par, "D2")[0]
    d = decide(P)
    return ((d == 0) & w["h"]).mean((0, 1)) * site["imp"] + 1e-9 * site["scale"]


# ----------------------------------------------------------------------------------------------------------------
# Self-tests
# ----------------------------------------------------------------------------------------------------------------
def selftests_v6(seed=42, verbose=True):
    res = []

    def rec(name, ok, detail):
        res.append(dict(name=name, passed=bool(ok), detail=detail))
        if verbose:
            print("  [%s] %s: %s" % ("PASS" if ok else "FAIL", name, detail))
    par = calibrate(seed, "scaffold", 3, 20)
    rng = rng_for(seed, "st", 0)
    site = make_site(rng, "scaffold")
    w = simulate_world(rng, site, 10, None, np.arange(site["N"]) % 10 == 0)
    P, ll, PA = run_estimator(w, site, par, "D2")
    rec("posterior probabilities lie in [0,1] and are finite", bool(np.isfinite(P).all() and P.min() >= 0 and P.max() <= 1), "range %.2e to %.4f" % (P.min(), P.max()))
    # no events possible: dynamic estimator equals the static Bayes update
    par0 = dict(par, e_all=0.0, e_nop=0.0, e_perm=0.0)
    w2 = simulate_world(rng_for(seed, "st", 1), site, 6, None, None)
    Pd = run_estimator(w2, site, par0, "D0")[0]
    Ps1 = run_estimator(w2, site, par, "S1")[0]
    rec("with no modification events the dynamic estimator reduces to static Bayes fusion of the surveys", bool(np.allclose(Pd, Ps1, atol=1e-9)), "max abs diff %.1e" % np.abs(Pd - Ps1).max())
    # perfect survey, exact state
    sitep = dict(site); sitep["dv"] = np.full(site["N"], 0.999); sitep["occluded"] = np.zeros(site["N"], bool)
    parp = dict(par, fv=1e-9)
    w3 = simulate_world(rng_for(seed, "st", 2), sitep, 4, None, None, params_override=dict(fv=0.0))
    w3["cover"] = np.ones(site["N"], bool)
    Pp = run_estimator(w3, sitep, parp, "D0")[0]
    t_s = np.flatnonzero(w3["surv_t"])[0]
    rec("a (nearly) perfect survey makes the posterior equal the true hazard at the survey epoch", bool(np.abs(Pp[t_s] - w3["h"][t_s]).max() < 1e-2), "max abs error %.4f" % np.abs(Pp[t_s] - w3["h"][t_s]).max())
    # flagged failed sensor contributes nothing
    wf = simulate_world(rng_for(seed, "st", 3), site, 6, None, np.ones(site["N"], bool))
    wf["flag_failed"][:] = True
    a = run_estimator(wf, site, par, "D2")[0]
    b = run_estimator(wf, site, par, "D2", use_sensors=False)[0]
    rec("a sensor flagged as failed contributes no evidence", bool(np.allclose(a, b, atol=1e-12)), "max abs diff %.1e" % np.abs(a - b).max())
    # permit suppression ignores a matched report
    ws = simulate_world(rng_for(seed, "st", 4), site, 4, None, np.ones(site["N"], bool))
    ws["Ye"][:] = False; ws["Ye"][5] = True; ws["W"][:] = False; ws["W"][5] = True; ws["flag_failed"][:] = False; ws["failed"][:] = False
    a = run_estimator(ws, site, par, "D1")[0]
    b = run_estimator(ws, site, par, "D0")[0]
    rec("permit suppression holds the posterior at a permit-matched report while the permit-free estimator raises it", bool(np.allclose(a[5], a[4]) and (b[5] > b[4]).all()), "suppressed %.4f -> %.4f, unsuppressed %.4f -> %.4f" % (a[4].mean(), a[5].mean(), b[4].mean(), b[5].mean()))
    # structure probability against enumeration (tiny structure)
    tiny = dict(N=6, crit=np.array([1, 0, 0, 0, 0, 0], bool), bay=np.array([0, 0, 0, 1, 1, 1]))
    pp = np.array([[0.1, 0.2, 0.3, 0.4, 0.05, 0.6]])
    import itertools
    tot = 0.0
    for bits in itertools.product([0, 1], repeat=6):
        pr = np.prod([pp[0, i] if b_ else 1 - pp[0, i] for i, b_ in enumerate(bits)])
        if structure_unsafe_truth(np.array([bits], bool), tiny)[0]:
            tot += pr
    rec("structure unsafe probability equals enumeration", abs(float(structure_unsafe_prob(pp, tiny)[0]) - tot) < 1e-12, "%.6f vs %.6f" % (float(structure_unsafe_prob(pp, tiny)[0]), tot))
    # event rates and permit coverage
    wr = simulate_world(rng_for(seed, "st", 5), make_site(rng_for(seed, "st", 6), "utility"), 60, None, None)
    D = DOMAINS["utility"]
    rate = wr["E"][1:].mean()
    exp = (D["lam_A"] + D["lam_U"])
    rec("simulated event rate matches the configured rate", abs(rate - exp) / exp < 0.12, "%.5f vs %.5f" % (rate, exp))
    ea = wr["EA"][1:]
    share = (ea & wr["W"][1:]).sum() / max(ea.sum(), 1)
    rec("most authorized events have an active permit at the event epoch (record rate x correct attribution)", abs(share - D["rho_rec"] * (1 - D["eta"])) < 0.08 + 0.05, "%.3f vs about %.3f" % (share, D["rho_rec"] * (1 - D["eta"])))
    # delay on a toy
    tw = dict(h=np.zeros((5, 1, 1), bool)); tw["h"][2:, 0, 0] = True
    Pt = np.zeros((5, 1, 1)); Pt[4] = 1.0
    dl = detection_delay(Pt, tw)
    rec("detection delay on a toy case", dl["n_flagged"] == 1 and dl["mean_delay"] == 2.0, str(dl))
    # rc curve against sorting
    rg = np.random.default_rng(1)
    sc_ = rg.random((20, 10, 10)) ** 3; hh = rg.random(sc_.shape) < sc_
    cov, risk = rc_points(sc_, hh)
    j = np.searchsorted(cov, 0.5)
    o = np.argsort(sc_.ravel()); k = int(0.5 * sc_.size)
    ref = hh.ravel()[o[:k]].mean()
    rec("histogram risk-coverage curve agrees with sorting", abs(risk[j] - ref) < 0.03, "%.3f vs %.3f" % (risk[j], ref))
    # gate dominates nominal
    wg = simulate_world(rng_for(seed, "st", 7), site, 6, None, np.arange(site["N"]) % 10 == 0)
    Pg, Pn, nk = run_gate(wg, site, par)
    rec("the gated probability is never below the nominal one when the nominal alternative is retained", bool((Pg >= Pn - 1e-12).mean() > 0.99), "share %.4f, mean retained alternatives %.2f" % ((Pg >= Pn - 1e-12).mean(), nk))
    # determinism
    wa = simulate_world(rng_for(seed, "st", 9), site, 3, None, None); wb = simulate_world(rng_for(seed, "st", 9), site, 3, None, None)
    rec("a simulated world is reproducible from its seed", bool(np.array_equal(wa["h"], wb["h"]) and np.array_equal(wa["Yv"], wb["Yv"])), "arrays equal")
    return res


# ----------------------------------------------------------------------------------------------------------------
# Experiments
# ----------------------------------------------------------------------------------------------------------------
METHODS = ["S0", "S0d", "S1", "D0", "D1", "D2", "G", "ORACLE"]
METHOD_LABEL = {"S0": "Static twin (surveys only, constant state)", "S0d": "Static twin with ad hoc confidence decay", "S1": "Static-state probabilistic fusion", "D0": "Dynamic estimator, no work records",
                "D1": "Dynamic, permit suppression", "D2": "Dynamic, permit as context", "G": "Reliability-gated (change-aware)", "ORACLE": "Oracle (true rates and sensor health)"}
KAPPA = 0.15


def _oracle_par(world, site, base):
    D = world["D"]; sc = world["scen"]
    rm = sc.get("rate_mult", 1.0)
    lamA, lamU = D["lam_A"] * rm, D["lam_U"] * rm
    rho = sc.get("rho_rec", D["rho_rec"]); eta = sc.get("eta", D["eta"])
    par = dict(base)
    # event statistics of the true world, from the world itself
    E, EA, W = world["E"][1:], world["EA"][1:], world["W"][1:]
    par["e_perm"] = float((E & W).sum() / max(W.sum(), 1)); par["a_perm"] = float((EA & W).sum() / max((E & W).sum(), 1))
    par["e_nop"] = float((E & ~W).sum() / max((~W).sum(), 1)); par["a_nop"] = float((EA & ~W).sum() / max((E & ~W).sum(), 1))
    par["e_all"] = float(E.mean()); par["a_all"] = float(EA.sum() / max(E.sum(), 1))
    return par


def estimate(world, site, par, method, **kw):
    """returns hazard probabilities (T+1, R, N) for a method"""
    if method == "S0":
        return run_estimator(world, site, par, "S0", **kw)[0]
    if method == "S0d":
        return run_estimator(world, site, par, "S0", kappa=KAPPA, **kw)[0]
    if method == "S1":
        return run_estimator(world, site, par, "S1", **kw)[0]
    if method in ("D0", "D1", "D2"):
        return run_estimator(world, site, par, method, **kw)[0]
    if method == "G":
        return run_gate(world, site, par, **kw)[0]
    if method == "ORACLE":
        o = _oracle_par(world, site, par)
        kw2 = dict(kw); kw2["health_aware"] = True
        w2 = dict(world); w2["flag_failed"] = world["failed"]                     # the oracle knows the true sensor health
        o["f_e"] = par["f_e"]
        return run_estimator(w2, site, o, "D2", **kw2)[0]
    raise ValueError(method)


def ci(vals):
    v = np.asarray([x for x in vals if np.isfinite(x)], float)
    if v.size == 0:
        return [None, None]
    m, h = S.ci_stats(v) if v.size > 1 else (float(v.mean()), float("nan"))
    return [float(m), None if np.isnan(h) else float(h)]


def agg(rows, keys):
    return {k: ci([r[k] for r in rows]) for k in keys}


MKEYS = ["coverage", "cond_risk", "unsafe_prob", "false_escalation_rate", "verify_share"]



# ----------------------------------------------------------------------------------------------------------------
# Evaluation of one world
# ----------------------------------------------------------------------------------------------------------------
BASELINES = ["ANY", "SSI", "SSI_NS"]
BASELINE_LABEL = {"ANY": "Any-alarm rule", "SSI": "Weighted index (0-100), permit-matched changes suppressed", "SSI_NS": "Weighted index (0-100), no suppression"}


def site_for(seed, dom, k):
    return make_site(rng_for(seed, "site-" + dom, k), dom)


def world_rng(seed, dom, tag, k):
    return rng_for(seed, "world-%s-%s" % (dom, tag), k)


def baseline_ssi_score(world, site, suppress=True, w_ev=40.0, w_sv=40.0):
    T = world["T"]
    imp = site["imp"] / site["imp"].sum() * 10.0
    score = np.zeros((T + 1, world["R"])); ev = np.zeros(world["R"]); sv = np.zeros(world["R"])
    for t in range(T + 1):
        rep = world["Ye"][t] & ~world["flag_failed"][t]
        if suppress:
            rep = rep & ~world["W"][t]
        ev = ev + (rep * imp[None, :]).sum(-1)
        if world["surv_t"][t]:
            sd = world["Yv"][t] & world["cover"][None, :]
            if suppress:
                sd = sd & ~world["W"][t]
            sv = (sd * imp[None, :]).sum(-1)
        score[t] = np.clip(w_ev * ev + w_sv * sv, 0, 100)
    return score


def evaluate(world, site, par, m, dom, **kw):
    """one site, one method -> dict of raw metrics; structure-level metrics for the scaffold"""
    out = {}
    if m in BASELINES:
        cont = baseline_any_alarm(world, site) if m == "ANY" else baseline_ssi(world, site, par, suppress=(m == "SSI"))
        truth = structure_unsafe_truth(world["h"], site)
        esc = ~cont
        out["structure"] = dict(coverage=float(cont.mean()), cond_risk=float((cont & truth).sum() / max(cont.sum(), 1)) if cont.any() else np.nan, unsafe_prob=float((cont & truth).sum() / cont.size),
                                escalate=float(esc.mean()), false_escalation_rate=float((esc & ~truth).sum() / max((~truth).sum(), 1)))
        if m != "ANY":
            sc_ = baseline_ssi_score(world, site, suppress=(m == "SSI"))
            out["s_curve"] = rc_curve(sc_ / 100.0 + 1e-9, truth)
        return out
    P = estimate(world, site, par, m, **kw)
    out["element"] = element_metrics(P, world)
    out["curve"] = rc_curve(P, world["h"])
    out["delay"] = detection_delay(P, world)
    if dom == "scaffold":
        Pu = structure_unsafe_prob(P, site)
        truth = structure_unsafe_truth(world["h"], site)
        out["structure"] = structure_metrics(Pu, truth)
        out["s_curve"] = rc_curve(Pu, truth)
    return out


def summarise(rows):
    """rows: list over sites of evaluate() outputs -> aggregated record with t-intervals over sites"""
    rec = {}
    if "element" in rows[0]:
        rec["element"] = agg([r["element"] for r in rows], MKEYS)
        rec["curve"] = [ci([r["curve"][j] for r in rows]) for j in range(CGRID.size)]
        rec["delay"] = dict(mean_delay=ci([r["delay"]["mean_delay"] for r in rows]), share_missed=ci([r["delay"]["share_missed"] for r in rows]))
    if "structure" in rows[0]:
        rec["structure"] = agg([r["structure"] for r in rows], ["coverage", "cond_risk", "unsafe_prob", "escalate", "false_escalation_rate"])
    if "s_curve" in rows[0]:
        rec["s_curve"] = [ci([r["s_curve"][j] for r in rows]) for j in range(CGRID.size)]
    return rec


def sensors_budget(strategy, frac, seed, dom, par=None):
    def fn(site, k):
        B = int(round(frac * site["N"]))
        rs = pilot_risk_score(seed, site, dom, par, 40, T_EPOCHS, k) if strategy == "risk_optimised" else None
        return allocate(strategy, site, B, rng_for(seed, "alloc-%s-%s" % (dom, strategy), k), rs)
    return fn


def run_methods(seed, dom, tag, n_sites, R, methods, par, scen=None, sensors_fn=None, survey_interval=DELTA, params_override=None, kw_by_method=None):
    rows = {m: [] for m in methods}
    for k in range(n_sites):
        site = site_for(seed, dom, k)
        sens = sensors_fn(site, k) if sensors_fn else None
        w = simulate_world(world_rng(seed, dom, tag, k), site, R, scen, sens, survey_interval, T_EPOCHS, params_override)
        for m in methods:
            rows[m].append(evaluate(w, site, par, m, dom, **((kw_by_method or {}).get(m, {}))))
    return {m: summarise(rows[m]) for m in methods}


# ----------------------------------------------------------------------------------------------------------------
# E1 / E2: dynamic versus static state, observation age
# ----------------------------------------------------------------------------------------------------------------
def exp_dynamic_static(seed, dom, n_sites, R, par, log):
    methods = ["S0", "S0d", "S1", "D0", "D2"]
    res = run_methods(seed, dom, "e1", n_sites, R, methods, par)
    ages = np.arange(DELTA)
    acc = {m: dict(rel=np.zeros((n_sites, DELTA)), uns=np.zeros((n_sites, DELTA)), pred=np.zeros((n_sites, DELTA)), n=np.zeros((n_sites, DELTA))) for m in methods}
    for k in range(n_sites):
        site = site_for(seed, dom, k)
        w = simulate_world(world_rng(seed, dom, "e1", k), site, R, None, None)
        age = (np.arange(T_EPOCHS + 1) % DELTA)
        for m in methods:
            P = estimate(w, site, par, m)
            d = decide(P) == 0
            for a in ages:
                tt = np.flatnonzero(age == a)
                acc[m]["n"][k, a] = P[tt].size
                acc[m]["rel"][k, a] = d[tt].sum()
                acc[m]["uns"][k, a] = (d[tt] & w["h"][tt]).sum()
                acc[m]["pred"][k, a] = (P[tt] * d[tt]).sum()
    res_age = {}
    for m in methods:
        a_ = acc[m]
        risk = a_["uns"] / np.maximum(a_["rel"], 1); cov = a_["rel"] / a_["n"]; pred = a_["pred"] / np.maximum(a_["rel"], 1)
        res_age[m] = dict(cond_risk=[ci(risk[:, a]) for a in ages], coverage=[ci(cov[:, a]) for a in ages], predicted=[ci(pred[:, a]) for a in ages])
    return dict(methods=res, by_age=res_age, ages=ages.tolist())


def exp_regime(seed, n_sites, R, log):
    """utility domain: static twin and dynamic estimator over event-rate multipliers and survey intervals (estimators recalibrated for each rate)"""
    dom = "utility"
    out = {}
    for rm in (0.25, 0.5, 1.0, 2.0, 4.0):
        sc = dict(rate_mult=rm)
        par = calibrate(seed, dom, 6, 30, sc)
        for iv in (6, 12, 24, 48):
            r = run_methods(seed, dom, "reg-%s-%s" % (rm, iv), n_sites, R, ["S0", "D2"], par, sc, None, iv)
            out["%s|%s" % (rm, iv)] = {m: dict(unsafe_prob=r[m]["element"]["unsafe_prob"], cond_risk=r[m]["element"]["cond_risk"], coverage=r[m]["element"]["coverage"]) for m in r}
        log("   regime rate x%s" % rm)
    return out


# ----------------------------------------------------------------------------------------------------------------
# E3: permit reconciliation
# ----------------------------------------------------------------------------------------------------------------
def exp_permits(seed, dom, n_sites, R, par, log):
    """a point sensor on every element, so that the evidence on each change is the same; the work-event information is the only difference between D0, D1 and D2"""
    methods = ["D0", "D1", "D2"]
    cases = ["no_change_no_permit", "change_valid_permit", "change_no_permit", "change_missing_or_wrong_record"]
    acc = {m: {c: np.zeros((n_sites, 3)) for c in cases} for m in methods}
    attr = {m: np.zeros((n_sites, 4)) for m in methods}
    base = {m: [] for m in methods}
    dl = {m: [] for m in methods}
    for k in range(n_sites):
        site = site_for(seed, dom, k)
        w = simulate_world(world_rng(seed, dom, "e3", k), site, R, None, np.ones(site["N"], bool))
        E, EA, EU, Wp, h = w["E"], w["EA"], w["EU"], w["W"], w["h"]
        T = w["T"]
        for m in methods:
            P, _, PA = run_estimator(w, site, par, m)
            flag = decide(P) != 0
            Ev = E[1:T - 1]; nxt = flag[3:T + 1]; hz = h[3:T + 1]
            Wm = Wp[1:T - 1]
            valid = EA[1:T - 1] & Wm
            nopermit = EU[1:T - 1] & ~Wm
            missing = EA[1:T - 1] & ~Wm
            quiet = ~Ev & ~Wm & ~h[1:T - 1]
            for c, mask in zip(cases, (quiet, valid, nopermit, missing)):
                n = mask.sum()
                acc[m][c][k] = [(nxt & mask).sum() / max(n, 1), (hz & mask).sum() / max(n, 1), ((~nxt) & hz & mask).sum() / max(n, 1)]
            rep = w["Ye"][1:T - 1] & Ev & ~w["flag_failed"][1:T - 1]
            pa = PA[1:T - 1]
            cls_a = pa > 0.8; cls_u = pa < 0.2
            attr[m][k] = [((cls_a & EA[1:T - 1]) & rep).sum(), ((cls_u & EU[1:T - 1]) & rep).sum(), ((~cls_a & ~cls_u) & rep).sum(), rep.sum()]
            base[m].append(element_metrics(P, w))
            dl[m].append(detection_delay(P, w))
    out = dict(cases=cases, methods={})
    for m in methods:
        rec = {c: dict(flagged=ci(acc[m][c][:, 0]), hazardous_after=ci(acc[m][c][:, 1]), hazard_missed=ci(acc[m][c][:, 2])) for c in cases}
        n = np.maximum(attr[m][:, 3], 1)
        rec["attribution"] = dict(correct_authorized=ci(attr[m][:, 0] / n), correct_unauthorized=ci(attr[m][:, 1] / n), uncertain=ci(attr[m][:, 2] / n),
                                  accuracy_when_decided=ci((attr[m][:, 0] + attr[m][:, 1]) / np.maximum(attr[m][:, 3] - attr[m][:, 2], 1)))
        rec["overall"] = agg(base[m], MKEYS)
        rec["delay"] = dict(mean_delay=ci([d["mean_delay"] for d in dl[m]]), share_missed=ci([d["share_missed"] for d in dl[m]]))
        out["methods"][m] = rec
    return out


# ----------------------------------------------------------------------------------------------------------------
# E4: hybrid sensing
# ----------------------------------------------------------------------------------------------------------------
def exp_hybrid(seed, dom, n_sites, R, par, log):
    D = DOMAINS[dom]
    out = {}
    configs = [("point_only_%d" % round(100 * f), f, T_EPOCHS + 1) for f in (0.05, 0.10, 0.20)]
    configs += [("survey_only_%d" % iv, 0.0, iv) for iv in (6, 12, 24)]
    configs += [("hybrid_%d_%d" % (round(100 * f), iv), f, iv) for f in (0.05, 0.10, 0.20) for iv in (12, 24)]
    for name, frac, iv in configs:
        use_survey = True
        r = run_methods(seed, dom, "e4-" + name, n_sites, R, ["D2", "G"], par, None, sensors_budget("uniform", frac, seed, dom) if frac > 0 else None, iv,
                        kw_by_method={"D2": dict(use_survey=use_survey), "G": dict(use_survey=use_survey)})
        nsurv = T_EPOCHS // iv + 1
        cost = frac * D["N"] * D["node_cost"] + nsurv * D["survey_cost"]
        out[name] = dict(point_share=frac, survey_interval=iv, cost=float(cost), methods={m: dict(element=r[m]["element"], delay=r[m]["delay"], structure=r[m].get("structure")) for m in r})
        log("   hybrid %s" % name)
    return out


# ----------------------------------------------------------------------------------------------------------------
# E5: sensor placement
# ----------------------------------------------------------------------------------------------------------------
def exp_placement(seed, dom, n_sites, R, par, log):
    out = {}
    for frac in (0.05, 0.10, 0.20):
        out[str(frac)] = {}
        for strat in ("random", "uniform", "uncertainty", "risk_optimised"):
            r = run_methods(seed, dom, "e5-%s-%s" % (strat, frac), n_sites, R, ["D2"], par, None, sensors_budget(strat, frac, seed, dom, par))
            out[str(frac)][strat] = dict(element=r["D2"]["element"], delay=r["D2"]["delay"], structure=r["D2"].get("structure"))
        log("   placement budget %s" % frac)
    return out


# ----------------------------------------------------------------------------------------------------------------
# E6 / E7 / ablation
# ----------------------------------------------------------------------------------------------------------------
def exp_transfer(seed, dom, n_sites, R, par, log):
    methods = ["S0", "S1", "D0", "D1", "D2", "G", "ORACLE"] + (BASELINES if dom == "scaffold" else [])
    return run_methods(seed, dom, "e6", n_sites, R, methods, par, None, sensors_budget("uniform", 0.10, seed, dom))


def exp_combined(seed, dom, n_sites, R, par, log):
    out = {}
    methods = ["S1", "D0", "D2", "G", "ORACLE"]
    for name, sc in SCENARIOS.items():
        out[name] = run_methods(seed, dom, "e7-" + name, n_sites, R, methods, par, sc, sensors_budget("uniform", 0.10, seed, dom))
        log("   scenario %s" % name)
    return out


def exp_ablation(seed, dom, n_sites, R, par, log):
    variants = {"full": ("G", {}), "no_gate_selection": ("G", dict(select=False)), "no_gate": ("D2", {}), "no_permit_context": ("D0", {}), "no_dynamics": ("S1", {}),
                "no_point_sensors": ("G", dict(use_sensors=False)), "no_survey": ("G", dict(use_survey=False)), "no_health_flags": ("G", dict(health_aware=False))}
    out = {}
    for name in ("nominal", "combined"):
        sc = SCENARIOS[name]
        out[name] = {}
        for v, (m, kw) in variants.items():
            r = run_methods(seed, dom, "e8-%s-%s" % (name, v), n_sites, R, [m], par, sc, sensors_budget("uniform", 0.10, seed, dom), kw_by_method={m: kw})
            out[name][v] = r[m]
        log("   ablation %s" % name)
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
    ns, R = (4, 20) if args.quick else (24, 60)
    res = {"meta": dict(software="SubSurface_v6.py", version=VERSION, command=" ".join(["python"] + sys.argv), seed=seed, python=sys.version.split()[0], numpy=np.__version__, quick=bool(args.quick),
                        n_test_sites=ns, worlds_per_site=R, epochs=T_EPOCHS, survey_interval=DELTA,
                        depends_on="SubSurface_MC.py (sensor capability of the utility domain; unchanged)"),
           "domains": DOMAINS, "scenarios": SCENARIOS, "thresholds": dict(tau_release=TAU_A, tau_escalate=TAU_P, tau_structure=TAU_S, gate_delta=GATE_DELTA, kappa_decay=KAPPA),
           "gate_members": [n for n, _ in GATE_MEMBERS], "method_label": METHOD_LABEL}
    log("1/9 self-tests")
    res["selftests"] = selftests_v6(seed)
    pars = {}
    for dom in DOMAINS:
        pars[dom] = calibrate(seed, dom, 4 if args.quick else 10, 20 if args.quick else 40)
    res["calibration"] = pars
    for key, fn, doms in (("dynamic_vs_static", exp_dynamic_static, DOMAINS), ("permits", exp_permits, DOMAINS), ("hybrid", exp_hybrid, DOMAINS), ("placement", exp_placement, DOMAINS),
                          ("transfer", exp_transfer, DOMAINS), ("combined_failures", exp_combined, DOMAINS), ("ablation", exp_ablation, DOMAINS)):
        log("%s" % key)
        res[key] = {dom: fn(seed, dom, ns, R, pars[dom], log) for dom in doms}
    log("regime map")
    res["regime"] = exp_regime(seed, max(4, ns // 2), max(20, R // 2), log)
    res["meta"]["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(args.out, "results_v6.json"), "w", encoding="utf-8") as fh:
        json.dump(S.jsonable(res), fh, indent=1)
    log("results_v6.json written (%.1f s)" % (time.time() - t0))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--reproduce", action="store_true")
    ap.add_argument("--out", default="results_v6")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.demo:
        r = selftests_v6(a.seed)
        print("%d of %d self-tests passed" % (sum(x["passed"] for x in r), len(r)))
        sys.exit(0 if all(x["passed"] for x in r) else 1)
    if a.reproduce:
        reproduce(a)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
