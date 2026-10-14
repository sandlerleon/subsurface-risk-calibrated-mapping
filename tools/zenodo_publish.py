# -*- coding: utf-8 -*-
"""Publish the two Zenodo records reserved by zenodo_reserve.py:

  software     the tagged GitHub release as a zip (MIT)
  preprint     the manuscript (docx only; no PDFs are deposited) (CC BY 4.0)

The DOIs were reserved first so that they could be written into the manuscript. The token is read from ZENODO_TOKEN and never written to disk.

    python zenodo_publish.py software|preprint [--version=1.1.0] [--ms=2] [--dry]
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ.get("ZENODO_TOKEN")
if not TOKEN:
    raise SystemExit("ZENODO_TOKEN is not set in the environment")
API = "https://zenodo.org/api"
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STATE = os.path.join("C:" + os.sep, "YouTube", "_subsurface_zenodo_state.json")
VERSION = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--version=")), "1.0.0")
MS = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--ms=")), "1")
TAG = "v" + VERSION
DRY = "--dry" in sys.argv
GITHUB = "https://github.com/sandlerleon/subsurface-risk-calibrated-mapping"
CREATORS = [{"name": "Sandler, Leon", "affiliation": "Independent Researcher", "orcid": "0009-0007-4584-808X"}]
TITLE_TUST = "Risk-Calibrated Sensor Fusion for Underground Utility Mapping: A Simulation-Based Decision-Support Framework for Excavation Safety"
TITLE_RESS = "Risk-Calibrated Sensor Fusion Under Model Uncertainty: A Simulation-Based Reliability Framework for Underground Utility Mapping"
TITLE_CA = "Change-Aware Reliability-Gated Sensor Fusion: Risk-Bounded Decisions Under Infrastructure Modifications and Model Uncertainty"
CA = int(MS) >= 6
RESS = int(MS) >= 4
TITLE_PAPER = TITLE_CA if CA else (TITLE_RESS if RESS else TITLE_TUST)
TITLE_CODE = "Risk-calibrated sensor fusion for underground utility mapping: simulation code, results, figures and manuscript"
KEYWORDS = ["digital twin", "change detection", "work-permit reconciliation", "reliability gate", "scaffolding", "reliability of decision support", "model uncertainty", "aleatory and epistemic uncertainty", "underground utility mapping", "ground-penetrating radar", "electromagnetic locator", "sensor fusion", "Bayesian filter", "probability calibration",
            "excavation safety", "Monte Carlo simulation", "unverified state", "decision support"]

JOURNAL = "Reliability Engineering &amp; System Safety" if RESS else "Tunnelling and Underground Space Technology"
if CA:
    ABOUT = """<p><strong>A simulation study. No field data are used; all parameters are assumptions, the scaffold hazard criterion is synthetic, and the reliability figures are conditional on the simulated environments.</strong> Prepared for submission to <em>%s</em> (Elsevier).
Change-aware reliability-gated sensor fusion: a hidden-Markov hazard estimator fed by asynchronous continuous point sensors, periodic surveys and work records; work-permit reconciliation that keeps authorization separate from hazard; and a gate that releases a decision only if the supremum over the model alternatives not rejected by the surveys meets a risk criterion. Evaluated on two structurally different problems (excavation clearance above buried utilities, continued use of an industrial scaffold) against static, dynamic and domain-specific baselines at matched decision coverage, under single and combined failures, with experiments on observation staleness, work-record reconciliation, hybrid sensing and sensor placement.</p>""" % JOURNAL
elif RESS:
    ABOUT = """<p><strong>A simulation study. No field data are used; all parameters are assumptions, and the reliability figures are conditional on the simulated environment.</strong> Prepared for submission to <em>%s</em> (Elsevier).
The study defines a safety failure event for excavation clearance (a segment released although a utility lies within its envelope) and the unsafe-release probability, conditional false-clearance risk and release coverage; compares fixed, sensor-quality-adjusted, expected-loss and robust release policies
for ground-penetrating radar and electromagnetic evidence with calibrated-abstention, health-aware and oracle baselines on reliability-coverage curves; separates aleatory variability from epistemic uncertainty over a parameter envelope and five structural models of the geometry;
simulates sensor-fault and common-cause combinations; and ranks failure drivers by global sensitivity analysis. A more complex lateral-tracking model is less reliable than a simpler one when a parallel utility is present.</p>""" % JOURNAL
else:
    ABOUT = """<p><strong>A simulation study. No field data are used; all parameters are assumptions.</strong> Prepared for submission to <em>%s</em> (Elsevier).
