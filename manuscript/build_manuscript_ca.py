# -*- coding: utf-8 -*-
"""Build the change-aware reliability manuscript (docx).   python build_manuscript_ca.py -> out/Manuscript_CA.docx   (parts: ca_p1.py ... ca_p5.py)"""
import json
import os
import re
import sys

from docx.shared import Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import docx_helpers as H  # noqa: E402
from common_ress import *  # noqa: E402,F401,F403
import common_ress as K  # noqa: E402
import SubSurface_v5 as W5  # noqa: E402
import SubSurface_v6 as W6  # noqa: E402

TITLE = "Change-Aware Reliability-Gated Sensor Fusion: Risk-Bounded Decisions Under Infrastructure Modifications and Model Uncertainty"
H.AUTO_MATH = False
doc = H.new_document(size=11, line=1.5)
H.page_numbers_and_line_numbers(doc, line_numbers=True)
WORDS = {"body": 0}
BODY = [False]
SUPP = []
MAIN_FIGS = ("fig20_", "fig23_", "fig26_", "fig31_", "fig32_", "fig33_", "fig34_", "fig35_", "fig36_", "fig37_", "fig38_")


def FIGX(doc_, path, w, cap=None, alt=None):
    if os.path.basename(path).startswith(MAIN_FIGS):
        H.figure(doc_, path, w, cap, alt)
    else:
        SUPP.append(dict(path=path, width=w, caption=cap))


def P(text, **kw):
    if BODY[0]:
        WORDS["body"] += len(re.sub(r"[*_^{}]", "", text).split())
    return H.para(doc, text, **kw)


def HD(text, lvl=1):
    return H.heading(doc, text, lvl)


# ------------------------------------------------------------------------------------------------ static survey layer (SubSurface_v5) accessors
ST = R5["scenario_study"]
SCN = ST["scenarios"]
DEC = R5["decomposition"]
GSA = R5["gsa"]
GM = R4["geometry_mismatch"]["levels"]
PN = {"P1": "P1_fixed", "P2": "P2_quality", "P3": "P3_exp_loss", "P4": "P4_robust_theta", "P5": "P5_robust_theta_struct", "P6": "P6_robust_exp_loss", "P7": "P7_robust_swath",
      "B1": "B1_fusion_fixed", "B2": "B2_1d_framework", "B5": "B5_oracle", "RCf": "RC_fusion", "RC1": "RC_1d_blind", "RCn": "RC_nominal", "RCq": "RC_quality", "RCr": "RC_robust"}


def q(sc, pol_, key="cond_risk", d=1, scale=100.0):
    v = SCN[sc]["policies"][PN.get(pol_, pol_)][key]
    return ("%." + str(d) + "f") % (scale * v[0])


def qv(sc, pol_, key="cond_risk"):
    return SCN[sc]["policies"][PN.get(pol_, pol_)][key][0]


SM = DEC["structural_models"]
ES = {p: [DEC["by_policy"][p][m]["epistemic_share"] for m in SM] for p in DEC["by_policy"]}


# ------------------------------------------------------------------------------------------------ change-aware layer (SubSurface_v6) accessors
exec(open(os.path.join(HERE, "ca_numbers.py"), encoding="utf-8").read())
DY = R6["dynamic_vs_static"]


def E1(dom, m, k, d=1, s=100.0, level="element"):
    return m6(DY[dom]["methods"][m][level][k], d, s)


def AGE(dom, m, key, a, d=2, s=100.0):
    return m6(DY[dom]["by_age"][m][key][a], d, s)


def PE(dom, m, case, key, d=0, s=100.0):
    return m6(PERM[dom][m][case][key], d, s)


def PEA(dom, m, key, d=0, s=100.0):
    return m6(PERM[dom][m]["attribution"][key], d, s)


def HY(dom, name, k, m="D2", d=1, s=100.0, level="element"):
    rec = R6["hybrid"][dom][name]["methods"][m]
    return m6(rec[level][k], d, s)


def HYD(dom, name, k, m="D2", d=1, s=100.0):
    return m6(R6["hybrid"][dom][name]["methods"][m]["delay"][k], d, s)


def PL(dom, frac, strat, k, d=2, s=100.0):
    return m6(R6["placement"][dom][frac][strat]["element"][k], d, s)


def PLD(dom, frac, strat, k, d=0, s=100.0):
    return m6(R6["placement"][dom][frac][strat]["delay"][k], d, s)


def TR(dom, m, k, d=1, s=100.0, level=None):
    rec = R6["transfer"][dom][m]
    level = level or ("structure" if dom == SF else "element")
    return m6(rec[level][k], d, s)


def CB(dom, sc, m, k, d=1, s=100.0, level=None):
    rec = R6["combined_failures"][dom][sc][m]
    level = level or ("structure" if dom == SF else "element")
    return m6(rec[level][k], d, s)


def CBr(dom, sc, a, b, c):
    """risk of method a at the coverage of method b (matched-coverage comparison) in a scenario; returns (risk_a_at_cov_b, cov_b)"""
    key, _ = lvl(dom)
    recb = R6["combined_failures"][dom][sc][b]
    covb = v6(recb["structure"]["coverage"] if dom == SF else recb["element"]["coverage"])
    j = int(np.argmin(np.abs(G6 - max(covb, G6[0]))))
    return v6(R6["combined_failures"][dom][sc][a][key][j]), covb


def AB(dom, sc, var, k, d=1, s=100.0, level=None):
    rec = R6["ablation"][dom][sc][var]
    level = level or ("structure" if dom == SF else "element")
    return m6(rec[level][k], d, s)


for _part in ("ca_p1.py", "ca_p2.py", "ca_p3.py", "ca_p4.py", "ca_p5.py"):
    try:
        exec(compile(open(os.path.join(HERE, _part), encoding="utf-8").read(), _part, "exec"))
    except Exception:
        print("ERROR in", _part)
        raise
