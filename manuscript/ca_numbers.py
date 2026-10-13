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
    "Infrastructure monitoring must support safety decisions while the monitored structure changes between observations, instruments fail, work records are incomplete and models are imperfect. "
    "This simulation study proposes change-aware reliability-gated sensor fusion and evaluates it on two structurally different problems: excavation clearance above buried utilities and continued use of an industrial scaffold. "
    "A hidden-Markov estimator tracks a latent hazard state from asynchronous continuous point sensors, periodic surveys and work records; authorization is treated as contextual evidence and never as proof of safety; "
    "and a decision is released only if the highest hazard probability over model alternatives that the surveys have not rejected meets a risk criterion. "
    "At matched decision coverage, dynamic estimation lowered the conditional unsafe-decision risk by a factor of %.1f (utilities) and %.1f (scaffolds) relative to static-state fusion, and the estimator’s predicted risk tracked the observed risk as the age of the last survey grew. "
    "Suppressing permit-matched changes left a hazardous, unflagged state after %s%% and %s%% of the changes made under a valid permit, against %s%% and %s%% when permits were used as context. "
    "Continuous point sensors added little to periodic surveys and risk-optimized placement was not consistently better than simple rules. "
    "The reliability gate lowered the risk under combined failures, but by abstaining rather than by better inference, and no method was reliable against every failure mode. "
    "All results are conditional on the simulated environments and have not been validated against field data; the scaffold hazard criterion is synthetic."
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
