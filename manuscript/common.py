# -*- coding: utf-8 -*-
"""Shared pieces for the manuscript, highlights and cover-letter builders: results, DOIs, reference list and citation helpers."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
R = json.load(open(os.path.join(ROOT, "results", "results.json"), encoding="utf-8"))
ZEN = json.load(open(os.path.join("C:" + os.sep, "YouTube", "_subsurface_zenodo_state.json")))
SW = (ZEN.get("software_1.2.0") or ZEN.get("software_1.1.0") or ZEN["software"])["doi"]
PP = (ZEN.get("publication_v3") or ZEN.get("publication_v2") or ZEN["publication"])["doi"]
SW_V11, PP_V2 = ZEN["software_1.1.0"]["doi"], ZEN["publication_v2"]["doi"]
SW_V1, PP_V1 = ZEN["software"]["doi"], ZEN["publication"]["doi"]
SW_CONCEPT, PP_CONCEPT = ZEN["software"]["concept_doi"], ZEN["publication"]["concept_doi"]
REPO = "https://github.com/sandlerleon/subsurface-risk-calibrated-mapping"
RELEASE = "v1.2.0"
TITLE = "Risk-Calibrated Sensor Fusion for Underground Utility Mapping: A Simulation-Based Decision-Support Framework for Excavation Safety"
FIG = os.path.join(ROOT, "results", "figures")
FIG4 = os.path.join(ROOT, "results_v4", "figures")
R4 = json.load(open(os.path.join(ROOT, "results_v4", "results_v4.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "results_v4", "results_v4.json")) else None

# ------------------------------------------------------------------------------------------------ references
REFS = json.load(open(os.path.join(ROOT, "refs", "refs.json"), encoding="utf-8"))
BYDOI = {r["doi"].lower(): r for r in REFS}
KEYS = {
    "metje07": "10.1016/j.tust.2007.04.002", "costello07": "10.1016/j.tust.2007.06.001", "hao12": "10.1016/j.tust.2011.10.011",
    "jaw13": "10.1016/j.tust.2012.11.007", "xie22": "10.1016/j.tust.2022.104402", "lai18": "10.1016/j.ndteint.2017.04.002",
    "dou16": "10.3390/s16111827", "dou17": "10.1109/tgrs.2016.2592679", "thomas09": "10.1016/j.jappgeo.2008.07.006",
    "metje15": "10.1680/muen.14.00035", "makana20": "10.1680/jinam.17.00033", "royal10": "10.1680/muen.2010.163.1.3",
    "adebiyi25": "10.1016/j.trip.2025.101539", "asce02": "10.1061/9780784406458", "doolittle95": "10.1016/0926-9851(95)90033-0",
    "annan09": "10.1016/b978-0-444-53348-7.00001-6", "stanley02": "10.1016/s1566-2535(02)00071-4", "milis03": "10.1016/s0031-3203(02)00251-0",
    "tesf12": "10.1109/icgpr.2012.6254983", "elfes89": "10.1109/2.30720", "chow70": "10.1109/tit.1970.1054406",
    "brier50": "10.1175/1520-0493(1950)078<0001:vofeit>2.0.co;2", "murphy73": "10.1175/1520-0450(1973)012<0595:anvpot>2.0.co;2",
    "gneiting07a": "10.1198/016214506000001437", "gneiting07b": "10.1111/j.1467-9868.2007.00587.x", "niculescu05": "10.1145/1102351.1102430",
    "naeini15": "10.1609/aaai.v29i1.9602", "zadrozny02": "10.1145/775047.775151", "hand01": "10.1111/j.1751-5823.2001.tb00465.x",
    "domingos97": "10.1023/a:1007413511361", "fawcett06": "10.1016/j.patrec.2005.10.010", "saito15": "10.1371/journal.pone.0118432",
    "numpy20": "10.1038/s41586-020-2649-2", "scipy20": "10.1038/s41592-019-0686-2", "mpl07": "10.1109/mcse.2007.55",
    "efron79": "10.1214/aos/1176344552", "field07": "10.1111/j.1467-9868.2007.00593.x", "brown01": "10.1214/ss/1009213286", "clopper34": "10.1093/biomet/26.4.404",
    "howard66": "10.1109/tssc.1966.300074", "dou20": "10.1016/j.autcon.2020.103229",
}
USED = []


def rec(key):
    return BYDOI[KEYS[key].lower()]


def fix_name(n):
    return {"Wai-Lok Lai": "Lai", "Pakdaman Naeini": "Naeini", "BRIER": "Brier", "CLOPPER": "Clopper", "PEARSON": "Pearson"}.get(n, n)


def _surname(a):
    return fix_name(a[0])


def _short(key):
    r = rec(key)
    au = r["authors"]
    n = _surname(au[0]) if au else "Anon."
    if n.startswith("American Society"):
        return "ASCE", r["year"]
    if len(au) == 1:
        s = n
    elif len(au) == 2:
        s = "%s and %s" % (n, _surname(au[1]))
    else:
        s = "%s et al." % n
    return s, r["year"]


def _note(key):
    if key not in USED:
        USED.append(key)


def C(*keys):
    """parenthetical citation (Metje et al., 2007; Costello et al., 2007)"""
    parts = []
    for k in keys:
        _note(k)
        s, y = _short(k)
        parts.append("%s, %s" % (s, y))
    return "(" + "; ".join(parts) + ")"


def CN(key):
    """narrative citation: Metje et al. (2007)"""
    _note(key)
    s, y = _short(key)
    return "%s (%s)" % (s, y)


def initials(given):
    parts = re.split(r"[\s\-]+", given.strip())
    return "".join(p[0].upper() + "." for p in parts if p)


def ref_line(key):
    r = rec(key)
    names = []
    for fam, giv in r["authors"]:
        fam = fix_name(fam)
        names.append("%s, %s" % (fam, initials(giv)) if giv else fam)
    if len(names) > 1:
        au = ", ".join(names[:-1]) + ", & " + names[-1]
    else:
        au = names[0] if names else ""
    au = au.replace("American Society of Civil Engineers", "American Society of Civil Engineers (ASCE)")
    jr = r["journal"]
    vol = r["volume"]
    pg = r["pages"]
    ttl = r["title"].rstrip(".")
    if key == "brier50":
        ttl = "Verification of forecasts expressed in terms of probability"
    if key == "murphy73":
        ttl = "A new vector partition of the probability score"
    if key == "clopper34":
        ttl = "The use of confidence or fiducial limits illustrated in the case of the binomial"
    if r["type"] == "book":
        body = "%s. %s." % (ttl, "American Society of Civil Engineers, Reston, VA")
    elif key in ("annan09",):
        body = "%s, in: Jol, H.M. (Ed.), Ground Penetrating Radar: Theory and Applications. Elsevier, Amsterdam." % ttl
    elif key in ("tesf12",):
        body = "%s, in: Proceedings of the 14th International Conference on Ground Penetrating Radar (GPR 2012). IEEE." % ttl
    elif key in ("niculescu05",):
        body = "%s, in: Proceedings of the 22nd International Conference on Machine Learning (ICML '05). ACM." % ttl
    elif key in ("zadrozny02",):
        body = "%s, in: Proceedings of the 8th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. ACM." % ttl
    elif key in ("naeini15",):
        body = "%s, in: Proceedings of the AAAI Conference on Artificial Intelligence, 29(1)." % ttl
    else:
        iss = "(%s)" % r["issue"] if r["issue"] else ""
        body = "%s. *%s* %s%s%s." % (ttl, jr, vol, iss, (", " + pg) if pg else "")
    return "%s (%s). %s https://doi.org/%s" % (au, r["year"], body, r["doi"])


def reference_list():
    keys = sorted(USED, key=lambda k: (fix_name(rec(k)["authors"][0][0]) if rec(k)["authors"] else "ASCE", rec(k)["year"]))
    return [ref_line(k) for k in keys]


# ------------------------------------------------------------------------------------------------ number helpers
def pc(x, d=1):
    return ("%." + str(d) + "f") % (100.0 * x)


M = R["main"]["methods"]


def mm(method, view, key, d=1):
    return pc(M[method][view][key][0], d)


def mh(method, view, key, d=1):
    return pc(M[method][view][key][1], d)


def mci(method, view, key, d=1):
    return "%s (%s)" % (pc(M[method][view][key][0], d), pc(M[method][view][key][1], d))
