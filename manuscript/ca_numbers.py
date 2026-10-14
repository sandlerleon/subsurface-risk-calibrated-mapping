# -*- coding: utf-8 -*-
"""Numbers, abstract and highlights of the change-aware manuscript (exec'd inside the builders' namespaces: needs R5, R6, W6)."""
import numpy as np

UT, SF = "utility", "scaffold"
DOMN = {UT: "underground utilities", SF: "industrial scaffolding"}
G6 = W6.CGRID


def m6(x, d=1, s=100.0):
    return "n/a" if x is None or x[0] is None else ("%." + str(d) + "f") % (s * x[0])


def ci6(x, d=1, s=100.0):
    if x is None or x[0] is None:
        return "n/a"
    h = "" if x[1] is None else " ± " + ("%." + str(d) + "f") % (s * x[1])
    return ("%." + str(d) + "f") % (s * x[0]) + h


def v6(x):
    return np.nan if x is None or x[0] is None else x[0]


def cvx(rec, key, c):
    """risk at released coverage c from a curve record"""
    j = int(np.argmin(np.abs(G6 - c)))
    return rec[key][j]


def lvl(dom):
    """curve key and label of the decision level used for matched-coverage comparisons"""
    return ("s_curve", "structure") if dom == SF else ("curve", "element")


def ratio_at(dom, a, b, c, exp="transfer"):
    key, _ = lvl(dom)
    src = R6[exp][dom]["methods"] if exp == "dynamic_vs_static" else R6[exp][dom]
    ra, rb = v6(cvx(src[a], key, c)), v6(cvx(src[b], key, c))
    return ra / rb, ra, rb


def ehv(dom, exp, m, k, d=1, s=100.0, sub=None):
    rec = R6[exp][dom][m] if sub is None else R6[exp][dom][sub][m]
    return m6(rec["element"][k], d, s)


def stv(dom, exp, m, k, d=1, s=100.0, sub=None):
    rec = R6[exp][dom][m] if sub is None else R6[exp][dom][sub][m]
    return m6(rec["structure"][k], d, s)


# ---- headline numbers used in the abstract and the conclusions -----------------------------------------------------
H1_UT = ratio_at(UT, "S1", "D2", 0.30)
H1_SF = ratio_at(SF, "S1", "D2", 0.30)
PERM = {d: R6["permits"][d]["methods"] for d in (UT, SF)}
SUPP_MISS = {d: PERM[d]["D1"]["change_valid_permit"]["hazard_missed"] for d in (UT, SF)}
CTX_MISS = {d: PERM[d]["D2"]["change_valid_permit"]["hazard_missed"] for d in (UT, SF)}
NOW_MISS = {d: PERM[d]["D0"]["change_valid_permit"]["hazard_missed"] for d in (UT, SF)}
REGIME = {k: v["S0"]["unsafe_prob"][0] / max(v["D2"]["unsafe_prob"][0], 1e-9) for k, v in R6["regime"].items()}

ABSTRACT_TEXT = (
    "Monitoring must support safety decisions while the monitored structure changes between observations, instruments fail, work records are incomplete and models are imperfect. "
    "This simulation study proposes change-aware reliability-gated sensor fusion and evaluates it on excavation clearance above buried utilities and on continued use of an industrial scaffold. "
    "A hidden-Markov estimator tracks a latent hazard state from asynchronous point sensors, periodic surveys and work records; authorization is contextual evidence, never proof of safety; "
    "a decision is released only if the highest hazard probability over the model alternatives that the surveys have not rejected meets a risk criterion, which is conditional on the assumed alternatives and not a guarantee. "
    "At matched decision coverage, dynamic estimation lowered the conditional unsafe-decision risk by a factor of %.1f (utilities) and %.1f (scaffolds) relative to static-state fusion, and its predicted risk tracked the observed risk as survey age grew. "
    "Suppressing permit-matched changes left a hazardous, unflagged state after %s%% and %s%% of the changes made under a valid permit, against %s%% and %s%% when permits were used as context. "
    "Point sensors added little to periodic surveys, and risk-optimized placement was not consistently better than simple rules. "
    "The gate lowered the risk under combined failures by abstaining rather than by better inference, and no method was reliable against every failure mode. "
    "The scaffold advantage held under 16 definitions of an unsafe structure. "
"Results are conditional on the simulated environments, are not validated against field data, and the scaffold criterion is synthetic."
) % (H1_UT[0], H1_SF[0], m6(SUPP_MISS[UT], 0), m6(SUPP_MISS[SF], 0), m6(CTX_MISS[UT], 0), m6(CTX_MISS[SF], 0))