A decision layer above ground-penetrating radar (250 and 600 MHz), an electromagnetic locator and a known anchor carries the probability that a utility lies on the tracked alignment along a corridor of 5 m segments
with a Bayesian filter, and reports each segment as present, absent or unverified; unverified marks soil, utility and depth combinations whose expected detection probability is below 0.3, so that sensor silence
is never reported as clearance. A seeded Monte Carlo study compares fifteen baselines and ablations, stress cases (lateral shifts, an uncertain anchor, sensor failure, correlated evidence), probability calibration and
an excavation-clearance trial, and reports detection, calibration, location and depth accuracy and the share left unverified separately, with explicit denominators.</p>""" % JOURNAL
NEWVER_130 = """<p><strong>Version 1.3.0 / preprint version 4.</strong> Retargeted to reliability engineering: adds <code>SubSurface_v5.py</code> (17 self-tests; <code>results_v5/</code>) with the safety failure event and reliability metrics, six release policies and calibrated-abstention, health-aware and oracle baselines, reliability-coverage curves with dominance analysis,
an aleatory/epistemic decomposition over a parameter envelope and five structural models, fault and common-cause scenarios with an attribution of unsafe releases, an ablation at equal released coverage, value-of-information verification prioritisation and a global sensitivity analysis. Version 3 and earlier were prepared for a different journal. Earlier results are unchanged.</p>"""
NEWVER = """<p><strong>Version 1.2.0 / preprint version 3.</strong> Reviewer revision: adds a comparison with the closest existing approaches, a physical-plausibility section (no published detection-versus-depth dataset was reproduced), a structural-mismatch experiment (piecewise-linear geometry with bends, a parallel utility and a branch), a parameter-uncertainty envelope, uses "modelled intersections" instead of "strikes", and reduces the main-text figures to ten. The mismatch experiment shows that with a parallel utility the lateral tracker trades false alarms for false clearance. Versions 1 and 2 are superseded: version 1 contained a clearance comparison that confounded the three-state rule with its operating point (withdrawn in version 2).</p>"""
NEWVER_131 = """<p><strong>Version 1.3.1 / preprint version 5.</strong> Wording revised after a copy-editing review (American spelling), the abstract and highlights now state the released coverage at which the robust and nominal policies are compared, the estimation of the Sobol indices from the surrogate is documented, and the title-page submission sentence is removed. No code and no result changed; results_v5.json was reproduced exactly from a fresh clone of v1.3.0.</p>"""
NEWVER_200 = """<p><strong>Version 2.0.0 / preprint version 6.</strong> Adds SubSurface_v6.py (12 self-tests; results_v6/): change-aware reliability-gated sensor fusion, with a dynamic hazard estimator, work-record reconciliation, asynchronous evidence, a reliability gate with model-validity selection, sensor-allocation strategies, and a synthetic scaffold benchmark as a second application. SubSurface_MC.py, SubSurface_v4.py and SubSurface_v5.py and their results are unchanged.</p>"""
NEWVER_210 = """<p><strong>Version 2.1.0 / preprint version 7.</strong> Corrections and one added experiment after a submission-readiness review: SubSurface_v6.py now has 14 self-tests and records the number of released decisions behind every conditional risk; a new experiment (E8) tests whether the scaffold conclusions depend on the definition of an unsafe structure (16 definitions); the manuscript replaces unresolved calculation placeholders by the computed numbers, shows coverage below 1% to one decimal, and states in Section 4.4 that the reliability gate bounds a modeled, assumption-conditional hazard probability and not a real failure probability. Every earlier result is unchanged. Simulation only; no field data.</p>"""
NEWVER = NEWVER_210 if VERSION == "2.1.0" else NEWVER_200 if VERSION == "2.0.0" else NEWVER_131 if VERSION == "1.3.1" else (NEWVER_130 if VERSION == "1.3.0" else NEWVER)
DESC_CODE = ABOUT + """<p>Contents: the simulation (<code>SubSurface_MC.py</code>, one file with 27 self-tests), the figure script, configuration, results.json, a manifest with SHA-256 hashes, the reference harvest, and the manuscript, cover letter and highlights builders.
Manuscript preprint: <a href="https://doi.org/{PP}">{PP}</a>.</p>"""
DESC_PAPER = ABOUT + """<p>Code and results: <a href="%s">%s</a>, archived at <a href="https://doi.org/{SW}">{SW}</a>.</p>""" % (GITHUB, GITHUB)


def req(method, url, data=None, headers=None, raw=None):
    h = {"Authorization": "Bearer " + TOKEN}
    if headers:
        h.update(headers)
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    if data is not None and raw is None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=600) as resp:
            t = resp.read()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        raise SystemExit("%s %s -> %s\n%s" % (method, url, e.code, e.read().decode()[:800]))


def clear_inherited(d):
    for f in req("GET", "%s/deposit/depositions/%s/files" % (API, d["id"])):
        req("DELETE", "%s/deposit/depositions/%s/files/%s" % (API, d["id"], f["id"]))


def upload(bucket, path, name):
    with open(path, "rb") as fh:
        req("PUT", "%s/%s" % (bucket, urllib.parse.quote(name)), raw=fh.read(), headers={"Content-Type": "application/octet-stream"})
    print("   uploaded %-62s %9.1f kB" % (name, os.path.getsize(path) / 1024.0))


def finish(did, meta):
    req("PUT", "%s/deposit/depositions/%s" % (API, did), data={"metadata": meta})
    print("   metadata written")
    if DRY:
        print("   DRY RUN - draft %s left unpublished" % did)
        return
    pub = req("POST", "%s/deposit/depositions/%s/actions/publish" % (API, did))
    rec = req("GET", "%s/records/%s" % (API, pub["id"]))
    print("   PUBLISHED  DOI %s  concept %s" % (rec.get("doi"), rec.get("conceptdoi")))


def software():
    st = json.load(open(STATE))
    d = st["software_" + VERSION] if "software_" + VERSION in st else st["software"]
    pp = st["publication_v" + MS] if "publication_v" + MS in st else st["publication"]
    tmp = os.path.join(os.environ.get("TEMP", "."), "subsurface-risk-calibrated-mapping-%s.zip" % VERSION)
    subprocess.check_call(["git", "-C", REPO, "archive", "--format=zip", "--prefix=subsurface-risk-calibrated-mapping-%s/" % VERSION, "-o", tmp, TAG])
    print("=== software draft %s (reserved DOI %s)" % (d["id"], d["doi"]))
    clear_inherited(d)
    upload(d["bucket"], tmp, os.path.basename(tmp))
    meta = {"title": TITLE_CODE, "upload_type": "software", "description": (NEWVER if VERSION != "1.0.0" else "") + DESC_CODE.replace("{PP}", pp["doi"]),
            "creators": CREATORS, "keywords": KEYWORDS, "access_right": "open", "license": "mit-license", "version": VERSION, "language": "eng",
            "prereserve_doi": {"doi": d["doi"]},
            "related_identifiers": [{"identifier": GITHUB + "/tree/" + TAG, "relation": "isSupplementTo", "scheme": "url"},
                                    {"identifier": pp["doi"], "relation": "isSupplementTo", "scheme": "doi"}]}
    finish(d["id"], meta)


def preprint():
    st = json.load(open(STATE))
    d = st["publication_v" + MS] if "publication_v" + MS in st else st["publication"]
    sw = st["software_" + VERSION] if "software_" + VERSION in st else st["software"]
    print("=== preprint draft %s (reserved DOI %s)" % (d["id"], d["doi"]))
    clear_inherited(d)
    for name in (("Manuscript_CA.docx", "Supplementary_Material_CA.docx") if CA else ("Manuscript_RESS.docx", "Supplementary_Material_RESS.docx") if RESS else ("Manuscript_TUST.docx", "Supplementary_Material_TUST.docx")):
        upload(d["bucket"], os.path.join(REPO, "manuscript", name), name)
    meta = {"title": TITLE_PAPER, "upload_type": "publication", "publication_type": "preprint",
            "description": (NEWVER if MS != "1" else "") + DESC_PAPER.replace("{SW}", sw["doi"]), "creators": CREATORS, "keywords": KEYWORDS, "access_right": "open",
            "license": "cc-by-4.0", "version": MS, "language": "eng", "prereserve_doi": {"doi": d["doi"]},
            "related_identifiers": [{"identifier": sw["doi"], "relation": "isSupplementedBy", "scheme": "doi"},
                                    {"identifier": GITHUB, "relation": "isSupplementedBy", "scheme": "url"}]}
    finish(d["id"], meta)


if __name__ == "__main__":
    what = [a for a in sys.argv[1:] if not a.startswith("--")]
    if what == ["software"]:
        software()
    elif what == ["preprint"]:
        preprint()
    else:
        raise SystemExit("usage: zenodo_publish.py software|preprint [--version=] [--dry]")
