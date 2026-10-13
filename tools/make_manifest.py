# -*- coding: utf-8 -*-
"""Write results/manifest.json, results_v4/manifest.json and results_v5/manifest.json: SHA-256 and size of every file that the paper's numbers and figures depend on.   python tools/make_manifest.py"""
import hashlib
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def manifest(files, out):
    d = {}
    for f in files:
        p = os.path.join(ROOT, f)
        d[f] = {"sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "bytes": os.path.getsize(p)}
    json.dump(d, open(os.path.join(ROOT, out), "w"), indent=1)
    print("%s: %d files" % (out, len(d)))


v1 = ["SubSurface_MC.py", "figure_generation.py", "requirements.txt", "tests/test_subsurface.py", "results/config.json", "results/results.json"]
v1 += sorted("results/figures/" + f for f in os.listdir(os.path.join(ROOT, "results", "figures")) if f.endswith(".png"))
manifest(v1, "results/manifest.json")
if os.path.exists(os.path.join(ROOT, "results_v4", "results_v4.json")):
    v4 = ["SubSurface_MC.py", "SubSurface_v4.py", "figure_generation_v4.py", "requirements.txt", "tests/test_subsurface.py", "results_v4/results_v4.json"]
    v4 += sorted("results_v4/figures/" + f for f in os.listdir(os.path.join(ROOT, "results_v4", "figures")) if f.endswith(".png"))
    manifest(v4, "results_v4/manifest.json")
if os.path.exists(os.path.join(ROOT, "results_v5", "results_v5.json")):
    v5 = ["SubSurface_MC.py", "SubSurface_v4.py", "SubSurface_v5.py", "figure_generation_v5.py", "requirements.txt", "tests/test_subsurface.py", "results_v5/results_v5.json"]
    v5 += sorted("results_v5/figures/" + f for f in os.listdir(os.path.join(ROOT, "results_v5", "figures")) if f.endswith(".png"))
    manifest(v5, "results_v5/manifest.json")