HL = [
    "Change-aware fusion tracks hazard states that evolve between observations.",
    "Work permits are used as context, not as proof that a change is safe.",
    "Suppressing permit-matched changes left many hazardous changes unflagged.",
    "A reliability gate lowers risk under mismatch mainly by abstaining.",
    "Benefits are tested on two infrastructure problems, in simulation only.",
]
for _t in HL:
    assert len(_t) <= 85, (len(_t), _t)


# ---- E8: sensitivity of the scaffold conclusions to the structural hazard definition (SubSurface_v6 2.1.0) ------------
SD = R6.get("structure_definitions")
SD_KEYS = [(cs, kb) for cs in W6.STRUCT_CRIT for kb in W6.STRUCT_K]
SD_BENCH = (0.20, 2)


def sdrec(scen, cs, kb):
    return SD[scen][W6.struct_key(cs, kb)]


def sd_risk(scen, cs, kb, m, c):
    return v6(cvx(sdrec(scen, cs, kb)["methods"][m], "s_curve", c))


def sd_ratio(scen, cs, kb, a, b, c=0.30):
    ra, rb = sd_risk(scen, cs, kb, a, c), sd_risk(scen, cs, kb, b, c)
    return ra / rb if (np.isfinite(ra) and np.isfinite(rb) and rb > 0) else np.nan


def sd_dominates(scen, cs, kb, a, b, covs=(0.1, 0.2, 0.3, 0.4, 0.5)):
    """True if method b has a lower mean risk than a at every matched coverage in covs where both are defined (and at least three are defined); None if undefined"""
    d = [(sd_risk(scen, cs, kb, a, c), sd_risk(scen, cs, kb, b, c)) for c in covs]
    d = [(x, y) for x, y in d if np.isfinite(x) and np.isfinite(y)]
    if len(d) < 3:
        return None
    return all(y < x for x, y in d)


if SD is not None:
    SDN = {}
    for _scen in ("nominal", "combined"):
        for _a in ("S1", "SSI"):
            rr = [sd_ratio(_scen, cs, kb, _a, "D2") for cs, kb in SD_KEYS]
            dom_ = [sd_dominates(_scen, cs, kb, _a, "D2") for cs, kb in SD_KEYS]
            SDN[(_scen, _a)] = dict(ratios=rr, n_def=sum(np.isfinite(x) for x in rr), n_dom=sum(1 for x in dom_ if x), n_eval=sum(1 for x in dom_ if x is not None),
                                    rmin=float(np.nanmin(rr)), rmed=float(np.nanmedian(rr)), rmax=float(np.nanmax(rr)))
    # gate under the combined failure: native thresholds, structure level
    _g = []
    for cs, kb in SD_KEYS:
        gs, ds = sdrec("combined", cs, kb)["methods"]["G"]["structure"], sdrec("combined", cs, kb)["methods"]["D2"]["structure"]
        _g.append((v6(gs["cond_risk"]), v6(ds["cond_risk"]), v6(gs["coverage"]), v6(ds["coverage"])))
    SDG = dict(n=len(_g), n_lower_cov=sum(1 for a, b, c, d in _g if c < d), n_lower_risk=sum(1 for a, b, c, d in _g if np.isfinite(a) and np.isfinite(b) and a < b),
               n_risk_def=sum(1 for a, b, c, d in _g if np.isfinite(a) and np.isfinite(b)), cov_max=max(c for a, b, c, d in _g))
    SDP = [v6(sdrec("nominal", cs, kb)["unsafe_share"]) for cs, kb in SD_KEYS]
# the abstract states that the dynamic advantage held under all 16 definitions: stop the build if the results ever say otherwise
assert SDN[("nominal", "S1")]["n_dom"] == SDN[("nominal", "S1")]["n_eval"] == 16 and SDN[("combined", "S1")]["n_dom"] == SDN[("combined", "S1")]["n_eval"] == 16, "abstract claim on E8 no longer holds"
