# -*- coding: utf-8 -*-
"""Publish the two Zenodo records reserved by zenodo_reserve.py:

  software     the tagged GitHub release as a zip (MIT)
  preprint     the manuscript (docx only; no PDFs are deposited) (CC BY 4.0)

The DOIs were reserved first so that they could be written into the manuscript. The token is read from ZENODO_TOKEN and never written to disk.

    python zenodo_publish.py software|preprint [--version=1.0.0] [--dry]
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
TAG = "v" + VERSION
DRY = "--dry" in sys.argv
GITHUB = "https://github.com/sandlerleon/subsurface-risk-calibrated-mapping"
CREATORS = [{"name": "Sandler, Leon", "affiliation": "Independent Researcher", "orcid": "0009-0007-4584-808X"}]
TITLE_PAPER = "Risk-Calibrated Sensor Fusion for Underground Utility Mapping: A Simulation-Based Decision-Support Framework for Excavation Safety"
TITLE_CODE = "Risk-calibrated sensor fusion for underground utility mapping: simulation code, results, figures and manuscript"
KEYWORDS = ["underground utility mapping", "ground-penetrating radar", "electromagnetic locator", "sensor fusion", "Bayesian filter", "probability calibration",
            "excavation safety", "Monte Carlo simulation", "unverified state", "decision support"]

ABOUT = """<p><strong>A simulation study. No field data are used; all parameters are assumptions.</strong> Prepared for submission to <em>Tunnelling and Underground Space Technology</em> (Elsevier).
A decision layer above ground-penetrating radar (250 and 600 MHz), an electromagnetic locator and a known anchor carries the probability that a utility lies on the tracked alignment along a corridor of 5 m segments
with a Bayesian filter, and reports each segment as present, absent or unverified; unverified marks soil, utility and depth combinations whose expected detection probability is below 0.3, so that sensor silence
is never reported as clearance. A seeded Monte Carlo study compares fifteen baselines and ablations, stress cases (lateral shifts, an uncertain anchor, sensor failure, correlated evidence), probability calibration and
an excavation-clearance trial, and reports detection, calibration, location and depth accuracy and the share left unverified separately, with explicit denominators.</p>"""
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
    d = st["software"]
    tmp = os.path.join(os.environ.get("TEMP", "."), "subsurface-risk-calibrated-mapping-%s.zip" % VERSION)
    subprocess.check_call(["git", "-C", REPO, "archive", "--format=zip", "--prefix=subsurface-risk-calibrated-mapping-%s/" % VERSION, "-o", tmp, TAG])
    print("=== software draft %s (reserved DOI %s)" % (d["id"], d["doi"]))
    clear_inherited(d)
    upload(d["bucket"], tmp, os.path.basename(tmp))
    meta = {"title": TITLE_CODE, "upload_type": "software", "description": DESC_CODE.replace("{PP}", st["publication"]["doi"]),
            "creators": CREATORS, "keywords": KEYWORDS, "access_right": "open", "license": "mit-license", "version": VERSION, "language": "eng",
            "prereserve_doi": {"doi": d["doi"]},
            "related_identifiers": [{"identifier": GITHUB + "/tree/" + TAG, "relation": "isSupplementTo", "scheme": "url"},
                                    {"identifier": st["publication"]["doi"], "relation": "isSupplementTo", "scheme": "doi"}]}
    finish(d["id"], meta)


def preprint():
    st = json.load(open(STATE))
    d = st["publication"]
    print("=== preprint draft %s (reserved DOI %s)" % (d["id"], d["doi"]))
    clear_inherited(d)
    for name in ("Manuscript_TUST.docx",):
        upload(d["bucket"], os.path.join(REPO, "manuscript", name), name)
    meta = {"title": TITLE_PAPER, "upload_type": "publication", "publication_type": "preprint",
            "description": DESC_PAPER.replace("{SW}", st["software"]["doi"]), "creators": CREATORS, "keywords": KEYWORDS, "access_right": "open",
            "license": "cc-by-4.0", "version": "1", "language": "eng", "prereserve_doi": {"doi": d["doi"]},
            "related_identifiers": [{"identifier": st["software"]["doi"], "relation": "isSupplementedBy", "scheme": "doi"},
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
