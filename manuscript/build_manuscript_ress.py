# -*- coding: utf-8 -*-
"""Build the RESS manuscript (docx).   python build_manuscript_ress.py -> out/Manuscript_RESS.docx   (parts: ress_partA.py, ress_partB.py)"""
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

H.AUTO_MATH = False
doc = H.new_document(size=11, line=1.5)
H.page_numbers_and_line_numbers(doc, line_numbers=True)
WORDS = {"body": 0}
BODY = [False]
SUPP = []
MAIN_FIGS = ("fig14_", "fig17_", "fig20_", "fig22_", "fig23_", "fig24_", "fig25_", "fig26_", "fig27_", "fig28_")


def FIGX(doc_, path, w, cap=None, alt=None):
    """main-text figure, or (for the supplementary set) collected for Supplementary_Material"""
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


# ------------------------------------------------------------------------------------------------ numbers
ST = R5["scenario_study"]
SCN = ST["scenarios"]
DEC = R5["decomposition"]
GSA = R5["gsa"]
SC5 = {n: {"label": SCN[n]["label"]} for n in SCN}
SC5_ORDER = [n for n, _ in W5.SCEN]
SC4 = R4["scenarios"]
GM = R4["geometry_mismatch"]["levels"]
PE = R4["parameter_envelope"]
PN = {"P1": "P1_fixed", "P2": "P2_quality", "P3": "P3_exp_loss", "P4": "P4_robust_theta", "P5": "P5_robust_theta_struct", "P6": "P6_robust_exp_loss", "P7": "P7_robust_swath",
      "B1": "B1_fusion_fixed", "B2": "B2_1d_framework", "B5": "B5_oracle", "RCf": "RC_fusion", "RC1": "RC_1d_blind", "RCn": "RC_nominal", "RCq": "RC_quality", "RCr": "RC_robust"}


def q(sc, pol_, key="cond_risk", d=1, scale=100.0):
    """point estimate in percent"""
    v = SCN[sc]["policies"][PN.get(pol_, pol_)][key]
    return ("%." + str(d) + "f") % (scale * v[0])


def qi(sc, pol_, key="cond_risk", d=1, scale=100.0):
    v = SCN[sc]["policies"][PN.get(pol_, pol_)][key]
    return "%s (%s to %s)" % tuple(("%." + str(d) + "f") % (scale * x) for x in v)


def qv(sc, pol_, key="cond_risk"):
    return SCN[sc]["policies"][PN.get(pol_, pol_)][key][0]


def sm4(sc, m, k, d=1):
    return pc(SC4[sc]["models"][m]["metrics"][k][0], d)


exec(open(os.path.join(HERE, "ress_numbers.py"), encoding="utf-8").read()) if os.path.exists(os.path.join(HERE, "ress_numbers.py")) else None
exec(compile(open(os.path.join(HERE, "ress_partA.py"), encoding="utf-8").read(), "ress_partA.py", "exec"))
for _part in ("ress_partB1.py", "ress_partB2.py", "ress_partB3.py"):
    try:
        exec(compile(open(os.path.join(HERE, _part), encoding="utf-8").read(), _part, "exec"))
    except Exception:
        print("ERROR in", _part)
        raise
